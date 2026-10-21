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
from reportlab.platypus import SimpleDocTemplate, Paragraph, PageBreak, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.graphics.shapes import Drawing, Rect, String, Line
from reportlab.graphics.charts.piecharts import Pie


# ─────────────────────────────────────────────────────────────────────────────
# Project Status → Colour Mapping  (matches the user's visual preview)
# ─────────────────────────────────────────────────────────────────────────────
STATUS_COLORS = {
    'not started':        '#94A3B8',   
    'awaiting info':      '#D97706',   
    'at beta':            '#2DD4BF',   
    'in progress':        '#80BF48',  
    'in testing':         '#FFAE10',   
    'complete':           '#DC2626',   
    'to be deployed':     '#EDE9FE',   
    'duplicate - closed': '#94A3B8',   
    'ongoing':            '#64748B',   
}
# Human-readable labels for the legend (preserves original capitalisation)
STATUS_LABELS = [
    ('Not Started',        '#94A3B8'),
    ('Awaiting Info',      '#D97706'),
    ('At Beta',            '#2DD4BF'),
    ('In Progress',        '#80BF48'),
    ('In Testing',         '#FFAE10'),
    ('Complete',           '#DC2626'),
    ('To Be Deployed',     '#EDE9FE'),
    ('Ongoing',            '#64748B'),
    ('Duplicate / Closed', '#94A3B8'),
]
DEFAULT_BAR_COLOR = '#94A3B8'


def get_status_color_hex(status_str: str) -> str:
    """Return the hex colour for a given project status string (case-insensitive)."""
    if not status_str:
        return DEFAULT_BAR_COLOR
    return STATUS_COLORS.get(str(status_str).strip().lower(), DEFAULT_BAR_COLOR)


# ─────────────────────────────────────────────────────────────────────────────
# 1. Calculation & Display Helpers
# ─────────────────────────────────────────────────────────────────────────────

def convert_hours_to_days(hours: float) -> float:
    """
    Convert working hours to days using the business rule:
    8 hours = 1 working day.
    Does not round the underlying value.
    """
    try:
        h = float(hours or 0)
        return h / 8.0
    except (ValueError, TypeError):
        return 0.0


def format_days_display(days: float) -> str:
    """
    Format day values for display only (chart values stay unrounded).

    Examples: 3.6d, 2.7d, 1.5d, 0.5d, 1d, 4d
    Whole numbers drop the decimal; half-days keep one decimal.
    """
    try:
        d = float(days or 0)
    except (ValueError, TypeError):
        return "0d"
    shown = round(d, 1)
    if abs(shown - round(shown)) < 1e-9:
        return f"{int(round(shown))}d"
    return f"{shown:.1f}d"


def get_employee_initials(name: str) -> str:
    """
    Convert employee full name to initials.
    Examples:
        'Prajwal Chaudhari' -> 'PC'
        'Vivek Jadhav'      -> 'VJ'
        'Yogesh Todkar'     -> 'YT'
        'PC'                -> 'PC'
    """
    if not name or not isinstance(name, str):
        return ""
    clean_name = name.strip()
    if not clean_name or clean_name.lower() in ('nan', 'none', 'null', '_'):
        return ""
    
    # Split by whitespace, period, hyphen, or underscore
    parts = [p for p in re.split(r'[\s\.\-_]+', clean_name) if p]
    if not parts:
        return ""
    
    # If the token is already uppercase initials (e.g. 'PC', 'VJ')
    if len(parts) == 1:
        if len(parts[0]) <= 3 and parts[0].isupper():
            return parts[0]
        return parts[0][0].upper()
    
    # Take the first letter of each part (capitalised)
    initials = "".join(p[0].upper() for p in parts if p[0].isalpha())
    return initials if initials else parts[0][:2].upper()


def format_project_employee_initials(emp_names) -> str:
    """
    Deduplicate and format employee initials for a project into a comma-separated string.
    Example: ['Prajwal Chaudhari', 'Yogesh Todkar', 'Prajwal Chaudhari'] -> 'PC, YT'
    """
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
    """
    Wrap long project names onto multiple lines instead of truncating.
    Uses HTML <br> for Plotly charts or \\n for ReportLab / plaintext.
    """
    lines = wrap_project_name_lines(name, width=width)
    if not lines:
        return ""
    separator = "<br>" if html else "\n"
    return separator.join(lines)


