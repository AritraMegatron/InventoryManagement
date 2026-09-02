from __future__ import annotations

from pathlib import Path
from typing import Any


DEMO_DOCUMENT_ROOT = (
    Path(__file__).resolve().parents[2]
    / 'demo_documents'
    / 'outlet_intelligence'
)


def load_demo_document(
    *,
    country_folder: str,
    document_id: str,
    name: str,
    content_type: str,
    mock_extract: str,
) -> dict[str, Any]:
    """Load one small synthetic demo document into the candidate record.

    Preloaded Outlet Intelligence documents are real files in the repository so
    they can be downloaded during a demo and, when the Vesper RAG Engine is
    enabled, sent through the same document-analysis path as user uploads.
    """

    candidate_id = str(document_id).split('-', 1)[0]
    path = DEMO_DOCUMENT_ROOT / country_folder / candidate_id / name
    if not path.is_file():
        raise FileNotFoundError(
            f'Missing Outlet Intelligence demo document: {path}'
        )

    content = path.read_bytes()
    return {
        'id': document_id,
        'name': name,
        'content_type': content_type,
        'size_bytes': len(content),
        'content': content,
        'source': 'demo',
        'demo_file': str(path.relative_to(DEMO_DOCUMENT_ROOT)),
        'mock_extract': mock_extract,
        'analysis_status': 'Preloaded demo document',
    }
