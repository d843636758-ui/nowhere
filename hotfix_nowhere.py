#!/usr/bin/env python3
from __future__ import annotations

import ast
from pathlib import Path

SERVER = Path("/app/nowhere/server.py")

# 只碰这三个真正涉及移动 / 恢复旅程的 async 主流程。
TARGETS = {
    "_open_door_locked",
    "walk_impl",
    "walk_to_impl",
}

# 给这两个 MCP 工具打印完整 traceback。
TRACE_TOOLS = {
    "continue_journey",
    "walk",
}

RADIO_NAME = "_RADIO_QUIET_VARIANTS"


COMPAT = r'''
# ---- downstream compatibility shim ---------------------------------

async def _compat_await(value):
    """
    Upstream 有些 helper 可能在更新中从同步函数改成 async。
    普通值直接返回；coroutine / awaitable 自动 await。
    """
    import inspect as _inspect

    if _inspect.isawaitable(value):
        return await value

    return value


def _trace_tool(func):
    """
    FastMCP 有时只打印 'Error calling tool'。
    这里先把完整 Python traceback 打到 Zeabur 日志。
    """
    import functools as _functools
    import traceback as _traceback

    @_functools.wraps(func)
    async def _wrapped(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception:
            _traceback.print_exc()
            raise

    return _wrapped

# --------------------------------------------------------------------
'''


RADIO_FALLBACK = r'''
_RADIO_QUIET_VARIANTS = (
    "电台的声音渐渐落到身后。",
    "收音机只剩下一点沙沙声。",
    "信号在风里淡下去。",
    "人声慢慢远了，只剩环境里的虫鸣和风声。",
)
'''


def _line_starts(text: str) -> list[int]:
    starts = [0]

    for line in text.splitlines(keepends=True):
        starts.append(starts[-1] + len(line))

    return starts


def _char_col(line: str, utf8_byte_col: int) -> int:
    """
    ast 的 col_offset 是 UTF-8 byte offset。
    server.py 里有大量中文，不能直接当 Python 字符下标。
    """
    raw = line.encode("utf-8")
    return len(raw[:utf8_byte_col].decode("utf-8"))


def _span(
    text: str,
    starts: list[int],
    node: ast.AST,
) -> tuple[int, int]:

    lines = text.splitlines(keepends=True)

    start = (
        starts[node.lineno - 1]
        + _char_col(
            lines[node.lineno - 1],
            node.col_offset,
        )
    )

    end = (
        starts[node.end_lineno - 1]
        + _char_col(
            lines[node.end_lineno - 1],
            node.end_col_offset,
        )
    )

    return start, end


def _after_imports(
    text: str,
    tree: ast.Module,
) -> int:

    body = tree.body
    i = 0

    # 模块 docstring。
    if (
        body
        and isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Constant)
        and isinstance(body[0].value.value, str)
    ):
        i = 1

    # 必须保留 __future__ / imports 在前面。
    while (
        i < len(body)
        and isinstance(
            body[i],
            (ast.Import, ast.ImportFrom),
        )
    ):
        i += 1

    if i == 0:
        return 0

    starts = _line_starts(text)

    return starts[
        body[i - 1].end_lineno
    ]


def _module_defines(
    tree: ast.Module,
    name: str,
) -> bool:

    for node in tree.body:

        if isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
                ast.ClassDef,
            ),
        ):
            if node.name == name:
                return True

        if isinstance(node, ast.Assign):
            for target in node.targets:
                if (
                    isinstance(target, ast.Name)
                    and target.id == name
                ):
                    return True

        if isinstance(node, ast.AnnAssign):
            if (
                isinstance(node.target, ast.Name)
                and node.target.id == name
            ):
                return True

    return False


def _patch_radio(text: str) -> str:
    """
    兼容之前碰到的 _RADIO_QUIET_VARIANTS 缺失。

    作者已经修好 -> 不动。
    作者重构掉 -> 不动。
    仍然引用却没定义 -> 自动补。
    """

    tree = ast.parse(
        text,
        filename=str(SERVER),
    )

    used = any(
        isinstance(node, ast.Name)
        and isinstance(node.ctx, ast.Load)
        and node.id == RADIO_NAME
        for node in ast.walk(tree)
    )

    if not used:
        print(
            f"[hotfix] {RADIO_NAME}: "
            "not referenced"
        )
        return text

    if _module_defines(
        tree,
        RADIO_NAME,
    ):
        print(
            f"[hotfix] {RADIO_NAME}: "
            "already defined upstream"
        )
        return text

    pos = _after_imports(
        text,
        tree,
    )

    print(
        f"[hotfix] {RADIO_NAME}: "
        "fallback added"
    )

    return (
        text[:pos]
        + "\n"
        + RADIO_FALLBACK.strip()
        + "\n\n"
        + text[pos:]
    )


