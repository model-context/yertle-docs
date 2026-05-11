"""Compare openapi.json against docs.json — what's public vs hidden vs broken.

Usage:
    python3 scripts/audit_docs.py

Prints three sections:
  - EXPOSED: in spec AND referenced by a nav entry → visible on docs.yertle.com
  - HIDDEN:  in spec but NOT referenced → backend exposes it, docs hide it
  - BROKEN:  referenced by nav but NOT in spec → renamed/removed route, will 404

Reads each MDX stub's frontmatter to extract the `openapi: <method> /path` line
and matches against the (method, path) keys of the loaded openapi.json.
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "openapi.json"
NAV = ROOT / "docs.json"
API_REF = ROOT / "api-reference"

# Matches a single frontmatter line like:  openapi: get /orgs/{org_id}/nodes
FRONTMATTER_LINE = re.compile(r"^openapi:\s*(\S+)\s+(\S+)\s*$", re.MULTILINE)


def spec_endpoints() -> set[tuple[str, str]]:
    spec = json.loads(SPEC.read_text())
    out = set()
    for path, ops in spec.get("paths", {}).items():
        for method, op in ops.items():
            if isinstance(op, dict) and method in {"get", "post", "put", "patch", "delete"}:
                out.add((method, path))
    return out


def nav_page_ids() -> list[str]:
    nav = json.loads(NAV.read_text())
    ids: list[str] = []

    def walk(node):
        if isinstance(node, list):
            for n in node:
                walk(n)
        elif isinstance(node, dict):
            for v in node.values():
                walk(v)
        elif isinstance(node, str):
            if node.startswith("api-reference/"):
                ids.append(node)

    walk(nav)
    return ids


def referenced_endpoints() -> tuple[set[tuple[str, str]], list[str]]:
    """Return (endpoints referenced via MDX frontmatter, list of nav ids missing the file)."""
    refs: set[tuple[str, str]] = set()
    missing_files: list[str] = []
    for page_id in nav_page_ids():
        mdx = ROOT / f"{page_id}.mdx"
        if not mdx.exists():
            missing_files.append(page_id)
            continue
        m = FRONTMATTER_LINE.search(mdx.read_text())
        if m:
            refs.add((m.group(1).lower(), m.group(2)))
    return refs, missing_files


def main() -> None:
    in_spec = spec_endpoints()
    in_nav, missing_files = referenced_endpoints()

    exposed = sorted(in_spec & in_nav)
    hidden = sorted(in_spec - in_nav)
    broken = sorted(in_nav - in_spec)

    def emit(title: str, rows: list[tuple[str, str]]) -> None:
        print(f"\n{title} ({len(rows)})")
        print("-" * len(title))
        for method, path in rows:
            print(f"  {method.upper():6} {path}")

    emit("EXPOSED — in spec and rendered in docs", exposed)
    emit("HIDDEN — in spec but not in docs nav", hidden)
    emit("BROKEN — in docs nav but not in spec", broken)

    if missing_files:
        print(f"\nMISSING MDX FILES ({len(missing_files)})")
        print("---------------------------")
        for f in missing_files:
            print(f"  {f}.mdx")

    print(f"\nTotals: spec={len(in_spec)}  exposed={len(exposed)}  hidden={len(hidden)}  broken={len(broken)}")


if __name__ == "__main__":
    main()
