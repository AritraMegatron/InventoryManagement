"""BOM explosion, outlet ingredient stock and net procurement calculations.

Finished-item safety stock remains an item-level recommendation. Automatic
production consumes actual finished stock, with no ingredient safety buffer.
Ingredient stock changes only through a future receiving workflow, not approval.
"""
from __future__ import annotations

from decimal import Decimal, ROUND_CEILING
import hashlib
from typing import Any

from app.data.ingredient_bom import BOM_BY_BRAND, VENDORS_BY_BRAND


def _d(value: Any) -> Decimal:
    return Decimal(str(value))


def _round_quantity(value: Decimal, unit: str) -> float:
    precision = Decimal('1') if unit in {'ea', 'piece', 'set'} else Decimal('0.001')
    return float(max(Decimal(0), value).quantize(precision, rounding=ROUND_CEILING))


def production_quantity(row: dict[str, Any]) -> Decimal:
    remaining = max(Decimal(0), _d(row['forecast']) - _d(row['on_hand']))
    if row.get('production_override'):
        return max(Decimal(0), _d(row.get('action_quantity', 0)))
    if row.get('action_type') == 'Order':
        return max(Decimal(0), _d(row.get('action_quantity', 0)))
    if row.get('action_type') == 'Transfer':
        remaining = max(Decimal(0), remaining - _d(row.get('action_quantity', 0)))
    return remaining


def _requirements(brand_id: str, rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        quantity = production_quantity(row)
        # Fail explicitly if a new menu item has no BOM; never silently omit it.
        for name, per_unit, unit, vendor, cost in BOM_BY_BRAND[brand_id][row['product']]:
            item = result.setdefault(name, {
                'ingredient': name, 'unit': unit, 'vendor': vendor,
                'unit_cost': cost, 'required': Decimal(0), 'products': [],
            })
            if (item['unit'], item['vendor'], item['unit_cost']) != (unit, vendor, cost):
                raise ValueError(f'Conflicting BOM definition for {name}')
            item['required'] += quantity * _d(per_unit)
            if quantity:
                item['products'].append(row['product'])
    return result


def ensure_ingredient_stock(
    brand_state: dict[str, Any], outlet_id: str, baseline_rows: list[dict[str, Any]],
) -> dict[str, float]:
    """Seed stock once per outlet from a fixed seven-day baseline.

    Stable across navigation, forecast runs and horizon changes; reset clears it.
    """
    inventories = brand_state.setdefault('ingredient_inventory', {})
    if outlet_id not in inventories:
        requirements = _requirements(brand_state['brand_id'], baseline_rows)
        stock = {}
        for name, item in requirements.items():
            seed = int(hashlib.sha256(
                f"{brand_state['brand_id']}:{outlet_id}:{name}".encode()
            ).hexdigest()[:8], 16)
            ratio = Decimal(str((0.35, 0.65, 1.15, 0.80)[seed % 4]))
            stock[name] = _round_quantity(item['required'] * ratio, item['unit'])
        inventories[outlet_id] = stock
    return inventories[outlet_id]


def build_ingredient_rows(
    brand_state: dict[str, Any], outlet_id: str, inventory_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    stock = brand_state['ingredient_inventory'][outlet_id]
    result = []
    for name, item in sorted(_requirements(brand_state['brand_id'], inventory_rows).items()):
        required = _round_quantity(item['required'], item['unit'])
        on_hand = float(stock.get(name, 0))
        shortage = _round_quantity(_d(required) - _d(on_hand), item['unit'])
        result.append({**item, 'required': required, 'on_hand': on_hand,
                       'shortage': shortage})
    return result


def build_ingredient_purchase_lines(
    brand_state: dict[str, Any], ingredient_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    vendors = VENDORS_BY_BRAND[brand_state['brand_id']]
    details = []
    for row in ingredient_rows:
        if row['shortage'] <= 0:
            continue
        vendor = vendors[row['vendor']]
        details.append({
            'id': len(details) + 1, 'item': row['ingredient'],
            'vendor': row['vendor'], 'vendor_phone': vendor['phone'],
            'vendor_address': vendor['address'], 'quantity': row['shortage'],
            'required_quantity': row['required'], 'on_hand_quantity': row['on_hand'],
            'unit': row['unit'], 'unit_cost': row['unit_cost'],
            'cost_value': round(row['shortage'] * row['unit_cost'], 2),
        })
    return details


def build_ingredient_equivalent_rows(
    brand_state: dict[str, Any], inventory_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Translate BOTH item-chart bars through the same per-serving BOM.

    These are equivalents embedded in finished items, not raw ingredient stock.
    Procurement deliberately continues to use build_ingredient_rows instead.
    Saved order/transfer choices do not change either availability-chart bar.
    """
    totals: dict[str, dict[str, Any]] = {}
    for row in inventory_rows:
        demand = max(Decimal(0), _d(row['forecast']))
        usable = max(Decimal(0), _d(row.get(
            'usable_stock', max(0, row['on_hand'] - row['safety_stock']),
        )))
        for name, per_unit, unit, _vendor, _cost in BOM_BY_BRAND[brand_state['brand_id']][row['product']]:
            item = totals.setdefault(name, {
                'ingredient': name, 'unit': unit,
                'demand_equivalent': Decimal(0), 'usable_stock_equivalent': Decimal(0),
            })
            if item['unit'] != unit:
                raise ValueError(f'Conflicting BOM units for {name}')
            item['demand_equivalent'] += demand * _d(per_unit)
            item['usable_stock_equivalent'] += usable * _d(per_unit)
    # No purchasing round-up: these are exact BOM equivalents of integer items.
    return [
        {**item, 'demand_equivalent': float(item['demand_equivalent']),
         'usable_stock_equivalent': float(item['usable_stock_equivalent'])}
        for _, item in sorted(totals.items())
    ]
