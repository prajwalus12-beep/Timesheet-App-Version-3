"""
Chart formatting and ReportLab PDF export helpers for Timesheet analytics.
Fully compatible with Streamlit Community Cloud (no browser / Kaleido dependency).
"""
import io
import re
import html
import textwrap
import copy
import math
import pandas as pd
from reportlab.lib.pagesizes import A4, A3, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, PageBreak, Table, TableStyle, Image as RLImage, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.graphics.shapes import Drawing, Rect, String, Line
from reportlab.graphics.charts.piecharts import Pie
from reportlab.pdfbase.pdfmetrics import stringWidth


# ─────────────────────────────────────────────────────────────────────────────
# Project Status → Colour Mapping
# ─────────────────────────────────────────────────────────────────────────────
STATUS_COLORS = {
    'not started':        '#94A3B8',
    'awaiting info':      '#D97706',
    'at beta':            '#2DD4BF',
    'in progress':        '#22C55E',
    'in testing':         '#FFAE10',
    'complete':           '#DC2626',
    'to be deployed':     '#8B5CF6',
    'duplicate - closed': '#94A3B8',
    'ongoing':            '#3B82F6',
}
STATUS_LABELS = [
    ('In Progress',        '#22C55E'),
    ('In Testing',         '#FFAE10'),
    ('Awaiting Info',      '#D97706'),
    ('Ongoing',            '#3B82F6'),
    ('At Beta',            '#2DD4BF'),
    ('Complete',           '#DC2626'),
    ('Not Started',        '#94A3B8'),
    ('To Be Deployed',     '#8B5CF6'),
    ('Duplicate / Closed', '#94A3B8'),
]
DEFAULT_BAR_COLOR = '#64748B'

# Pastel palette for pie slices — 20 colors, cycles for larger sets
PIE_COLORS = [
    '#8dd3c7', '#ffffb3', '#bebada', '#fb8072', '#80b1d3',
    '#fdb462', '#b3de69', '#fccde5', '#d9d9d9', '#bc80bd',
    '#ccebc5', '#ffed6f', '#a6cee3', '#1f78b4', '#b2df8a',
    '#33a02c', '#fbb4ae', '#b3cde3', '#decbe4', '#e5d8bd',
]

# Maximum slices per single pie chart before splitting into multiple charts
PIE_MAX_SLICES_PER_CHART = 20

# Outside labels configuration: only label top 8 projects with at least 2% duration
PIE_LABEL_TOP_N = 8
PIE_LABEL_MIN_PCT = 2.0  # Projects below 2% or below top 8 don't get outside labels


def get_status_color_hex(status_str: str) -> str:
    """Return the hex colour for a given project status string (case-insensitive)."""
    if not status_str:
        return DEFAULT_BAR_COLOR
    return STATUS_COLORS.get(str(status_str).strip().lower(), DEFAULT_BAR_COLOR)


# ─────────────────────────────────────────────────────────────────────────────
# Bar Chart: In Progress gradient & Status Color Logic
# ─────────────────────────────────────────────────────────────────────────────

def get_in_progress_gradient_color(days: float, min_days: float, max_days: float) -> str:
    """
    Return a green hex color for 'In Progress' projects based on days:
    - Lowest shade (e.g. 0.1d) → very light soft green (#bbf7d0)
    - Medium days (e.g. 1.0d) → medium fresh green (#4ade80)
    - Highest shade (e.g. 2.0d+) → bright vibrant green (#22c55e)
    Ensures black text font (#1e293b / #000000) remains easily readable across all gradient levels.
    """
    try:
        d = max(0.0, float(days or 0))
        d_min = max(0.0, float(min_days or 0))
        d_max = max(d_min + 0.001, float(max_days or (d_min + 0.001)))
    except (ValueError, TypeError):
        return '#22c55e'

    if d_max <= d_min:
        ratio = 0.5
    else:
        ratio = max(0.0, min(1.0, (d - d_min) / (d_max - d_min)))

    if ratio <= 0.5:
        sub = ratio / 0.5
        # Stop 0 (#bbf7d0: 187, 247, 208) -> Stop 1 (#4ade80: 74, 222, 128)
        r = int(187 + sub * (74 - 187))
        g = int(247 + sub * (222 - 247))
        b = int(208 + sub * (128 - 208))
    else:
        sub = (ratio - 0.5) / 0.5
        # Stop 1 (#4ade80: 74, 222, 128) -> Stop 2 (#22c55e: 34, 197, 94)
        r = int(74 + sub * (34 - 74))
        g = int(222 + sub * (197 - 222))
        b = int(128 + sub * (94 - 128))

    return f'#{r:02x}{g:02x}{b:02x}'


def get_bar_project_color(status: str, days: float, in_prog_min: float = 0.0, in_prog_max: float = 1.0) -> str:
    """
    Determine color for a project bar:
    - If status is 'In Progress': green gradient based on relative days.
    - Otherwise: designated status color from STATUS_COLORS:
        • Awaiting Info → #D97706 (brown / amber)
        • In Testing    → #FFAE10 (orange)
        • Ongoing       → #3B82F6 (blue)
        • Complete      → #DC2626 (red)
        • At Beta       → #2DD4BF (teal)
    """
    st = str(status or '').strip().lower()
    if st == 'in progress':
        return get_in_progress_gradient_color(days, in_prog_min, in_prog_max)
    return get_status_color_hex(st)


