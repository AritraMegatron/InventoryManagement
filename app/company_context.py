from __future__ import annotations


COMPANY_SNAPSHOT = """
VESPER DEMO COMPANY SNAPSHOT

Business profile
- Multi-location dessert and beverage chain operating in India.
- 63 active outlets across Delhi NCR, North, West, South, East, and Central India.
- The figures below are simulated concept data used by the Vesper prototype.

Executive performance
- Current monthly revenue: ₹12.8 crore.
- Projected next-month revenue: ₹13.4 crore.
- Projected next-month growth: 4.8%.
- Current operating profit: ₹2.3 crore.
- Operating margin: 18.0%.
- Underperforming outlets: 9.
- Current revenue at risk from top operational issues: ₹4.6 lakh.

Priority actions
- Noida inventory shortage: ₹1.8 lakh sales at risk. Recommended action: approve a stock transfer.
- Indiranagar margin decline: ₹1.1 lakh monthly profit at risk. Recommended action: begin an outlet recovery review.
- High-Protein Chocolate Shake: opportunity score 89/100. Recommended action: approve a six-outlet pilot.

Demand and inventory
- Demand forecasts combine historical sales with calendar, weather, local-event, and public-sentiment signals.
- The system monitors product availability, ingredient capacity, stockout risk, transfers, procurement, and avoidable waste.
- Noida currently has the most urgent inventory issue in the executive action queue.

Outlet expansion
- Sector 62, Noida: score 84/100, expected monthly sales ₹19.4 lakh, contribution margin 21%, estimated payback 17 months, low cannibalization risk.
- Golf Course Road, Gurugram: strong revenue potential but weak economics due to rent and network overlap.
- Sector V, Salt Lake: favorable weekday-led compact-store opportunity.
- Indiranagar, Bengaluru: high demand but high rent and competition; not recommended at current terms.

Network intelligence
- 63 outlets are represented in the prototype.
- Metrics include revenue, profit, next-month forecast, employees, revenue per employee, rent ratio, stockout rate, waste, and customer rating.
- Current executive focus: nine underperforming outlets and the Indiranagar recovery review.

Product innovation
- High-Protein Chocolate Shake: 89/100, 82% ingredient overlap, estimated 66% gross margin, low complexity, pilot recommendation.
- Mini Shake Flight: 86/100, 96% ingredient overlap, estimated 69% gross margin, pilot recommendation.
- Rose Falooda Sundae: 84/100, estimated 64% gross margin, pilot recommendation.
- Low-Sugar Alphonso Shake: 81/100, 88% ingredient overlap, pilot recommendation.
- Mango Cheesecake Boba Shake: 73/100, high complexity, research recommendation.
- Matcha Cold Coffee: 64/100, niche and polarizing, watch recommendation.
"""


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
