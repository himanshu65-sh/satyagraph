import re

CUSTOM_CSS = """
<style>
    /* Hero Header Banner (Self-contained colors, never clashes with Streamlit light/dark mode) */
    .main-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        padding: 1.5rem 2rem;
        border-radius: 14px;
        border: 1px solid rgba(56, 189, 248, 0.3);
        border-left: 7px solid #38bdf8;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
        color: #f8fafc !important;
        margin-bottom: 1.4rem;
    }

    .badge-row {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin-top: 0.65rem;
    }

    .cyber-badge {
        background: rgba(56, 189, 248, 0.14);
        border: 1px solid rgba(56, 189, 248, 0.4);
        color: #7dd3fc !important;
        padding: 0.22rem 0.72rem;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.02em;
    }

    /* Verdict Banners */
    .verdict-box {
        padding: 1.2rem 1.4rem;
        border-radius: 12px;
        font-weight: 700;
        font-size: 1.15rem;
        margin-bottom: 1.1rem;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.2);
    }
    .verdict-true {
        background: linear-gradient(90deg, #064e3b 0%, #065f46 100%);
        color: #6ee7b7 !important;
        border: 1px solid #10b981;
        border-left: 6px solid #34d399;
    }
    .verdict-false {
        background: linear-gradient(90deg, #7f1d1d 0%, #991b1b 100%);
        color: #fca5a5 !important;
        border: 1px solid #ef4444;
        border-left: 6px solid #f87171;
    }
    .verdict-warn {
        background: linear-gradient(90deg, #78350f 0%, #92400e 100%);
        color: #fde68a !important;
        border: 1px solid #f59e0b;
        border-left: 6px solid #fbbf24;
    }

    /* High-Contrast Forensic Report & Explainer Cards (Self-contained dark slate card with crisp white text) */
    .report-card {
        background: #0f172a;
        border: 1px solid #334155;
        border-left: 5px solid #38bdf8;
        border-radius: 12px;
        padding: 1.15rem 1.35rem;
        margin-bottom: 1rem;
        color: #f8fafc !important;
        font-size: 0.96rem;
        line-height: 1.65;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.18);
    }
    .report-card p, .report-card li, .report-card ul {
        color: #f8fafc !important;
    }
    .report-card strong, .report-card b {
        color: #38bdf8 !important;
    }
    .report-card code {
        background: #1e293b;
        color: #7dd3fc !important;
        padding: 0.15rem 0.45rem;
        border-radius: 4px;
        font-weight: 600;
    }

    .report-card-hi {
        background: #064e3b;
        border: 1px solid #059669;
        border-left: 5px solid #34d399;
        border-radius: 12px;
        padding: 1.1rem 1.35rem;
        margin-bottom: 1rem;
        color: #ecfdf5 !important;
        font-size: 0.98rem;
        line-height: 1.65;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.18);
    }
    .report-card-hi p, .report-card-hi li {
        color: #ecfdf5 !important;
    }

    /* Evidence Source Card */
    .source-card {
        background: #1e293b;
        border: 1px solid #334155;
        border-left: 4px solid #0ea5e9;
        border-radius: 10px;
        padding: 0.75rem 1rem;
        margin-bottom: 0.55rem;
        color: #f8fafc !important;
        font-size: 0.92rem;
    }
    .source-card a {
        color: #38bdf8 !important;
        text-decoration: none;
        font-weight: 700;
    }
    .source-card a:hover {
        text-decoration: underline;
    }

    /* Agent Execution Trace Steps */
    .trace-step {
        font-family: 'JetBrains Mono', 'Consolas', monospace;
        font-size: 0.87rem;
        padding: 0.55rem 0.85rem;
        margin-bottom: 0.4rem;
        border-radius: 8px;
        background-color: #0f172a;
        color: #e2e8f0 !important;
        border-left: 3px solid #38bdf8;
        border: 1px solid #334155;
    }
</style>
"""

def render_verdict_banner(verdict: str, confidence: int) -> str:
    v_upper = verdict.upper()
    if ("TRUE" in v_upper or "AUTHENTIC" in v_upper or "LOW ANOMALY" in v_upper) and "FALSE" not in v_upper:
        css_class = "verdict-true"
    elif "FALSE" in v_upper or "DEBUNK" in v_upper or "HIGH MANIPULATION" in v_upper or "DEEPFAKE" in v_upper:
        css_class = "verdict-false"
    else:
        css_class = "verdict-warn"
    return f'<div class="verdict-box {css_class}">🛡️ VERDICT: {verdict} &nbsp;&bull;&nbsp; CONFIDENCE / RISK SCORE: {confidence}%</div>'

def format_report_html(text: str, is_hindi: bool = False) -> str:
    """Renders markdown text inside a high-contrast, self-contained forensic card."""
    if not text:
        return ""
    safe = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    safe = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", safe)
    safe = re.sub(r"`(.+?)`", r"<code>\1</code>", safe)
    lines = safe.split("\n")
    out = []
    in_list = False
    for line in lines:
        s = line.strip()
        if s.startswith("- ") or s.startswith("* "):
            if not in_list:
                out.append('<ul style="margin:0.4rem 0 0.4rem 1.2rem; padding:0;">')
                in_list = True
            out.append(f'<li style="margin-bottom:0.35rem;">{s[2:]}</li>')
        else:
            if in_list:
                out.append("</ul>")
                in_list = False
            if s:
                out.append(f'<p style="margin:0 0 0.45rem 0;">{s}</p>')
    if in_list:
        out.append("</ul>")
    card_cls = "report-card-hi" if is_hindi else "report-card"
    return f'<div class="{card_cls}">{"".join(out)}</div>'