def get_duration_gradient_color(days: float, max_days: float) -> str:
    """Fallback duration gradient helper with high-contrast text readability."""
    try:
        d = max(0.0, float(days or 0))
        m = max(1.0, float(max_days or 1))
    except (ValueError, TypeError):
        d, m = 0.0, 1.0
    ratio = min(1.0, d / m)
    r_start, g_start, b_start = 224, 242, 254  # #e0f2fe (very light sky)
    r_end,   g_end,   b_end   = 56,  189, 248  # #38bdf8 (sky-400, high black contrast)
    r = int(r_start + ratio * (r_end - r_start))
    g = int(g_start + ratio * (g_end - g_start))
    b = int(b_start + ratio * (b_end - b_start))
    return f'#{r:02x}{g:02x}{b:02x}'


def get_duration_gradient_color_rl(days: float, max_days: float):
    return colors.HexColor(get_duration_gradient_color(days, max_days))


# ─────────────────────────────────────────────────────────────────────────────
# 1. Calculation & Display Helpers
# ─────────────────────────────────────────────────────────────────────────────

def convert_hours_to_days(hours: float) -> float:
    """Convert working hours to days: 8 hours = 1 working day."""
    try:
        h = float(hours or 0)
        return h / 8.0
    except (ValueError, TypeError):
        return 0.0


def format_days_display(days: float) -> str:
    """Format day values: 3.6d, 2.7d, 1.5d, 0.5d, 1d, 4d"""
    try:
        d = float(days or 0)
    except (ValueError, TypeError):
        return "0d"
    shown = round(d, 1)
    if abs(shown - round(shown)) < 1e-9:
        return f"{int(round(shown))}d"
    return f"{shown:.1f}d"


def get_employee_initials(name: str) -> str:
    """Convert employee full name to initials: 'Prajwal Chaudhari' -> 'PC'"""
    if not name or not isinstance(name, str):
        return ""
    clean_name = name.strip()
    if not clean_name or clean_name.lower() in ('nan', 'none', 'null', '_'):
        return ""
    parts = [p for p in re.split(r'[\s\.\-_]+', clean_name) if p]
    if not parts:
        return ""
    if len(parts) == 1:
        if len(parts[0]) <= 3 and parts[0].isupper():
            return parts[0]
        return parts[0][0].upper()
    initials = "".join(p[0].upper() for p in parts if p[0].isalpha())
    return initials if initials else parts[0][:2].upper()


def format_project_employee_initials(emp_names) -> str:
    """Deduplicate and format employee initials: ['Prajwal Chaudhari', 'YT'] -> 'PC, YT'"""
    seen = set()
    initials_list = []
    for ename in emp_names:
        if not ename or pd.isna(ename):
            continue
        init = get_employee_initials(str(ename))
        if init and init not in seen:
            seen.add(init)
            initials_list.append(init)
    return ", ".join(initials_list)


def wrap_project_name_lines(name: str, width: int = 38) -> list:
    """Return wrapped lines for a project name. Never truncates with ellipsis."""
    if not name or not isinstance(name, str):
        return []
    text = str(name).strip()
    if not text:
        return []
    lines = textwrap.wrap(text, width=width, break_long_words=True, break_on_hyphens=True)
    return lines if lines else [text]


def wrap_project_name(name: str, width: int = 38, html: bool = True) -> str:
    """Wrap long project names. Uses <br> for Plotly or \n for ReportLab."""
    lines = wrap_project_name_lines(name, width=width)
    if not lines:
        return ""
    separator = "<br>" if html else "\n"
    return separator.join(lines)


def format_date_short(val) -> str:
    """Format date to '%d %b' (e.g. '24 Sep'). Returns empty string if invalid."""
    if val is None or pd.isna(val):
        return ""
    try:
        dt = pd.to_datetime(val)
        if pd.isna(dt):
            return ""
        return dt.strftime("%d %b")
    except Exception:
        return ""


def build_project_metadata_text(
    days: float,
    pct: float,
    initials_str: str = "",
    start_date_str: str = "",
    end_date_str: str = "",
    status_str: str = ""
) -> str:
    """Build hover/tooltip metadata text for a project bar/pie entry."""
    day_pct_str = f"{format_days_display(days)} ({pct:.1f}%)"
    start_disp = start_date_str if start_date_str else "—"
    end_disp = end_date_str if end_date_str else "—"
    meta_parts = [f"Start: {start_disp}", f"End: {end_disp}"]
    status_clean = str(status_str).strip() if status_str is not None else ""
    if status_clean and status_clean.lower() not in ('nan', 'none', '_', ''):
        meta_parts.append(status_clean)
    joined_meta = " | ".join(meta_parts)
    if initials_str:
        return f"{day_pct_str} — {initials_str} | {joined_meta}"
    return f"{day_pct_str} | {joined_meta}"


# ─────────────────────────────────────────────────────────────────────────────
# Bar Chart Label Positioning & Overlap Configuration
# ─────────────────────────────────────────────────────────────────────────────
BAR_OVERLAP_THRESHOLD_DAYS: float = 3.5
BAR_LABEL_OVERLAP_RATIO: float = 0.55
BAR_OUTSIDE_MARGIN_PX: float = 8.0


def calculate_bar_label_overlap(
    days: float,
    pct: float = 0.0,
    initials: str = "",
    bar_width_units: float = 100.0,
    font_size: float = 12.0,
    char_width_factor: float = 0.58,
    threshold_days: float = BAR_OVERLAP_THRESHOLD_DAYS,
    overlap_ratio: float = BAR_LABEL_OVERLAP_RATIO,
    outside_margin: float = BAR_OUTSIDE_MARGIN_PX,
) -> float:
    """
    Calculate the horizontal shift for a horizontal bar chart label.
    Labels are consistently placed cleanly outside the bar with margin (outside_margin)
    to guarantee that text labels NEVER collide or overlap with each other or the bar.
    """
    return float(outside_margin)



