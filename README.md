# Marketing Insights – Executive Summary (TCS Dashboard Recreation)

Recreation of the cross-channel *Executive Summary* page from the assignment screenshot, built as a
self-contained web dashboard (HTML + vanilla JS + SVG, no BI licence needed) on a fully synthetic dataset.

| File | What it is |
|---|---|
| `index.html` | **The dashboard** (data embedded): live at https://homero007.github.io/improvado-tcs-dashboard/ or open locally by double-click |
| `generate_data.py` | Seeded (reproducible) dummy-data generator |
| `marketing_data.csv` | Generated dataset, 12,044 rows, daily grain, 2022-01-01 → 2023-12-31 |

Regenerate the data: `pip install numpy pandas && python generate_data.py`

## Widgets

| Widget | Shows | Why it matters |
|---|---|---|
| 8 KPI cards + sparklines | Spend, CPM, CTR, CPC, Video Views, Impressions, Conversions, Conversion Rate with Δ vs. comparison period | One-glance health check; the sparkline shows whether the number is stable, trending or spiking |
| Channel Performance | Impressions & CTR per channel, % change, heat-shaded | Where reach comes from and which channel engages best |
| Data Source Performance | Same metrics per platform | Spot a single platform causing a channel-level change |
| Campaign Performance | Same metrics per campaign | Optimise or pause individual campaigns |
| Time series | Monthly impressions by channel (drill to weekly/daily, switch metric to Conversions/Spend/CTR) | Seasonality, launches, anomalies; the shaded band marks the selected period |

**Interactions:** Data Source / Channel / Campaign / Ad Set multi-select filters; date presets + custom range;
comparison *Previous year* (default) or *Previous period*; click any table row to filter the whole page;
sort by column headers; search rows; copy any table or chart series as CSV; sidebar shortcuts (Paid Search,
Paid Social, Programmatic, SEO, Organic Social) apply a channel/source filter.

**Metric definitions:** CTR = clicks / impressions · CPM and CPC use paid media only (organic has no cost) ·
Conversion rate = conversions / clicks · Δ for ratios is shown in percentage points (pp).

## Data generation approach

Grain: **day × data source × campaign (ad set)** — the same grain a marketing data pipeline delivers,
so every widget is a simple aggregation of one fact table.

1. **Realistic source baselines.** Each platform gets industry-typical ranges: programmatic CTR ≈ 0.15–0.25 % at
   $5–8 CPM, Google search CTR ≈ 5 % at ≈ $2.85 CPC, LinkedIn CPM ≈ $36, Facebook CPM ≈ $11, and so on.
   Search is cost-per-click, display/social is cost-per-thousand.
2. **14 campaigns with flights and personalities:** always-on brand, retargeting (high CVR), brand vs. non-brand
   search, competitor conquesting (expensive, weak CVR), B2B lead gen on LinkedIn, and seasonal bursts
   (Spring launch, Summer Sale, Back to School video, Black Friday/Cyber Monday, Holiday Gifting).
3. **Seasonality and weekday effects:** January dip, spring ramp, July dip, Q4 peak; B2B sources fall ~40 % on weekends.
4. **Noise that behaves like real data:** log-normal daily volume noise; clicks and conversions are drawn from a
   binomial distribution, so small-volume rows jitter more than large ones, as in real data.
5. **Planted stories:** two years of data so every period has a comparison, with ~19 % YoY impression growth.
   Also planted: organic growth through 2023, StackAdapt creative fatigue in Q3, a Facebook tracking outage
   (12–18 Sep 2023), a Bing budget increase from Q2, and a Black Friday spike.

Note: the screenshot's own numbers are internally inconsistent ($36 M spend on 89 K impressions implies a
$405 K CPM). I matched the layout but kept the metrics mutually consistent.

## Insights in the data (full year 2023)

- Growth: spend $3.87 M (+31 % YoY), conversions 124 K (+29 %), impressions 170 M (+19 %). Cost per
  conversion crept up slightly ($36.9 → $38.0), so the growth is paid for rather than coming from efficiency.
- Budget vs. outcome mismatch: Paid Search takes 70 % of spend and drives 61 % of conversions at $35 CPA.
  Programmatic delivers 41 % of impressions but only 3 % of conversions ($151 CPA) — it's an awareness channel
  and should be judged on reach/video views, not CPA.
- Best campaigns: Retargeting ($19 CPA) and Brand Search ($19 CPA, 8.6 % CTR). **Worst:** Competitor
  Conquesting ($196 CPA) — first candidate to cut or rework.
- Creative fatigue: StackAdapt CTR slid from ~0.39 % in June to ~0.27 % in Aug–Sep and recovered to 0.39 % after the
  October refresh → set a creative-rotation alert.
- Tracking incident: Facebook conversions fell from ~40/day to ~4/day on 12–18 Sep while spend stayed flat —
  a measurement issue, not a performance one (visible in the Conversions sparkline / daily drill-down).
- Organic compounding: organic impressions +68 % from Q1 to Q4 2023 with zero media cost.
- Seasonality: Black Friday week produced ~2.4× an average week's conversions. Q1 vs. previous period
  looks red everywhere only because it's compared against the Q4 holiday peak — hence the YoY default.

