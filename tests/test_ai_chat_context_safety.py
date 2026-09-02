from __future__ import annotations

import ast
from pathlib import Path


AI_CHAT_PATH = Path(__file__).resolve().parents[1] / 'app' / 'ai_chat.py'


def _tree() -> ast.Module:
    return ast.parse(AI_CHAT_PATH.read_text(encoding='utf-8'))


def _method(tree: ast.Module, name: str) -> ast.FunctionDef | ast.AsyncFunctionDef:
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == 'AIChatController':
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and child.name == name:
                    return child
    raise AssertionError(f'AIChatController.{name} was not found')


def test_chat_does_not_spawn_detached_tasks() -> None:
    tree = _tree()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == 'create_task':
                raise AssertionError('AI chat must not use detached asyncio.create_task handlers')


def test_send_does_not_resolve_tab_storage_from_async_context() -> None:
    source = AI_CHAT_PATH.read_text(encoding='utf-8')
    send_node = _method(_tree(), 'send')
    segment = ast.get_source_segment(source, send_node) or ''
    assert 'app.storage.tab' not in segment
    assert 'self.tab_storage.get' in segment


def test_enter_and_suggestion_handlers_are_awaited_async_handlers() -> None:
    tree = _tree()
    assert isinstance(_method(tree, '_handle_enter'), ast.AsyncFunctionDef)
    assert isinstance(_method(tree, 'ask_suggestion'), ast.AsyncFunctionDef)