# ─────────────────────────────────────────────────────────────────────────────
# Pie Chart Label Formatting
# ─────────────────────────────────────────────────────────────────────────────

def clean_project_name_and_initials(project_name: str, initials_str: str) -> str:
    """Ensure initials are not duplicated if already embedded in the project name."""
    p_name = str(project_name or '').strip()
    has_initials = bool(re.search(r'(\[[A-Za-z\s,/.\-]+\]|\([A-Za-z\s,/.\-]+\))$', p_name))
    init_clean = str(initials_str or '').strip()
    if init_clean and init_clean.lower() not in ('nan', 'none', '_', '') and not has_initials:
        return f"{p_name} [{init_clean}]"
    return p_name


def format_pie_slice_label_simple(
    project_name: str,
    days: float,
    initials_str: str = "",
    wrap_width: int = 28,
    html_mode: bool = True
) -> str:
    """
    Simplified outside label for pie/donut chart slices.
    Format: "<b>Project Name [Initials]</b><br>Xd"
    Avoids duplicate initials if the name already contains them.
    Metadata (dates, status, %) are shown only in the hover tooltip.
    """
    import html as _html
    display_title = clean_project_name_and_initials(project_name, initials_str)
    d_str = format_days_display(days)
    lines = wrap_project_name_lines(display_title, width=wrap_width)
    if html_mode:
        w_name = "<br>".join(_html.escape(l) for l in lines)
        return f"<b>{w_name}</b><br>{d_str}"
    else:
        w_name = "\n".join(lines)
        return f"{w_name} {d_str}"


def format_pie_slice_label(
    project_name: str,
    days: float,
    pct: float,
    initials_str: str = "",
    start_date_str: str = "",
    end_date_str: str = "",
    status_str: str = "",
    wrap_width: int = 24,
    html_mode: bool = True
) -> str:
    """
    Simplified pie label — delegates to format_pie_slice_label_simple.
    The pct, dates and status are only shown in the hover tooltip.
    """
    return format_pie_slice_label_simple(
        project_name, days, initials_str,
        wrap_width=wrap_width, html_mode=html_mode
    )


def build_pie_connector_shapes(pie_df, total_pie_days: float, cx: float = 0.50, cy: float = 0.50) -> list:
    """Returns empty list — Plotly draws native leader lines automatically."""
    return []


# ─────────────────────────────────────────────────────────────────────────────
# Pie Chart Splitting Logic
# ─────────────────────────────────────────────────────────────────────────────

def split_pie_data(pie_rows: list, max_per_chart: int = PIE_MAX_SLICES_PER_CHART) -> list:
    """
    Split pie rows into groups of max_per_chart.
    ALL projects are represented — no 'Other' grouping.
    Returns a list of lists (chunks).
    """
    if not pie_rows:
        return []
    return [pie_rows[i:i + max_per_chart] for i in range(0, len(pie_rows), max_per_chart)]


def _create_pie_plotly_fig(pie_df, total_pie_days: float, chart_index: int = 0, chart_total: int = 1):
    """Build a standalone Plotly Donut Chart figure for a chunk of pie_df."""
    import plotly.graph_objects as go
    val_col = 'days' if 'days' in pie_df.columns else ('hours' if 'hours' in pie_df.columns else pie_df.columns[1])
    num_slices = len(pie_df)
    slice_colors = [PIE_COLORS[i % len(PIE_COLORS)] for i in range(num_slices)]

    text_list = []
    if 'outside_label' in pie_df.columns:
        text_list = pie_df['outside_label'].tolist()
    else:
        for idx, (_, row) in enumerate(pie_df.iterrows()):
            d = float(row[val_col])
            pct = (d / total_pie_days * 100) if total_pie_days > 0 else 0
            # Use display_name_with_code if available, otherwise fall back to project_name
            display_name = str(row.get('display_name_with_code', row.get('project_name', '')))
            if idx < PIE_LABEL_TOP_N and pct >= PIE_LABEL_MIN_PCT:
                text_list.append(format_pie_slice_label_simple(
                    display_name, d,
                    str(row.get('initials', '')), wrap_width=22, html_mode=True
                ))
            else:
                text_list.append("")

    customdata = []
    for _, row in pie_df.iterrows():
        d = float(row[val_col])
        pct = (d / total_pie_days * 100) if total_pie_days > 0 else 0
        customdata.append([
            format_days_display(d), f"{pct:.1f}%",
            str(row.get('initials', '')), str(row.get('status', '')),
        ])

    # Use display_name_with_code for labels if available
    label_col = 'display_name_with_code' if 'display_name_with_code' in pie_df.columns else 'project_name'
    title_suffix = f" ({chart_index + 1}/{chart_total})" if chart_total > 1 else ""
    fig = go.Figure(go.Pie(
        labels=pie_df[label_col],
        values=pie_df[val_col],
        hole=0.42,
        customdata=customdata,
        text=text_list,
        textinfo='text',
        textposition='outside',
        textfont=dict(size=10.5, color='#1e293b', family='Inter, Arial, sans-serif'),
        outsidetextfont=dict(size=10.5, color='#1e293b', family='Inter, Arial, sans-serif'),
        hovertemplate=(
            '<b>%{label}</b><br>'
            '%{customdata[0]} (%{customdata[1]})<br>'
            'Employees: %{customdata[2]}<br>'
            'Status: %{customdata[3]}'
            '<extra></extra>'
        ),
        marker=dict(colors=slice_colors, line=dict(color='#ffffff', width=2)),
        showlegend=False,
        sort=False,
        direction='clockwise',
        rotation=0,
        domain=dict(x=[0.18, 0.82], y=[0.10, 0.88]),
    ))
    fig.update_layout(
        title=dict(
            text=f'<b>Total Value by Project{title_suffix}</b>',
            font=dict(size=16, color='#1e293b', family='Inter, Arial, sans-serif'),
            x=0.5, xanchor='center',
        ),
        shapes=[],
        margin=dict(l=30, r=30, t=50, b=50),
        height=720,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        autosize=True,
    )
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# 2. ReportLab PDF Generation (Server-Side, Zero Chrome/Kaleido)
# ─────────────────────────────────────────────────────────────────────────────

