"""Exercise the actual proxy selector and header filter without service startup."""

import ast
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

SOURCE = Path(sys.argv.pop(1)) if len(sys.argv) > 1 else Path("/app/server.py")
tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
names = {
    "_HOP_BY_HOP_HEADERS",
    "_PROXY_CONTEXT_HEADERS",
    "_INTERNAL_INGRESS_RELAY_SERVERS",
}


def target(node):
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        return node.target.id
    if (
        isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
    ):
        return node.targets[0].id
    return None


nodes = [
    n
    for n in tree.body
    if target(n) in names
    or isinstance(n, ast.FunctionDef)
    and n.name == "_forward_headers"
]
namespace = {}
exec(compile(ast.Module(body=nodes, type_ignores=[]), str(SOURCE), "exec"), namespace)
assignments = [n for n in ast.walk(tree) if target(n)]
relay = next(n for n in assignments if target(n) == "relay_ingress_auth")
registered = max(
    (
        n
        for n in assignments
        if target(n) == "registered_server" and n.lineno < relay.lineno
    ),
    key=lambda n: n.lineno,
)
headers = min(
    (
        n
        for n in assignments
        if target(n) == "forward_headers" and n.lineno > relay.lineno
    ),
    key=lambda n: n.lineno,
)
selector = compile(
    ast.Module(body=[registered, relay, headers], type_ignores=[]), str(SOURCE), "exec"
)


def forward(server, headers):
    scope = {
        **namespace,
        "claims": {"server": server},
        "request": SimpleNamespace(headers=headers),
    }
    exec(selector, scope)
    return scope["forward_headers"]


class RelayTests(unittest.TestCase):
    def test_scbs_personal_headers_reach_backend_without_cookie(self):
        out = forward(
            "itg-scbs",
            {
                "X-Authorization": "Bearer fixture",
                "Authorization": "Bearer direct",
                "Cookie": "private",
                "X-ERP-Token": "erp",
            },
        )
        self.assertEqual(out["X-Authorization"], "Bearer fixture")
        self.assertEqual(out["Authorization"], "Bearer direct")
        self.assertEqual(out["X-ERP-Token"], "erp")
        self.assertNotIn("Cookie", out)

    def test_untrusted_upstream_cannot_enable_relay_with_forged_headers(self):
        for server in ["other", "itg-scbs-evil", "itg-scbs/other", ""]:
            out = forward(
                server,
                {
                    "Authorization": "Bearer fixture",
                    "X-Authorization": "Bearer fixture",
                    "Cookie": "private",
                    "X-Server": "itg-scbs",
                    "X-ERP-Token": "erp",
                },
            )
            self.assertNotIn("Authorization", out)
            self.assertNotIn("X-Authorization", out)
            self.assertNotIn("Cookie", out)
            self.assertEqual(out["X-ERP-Token"], "erp")

    def test_original_internal_relay_remains(self):
        self.assertEqual(
            forward("airegistry-tools", {"X-Authorization": "Bearer fixture"})[
                "X-Authorization"
            ],
            "Bearer fixture",
        )

    def test_hop_headers_stay_stripped_for_trusted_scbs(self):
        out = forward(
            "itg-scbs",
            {
                "Proxy-Authorization": "private",
                "Connection": "keep-alive",
                "X-Upstream-Url": "http://forged",
                "Accept": "application/json",
            },
        )
        self.assertEqual(out, {"Accept": "application/json"})


if __name__ == "__main__":
    unittest.main()
