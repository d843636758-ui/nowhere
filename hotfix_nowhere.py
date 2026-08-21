#!/usr/bin/env python3
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path("/app/nowhere")
NAME = "_RADIO_QUIET_VARIANTS"

FALLBACK = '''
# Compatibility fallback:
# Some upstream revisions reference this pool from walk/radio events
# without defining it. If upstream defines it normally, this patch
# will not be applied.
_RADIO_QUIET_VARIANTS = (
    "电台的声音渐渐落到身后。",
    "收音机只剩下一点沙沙声。",
    "信号在风里淡下去。",
    "人声慢慢远了，只剩环境里的虫鸣和风声。",
)
'''


def module_uses_name(tree: ast.Module, name: str) -> bool:
    return any(
        isinstance(node, ast.Name)
        and isinstance(node.ctx, ast.Load)
        and node.id == name
        for node in ast.walk(tree)
    )


def module_binds_name(tree: ast.Module, name: str) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            if isinstance(node, ast.Assign):
                targets = node.targets
            else:
                targets = [node.target]

            for target in targets:
                for sub in ast.walk(target):
                    if isinstance(sub, ast.Name) and sub.id == name:
                        return True

        elif isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef),
        ):
            if node.name == name:
                return True

        elif isinstance(node, ast.Import):
            for alias in node.names:
                bound = alias.asname or alias.name.split(".")[0]
                if bound == name:
                    return True

        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                bound = alias.asname or alias.name
                if bound == name:
                    return True

    return False


def insertion_line(tree: ast.Module) -> int:
    """
    Insert after the module docstring and __future__ imports.

    This avoids breaking Python's requirement that __future__ imports
    must remain at the beginning of the module.
    """
    line = 0
    body = tree.body
    idx = 0

    if (
        body
        and isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Constant)
        and isinstance(body[0].value.value, str)
    ):
        line = body[0].end_lineno or body[0].lineno
        idx = 1

    while idx < len(body):
        node = body[idx]

        if (
            isinstance(node, ast.ImportFrom)
            and node.module == "__future__"
        ):
            line = node.end_lineno or node.lineno
            idx += 1
            continue

        break

    return line


def patch_file(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")

    if NAME not in text:
        return False

    tree = ast.parse(text, filename=str(path))

    # Merely mentioning it in a comment/string is not enough.
    if not module_uses_name(tree, NAME):
        return False

    # New upstream already fixed it.
    if module_binds_name(tree, NAME):
        print(
            f"[hotfix] upstream already defines {NAME}: "
            f"{path.relative_to(ROOT.parent)}"
        )
        return False

    lines = text.splitlines(keepends=True)
    at = insertion_line(tree)

    lines[at:at] = [FALLBACK]

    path.write_text(
        "".join(lines),
        encoding="utf-8",
    )

    print(
        f"[hotfix] added fallback {NAME}: "
        f"{path.relative_to(ROOT.parent)}"
    )

    return True


def main() -> None:
    if not ROOT.exists():
        raise SystemExit(
            f"Nowhere source directory not found: {ROOT}"
        )

    referenced = []
    patched = []

    for path in sorted(ROOT.rglob("*.py")):
        text = path.read_text(
            encoding="utf-8",
            errors="ignore",
        )

        if NAME not in text:
            continue

        referenced.append(path)

        if patch_file(path):
            patched.append(path)

    if not referenced:
        print(
            f"[hotfix] {NAME} is not referenced by "
            "this upstream revision; nothing to do."
        )

    elif not patched:
        print(
            f"[hotfix] {NAME} references are already "
            "satisfied upstream; nothing to do."
        )

    else:
        print(
            f"[hotfix] patched {len(patched)} module(s)."
        )


if __name__ == "__main__":
    main()