def _rl_hex(h: str):
    """Parse hex string to ReportLab HexColor safely."""
    try:
        return colors.HexColor(h)
    except Exception:
        return colors.grey


def _build_rl_pie_drawing(pie_df, total_pie_days: float, pw: float, drawing_h: float = 420) -> Drawing:
    """Pure ReportLab pie drawing — fallback when Kaleido is unavailable."""
    val_col = 'days' if 'days' in pie_df.columns else ('hours' if 'hours' in pie_df.columns else pie_df.columns[1])
    p_data = [max(0.001, float(v)) for v in pie_df[val_col].tolist()]
    dwg = Drawing(pw, drawing_h)
    pie_chart = Pie()
    pie_r = min(pw * 0.28, drawing_h * 0.38)
    pie_chart.x = int(pw / 2) - int(pie_r)
    pie_chart.y = int(drawing_h / 2) - int(pie_r)
    pie_chart.width = int(pie_r * 2)
    pie_chart.height = int(pie_r * 2)
    pie_chart.data = p_data
    pie_chart.innerRadiusFraction = 0.40
    pie_chart.sideLabels = 1
    pie_chart.sideLabelsOffset = 0.15
    pie_chart.simpleLabels = 0
    pie_labels = []
    for idx, (_, row) in enumerate(pie_df.iterrows()):
        d = float(row[val_col])
        pct = (d / total_pie_days * 100) if total_pie_days > 0 else 0
        # Use display_name_with_code if available, otherwise fall back to project_name
        display_name = str(row.get('display_name_with_code', row.get('project_name', '')))
        if idx < PIE_LABEL_TOP_N and pct >= PIE_LABEL_MIN_PCT:
            pie_labels.append(format_pie_slice_label_simple(
                display_name, d,
                str(row.get('initials', '')), wrap_width=18, html_mode=False
            ))
        else:
            pie_labels.append("")
    pie_chart.labels = pie_labels
    pie_palette_rl = [_rl_hex(c) for c in PIE_COLORS]
    for idx in range(len(p_data)):
        pie_chart.slices[idx].fillColor = pie_palette_rl[idx % len(pie_palette_rl)]
        pie_chart.slices[idx].strokeColor = colors.white
        pie_chart.slices[idx].strokeWidth = 1.5
        pie_chart.slices[idx].labelRadius = 1.30
        pie_chart.slices[idx].fontSize = 8.0
    dwg.add(pie_chart)
    return dwg


def clean_bar_project_title(name: str) -> str:
    """
    Remove content within square brackets from project title for bar chart display in PDF.
    E.g. 'Boarder app updates [VJ, KR]' -> 'Boarder app updates'
    """
    if not name or not isinstance(name, str):
        return ""
    cleaned = re.sub(r'\[.*?\]', '', str(name))
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned if cleaned else str(name).strip()


def get_bar_day_segments(days: float, max_per_row: float = 15.0) -> list:
    """
    Split days into rows of at most max_per_row (default 15 days).
    E.g. 30 -> [15.0, 15.0], 22 -> [15.0, 7.0], 12 -> [12.0]
    """
    try:
        d = max(0.0, float(days or 0.0))
    except (ValueError, TypeError):
        d = 0.0
    if d <= max_per_row:
        return [d]
    segments = []
    rem = d
    while rem > max_per_row:
        segments.append(max_per_row)
        rem -= max_per_row
    if rem > 0:
        segments.append(round(rem, 2))
    return segments


def compute_bar_chunk_height(bchunk, min_h: float = 340.0, pw: float = 1120.0, max_allowed_h: float = 2000.0) -> float:
    """Compute required drawing height dynamically based on project name wrapping and vertical spacing."""
    if bchunk.empty:
        return min_h
    b_margin_t, b_margin_b = 15, 40
    wrap_width = 58 if pw > 900 else 50
    # Base slot height: 38.0 per project + extra for multi-line names and split bars
    total_slots = sum(
        38.0 + (max(1, len(wrap_project_name_lines(clean_bar_project_title(str(r['project_name'])), width=wrap_width)[:3])) - 1) * 14.0
        + (len(get_bar_day_segments(float(r.get('days', 0.0) or 0.0), max_per_row=15.0)) - 1) * 16.0
        for _, r in bchunk.iterrows()
    )
    computed_h = max(min_h, total_slots + b_margin_t + b_margin_b)
    return min(computed_h, max_allowed_h)


