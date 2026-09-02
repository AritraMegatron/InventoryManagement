from __future__ import annotations

from typing import Any


def format_money(
    value: float,
    profile: dict[str, Any],
    *,
    compact: bool = True,
    decimals: int = 1,
) -> str:
    """Format native-currency values for Vesper UI without external locale deps."""

    symbol = profile['currency_symbol']
    code = profile['currency_code']

    if not compact:
        places = 0 if code == 'INR' else 2
        return f'{symbol}{value:,.{places}f}'

    absolute = abs(value)

    if code == 'INR':
        if absolute >= 10_000_000:
            return f'{symbol}{value / 10_000_000:.{decimals}f} Cr'
        if absolute >= 100_000:
            return f'{symbol}{value / 100_000:.{decimals}f} L'
        if absolute >= 1_000:
            return f'{symbol}{value / 1_000:.{decimals}f}K'
        return f'{symbol}{value:,.0f}'

    if absolute >= 1_000_000:
        return f'{symbol}{value / 1_000_000:.{decimals}f}M'
    if absolute >= 1_000:
        return f'{symbol}{value / 1_000:.{decimals}f}K'
    return f'{symbol}{value:,.2f}'
