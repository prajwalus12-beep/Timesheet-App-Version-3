# Admin Guide 6 — Reports & Analytics

> [!IMPORTANT]
> This module is accessible to **Admins only**.

---

## Overview

The Reports & Analytics module provides visual summaries of timesheet data, including KPI cards, pie charts, bar charts, and PDF export functionality.

**Navigation:** Sidebar → 📊 **Reports**

---

## 1. KPI Summary Cards

At the top of the Reports page, **KPI (Key Performance Indicator) cards** display summary statistics for the selected filters:

| KPI Card | Description |
|----------|-------------|
| Total Hours | Sum of all logged hours |
| Total Days | Total equivalent working days |
| Headcount | Number of unique employees with entries |
| Projects | Number of unique projects with entries |

---

## 2. Filters

Apply filters to narrow down the data shown in all charts and KPI cards:

| Filter | Type | Description |
|--------|------|-------------|
| Employee | Multi-select | Filter by one or more employees |
| Project | Multi-select | Filter by one or more project codes/names |
| Date Range | Date picker | Select start and end dates for the report period |

> [!TIP]
> All charts and KPI cards update automatically when filters change. No "Apply" button is needed.

---

## 3. Charts Available

### Pie Charts

| Chart | Description |
|-------|-------------|
| Hours by Status | Distribution of hours across project statuses |
| Hours by Project | Which projects consumed the most hours |
| Hours by Employee | Each employee's share of total hours |

### Bar Charts

| Chart | Description |
|-------|-------------|
| Hours Trend | Hour totals over time (weekly or daily) |
| Hours by Employee (Initials) | Bar chart using employee initials for compact display |

---

## 4. Exporting Reports to PDF

1. Apply the desired filters (employee, project, date range).
2. Click the **"Export PDF"** or **"Download Report"** button.
3. A PDF file downloads containing:
   - KPI summary cards
   - All visible charts
   - Filter context (which filters were applied)

> [!NOTE]
> The PDF reflects exactly what is shown on screen at the time of export. Apply all filters before exporting.

---

## 5. Using Reports Effectively

### Finding Underperforming Areas

- Use the **Hours by Employee** chart to identify employees logging significantly fewer hours.
- Cross-reference with the **Employee filter** in Timesheet Administration.

### Tracking Project Effort

- Use **Hours by Project** to see which projects have the highest time investment.
- Use the **Date Range** filter to compare periods.

### Monitoring Attendance Trends

- Use the **Hours Trend** bar chart to identify weeks with low overall hours — may indicate holidays, illness, or missing entries.

---

## 6. Data Freshness

Reports reflect **real-time data** from the database. There is no caching — every page load pulls fresh data.
