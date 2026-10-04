"""Brand network rollups of the same daily items used by Demand & Inventory."""
from datetime import date, timedelta

from app.data.brand_catalog import CANADA_BRAND_ID, INDIA_BRAND_ID
from app.data.network_demo_data import _status
from app.services.demand_inventory_service import (
    _dataset, build_inventory_planning_data,
)
from app.services.demand_dataset_service import period_item_totals


def sync_brand_network(brand_state):
    """Derive network values without running/loading the D&I UI workflow.

    Financial field names are retained for existing consumers, but these brands use
    rolling 30-day periods (explicit metadata and UI labels), not calendar months.
    Staff, rent, ratings and margin assumptions remain synthetic network inputs.
    """
    if brand_state['brand_id'] not in (CANADA_BRAND_ID, INDIA_BRAND_ID):
        return
    for row in brand_state['network']['outlets']:
        dataset = _dataset(brand_state, row['store_id'])
        anchor = date.fromisoformat(dataset['as_of'])
        historical_revenue = round(sum(
            sum(item['daily'][str(i)] for i in range(-29, 1)) * item['price']
            for item in dataset['items']), 2)
        historical_units = sum(
            sum(item['daily'][str(i)] for i in range(-29, 1))
            for item in dataset['items'])
        historical_orders = sum(dataset['daily_orders'][str(i)] for i in range(-29, 1))
        windows = {}
        for horizon in (7, 14, 30):
            totals = period_item_totals(dataset, horizon)
            metrics = {
                'predicted_units': sum(totals.values()),
                'expected_revenue': round(sum(totals[item['product']] * item['price']
                                              for item in dataset['items']), 2),
                'forecast_orders': sum(dataset['daily_orders'][str(i)] for i in range(1, horizon + 1)),
                'start': (anchor + timedelta(days=1)).isoformat(),
                'end': (anchor + timedelta(days=horizon)).isoformat(),
            }
            if horizon in (7, 14):
                planning = build_inventory_planning_data(brand_state, row['store_id'], horizon)
                for key in ('service_level', 'at_risk_count', 'avoidable_waste', 'sales_at_risk'):
                    metrics[key] = planning[key]
            windows[str(horizon)] = metrics
        row.update(
            demand_windows=windows,
            sales_period={'start': (anchor - timedelta(days=29)).isoformat(), 'end': anchor.isoformat()},
            monthly_revenue=historical_revenue,
            monthly_item_units=historical_units,
            monthly_orders=historical_orders,
            average_ticket=round(historical_revenue / max(1, historical_orders), 2),
            next_month_revenue=windows['30']['expected_revenue'],
            growth_pct=round((windows['30']['expected_revenue'] / historical_revenue - 1) * 100, 1),
            operating_profit=round(historical_revenue * row['margin_pct'] / 100, 2),
            rent_ratio_pct=round(row['monthly_rent'] / historical_revenue * 100, 1),
            # These are projected 7-day exposures, not historical incident rates.
            stockout_pct=round(100 - windows['7']['service_level'], 1),
            waste_pct=round(100 * windows['7']['avoidable_waste'] /
                            max(1, windows['7']['expected_revenue']), 1),
        )
        row['status'] = _status(row['age_months'], row['margin_pct'], row['growth_pct'])
    brand_state['network']['periods'] = {
        'revenue': 'Last 30 days, including as-of date',
        'forecast': 'Next 30 days, starting after as-of date',
        'inventory_risk': 'Next 7 days; item safety stock deducted',
        'waste_pct': '7-day avoidable waste value / 7-day forecast revenue',
        'stockout_pct': '100 minus 7-day projected service level',
        'as_of': brand_state['demand_dataset_v1']['as_of'],
    }
