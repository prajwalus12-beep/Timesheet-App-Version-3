"""
Chart formatting and ReportLab PDF export helpers for Timesheet analytics.
Fully compatible with Streamlit Community Cloud (no browser / Kaleido dependency).
"""
import io
import re
import textwrap
import pandas as pd
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.graphics.shapes import Drawing, Rect, String, Line
from reportlab.graphics.charts.piecharts import Pie


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
# 2. ReportLab PDF Generation (Server-Side, Zero Chrome/Kaleido)
# ─────────────────────────────────────────────────────────────────────────────

def build_charts_pdf_report(r_start, r_end, pie_df: pd.DataFrame, total_pie_days: float, bar_df: pd.DataFrame) -> bytes:
    """
    Render a professional 2-page landscape PDF using pure ReportLab vector graphics.
    Page 1: Total Value by Project (Donut Pie Chart in Days + Metadata Legend)
    Page 2: Total Value by Project (Horizontal Bar Chart in Days with metadata)
    """
    pdf_buf = io.BytesIO()
    doc = SimpleDocTemplate(
        pdf_buf,
        pagesize=landscape(A4),
        leftMargin=30, rightMargin=30,
        topMargin=25, bottomMargin=25
    )
    
    pw = landscape(A4)[0] - 60  # ~781.89 pt
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'ChartTitle',
        parent=styles['Heading1'],
        fontSize=15,
        leading=18,
        textColor=colors.HexColor('#0f172a'),
        alignment=TA_CENTER,
        spaceAfter=3,
    )
    sub_style = ParagraphStyle(
        'ChartSub',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#64748b'),
        alignment=TA_CENTER,
        spaceAfter=12,
    )
    
    story = []
    
    # ── Page 1: Pie Chart ─────────────────────────────────────────────────────
    story.append(Paragraph('<b>📈 Timesheet Analytics — Total Value by Project</b>', title_style))
    story.append(Paragraph(
        f'Period: <b>{r_start.strftime("%d-%m-%Y")}</b> to <b>{r_end.strftime("%d-%m-%Y")}</b>',
        sub_style
    ))
    
    pie_palette = [
        colors.HexColor('#8dd3c7'), colors.HexColor('#ffffb3'), colors.HexColor('#bebada'),
        colors.HexColor('#fb8072'), colors.HexColor('#80b1d3'), colors.HexColor('#fdb462'),
        colors.HexColor('#b3de69'), colors.HexColor('#fccde5'), colors.HexColor('#d9d9d9'),
        colors.HexColor('#bc80bd'), colors.HexColor('#ccebc5'), colors.HexColor('#ffed6f')
    ]
    
    dwg_pie = Drawing(pw, 440)
    
    if not pie_df.empty and total_pie_days > 0:
        val_col = 'days' if 'days' in pie_df.columns else ('hours' if 'hours' in pie_df.columns else pie_df.columns[1])
        p_data = [float(v) for v in pie_df[val_col].tolist()]
        
        pie_chart = Pie()
        pie_chart.x = 20
        pie_chart.y = 40
        pie_chart.width = 330
        pie_chart.height = 330
        pie_chart.data = p_data
        pie_chart.innerRadiusFraction = 0.40
        pie_chart.sideLabels = 0
        pie_chart.simpleLabels = 0
        
        pie_chart.labels = [
            f"{(val / total_pie_days * 100):.1f}%" if (total_pie_days > 0 and (val / total_pie_days * 100) >= 3.5) else ""
            for val in p_data
        ]
        
        for idx in range(len(p_data)):
            pie_chart.slices[idx].fillColor = pie_palette[idx % len(pie_palette)]
            pie_chart.slices[idx].strokeColor = colors.white
            pie_chart.slices[idx].strokeWidth = 1.5
            pie_chart.slices[idx].labelRadius = 0.70
            
        dwg_pie.add(pie_chart)
        
        # Legend on right side — extra vertical space for wrapped names + metadata
        leg_x = 365
        leg_y_start = 370
        n_pie = len(pie_df)
        leg_step = 36 if n_pie <= 8 else (32 if n_pie <= 11 else 28)
        
        for idx, (_, row) in enumerate(pie_df.iterrows()):
            raw_name = str(row.get('display_name', row['project_name']))
            name_lines = wrap_project_name_lines(raw_name, width=48)
            legend_meta = str(row.get('metadata_text', ''))
            if not legend_meta:
                d = float(row[val_col])
                pct = (d / total_pie_days * 100) if total_pie_days > 0 else 0
                legend_meta = f"{format_days_display(d)} ({pct:.1f}%)"

            y_pos = leg_y_start - idx * leg_step

            dwg_pie.add(Rect(leg_x, y_pos, 11, 11, fillColor=pie_palette[idx % len(pie_palette)], strokeColor=colors.HexColor('#94a3b8'), strokeWidth=0.5))
            first_line = name_lines[0] if name_lines else raw_name
            dwg_pie.add(String(leg_x + 18, y_pos + 4, first_line, fontSize=7.5, fontName="Helvetica-Bold", fillColor=colors.HexColor('#1e293b')))
            second = name_lines[1] if len(name_lines) > 1 else ""
            extra = f"{second}  {legend_meta}".strip() if second else legend_meta
            dwg_pie.add(String(leg_x + 18, y_pos - 7, extra[:110], fontSize=6.8, fontName="Helvetica", fillColor=colors.HexColor('#475569')))
    else:
        dwg_pie.add(String(pw / 2 - 80, 220, "No pie chart data available.", fontSize=12, fontName="Helvetica", fillColor=colors.HexColor('#64748b')))
        
    story.append(dwg_pie)
    
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
            colors.HexColor('#174d8c'),
            colors.HexColor('#2979b9'),
            colors.HexColor('#65a5d1'),
            colors.HexColor('#8ebdde'),
            colors.HexColor('#adcde6'),
            colors.HexColor('#bad1e8'),
            colors.HexColor('#d9e6f2'),
            colors.HexColor('#e6f0fa')
        ]
        
        n_bars = len(bar_df)
        bar_slot_h = b_plot_h / max(n_bars, 1)
        bar_height = min(22, max(12, bar_slot_h * 0.65))
        
        for i, (_, row) in enumerate(bar_df.iterrows()):
            y_center = b_margin_b + b_plot_h - (i + 0.5) * bar_slot_h
            y_bar = y_center - bar_height / 2
            
            p_name = str(row['project_name'])
            lines = wrap_project_name_lines(p_name, width=36)
            if len(lines) <= 1:
                dwg_bar.add(String(b_margin_l - 8, y_center - 3, lines[0] if lines else "", fontSize=8.5, fontName="Helvetica", textAnchor="end", fillColor=colors.HexColor('#1e293b')))
            else:
                dwg_bar.add(String(b_margin_l - 8, y_center + 4, lines[0], fontSize=8, fontName="Helvetica", textAnchor="end", fillColor=colors.HexColor('#1e293b')))
                dwg_bar.add(String(b_margin_l - 8, y_center - 7, lines[1], fontSize=8, fontName="Helvetica", textAnchor="end", fillColor=colors.HexColor('#1e293b')))
                if len(lines) > 2:
                    dwg_bar.add(String(b_margin_l - 8, y_center - 16, lines[2], fontSize=7.5, fontName="Helvetica", textAnchor="end", fillColor=colors.HexColor('#1e293b')))
                
            bw = (row['days'] / x_max) * b_plot_w
            color_idx = min(i, len(bar_blues) - 1)
            fill_c = bar_blues[color_idx]
            stroke_c = colors.HexColor('#2979b9') if color_idx >= 6 else colors.HexColor('#3a82f6')
            
            dwg_bar.add(Rect(b_margin_l, y_bar, bw, bar_height, fillColor=fill_c, strokeColor=stroke_c, strokeWidth=0.6))
            
            label_text = row['metadata_text']
            dwg_bar.add(String(b_margin_l + bw + 6, y_center - 3, label_text, fontSize=7.8, fontName="Helvetica", fillColor=colors.HexColor('#334155')))
    else:
        dwg_bar.add(String(pw / 2 - 80, 220, "No bar chart data available.", fontSize=12, fontName="Helvetica", fillColor=colors.HexColor('#64748b')))
        
    story.append(dwg_bar)
    
    doc.build(story)
    return pdf_buf.getvalue()
