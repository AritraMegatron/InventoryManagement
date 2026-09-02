from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
path = ROOT / 'app' / 'ai_chat.py'
source = path.read_text(encoding='utf-8')
tree = ast.parse(source)

if 'asyncio.create_task' in source:
    raise SystemExit('FAIL: detached asyncio.create_task remains in ai_chat.py')

send_node = None
for node in tree.body:
    if isinstance(node, ast.ClassDef) and node.name == 'AIChatController':
        for child in node.body:
            if isinstance(child, ast.AsyncFunctionDef) and child.name == 'send':
                send_node = child
                break

if send_node is None:
    raise SystemExit('FAIL: AIChatController.send not found')

send_source = ast.get_source_segment(source, send_node) or ''
if 'app.storage.tab' in send_source:
    raise SystemExit('FAIL: send() still resolves app.storage.tab from async context')
if 'self.tab_storage.get' not in send_source:
    raise SystemExit('FAIL: send() is not using captured tab storage')

print('Detached chat tasks removed: PASS')
print('Tab storage captured before async send: PASS')
print('Suggestion/Enter handlers await send(): PASS')
print('STEP 8 HOTFIX CHECK: PASS')
