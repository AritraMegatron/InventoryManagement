from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.data.outlet_candidates import clone_default_candidates
from app.services.ai_live_state_service import get_location_candidates
from app.services.outlet_state_service import (
    get_outlet_ai_snapshot,
    persist_outlet_ai_snapshot,
)
from app.state.demo_state import build_brand_state


def main() -> None:
    ai_chat_source = (ROOT / 'app' / 'ai_chat.py').read_text(encoding='utf-8')

    # Comments are allowed to mention why tab storage is unsafe. Runtime code
    # must not resolve it from the chat controller.
    executable_mentions = [
        line.strip()
        for line in ai_chat_source.splitlines()
        if 'app.storage.tab' in line and not line.lstrip().startswith('#')
    ]
    assert not executable_mentions, executable_mentions

    for brand_id in ('northstar_india', 'maple_mason_canada'):
        brand_state = build_brand_state(brand_id)
        candidates = clone_default_candidates(brand_id)
        first_id = next(iter(candidates))

        # Simulate the kind of raw bytes an uploaded PDF/DOCX may contain.
        candidates[first_id]['documents'][0]['content'] = b'raw-upload-bytes'
        persist_outlet_ai_snapshot(
            brand_state,
            candidates=candidates,
            decisions={first_id: 'Shortlist'},
            selected=first_id,
        )

        snapshot = get_outlet_ai_snapshot(brand_state)
        assert snapshot is not None
        assert 'documents' not in snapshot['candidates'][first_id]
        assert b'raw-upload-bytes' not in repr(snapshot).encode('utf-8')

        rows = get_location_candidates(brand_state)
        first_row = next(row for row in rows if row['candidate_id'] == first_id)
        assert first_row['management_decision'] == 'Shortlist'
        print(
            f"{brand_id}: {len(rows)} candidates · "
            f"{first_row['name']} · AI snapshot PASS"
        )

    print('AI CHAT STORAGE FIX: PASS')


if __name__ == '__main__':
    main()
