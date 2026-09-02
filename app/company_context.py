from __future__ import annotations


# Page-level guidance is intentionally static. Company/brand facts are not kept
# here anymore; Ask AI receives a fresh read-only live-state snapshot for every
# question from app.services.ai_live_state_service.


PAGE_CONTEXTS = {
    'command_center': """
The user is currently viewing the Command Center. Focus on executive KPIs,
what changed, financial impact, pending decisions, and concise next actions.
""",
    'demand_inventory': """
The user is currently viewing Demand & Inventory. Focus on demand forecasts,
stock availability, ingredient constraints, stockout exposure, transfers,
procurement, service level, and waste reduction.
""",
    'outlet_intelligence': """
The user is currently viewing Outlet Intelligence. Focus on candidate-site
sales potential, rent, contribution margin, payback, cannibalization,
competitive intensity, location evidence, and recommended store format.
""",
    'network_intelligence': """
The user is currently viewing Network Intelligence. Focus on existing-outlet
revenue, profitability, staffing productivity, growth, rent burden, waste,
stockouts, and recovery opportunities.
""",
    'product_innovation': """
The user is currently viewing Product Innovation. Help interpret market
signals, compare product concepts, assess ingredient reuse, pricing, margin,
complexity, regional fit, cannibalization, and design controlled pilots.
""",
}