def format_date_short(val) -> str:
    """
    Format date to '%d %b' (e.g. '24 Sep', '02 Oct').
    Returns empty string if invalid or missing.
    """
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
    """
    {days} ({percentage}%) — {employee initials} | Start: {start date} | End: {end date} | {status}

    Missing dates render as "—" so no invented dates appear.
    """
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
# Fixed threshold in working days:
# - > 3.5 days: allow approximately 50-60% of the label section to overlap the bar
# - <= 3.5 days: 0% overlap; keep the entire label outside the bar with clean spacing
BAR_OVERLAP_THRESHOLD_DAYS: float = 3.5

# Configurable overlap ratio targeting 50%–60% of the 'Xd (Y%) — Initials' section
BAR_LABEL_OVERLAP_RATIO: float = 0.55  # 55% overlap (within the 50%-60% target range)

# Spacing in pixels / points when the label is completely outside the bar (<= 3.5 days)
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
    Calculate the horizontal shift/overlap for a horizontal bar label.

    Binary Rule:
      - If project duration > threshold_days (3.5 days):
          Target overlap = 50%–60% of the 'Xd (Y%) — Initials' label section.
          Returns negative shift (in pixels/points) so text overlaps inside the bar tip.
          Safeguarded so text never precedes the bar origin.
      - If project duration <= threshold_days (3.5 days):
          0% overlap. Returns positive shift (outside_margin) keeping the entire
          label outside the bar.
    """
    try:
        d = float(days or 0.0)
    except (ValueError, TypeError):
        d = 0.0

    if d <= threshold_days:
        return float(outside_margin)

    # Build the label section: 'Xd (Y%) — Initials'
    d_str = format_days_display(d)
    pct_val = float(pct or 0.0)
    pct_str = f"{pct_val:.1f}%"
    sec_txt = f"{d_str} ({pct_str})"
    init_clean = str(initials).strip() if initials else ""
    if init_clean and init_clean.lower() not in ('nan', 'none', '_', ''):
        sec_txt += f" — {init_clean}"

    # Estimated width of this section in pixels/points
    sec_w = len(sec_txt) * (font_size * char_width_factor)
    target_overlap = sec_w * overlap_ratio

    # Safeguard: never overlap more than the bar itself minus a safety buffer (6px)
    safe_max_overlap = max(0.0, float(bar_width_units) - 6.0)
    overlap = min(target_overlap, safe_max_overlap)

    return -float(round(overlap))


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
    Format a multi-line label for donut/pie chart outside labels.
    Wraps project names onto multiple short lines and breaks metadata
    into compact lines to prevent horizontal overflow and clipping on UI and PDF.
    """
    p_clean = str(project_name).strip()
    d_str = format_days_display(days)
    p_pct_str = f"{pct:.1f}%"

    if p_clean.lower() == 'other':
        if html_mode:
            return f"<b>Other</b><br>{d_str} ({p_pct_str})"
        return f"Other\n{d_str} ({p_pct_str})"

    lines = wrap_project_name_lines(p_clean, width=wrap_width)
    if html_mode:
        w_name = "<br>".join(html.escape(l) for l in lines)
    else:
        w_name = "\n".join(lines)

    # Line 2: Value and initials
    val_part = f"{d_str} ({p_pct_str})"
    if initials_str and str(initials_str).strip():
        line2 = f"{val_part} — {str(initials_str).strip()}"
    else:
        line2 = val_part

    # Line 3: Dates and status (omit dates when both are blank to save space)
    start_disp = str(start_date_str).strip() if start_date_str else ""
    end_disp = str(end_date_str).strip() if end_date_str else ""
    meta_parts = []
    if start_disp or end_disp:
        meta_parts.append(f"Start: {start_disp or '—'} | End: {end_disp or '—'}")
    status_clean = str(status_str).strip() if status_str is not None else ""
    if status_clean and status_clean.lower() not in ('nan', 'none', '_', ''):
        meta_parts.append(status_clean)
    line3 = " | ".join(meta_parts)

    parts = [f"<b>{w_name}</b>" if html_mode else w_name, line2]
    if line3:
        parts.append(line3)

    separator = "<br>" if html_mode else "\n"
    return separator.join(parts)


