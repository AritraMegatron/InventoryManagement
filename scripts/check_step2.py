from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.data.brand_catalog import CANADA_BRAND_ID, INDIA_BRAND_ID
from app.services.auth_service import (
    authenticate_demo_account,
    get_authenticated_brand_id,
    is_authenticated,
    logout_demo_account,
)
from app.state.demo_state import get_brand_state


def main() -> None:
    storage: dict = {}

    assert not is_authenticated(storage)
    assert not authenticate_demo_account(storage, 'northstar', 'wrong-password')
    assert not is_authenticated(storage)

    assert authenticate_demo_account(storage, 'northstar', 'vesperindia')
    assert get_authenticated_brand_id(storage) == INDIA_BRAND_ID
    india = get_brand_state(storage)
    assert india['profile']['currency_code'] == 'INR'
    print(
        f"India login: PASS — {india['profile']['display_name']} | "
        f"{len(india['network']['outlets'])} outlets | INR"
    )

    logout_demo_account(storage)
    assert not is_authenticated(storage)

    assert authenticate_demo_account(storage, 'maplemason', 'vespercanada')
    assert get_authenticated_brand_id(storage) == CANADA_BRAND_ID
    canada = get_brand_state(storage)
    assert canada['profile']['currency_code'] == 'CAD'
    print(
        f"Canada login: PASS — {canada['profile']['display_name']} | "
        f"{len(canada['network']['outlets'])} outlets | CAD"
    )

    # Switching tenants must not destroy the other brand's isolated state.
    assert INDIA_BRAND_ID in storage['vesper_demo_session_v1']['brands']
    assert CANADA_BRAND_ID in storage['vesper_demo_session_v1']['brands']

    print('STEP 2 CHECK: PASS')


if __name__ == '__main__':
    main()
