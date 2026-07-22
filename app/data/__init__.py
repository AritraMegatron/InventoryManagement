"""Static demo datasets used by Vesper application modules."""

from app.data.outlet_candidates import (
    OUTLET_STATE_SCHEMA_VERSION,
    SOURCE_CATALOG,
    clone_default_candidates,
    create_empty_candidate,
)

__all__ = [
    'OUTLET_STATE_SCHEMA_VERSION',
    'SOURCE_CATALOG',
    'clone_default_candidates',
    'create_empty_candidate',
]
