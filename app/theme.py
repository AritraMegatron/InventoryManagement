from nicegui import ui

BURGUNDY = '#5A1534'
BURGUNDY_DARK = '#3B0D22'
CREAM = '#F7F3EA'
PAPER = '#FFFCF6'
INK = '#211A1E'
MUTED = '#746A70'
GOLD = '#F2B544'
GREEN = '#197A59'
RED = '#B33A3A'
BLUE = '#2A608D'

GLOBAL_CSS = f'''
:root {{
    --brand: {BURGUNDY};
    --brand-dark: {BURGUNDY_DARK};
    --cream: {CREAM};
    --paper: {PAPER};
    --ink: {INK};
    --muted: {MUTED};
    --gold: {GOLD};
    --positive: {GREEN};
    --negative: {RED};
}}

body {{
    background: var(--cream);
    color: var(--ink);
    font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}}

.q-page {{
    background:
        radial-gradient(circle at 95% 0%, rgba(242,181,68,0.10), transparent 30%),
        var(--cream);
}}

.app-header {{
    background: rgba(255, 252, 246, 0.96);
    color: var(--ink);
    border-bottom: 1px solid rgba(90, 21, 52, 0.10);
    backdrop-filter: blur(14px);
    box-shadow: none;
}}

.app-drawer {{
    background: var(--brand-dark);
    color: white;
    border-right: none !important;
}}

.brand-mark {{
    width: 38px;
    height: 38px;
    border-radius: 12px;
    background: var(--gold);
    color: var(--brand-dark);
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 900;
    letter-spacing: -0.03em;
    box-shadow: 0 8px 24px rgba(242,181,68,0.25);
}}

.nav-button {{
    width: 100%;
    min-height: 44px;
    border-radius: 12px;
    justify-content: flex-start;
    color: rgba(255,255,255,0.72);
}}

.nav-button-active {{
    background: rgba(255,255,255,0.12);
    color: white;
}}

.surface {{
    background: rgba(255, 252, 246, 0.96);
    border: 1px solid rgba(90, 21, 52, 0.09);
    border-radius: 18px;
    box-shadow: 0 12px 35px rgba(59, 13, 34, 0.055);
}}

.metric-card {{
    background: rgba(255, 252, 246, 0.98);
    border: 1px solid rgba(90, 21, 52, 0.09);
    border-radius: 16px;
    min-height: 126px;
    box-shadow: 0 10px 28px rgba(59, 13, 34, 0.045);
}}

.metric-icon {{
    width: 38px;
    height: 38px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(90, 21, 52, 0.08);
    color: var(--brand);
}}

.section-kicker {{
    color: var(--brand);
    font-size: 0.72rem;
    line-height: 1rem;
    font-weight: 800;
    letter-spacing: 0.11em;
    text-transform: uppercase;
}}

.muted {{
    color: var(--muted);
}}

.recommendation-panel {{
    background: linear-gradient(150deg, var(--brand-dark), var(--brand));
    color: white;
    border-radius: 18px;
    min-height: 100%;
    box-shadow: 0 16px 40px rgba(59, 13, 34, 0.20);
}}

.ai-badge {{
    background: rgba(242,181,68,0.18);
    color: #FFD985;
    border: 1px solid rgba(242,181,68,0.30);
    border-radius: 999px;
    padding: 5px 10px;
    font-size: 0.70rem;
    font-weight: 800;
    letter-spacing: 0.08em;
}}

.action-bar {{
    background: rgba(255, 252, 246, 0.88);
    border: 1px solid rgba(90, 21, 52, 0.09);
    border-radius: 16px;
}}

.status-pill {{
    border-radius: 999px;
    padding: 4px 9px;
    font-size: 0.73rem;
    font-weight: 700;
}}

.table-shell .q-table__top,
.table-shell .q-table__bottom {{
    background: transparent;
}}

.table-shell .q-table thead tr {{
    background: rgba(90,21,52,0.045);
}}

.table-shell .q-table th {{
    color: var(--muted);
    font-size: 0.70rem;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    font-weight: 800;
}}

.table-shell .q-table tbody td {{
    color: var(--ink);
    font-size: 0.83rem;
}}

.demo-chip {{
    background: rgba(90,21,52,0.06);
    color: var(--brand);
    border: 1px solid rgba(90,21,52,0.08);
}}

@media (max-width: 1024px) {{
    .desktop-only {{
        display: none;
    }}
}}
'''


def apply_theme() -> None:
    ui.colors(
        primary=BURGUNDY,
        secondary=GOLD,
        accent=BLUE,
        positive=GREEN,
        negative=RED,
        warning=GOLD,
        dark=BURGUNDY_DARK,
    )
    ui.add_css(GLOBAL_CSS)
    ui.add_head_html(
        '<meta name="darkreader-lock">'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
    )