def _build_rl_bar_drawing(
    bar_df,
    total_ref_days: float,
    pw: float,
    drawing_h: float = 550,
    use_gradient: bool = True,
    global_max_days: float = None,
    show_xaxis: bool = True,
) -> Drawing:
    """
    ReportLab horizontal bar chart with consecutive 15-day maximum bars.
    - All text font sizes set to 9.5pt.
    - Increased vertical spacing between project bars/rows.
    - All consecutive bars belonging to the same project have the exact same height/thickness.
    - If bar duration > 3.5 days, metadata is placed INSIDE the bar at approximately 60%–70% width, bold.
    - If bar duration <= 3.5 days, metadata is placed OUTSIDE the bar with clean margin.
    - Drawing height is bounded so it never overflows the PDF frame.
    - show_xaxis: when False the x-axis ticks and Days label are omitted and the bottom
      margin is collapsed to 5px so chunks flow seamlessly in pageless mode.
    """
    if bar_df.empty:
        dwg = Drawing(pw, drawing_h)
        dwg.add(String(pw / 2 - 80, drawing_h / 2, "No bar chart data available.",
                       fontSize=9.5, fontName="Helvetica", fillColor=_rl_hex('#64748b')))
        return dwg

    b_margin_l = 350 if pw > 900 else 310
    b_margin_r = 120 if pw > 900 else 100
    # Collapse bottom margin for intermediate chunks so no x-axis dead-zone appears
    b_margin_b = 40 if show_xaxis else 5
    b_margin_t = 15
    b_plot_w = pw - b_margin_l - b_margin_r
    wrap_width = 58 if pw > 900 else 50

    row_lines = []
    slot_heights = []
    for _, row in bar_df.iterrows():
        # Use display_name_with_code if available, otherwise fall back to project_name
        if 'display_name_with_code' in bar_df.columns:
            title = str(row['display_name_with_code'])
        else:
            p_code = str(row.get('project_code', '')).strip()
            p_name = clean_bar_project_title(str(row['project_name']))
            title = f"[{p_code}] {p_name}" if p_code else p_name
        lns = wrap_project_name_lines(title, width=wrap_width)[:3]
        row_lines.append(lns)
        n_text_lines = max(1, len(lns))
        d_val_row = float(row.get('days', 0.0) or 0.0)
        n_segs_row = len(get_bar_day_segments(d_val_row, max_per_row=15.0))
        # Extra slot height for split projects so consecutive bars have a clear vertical gap
        extra_split_h = (n_segs_row - 1) * 16.0 if n_segs_row > 1 else 0.0
        slot_h = 38.0 + (n_text_lines - 1) * 14.0 + extra_split_h
        slot_heights.append(slot_h)

    total_slots_h = sum(slot_heights)
    # Cap drawing to drawing_h so it always fits within the PDF page frame.
    # The scale_y factor below will compress/expand bars to fill the available space.
    b_plot_h = drawing_h - b_margin_t - b_margin_b
    actual_drawing_h = drawing_h
    dwg = Drawing(pw, actual_drawing_h)

    # X-axis ticks: use global_max_days so all pages share the same scale
    max_days = float(global_max_days) if (global_max_days is not None and global_max_days > 0) else (float(bar_df['days'].max()) if not bar_df.empty else 1.0)
    x_max = max(max_days * 2.3, max_days + 8.0) if max_days > 0 else 10.0

    if x_max <= 10.0:
        ticks = [0, 2, 4, 6, 8, 10]
    elif x_max <= 20.0:
        ticks = [0, 4, 8, 12, 16, 20]
    elif x_max <= 40.0:
        ticks = [0, 10, 20, 30, 40]
    elif x_max <= 80.0:
        ticks = [0, 20, 40, 60, 80]
    else:
        tick_step = 20
        ticks = [i * tick_step for i in range(int(x_max // tick_step) + 1)]

    for t in ticks:
        x_pos = b_margin_l + (t / x_max) * b_plot_w
        dwg.add(Line(x_pos, b_margin_b, x_pos, b_margin_b + b_plot_h,
                     strokeColor=_rl_hex('#f1f5f9'), strokeWidth=0.8))
        if show_xaxis:
            dwg.add(String(x_pos - 4, b_margin_b - 14, str(t),
                           fontSize=9.5, fontName="Helvetica", fillColor=_rl_hex('#64748b')))
    if show_xaxis:
        dwg.add(String(b_margin_l + b_plot_w / 2 - 12, b_margin_b - 28, "Days",
                       fontSize=9.5, fontName="Helvetica-Bold", fillColor=_rl_hex('#334155')))

    bar_total_days = float(bar_df['days'].sum()) if 'days' in bar_df.columns else 1.0

    in_prog_days = [
        float(r['days']) for _, r in bar_df.iterrows()
        if str(r.get('status', '')).strip().lower() == 'in progress'
    ]
    in_prog_min = min(in_prog_days) if in_prog_days else 0.0
    in_prog_max = max(in_prog_days) if in_prog_days else 1.0

    current_y_top = b_margin_b + b_plot_h
    line_gap = 12.0

    # Scale slot heights if total_slots_h differs from b_plot_h
    scale_y = (b_plot_h / total_slots_h) if total_slots_h > 0 else 1.0

    for i, (_, row) in enumerate(bar_df.iterrows()):
        slot_h = slot_heights[i] * scale_y
        y_center = current_y_top - (slot_h / 2.0)
        current_y_top -= slot_h

        lines = row_lines[i]
        # Y-axis project name: EXACT font size 9.5pt across all lines
        if len(lines) == 1:
            dwg.add(String(b_margin_l - 8, y_center - 3.5, lines[0],
                           fontSize=9.5, fontName="Helvetica", textAnchor="end",
                           fillColor=_rl_hex('#1e293b')))
        else:
            top_y = y_center + ((len(lines) - 1) * line_gap / 2.0) - 3.5
            for li, ln in enumerate(lines):
                dwg.add(String(b_margin_l - 8, top_y - li * line_gap, ln,
                               fontSize=9.5, fontName="Helvetica",
                               textAnchor="end", fillColor=_rl_hex('#1e293b')))

        st_val = str(row.get('status', ''))
        fill_hex = get_bar_project_color(st_val, float(row['days']), in_prog_min, in_prog_max)
        fill_c = _rl_hex(fill_hex)

        # Separate metadata parts
        init_str = str(row.get('initials', '')).strip()
        prefix_meta = f" \u2014 {init_str}" if (init_str and init_str.lower() not in ('nan', 'none', '_', '')) else ""
        start_d = str(row.get('start_str', '')).strip()
        end_d   = str(row.get('end_str', '')).strip()
        if start_d:
            prefix_meta += f" | start: {start_d}"

        rem_meta_parts = []
        if end_d:
            rem_meta_parts.append(f" | End: {end_d}")
        if st_val and st_val.lower() not in ('nan', 'none', '_', ''):
            rem_meta_parts.append(f" | {st_val}")
        remaining_meta = "".join(rem_meta_parts)

        d_val = float(row.get('days', 0.0) or 0.0)
        segs = get_bar_day_segments(d_val, max_per_row=15.0)
        n_segs = len(segs)

        # Equal bar height for all bars of this project (and consistent with other bars)
        # Increased bar_gap between consecutive bars belonging to the same split project in PDF
        if n_segs == 1:
            bar_h = min(16.0, max(12.0, slot_h * 0.42))
            bar_gap = 0.0
        else:
            bar_gap = 6.0
            avail_h = max(19.0, slot_h * 0.72)
            bar_h = min(12.0, max(9.5, (avail_h - (n_segs - 1) * bar_gap) / n_segs))

        total_bars_stack_h = n_segs * bar_h + (n_segs - 1) * bar_gap
        top_bar_y = y_center + (total_bars_stack_h / 2.0) - bar_h

        for s_idx, seg_d in enumerate(segs):
            y_bar = top_bar_y - s_idx * (bar_h + bar_gap)
            bw = (seg_d / x_max) * b_plot_w

            # Draw bar rectangle (always drawn for every segment)
            dwg.add(Rect(b_margin_l, y_bar, bw, bar_h, fillColor=fill_c, strokeColor=fill_c, strokeWidth=0.3))

            # Only the first bar shows the label, using total project days.
            # Subsequent bars have no label at all.
            if s_idx > 0:
                continue

            total_pct = (d_val / bar_total_days) * 100.0 if bar_total_days > 0 else 0.0
            inside_text = f"{format_days_display(d_val)} ({total_pct:.1f}%){prefix_meta}"
            full_meta_str = f"{inside_text}{remaining_meta}"

            if seg_d > 3.5:
                # Text starts inside the bar: bold metric/initials followed by normal remaining metadata
                x_start = b_margin_l + min((3.5 / x_max) * b_plot_w, bw * 0.25)
                dwg.add(String(x_start, y_bar + bar_h / 2.0 - 3.5, inside_text,
                               fontSize=9.5, fontName="Helvetica-Bold", fillColor=_rl_hex('#000000')))

                if remaining_meta:
                    bold_w = stringWidth(inside_text, "Helvetica-Bold", 9.5)
                    dwg.add(String(x_start + bold_w, y_bar + bar_h / 2.0 - 3.5, remaining_meta,
                                   fontSize=9.5, fontName="Helvetica", fillColor=_rl_hex('#000000')))
            else:
                # Outside the bar: entire label is NORMAL / regular weight
                x_label = b_margin_l + bw + 8.0
                dwg.add(String(x_label, y_bar + bar_h / 2.0 - 3.5, full_meta_str,
                               fontSize=9.5, fontName="Helvetica", fillColor=_rl_hex('#1e293b')))
    return dwg


def _pdf_styles():
    """Return shared ReportLab paragraph styles for chart PDFs."""
    styles = getSampleStyleSheet()
    return (
        ParagraphStyle('ChartTitle', parent=styles['Heading1'],
                       fontSize=14, leading=17, textColor=_rl_hex('#0f172a'),
                       alignment=TA_CENTER, spaceAfter=2),
        ParagraphStyle('ChartSub', parent=styles['Normal'],
                       fontSize=9, leading=12, textColor=_rl_hex('#64748b'),
                       alignment=TA_CENTER, spaceAfter=6),
    )


def _pdf_period_str(r_start, r_end) -> str:
    return f'Period: <b>{r_start.strftime("%d-%m-%Y")}</b> to <b>{r_end.strftime("%d-%m-%Y")}</b>'


def _pdf_add_pie_pages(story, pie_df, total_pie_days, pw, ph, title_style, sub_style, period_str, fig=None):
    """Add a single pie chart page to a ReportLab story (all projects in one chart, top 8 labelled)."""
    if not pie_df.empty and total_pie_days > 0:
        story.append(Paragraph('<b>Timesheet Analytics — Total Value by Project</b>', title_style))
        story.append(Paragraph(period_str, sub_style))
        img_bytes = None
        try:
            if fig is not None:
                export_fig = copy.deepcopy(fig)
            else:
                export_fig = _create_pie_plotly_fig(pie_df, total_pie_days, 0, 1)
            export_fig.update_layout(title=dict(text=''), shapes=[],
                                     margin=dict(l=30, r=30, t=25, b=40),
                                     height=600, paper_bgcolor='white', plot_bgcolor='white')
            export_fig.update_traces(domain=dict(x=[0.18, 0.82], y=[0.10, 0.88]))
            img_bytes = export_fig.to_image(format='png', scale=2, width=1050, height=600)
        except Exception:
            img_bytes = None
        if img_bytes:
            story.append(RLImage(io.BytesIO(img_bytes), width=pw, height=min(ph - 70, 430)))
        else:
            story.append(_build_rl_pie_drawing(pie_df, total_pie_days, pw, drawing_h=400))
    else:
        story.append(Paragraph('<b>Timesheet Analytics — Total Value by Project</b>', title_style))
        story.append(Paragraph(period_str, sub_style))
        story.append(Paragraph('<br/><br/>No pie chart data available.', sub_style))


def build_charts_pdf_report(r_start, r_end, pie_df, total_pie_days: float, bar_df, fig=None) -> bytes:
    """
    Render a pageless (single continuous tall page) PDF — like Google Docs pageless mode.
    Pie chart section flows directly into bar chart section with no page breaks.
    """
    pdf_buf = io.BytesIO()
    page_w = landscape(A4)[0]
    pw = page_w - 50

    BAR_PAGE_SIZE = 15
    bar_chunks = ([bar_df.iloc[i:i + BAR_PAGE_SIZE] for i in range(0, len(bar_df), BAR_PAGE_SIZE)]
                  if not bar_df.empty else [pd.DataFrame()])

    # Dynamically calculate total page height for pageless layout
    pie_section_h = 460 if (not pie_df.empty and total_pie_days > 0) else 60
    chunk_draw_heights = []
    for bchunk in bar_chunks:
        if not bchunk.empty:
            draw_h = compute_bar_chunk_height(bchunk, min_h=280.0, pw=pw, max_allowed_h=10000.0)
            chunk_draw_heights.append(draw_h)
        else:
            chunk_draw_heights.append(50)
    # Per-chunk overhead: bar title (~17) + sub (~12) ≈ 29; first chunk covered by section header
    bar_section_h = sum(chunk_draw_heights) + 50  # 50 for bar section title + sub
    total_content_h = pie_section_h + bar_section_h + 60  # 60 buffer
    page_h = total_content_h + 40  # doc top+bottom margins = 36

    doc = SimpleDocTemplate(pdf_buf, pagesize=(page_w, page_h),
                            leftMargin=25, rightMargin=25, topMargin=18, bottomMargin=18)
    title_style, sub_style = _pdf_styles()
    period_str = _pdf_period_str(r_start, r_end)
    story = []

    _pdf_add_pie_pages(story, pie_df, total_pie_days, pw, page_h - 36, title_style, sub_style, period_str, fig)

    # No PageBreak — content flows continuously
    story.append(Paragraph('<b>Timesheet Analytics — Total Value by Project (Bar)</b>', title_style))
    story.append(Paragraph(period_str, sub_style))
    if not bar_df.empty:
        for bi, bchunk in enumerate(bar_chunks):
            draw_h = chunk_draw_heights[bi]
            story.append(_build_rl_bar_drawing(bchunk, float(bar_df['days'].sum()), pw, drawing_h=draw_h, use_gradient=True))
            # No PageBreak between chunks in pageless mode
    else:
        story.append(Paragraph('<br/><br/>No bar chart data available.', sub_style))

    doc.build(story)
    return pdf_buf.getvalue()


def build_pie_pdf_report(r_start, r_end, pie_df, total_pie_days: float, fig=None) -> bytes:
    """
    Render landscape PDF page(s) containing only Pie Chart(s).
    Splits into multiple pages when > PIE_MAX_SLICES_PER_CHART projects.
    """
    pdf_buf = io.BytesIO()
    doc = SimpleDocTemplate(pdf_buf, pagesize=landscape(A4),
                            leftMargin=25, rightMargin=25, topMargin=18, bottomMargin=18)
    pw = landscape(A4)[0] - 50
    ph = landscape(A4)[1] - 36
    title_style, sub_style = _pdf_styles()
    period_str = _pdf_period_str(r_start, r_end)
    story = []
    _pdf_add_pie_pages(story, pie_df, total_pie_days, pw, ph, title_style, sub_style, period_str, fig)
    doc.build(story)
    return pdf_buf.getvalue()


def build_bar_pdf_report(r_start, r_end, bar_df) -> bytes:
    """
    Render a pageless (single continuous tall page) landscape PDF — like Google Docs pageless mode.
    All bar chart content flows on one page with no page breaks.
    """
    pdf_buf = io.BytesIO()
    page_w = landscape(A3)[0]
    pw = page_w - 70  # usable width

    BAR_PAGE_SIZE = 15
    bar_chunks = ([bar_df.iloc[i:i + BAR_PAGE_SIZE] for i in range(0, len(bar_df), BAR_PAGE_SIZE)]
                  if not bar_df.empty else [pd.DataFrame()])
    n_bar_chunks = len(bar_chunks)
    max_days_global = float(bar_df['days'].max()) if not bar_df.empty else 1.0

    # Compute draw heights without page-height cap for pageless layout
    chunk_draw_heights = []
    for bchunk in bar_chunks:
        if not bchunk.empty:
            draw_h = compute_bar_chunk_height(bchunk, min_h=300.0, pw=pw, max_allowed_h=10000.0)
            chunk_draw_heights.append(draw_h)
        else:
            chunk_draw_heights.append(50)

    # Overhead per chunk: title(~22) + sub(~14+14) ≈ 60
    overhead_per_chunk = 60
    summary_h = 40  # project summary banner rendered once at the top
    total_content_h = sum(chunk_draw_heights) + n_bar_chunks * overhead_per_chunk + summary_h + 60
    page_h = total_content_h + 50  # doc top+bottom margins = 50

    doc = SimpleDocTemplate(pdf_buf, pagesize=(page_w, page_h),
                            leftMargin=35, rightMargin=35, topMargin=25, bottomMargin=25)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('ChartTitle', parent=styles['Heading1'],
                                  fontSize=18, leading=22, textColor=_rl_hex('#0f172a'),
                                  alignment=TA_CENTER, spaceAfter=4)
    sub_style = ParagraphStyle('ChartSub', parent=styles['Normal'],
                                fontSize=11, leading=14, textColor=_rl_hex('#64748b'),
                                alignment=TA_CENTER, spaceAfter=14)
    period_str = _pdf_period_str(r_start, r_end)
    story = []

    for bi, bchunk in enumerate(bar_chunks):
        # Title and period are shown only once, for the first chunk.
        # Subsequent chunks flow their bars directly — no repeated mid-document header.
        if bi == 0:
            story.append(Paragraph('<b>Timesheet Analytics — Total Value by Project</b>', title_style))
            story.append(Paragraph(period_str, sub_style))

            # ── Project Summary Banner ──────────────────────────────────────
            if not bar_df.empty:
                _ss = getSampleStyleSheet()
                _sum_bold_style = ParagraphStyle(
                    'SumBold', parent=_ss['Normal'],
                    fontSize=9, leading=11, fontName='Helvetica-Bold',
                    textColor=_rl_hex('#0f172a'),
                )
                _sum_pill_style = ParagraphStyle(
                    'SumPill', parent=_ss['Normal'],
                    fontSize=8.5, leading=11, fontName='Helvetica',
                    textColor=_rl_hex('#1e293b'),
                )

                # Totals
                n_projects = len(bar_df)
                total_days = float(bar_df['days'].sum())
                total_days_str = (
                    f"{int(total_days)}d" if abs(total_days - round(total_days)) < 1e-9
                    else f"{round(total_days, 1)}d"
                )

                # Per-status counts
                status_counts = {}
                for _s in bar_df['status'].dropna():
                    _sc = str(_s).strip()
                    if _sc and _sc.lower() not in ('nan', 'none', '_', ''):
                        status_counts[_sc.lower()] = status_counts.get(_sc.lower(), 0) + 1

                # Fixed display order
                _status_display_order = [
                    ('in progress',        'In Progress',       '#22C55E'),
                    ('in testing',         'In Testing',        '#FFAE10'),
                    ('awaiting info',      'Awaiting Info',     '#D97706'),
                    ('ongoing',            'Ongoing',           '#3B82F6'),
                    ('at beta',            'At Beta',           '#2DD4BF'),
                    ('complete',           'Complete',          '#DC2626'),
                    ('not started',        'Not Started',       '#94A3B8'),
                    ('to be deployed',     'To Be Deployed',    '#8B5CF6'),
                    ('on hold',            'On Hold',           '#64748B'),
                    ('duplicate - closed', 'Duplicate/Closed',  '#94A3B8'),
                    ('duplicate',          'Duplicate/Closed',  '#94A3B8'),
                ]

                pill_sz = 10
                summary_row = [
                    Paragraph('<b>Project Summary</b>', _sum_bold_style),
                    Paragraph(f'<b>{n_projects}</b> Projects', _sum_pill_style),
                    Paragraph(f'<b>{total_days_str}</b> Effort Days', _sum_pill_style),
                ]
                col_widths = [100, 70, 90]

                seen_keys = set()
                for _key, _label, _hex in _status_display_order:
                    _cnt = status_counts.get(_key, 0)
                    if _cnt == 0 or _key in seen_keys:
                        continue
                    seen_keys.add(_key)
                    _sw = Drawing(pill_sz, pill_sz)
                    _sw.add(Rect(0, 0, pill_sz, pill_sz,
                                 fillColor=_rl_hex(_hex), strokeColor=_rl_hex(_hex), strokeWidth=0))
                    summary_row.append(_sw)
                    summary_row.append(Paragraph(f'<b>{_cnt}</b> {_label}', _sum_pill_style))
                    col_widths.extend([pill_sz + 4, 90])

                sum_table = Table([summary_row], colWidths=col_widths)
                sum_table.setStyle(TableStyle([
                    ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
                    ('LEFTPADDING',   (0, 0), (-1, -1), 5),
                    ('RIGHTPADDING',  (0, 0), (-1, -1), 6),
                    ('TOPPADDING',    (0, 0), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('BACKGROUND',    (0, 0), (-1, -1), _rl_hex('#f8fafc')),
                    ('LINEBELOW',     (0, 0), (-1, -1), 0.5, _rl_hex('#e2e8f0')),
                    ('LINEABOVE',     (0, 0), (-1, -1), 0.5, _rl_hex('#e2e8f0')),
                ]))
                story.append(sum_table)
                story.append(Spacer(1, 8))
        if not bchunk.empty:
            draw_h = chunk_draw_heights[bi]
            story.append(_build_rl_bar_drawing(
                bchunk, float(bar_df['days'].sum()) if not bar_df.empty else 1.0,
                pw, drawing_h=draw_h, use_gradient=True,
                global_max_days=max_days_global,
                show_xaxis=(bi == n_bar_chunks - 1)))
        else:
            story.append(Paragraph('<br/><br/>No bar chart data available.', sub_style))
        # No PageBreak between chunks — pageless continuous layout



    doc.build(story)
    return pdf_buf.getvalue()