def build_pie_connector_shapes(pie_df: pd.DataFrame, total_pie_days: float, cx: float = 0.50, cy: float = 0.50) -> list:
    """
    Plotly natively draws clean, non-overlapping elbow connector lines for
    displaced outside labels without colliding with multi-line text data.
    Returns an empty list to eliminate rigid manual lines that strike through text.
    """
    return []


def _create_pie_plotly_fig(pie_df: pd.DataFrame, total_pie_days: float):
    """Build a standalone Plotly Donut Chart figure for pie_df."""
    import plotly.graph_objects as go
    PIE_COLORS = [
        '#8dd3c7', '#ffffb3', '#bebada', '#fb8072', '#80b1d3',
        '#fdb462', '#b3de69', '#fccde5', '#d9d9d9', '#bc80bd', '#ccebc5', '#ffed6f'
    ]
    val_col = 'days' if 'days' in pie_df.columns else ('hours' if 'hours' in pie_df.columns else pie_df.columns[1])
    num_slices = len(pie_df)

    text_list = []
    if 'outside_label' in pie_df.columns:
        text_list = pie_df['outside_label'].tolist()
    else:
        for _, row in pie_df.iterrows():
            d = float(row[val_col])
            pct = (d / total_pie_days * 100) if total_pie_days > 0 else 0
            p_name = str(row.get('project_name', ''))
            init = str(row.get('initials', ''))
            s_str = str(row.get('start_str', ''))
            e_str = str(row.get('end_str', ''))
            stat = str(row.get('status', ''))
            text_list.append(format_pie_slice_label(p_name, d, pct, init, s_str, e_str, stat, wrap_width=24, html_mode=True))

    fig = go.Figure(go.Pie(
        labels=pie_df['project_name'],
        values=pie_df[val_col],
        hole=0.45,
        text=text_list,
        textinfo='text',
        textposition='outside',
        textfont=dict(size=10.5, color='#1e293b', family='Arial, sans-serif'),
        outsidetextfont=dict(size=10.5, color='#1e293b', family='Arial, sans-serif'),
        marker=dict(
            colors=PIE_COLORS[:num_slices],
            line=dict(color='#ffffff', width=2)
        ),
        showlegend=False,
        sort=False,
        direction='clockwise',
        rotation=0,
        domain=dict(x=[0.20, 0.80], y=[0.14, 0.80]),
    ))
    fig.update_layout(
        title=dict(text=''),
        shapes=[],
        margin=dict(l=30, r=30, t=45, b=55),
        height=820,
    )
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# 2. ReportLab PDF Generation (Server-Side, Zero Chrome/Kaleido)
# ─────────────────────────────────────────────────────────────────────────────