def _add_compat_block(text: str) -> str:

    tree = ast.parse(
        text,
        filename=str(SERVER),
    )

    if _module_defines(
        tree,
        "_compat_await",
    ):
        return text

    pos = _after_imports(
        text,
        tree,
    )

    return (
        text[:pos]
        + "\n"
        + COMPAT.strip()
        + "\n\n"
        + text[pos:]
    )


def _assignment_calls(
    tree: ast.Module,
) -> list[ast.Call]:
    """
    找出三个目标 async 流程中：

        result = some_function(...)

    这种调用。

    后续统一变成：

        result = await _compat_await(
            some_function(...)
        )

    如果 some_function 仍是同步函数，
    _compat_await 会直接返回，不影响行为。

    如果作者把它改成 async，
    就会自动 await。
    """

    found: list[ast.Call] = []

    class Visitor(ast.NodeVisitor):

        def __init__(self):
            self.active = False

        def visit_AsyncFunctionDef(
            self,
            node: ast.AsyncFunctionDef,
        ):

            old = self.active

            self.active = (
                node.name in TARGETS
            )

            if self.active:
                for stmt in node.body:
                    self.visit(stmt)

            elif not old:
                self.generic_visit(node)

            self.active = old

        def _take(self, value):

            if (
                not self.active
                or not isinstance(
                    value,
                    ast.Call,
                )
            ):
                return

            func = value.func

            # 已经处理过。
            if (
                isinstance(func, ast.Name)
                and func.id == "_compat_await"
            ):
                return

            # Task 本来就应该作为 task 保存，
            # 不在这里提前 await。
            if (
                isinstance(
                    func,
                    ast.Attribute,
                )
                and isinstance(
                    func.value,
                    ast.Name,
                )
                and func.value.id == "asyncio"
                and func.attr in {
                    "create_task",
                    "ensure_future",
                }
            ):
                return

            found.append(value)

        def visit_Assign(
            self,
            node: ast.Assign,
        ):

            self._take(node.value)
            self.generic_visit(node)

        def visit_AnnAssign(
            self,
            node: ast.AnnAssign,
        ):

            self._take(node.value)
            self.generic_visit(node)

    Visitor().visit(tree)

    return found


def _patch_async_boundaries(
    text: str,
) -> tuple[str, int]:

    tree = ast.parse(
        text,
        filename=str(SERVER),
    )

    starts = _line_starts(text)

    edits: list[
        tuple[int, int, str]
    ] = []

    for call in _assignment_calls(tree):

        start, end = _span(
            text,
            starts,
            call,
        )

        original = text[start:end]

        replacement = (
            "await _compat_await("
            + original
            + ")"
        )

        edits.append(
            (
                start,
                end,
                replacement,
            )
        )

    # 从文件尾巴往前替换，
    # 避免前面的 offset 被后面的修改推歪。
    for (
        start,
        end,
        replacement,
    ) in sorted(
        edits,
        reverse=True,
    ):

        text = (
            text[:start]
            + replacement
            + text[end:]
        )

    return text, len(edits)


def _add_trace_decorators(
    text: str,
) -> tuple[str, int]:

    tree = ast.parse(
        text,
        filename=str(SERVER),
    )

    lines = text.splitlines(
        keepends=True,
    )

    inserts: list[
        tuple[int, str]
    ] = []

    for node in tree.body:

        if (
            not isinstance(
                node,
                ast.AsyncFunctionDef,
            )
            or node.name
            not in TRACE_TOOLS
        ):
            continue

        def_index = (
            node.lineno - 1
        )

        nearby = "".join(
            lines[
                max(
                    0,
                    def_index - 4,
                ):
                def_index + 1
            ]
        )

        if "@_trace_tool" in nearby:
            continue

        inserts.append(
            (
                def_index,
                (
                    " "
                    * node.col_offset
                    + "@_trace_tool\n"
                ),
            )
        )

    for (
        index,
        payload,
    ) in sorted(
        inserts,
        reverse=True,
    ):

        lines.insert(
            index,
            payload,
        )

    return (
        "".join(lines),
        len(inserts),
    )


def main():

    if not SERVER.exists():
        raise SystemExit(
            f"missing: {SERVER}"
        )

    text = SERVER.read_text(
        encoding="utf-8",
    )

    # 1. 老 radio bug 兼容。
    text = _patch_radio(text)

    # 2. 加 maybe-await + traceback helper。
    text = _add_compat_block(text)

    # 3. 给核心流程加 sync/async 兼容。
    text, wrapped = (
        _patch_async_boundaries(text)
    )

    # 4. 给 walk / continue 打完整 traceback。
    text, traced = (
        _add_trace_decorators(text)
    )

    # 5. 写入前先做一次 Python 语法验证。
    compile(
        text,
        str(SERVER),
        "exec",
    )

    SERVER.write_text(
        text,
        encoding="utf-8",
    )

    print(
        "[hotfix] async compatibility: "
        f"{wrapped} assignment call(s) wrapped"
    )

    print(
        "[hotfix] traceback logging: "
        f"{traced} tool(s) decorated"
    )

    print(
        "[hotfix] syntax check passed"
    )


if __name__ == "__main__":
    main()