def build_charts_pdf_report(r_start, r_end, pie_df: pd.DataFrame, total_pie_days: float, bar_df: pd.DataFrame, fig=None) -> bytes:
    """
    Render a professional 2-page landscape PDF using pure ReportLab vector graphics.
    Page 1: Total Value by Project (Donut Pie Chart in Days matching UI)
    Page 2: Total Value by Project (Horizontal Bar Chart in Days with metadata)
    """
    pdf_buf = io.BytesIO()
    doc = SimpleDocTemplate(
        pdf_buf,
        pagesize=landscape(A4),
        leftMargin=25, rightMargin=25,
        topMargin=18, bottomMargin=18
    )
    
    pw = landscape(A4)[0] - 50
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'ChartTitle',
        parent=styles['Heading1'],
        fontSize=14,
        leading=17,
        textColor=colors.HexColor('#0f172a'),
        alignment=TA_CENTER,
        spaceAfter=2,
    )
    sub_style = ParagraphStyle(
        'ChartSub',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#64748b'),
        alignment=TA_CENTER,
        spaceAfter=6,
    )
    
    story = []
    
    # ── Page 1: Pie Chart ─────────────────────────────────────────────────────
    story.append(Paragraph('<b>Timesheet Analytics — Total Value by Project</b>', title_style))
    story.append(Paragraph(
        f'Period: <b>{r_start.strftime("%d-%m-%Y")}</b> to <b>{r_end.strftime("%d-%m-%Y")}</b>',
        sub_style
    ))
    
    if not pie_df.empty and total_pie_days > 0:
        img_bytes = None
        try:
            if fig is not None:
                export_fig = copy.deepcopy(fig)
            else:
                export_fig = _create_pie_plotly_fig(pie_df, total_pie_days)

            export_fig.update_layout(
                title=dict(text=''),
                shapes=[],
                margin=dict(l=30, r=30, t=25, b=40),
                height=700,
                paper_bgcolor='white',
                plot_bgcolor='white',
            )
            export_fig.update_traces(
                domain=dict(x=[0.20, 0.80], y=[0.14, 0.80])
            )
            img_bytes = export_fig.to_image(format='png', scale=2, width=1100, height=700)
        except Exception:
            img_bytes = None

        if img_bytes:
            story.append(RLImage(io.BytesIO(img_bytes), width=pw, height=480))
        else:
            val_col = 'days' if 'days' in pie_df.columns else ('hours' if 'hours' in pie_df.columns else pie_df.columns[1])
            p_data = [float(v) for v in pie_df[val_col].tolist()]
            dwg_pie = Drawing(pw, 460)
            pie_chart = Pie()
            pie_chart.x = int(pw / 2) - 150
            pie_chart.y = 60
            pie_chart.width = 300
            pie_chart.height = 300
            pie_chart.data = p_data
            pie_chart.innerRadiusFraction = 0.42
            pie_chart.sideLabels = 1
            pie_chart.sideLabelsOffset = 0.18
            pie_chart.simpleLabels = 0
            pie_chart.labels = [
                format_pie_slice_label(
                    row.get('project_name', ''), float(row[val_col]),
                    (float(row[val_col]) / total_pie_days * 100) if total_pie_days > 0 else 0,
                    row.get('initials', ''), row.get('start_str', ''), row.get('end_str', ''),
                    row.get('status', ''), wrap_width=20, html_mode=False
                )
                for _, row in pie_df.iterrows()
            ]
            pie_palette = [
                colors.HexColor('#8dd3c7'), colors.HexColor('#ffffb3'), colors.HexColor('#bebada'),
                colors.HexColor('#fb8072'), colors.HexColor('#80b1d3'), colors.HexColor('#fdb462'),
                colors.HexColor('#b3de69'), colors.HexColor('#fccde5'), colors.HexColor('#d9d9d9'),
                colors.HexColor('#bc80bd'), colors.HexColor('#ccebc5'), colors.HexColor('#ffed6f')
            ]
            for idx in range(len(p_data)):
                pie_chart.slices[idx].fillColor = pie_palette[idx % len(pie_palette)]
                pie_chart.slices[idx].strokeColor = colors.white
                pie_chart.slices[idx].strokeWidth = 1.5
                pie_chart.slices[idx].labelRadius = 1.35
                pie_chart.slices[idx].fontSize = 8.5
            dwg_pie.add(pie_chart)
            story.append(dwg_pie)
    else:
        story.append(Paragraph('<br><br>No pie chart data available.', sub_style))
    
    # ── Page 2: Bar Chart ─────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph('<b>📊 Timesheet Analytics — Total Value by Project (Top 20)</b>', title_style))
    story.append(Paragraph(
        f'Period: <b>{r_start.strftime("%d-%m-%Y")}</b> to <b>{r_end.strftime("%d-%m-%Y")}</b>',
        sub_style
    ))
    
    dwg_bar = Drawing(pw, 440)
    
    if not bar_df.empty:
        b_margin_l = 210
        b_margin_r = 25
        b_margin_b = 40
        b_margin_t = 15
        
        b_plot_w = pw - b_margin_l - b_margin_r
        b_plot_h = 440 - b_margin_t - b_margin_b
        
        max_days = bar_df['days'].max() if not bar_df.empty else 1.0
        x_max = max(max_days * 2.2, 1.0)
        
        # Calculate tick interval
        if x_max <= 5:
            tick_step = 1
        elif x_max <= 12:
            tick_step = 2
        elif x_max <= 30:
            tick_step = 5
        elif x_max <= 70:
            tick_step = 10
        else:
            tick_step = 20
            
        ticks = [i * tick_step for i in range(int(x_max // tick_step) + 1)]
        if ticks[-1] < x_max:
            ticks.append(ticks[-1] + tick_step)
        x_max = ticks[-1]
        
        # Gridlines & tick labels
        for t in ticks:
            x_pos = b_margin_l + (t / x_max) * b_plot_w
            dwg_bar.add(Line(x_pos, b_margin_b, x_pos, b_margin_b + b_plot_h, strokeColor=colors.HexColor('#f1f5f9'), strokeWidth=0.8))
            dwg_bar.add(String(x_pos - 3, b_margin_b - 14, str(t), fontSize=8.5, fontName="Helvetica", fillColor=colors.HexColor('#64748b')))
            
        # X-axis label
        dwg_bar.add(String(b_margin_l + b_plot_w / 2 - 12, b_margin_b - 28, "Days", fontSize=10, fontName="Helvetica-Bold", fillColor=colors.HexColor('#334155')))
        
        bar_blues = [
            colors.HexColor('#174d8c'), colors.HexColor('#2979b9'), colors.HexColor('#65a5d1'),
            colors.HexColor('#8ebdde'), colors.HexColor('#adcde6'), colors.HexColor('#bad1e8'),
            colors.HexColor('#d9e6f2'), colors.HexColor('#e6f0fa')
        ]
        
        n_bars = len(bar_df)
        bar_slot_h = b_plot_h / max(n_bars, 1)
        bar_height = min(18, max(10, bar_slot_h * 0.58))
        
        for i, (_, row) in enumerate(bar_df.iterrows()):
            y_center = b_margin_b + b_plot_h - (i + 0.5) * bar_slot_h
            y_bar = y_center - bar_height / 2
            
            p_name = str(row['project_name'])
            lines = wrap_project_name_lines(p_name, width=36)
            if len(lines) <= 1:
                dwg_bar.add(String(b_margin_l - 8, y_center - 3.5, lines[0] if lines else "", fontSize=9.5, fontName="Helvetica", textAnchor="end", fillColor=colors.HexColor('#1e293b')))
            else:
                dwg_bar.add(String(b_margin_l - 8, y_center + 4, lines[0], fontSize=8.5, fontName="Helvetica", textAnchor="end", fillColor=colors.HexColor('#1e293b')))
                dwg_bar.add(String(b_margin_l - 8, y_center - 7, lines[1], fontSize=8.5, fontName="Helvetica", textAnchor="end", fillColor=colors.HexColor('#1e293b')))
                if len(lines) > 2:
                    dwg_bar.add(String(b_margin_l - 8, y_center - 16, lines[2], fontSize=8.0, fontName="Helvetica", textAnchor="end", fillColor=colors.HexColor('#1e293b')))
                
            bw = (row['days'] / x_max) * b_plot_w
            status_hex = get_status_color_hex(str(row.get('status', '')))
            fill_c = colors.HexColor(status_hex)
            
            dwg_bar.add(Rect(b_margin_l, y_bar, bw, bar_height, fillColor=fill_c, strokeColor=fill_c, strokeWidth=0.4))
            
            label_text = str(row.get('metadata_text', ''))
            pct_val = float(row.get('pct', 0.0))
            if pct_val <= 0 and total_pie_days > 0:
                pct_val = (float(row['days']) / total_pie_days) * 100

            shift = calculate_bar_label_overlap(
                days=float(row['days']),
                pct=pct_val,
                initials=str(row.get('initials', '')),
                bar_width_units=bw,
                font_size=8.8,
                threshold_days=BAR_OVERLAP_THRESHOLD_DAYS,
                overlap_ratio=BAR_LABEL_OVERLAP_RATIO,
                outside_margin=BAR_OUTSIDE_MARGIN_PX,
            )
            text_x = b_margin_l + bw + shift
            dwg_bar.add(String(text_x, y_center - 3, label_text, fontSize=8.8, fontName="Helvetica", fillColor=colors.HexColor('#1e293b')))
    else:
        dwg_bar.add(String(pw / 2 - 80, 220, "No bar chart data available.", fontSize=12, fontName="Helvetica", fillColor=colors.HexColor('#64748b')))
        
    story.append(dwg_bar)
    
    doc.build(story)
    return pdf_buf.getvalue()


def build_pie_pdf_report(r_start, r_end, pie_df: pd.DataFrame, total_pie_days: float, fig=None) -> bytes:
    """
    Render a 1-page landscape PDF containing only the Pie Chart.
    Exports the exact Plotly donut chart as shown on the UI in high-resolution,
    with a graceful ReportLab vector fallback if image generation is unavailable.
    """
    pdf_buf = io.BytesIO()
    doc = SimpleDocTemplate(
        pdf_buf,
        pagesize=landscape(A4),
        leftMargin=25, rightMargin=25,
        topMargin=18, bottomMargin=18
    )
    pw = landscape(A4)[0] - 50

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'ChartTitle', parent=styles['Heading1'],
        fontSize=14, leading=17,
        textColor=colors.HexColor('#0f172a'),
        alignment=TA_CENTER, spaceAfter=2,
    )
    sub_style = ParagraphStyle(
        'ChartSub', parent=styles['Normal'],
        fontSize=9, leading=12,
        textColor=colors.HexColor('#64748b'),
        alignment=TA_CENTER, spaceAfter=6,
    )

    story = []
    story.append(Paragraph('<b>Timesheet Analytics — Total Value by Project</b>', title_style))
    story.append(Paragraph(
        f'Period: <b>{r_start.strftime("%d-%m-%Y")}</b> to <b>{r_end.strftime("%d-%m-%Y")}</b>',
        sub_style
    ))

    if not pie_df.empty and total_pie_days > 0:
        img_bytes = None
        try:
            if fig is not None:
                export_fig = copy.deepcopy(fig)
            else:
                export_fig = _create_pie_plotly_fig(pie_df, total_pie_days)

            export_fig.update_layout(
                title=dict(text=''),
                shapes=[],
                margin=dict(l=30, r=30, t=25, b=40),
                height=700,
                paper_bgcolor='white',
                plot_bgcolor='white',
            )
            export_fig.update_traces(
                domain=dict(x=[0.20, 0.80], y=[0.14, 0.80])
            )
            img_bytes = export_fig.to_image(format='png', scale=2, width=1100, height=700)
        except Exception:
            img_bytes = None

        if img_bytes:
            story.append(RLImage(io.BytesIO(img_bytes), width=pw, height=480))
        else:
            # Fallback to vector Drawing if image export fails
            val_col = 'days' if 'days' in pie_df.columns else ('hours' if 'hours' in pie_df.columns else pie_df.columns[1])
            p_data = [float(v) for v in pie_df[val_col].tolist()]
            dwg_pie = Drawing(pw, 460)
            pie_chart = Pie()
            pie_chart.x = int(pw / 2) - 150
            pie_chart.y = 60
            pie_chart.width = 300
            pie_chart.height = 300
            pie_chart.data = p_data
            pie_chart.innerRadiusFraction = 0.42
            pie_chart.sideLabels = 1
            pie_chart.sideLabelsOffset = 0.18
            pie_chart.simpleLabels = 0
            pie_chart.labels = [
                format_pie_slice_label(
                    row.get('project_name', ''), float(row[val_col]),
                    (float(row[val_col]) / total_pie_days * 100) if total_pie_days > 0 else 0,
                    row.get('initials', ''), row.get('start_str', ''), row.get('end_str', ''),
                    row.get('status', ''), wrap_width=20, html_mode=False
                )
                for _, row in pie_df.iterrows()
            ]
            pie_palette = [
                colors.HexColor('#8dd3c7'), colors.HexColor('#ffffb3'), colors.HexColor('#bebada'),
                colors.HexColor('#fb8072'), colors.HexColor('#80b1d3'), colors.HexColor('#fdb462'),
                colors.HexColor('#b3de69'), colors.HexColor('#fccde5'), colors.HexColor('#d9d9d9'),
                colors.HexColor('#bc80bd'), colors.HexColor('#ccebc5'), colors.HexColor('#ffed6f')
            ]
            for idx in range(len(p_data)):
                pie_chart.slices[idx].fillColor = pie_palette[idx % len(pie_palette)]
                pie_chart.slices[idx].strokeColor = colors.white
                pie_chart.slices[idx].strokeWidth = 1.5
                pie_chart.slices[idx].labelRadius = 1.35
                pie_chart.slices[idx].fontSize = 8.5
            dwg_pie.add(pie_chart)
            story.append(dwg_pie)
    else:
        story.append(Paragraph('<br><br>No pie chart data available.', sub_style))

    doc.build(story)
    return pdf_buf.getvalue()


def build_bar_pdf_report(r_start, r_end, bar_df: pd.DataFrame) -> bytes:
    """
    Render a 1-page landscape A3 PDF containing the Bar Chart (Top 20 Projects)
    with ample horizontal space, clear readable text directly to the right of bars,
    and a clean status color legend underneath.
    """
    pdf_buf = io.BytesIO()
    doc = SimpleDocTemplate(
        pdf_buf,
        pagesize=landscape(A3),
        leftMargin=35, rightMargin=35,
        topMargin=25, bottomMargin=25
    )
    pw = landscape(A3)[0] - 70

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'ChartTitle', parent=styles['Heading1'],
        fontSize=18, leading=22,
        textColor=colors.HexColor('#0f172a'),
        alignment=TA_CENTER, spaceAfter=4,
    )
    sub_style = ParagraphStyle(
        'ChartSub', parent=styles['Normal'],
        fontSize=11, leading=14,
        textColor=colors.HexColor('#64748b'),
        alignment=TA_CENTER, spaceAfter=14,
    )

    story = []
    story.append(Paragraph('<b>📊 Timesheet Analytics — Total Value by Project (Top 20)</b>', title_style))
    story.append(Paragraph(
        f'Period: <b>{r_start.strftime("%d-%m-%Y")}</b> to <b>{r_end.strftime("%d-%m-%Y")}</b>',
        sub_style
    ))

    dwg_bar = Drawing(pw, 630)

    if not bar_df.empty:
        b_margin_l = 280
        b_margin_r = 35
        b_margin_b = 45
        b_margin_t = 15
        b_plot_w = pw - b_margin_l - b_margin_r
        b_plot_h = 630 - b_margin_t - b_margin_b

        max_days = bar_df['days'].max() if not bar_df.empty else 1.0
        x_max = max(max_days * 2.3, max_days + 8.0) if max_days > 0 else 10.0

        if x_max <= 5:      tick_step = 1
        elif x_max <= 15:   tick_step = 2
        elif x_max <= 35:   tick_step = 5
        elif x_max <= 80:   tick_step = 10
        else:               tick_step = 20

        ticks = [i * tick_step for i in range(int(x_max // tick_step) + 1)]
        if ticks[-1] < x_max:
            ticks.append(ticks[-1] + tick_step)
        x_max = ticks[-1]

        for t in ticks:
            x_pos = b_margin_l + (t / x_max) * b_plot_w
            dwg_bar.add(Line(x_pos, b_margin_b, x_pos, b_margin_b + b_plot_h, strokeColor=colors.HexColor('#f1f5f9'), strokeWidth=0.8))
            dwg_bar.add(String(x_pos - 4, b_margin_b - 14, str(t), fontSize=10, fontName="Helvetica", fillColor=colors.HexColor('#64748b')))

        dwg_bar.add(String(b_margin_l + b_plot_w / 2 - 15, b_margin_b - 30, "Days", fontSize=12, fontName="Helvetica-Bold", fillColor=colors.HexColor('#334155')))

        n_bars = len(bar_df)
        bar_slot_h = b_plot_h / max(n_bars, 1)
        bar_height = min(20, max(13, bar_slot_h * 0.60))

        bar_total_days = bar_df['days'].sum() if 'days' in bar_df.columns else 1.0

        for i, (_, row) in enumerate(bar_df.iterrows()):
            y_center = b_margin_b + b_plot_h - (i + 0.5) * bar_slot_h
            y_bar = y_center - bar_height / 2
            p_name = str(row['project_name'])
            lines = wrap_project_name_lines(p_name, width=42)
            if len(lines) <= 1:
                dwg_bar.add(String(b_margin_l - 10, y_center - 3.5, lines[0] if lines else "", fontSize=11.0, fontName="Helvetica", textAnchor="end", fillColor=colors.HexColor('#1e293b')))
            else:
                dwg_bar.add(String(b_margin_l - 10, y_center + 4, lines[0], fontSize=10.0, fontName="Helvetica", textAnchor="end", fillColor=colors.HexColor('#1e293b')))
                dwg_bar.add(String(b_margin_l - 10, y_center - 7, lines[1], fontSize=10.0, fontName="Helvetica", textAnchor="end", fillColor=colors.HexColor('#1e293b')))
                if len(lines) > 2:
                    dwg_bar.add(String(b_margin_l - 10, y_center - 17, lines[2], fontSize=9.0, fontName="Helvetica", textAnchor="end", fillColor=colors.HexColor('#1e293b')))
            bw = (row['days'] / x_max) * b_plot_w
            # Colour bar by project status
            status_hex = get_status_color_hex(str(row.get('status', '')))
            fill_c = colors.HexColor(status_hex)
            dwg_bar.add(Rect(b_margin_l, y_bar, bw, bar_height, fillColor=fill_c, strokeColor=fill_c, strokeWidth=0.4))
            label_text = str(row.get('metadata_text', ''))

            pct_val = float(row.get('pct', 0.0))
            if pct_val <= 0 and bar_total_days > 0:
                pct_val = (float(row['days']) / bar_total_days) * 100

            shift = calculate_bar_label_overlap(
                days=float(row['days']),
                pct=pct_val,
                initials=str(row.get('initials', '')),
                bar_width_units=bw,
                font_size=10.5,
                threshold_days=BAR_OVERLAP_THRESHOLD_DAYS,
                overlap_ratio=BAR_LABEL_OVERLAP_RATIO,
                outside_margin=BAR_OUTSIDE_MARGIN_PX,
            )
            text_x = b_margin_l + bw + shift

            dwg_bar.add(String(text_x, y_center - 3.5, label_text, fontSize=10.5, fontName="Helvetica", fillColor=colors.HexColor('#1e293b')))
    else:
        dwg_bar.add(String(pw / 2 - 80, 220, "No bar chart data available.", fontSize=12, fontName="Helvetica", fillColor=colors.HexColor('#64748b')))

    story.append(dwg_bar)

    # ── Status colour legend (only statuses present in this data) ────────────────
    if not bar_df.empty and 'status' in bar_df.columns:
        present_statuses = bar_df['status'].dropna().unique()
        legend_rows = [
            (lbl, hex_c) for lbl, hex_c in STATUS_LABELS
            if any(str(s).strip().lower() == lbl.lower().replace(' / ', ' - ') or
                   str(s).strip().lower() == lbl.lower()
                   for s in present_statuses)
        ]
        # Fallback: show all if nothing matched
        if not legend_rows:
            legend_rows = STATUS_LABELS

        leg_style = ParagraphStyle(
            'LegLabel', parent=getSampleStyleSheet()['Normal'],
            fontSize=9.5, leading=12, textColor=colors.HexColor('#1e293b'),
        )
        leg_title_style = ParagraphStyle(
            'LegTitle', parent=getSampleStyleSheet()['Normal'],
            fontSize=10.5, leading=13, fontName='Helvetica-Bold',
            textColor=colors.HexColor('#1e293b'), spaceAfter=4,
        )
        legend_cell_size = 14
        cells_per_row = 5
        table_data = []
        row_cells = [Paragraph('<b>Status Legend:</b>', leg_title_style)]
        # pad first row
        row_cells += [''] * (cells_per_row * 2 - 1)
        table_data.append(row_cells)
        current = []
        for lbl, hex_c in legend_rows:
            swatch = Drawing(legend_cell_size, legend_cell_size)
            swatch.add(Rect(0, 0, legend_cell_size, legend_cell_size,
                            fillColor=colors.HexColor(hex_c),
                            strokeColor=colors.HexColor(hex_c), strokeWidth=0))
            current.append(swatch)
            current.append(Paragraph(lbl, leg_style))
            if len(current) >= cells_per_row * 2:
                table_data.append(current)
                current = []
        if current:
            current += [''] * (cells_per_row * 2 - len(current))
            table_data.append(current)

        col_widths = [legend_cell_size + 6, 120] * cells_per_row
        leg_table = Table(table_data, colWidths=col_widths)
        leg_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('SPAN', (0, 0), (-1, 0)),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f8fafc')),
            ('LINEBELOW', (0, 0), (-1, 0), 0.5, colors.HexColor('#e2e8f0')),
        ]))
        story.append(leg_table)

    doc.build(story)
    return pdf_buf.getvalue()
