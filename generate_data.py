"""
Dummy marketing data generator for the Improvado TCS dashboard-recreation challenge.

Grain: one row per day x campaign x data source (ad set), 2022-01-01 .. 2023-12-31.
2022 exists so every period in 2023 has a "previous period" to compare against.

Design principles
-----------------
1. Each data source has a realistic *base profile* (daily impressions, CTR, CPM or CPC,
   click->conversion rate, video-view rate) taken from typical industry ranges.
2. Campaigns are *flighted* (start/end dates) and carry performance multipliers,
   so campaign-level metrics differ in a believable way (retargeting converts,
   awareness/video drives views, conquesting is expensive and converts poorly).
3. Seasonality: January hangover, spring ramp, July dip, Q4 holiday peak, plus
   day-of-week effects (B2B sources drop on weekends, B2C social rises).
4. Deliberate "stories" planted for the walkthrough:
   - YoY growth of ~12% in paid media volume (2022 is generated at a lower scale).
   - Organic (SEO + organic social) grows ~40% across 2023 -> content investment paying off.
   - StackAdapt creative fatigue: CTR decays through Q3, recovers after an October refresh.
   - Facebook pixel / tracking outage 12-18 Sep 2023: conversions collapse, spend doesn't.
   - Bing budget increased from Q2 2023 (x1.6 volume).
   - Black Friday / Cyber Monday burst in late November.
5. Multiplicative log-normal daily noise + binomial sampling for clicks / conversions
   so ratios (CTR, CVR) jitter naturally instead of looking synthetic.
"""
import json
from datetime import date, timedelta

import numpy as np
import pandas as pd

rng = np.random.default_rng(2023)

START, END = date(2022, 1, 1), date(2023, 12, 31)
DAYS = [START + timedelta(d) for d in range((END - START).days + 1)]

# ----------------------------------------------------------------------------- sources
# imp: daily impressions at 1.0 scale, ctr, cost model ('cpm' or 'cpc', value in USD),
# cvr: conversions / clicks, vvr: video views / impression, b2b: weekday-heavy
SOURCES = {
    "Amazon Ad Server (Sizmek)":         dict(channel="Programmatic", imp=110_000, ctr=0.0019, cpm=6.5,  cvr=0.012, vvr=0.22, b2b=False),
    "StackAdapt":                        dict(channel="Programmatic", imp=95_000,  ctr=0.0023, cpm=8.0,  cvr=0.015, vvr=0.18, b2b=False),
    "Google Display & Video 360":        dict(channel="Programmatic", imp=120_000, ctr=0.0016, cpm=5.6,  cvr=0.010, vvr=0.28, b2b=False),
    "Google Search Ads 360":             dict(channel="Paid Search",  imp=42_000,  ctr=0.055,  cpc=2.85, cvr=0.052, vvr=0.0,  b2b=True),
    "Bing Ads (Microsoft Advertising)":  dict(channel="Paid Search",  imp=14_000,  ctr=0.043,  cpc=1.95, cvr=0.047, vvr=0.0,  b2b=True),
    "Facebook":                          dict(channel="Paid Social",  imp=115_000, ctr=0.0115, cpm=10.8, cvr=0.027, vvr=0.16, b2b=False),
    "LinkedIn Ads":                      dict(channel="Paid Social",  imp=30_000,  ctr=0.0055, cpm=36.0, cvr=0.038, vvr=0.09, b2b=True),
    "Google Search Console":             dict(channel="Organic",      imp=75_000,  ctr=0.031,  cpm=0.0,  cvr=0.024, vvr=0.0,  b2b=True),
    "Instagram (Organic)":               dict(channel="Organic",      imp=32_000,  ctr=0.0085, cpm=0.0,  cvr=0.007, vvr=0.21, b2b=False),
}

# ---------------------------------------------------------------------------- campaigns
# sources: {source: (share of that source's volume, ad set name)}
# flight: list of (start "MM-DD", end "MM-DD") repeated each year; None = always on
# m_ctr / m_cvr / m_vvr / m_cost: multipliers vs. source baseline
CAMPAIGNS = [
    dict(name="Always-On Brand Awareness", flight=None, m_ctr=0.85, m_cvr=0.6, m_vvr=1.4, m_cost=0.95,
         sources={"Google Display & Video 360": (0.45, "Contextual - Broad Reach"),
                  "Amazon Ad Server (Sizmek)": (0.35, "Audience - In-Market"),
                  "Facebook": (0.25, "Prospecting - Broad")}),
    dict(name="Retargeting - Site Visitors", flight=None, m_ctr=1.9, m_cvr=2.6, m_vvr=0.6, m_cost=1.25,
         sources={"Amazon Ad Server (Sizmek)": (0.20, "Retargeting - 30 Day"),
                  "StackAdapt": (0.25, "Retargeting - 7 Day"),
                  "Facebook": (0.18, "Retargeting - Cart Abandoners")}),
    dict(name="Brand Search - Exact Match", flight=None, m_ctr=1.7, m_cvr=1.5, m_vvr=0, m_cost=0.55,
         sources={"Google Search Ads 360": (0.35, "Brand - Exact"),
                  "Bing Ads (Microsoft Advertising)": (0.40, "Brand - Exact")}),
    dict(name="Non-Brand Search - Core Keywords", flight=None, m_ctr=0.75, m_cvr=0.8, m_vvr=0, m_cost=1.15,
         sources={"Google Search Ads 360": (0.40, "Generic - Phrase"),
                  "Bing Ads (Microsoft Advertising)": (0.45, "Generic - Phrase")}),
    dict(name="Competitor Conquesting", flight=[("04-01", "12-31")], m_ctr=0.55, m_cvr=0.45, m_vvr=0, m_cost=1.7,
         sources={"Google Search Ads 360": (0.12, "Competitor - Exact")}),
    dict(name="B2B Lead Gen - Decision Makers", flight=None, m_ctr=1.0, m_cvr=1.25, m_vvr=1.0, m_cost=1.0,
         sources={"LinkedIn Ads": (0.55, "Job Title - Director+")}),
    dict(name="Webinar Series Promotion", flight=[("02-01", "02-28"), ("05-01", "05-31"), ("09-15", "10-15")],
         m_ctr=1.2, m_cvr=1.6, m_vvr=0.8, m_cost=1.05,
         sources={"LinkedIn Ads": (0.30, "ABM - Target Accounts"),
                  "Facebook": (0.08, "Lookalike 1% - Registrants")}),
    dict(name="Spring Product Launch - Prospecting", flight=[("03-01", "05-31")], m_ctr=1.15, m_cvr=0.9, m_vvr=1.2, m_cost=1.05,
         sources={"StackAdapt": (0.45, "Native - Prospecting"),
                  "Facebook": (0.30, "Interest - Category Buyers"),
                  "LinkedIn Ads": (0.15, "Lookalike - Customers")}),
    dict(name="Summer Sale", flight=[("06-15", "08-31")], m_ctr=1.3, m_cvr=1.35, m_vvr=0.9, m_cost=1.0,
         sources={"Facebook": (0.30, "Advantage+ Shopping"),
                  "StackAdapt": (0.30, "Native - Deals"),
                  "Google Search Ads 360": (0.15, "Promo - Broad")}),
    dict(name="Back to School - Video", flight=[("08-01", "09-15")], m_ctr=0.9, m_cvr=0.8, m_vvr=1.9, m_cost=1.1,
         sources={"Google Display & Video 360": (0.40, "YouTube - In-Stream"),
                  "Amazon Ad Server (Sizmek)": (0.30, "OTT / CTV"),
                  "Facebook": (0.20, "Reels Placement")}),
    dict(name="Black Friday / Cyber Monday", flight=[("11-15", "12-02")], m_ctr=1.45, m_cvr=1.9, m_vvr=1.1, m_cost=1.35,
         sources={"Google Display & Video 360": (0.9, "Audience - High Intent"),
                  "Amazon Ad Server (Sizmek)": (0.9, "Audience - Shoppers"),
                  "StackAdapt": (0.8, "Native - Deals"),
                  "Facebook": (0.9, "Advantage+ Shopping"),
                  "Google Search Ads 360": (0.6, "Promo - Broad"),
                  "Bing Ads (Microsoft Advertising)": (0.5, "Promo - Broad")}),
    dict(name="Holiday Gifting", flight=[("12-03", "12-24")], m_ctr=1.2, m_cvr=1.4, m_vvr=1.2, m_cost=1.2,
         sources={"Facebook": (0.45, "Gift Guide - Interest"),
                  "Google Display & Video 360": (0.40, "YouTube - Gift Guide"),
                  "Google Search Ads 360": (0.30, "Gifts - Phrase")}),
    dict(name="SEO - Blog & Guides", flight=None, m_ctr=1.0, m_cvr=1.0, m_vvr=0, m_cost=0,
         sources={"Google Search Console": (1.0, "Organic Search")}),
    dict(name="Organic Social - Community", flight=None, m_ctr=1.0, m_cvr=1.0, m_vvr=1.0, m_cost=0,
         sources={"Instagram (Organic)": (1.0, "Organic Social")}),
]


def in_flight(d: date, flight) -> bool:
    if flight is None:
        return True
    md = d.strftime("%m-%d")
    return any(a <= md <= b for a, b in flight)


def seasonality(d: date) -> float:
    """Smooth yearly curve: Jan dip, spring ramp, July dip, Q4 peak."""
    doy = d.timetuple().tm_yday
    knots = {1: 0.82, 32: 0.90, 75: 1.02, 135: 1.08, 196: 0.86, 245: 0.97, 290: 1.05, 320: 1.22, 340: 1.35, 358: 1.18, 366: 0.85}
    xs, ys = list(knots), list(knots.values())
    return float(np.interp(doy, xs, ys))


def dow_effect(d: date, b2b: bool) -> float:
    wd = d.weekday()
    if b2b:
        return [1.08, 1.12, 1.12, 1.08, 0.98, 0.62, 0.58][wd]
    return [0.97, 0.98, 0.98, 1.0, 1.03, 1.08, 1.06][wd]


rows = []
for c in CAMPAIGNS:
    for src, (share, adset) in c["sources"].items():
        p = SOURCES[src]
        for d in DAYS:
            if not in_flight(d, c["flight"]):
                continue
            y23 = d.year == 2023
            t = (d - date(d.year, 1, 1)).days / 365  # 0..1 within year

            scale = 1.0 if y23 else 0.88                      # ~12-14% YoY growth
            if p["channel"] == "Organic":
                scale = (0.78 + 0.10 * t) if not y23 else (0.88 + 0.40 * t)  # SEO compounding in 2023
            if src.startswith("Bing") and y23 and d >= date(2023, 4, 1):
                scale *= 1.6                                    # budget increase

            imp_mean = p["imp"] * share * scale * seasonality(d) * dow_effect(d, p["b2b"])
            imps = int(max(0, imp_mean * rng.lognormal(0, 0.13)))

            ctr = p["ctr"] * c["m_ctr"] * rng.lognormal(0, 0.08)
            if y23 and src == "StackAdapt" and date(2023, 7, 1) <= d <= date(2023, 10, 8):
                ctr *= 1 - 0.45 * min(1, (d - date(2023, 7, 1)).days / 90)   # creative fatigue
            if not y23:
                ctr *= 0.95
            clicks = int(rng.binomial(imps, min(ctr, 0.5))) if imps else 0

            cost_mult = c["m_cost"] * rng.lognormal(0, 0.06) * (1.0 if y23 else 0.94)
            if "cpc" in p:
                spend = clicks * p["cpc"] * cost_mult * (1.15 if d.month in (11, 12) else 1.0)
            else:
                spend = imps / 1000 * p["cpm"] * cost_mult * (1.2 if d.month in (11, 12) else 1.0)

            cvr = p["cvr"] * c["m_cvr"] * rng.lognormal(0, 0.10)
            if y23 and src == "Facebook" and date(2023, 9, 12) <= d <= date(2023, 9, 18):
                cvr *= 0.1                                      # pixel outage
            conversions = int(rng.binomial(clicks, min(cvr, 0.9))) if clicks else 0

            vvr = p["vvr"] * c["m_vvr"]
            video_views = int(rng.binomial(imps, min(vvr * rng.lognormal(0, 0.08), 0.95))) if vvr and imps else 0

            rows.append(dict(date=d.isoformat(), channel=p["channel"], data_source=src, campaign=c["name"],
                             ad_set=adset, impressions=imps, clicks=clicks, spend=round(spend, 2),
                             video_views=video_views, conversions=conversions))

df = pd.DataFrame(rows).sort_values(["date", "channel", "data_source", "campaign"]).reset_index(drop=True)
df.to_csv("marketing_data.csv", index=False)

# ---------------------------------------------------------- compact JSON for the HTML page
dims = df[["channel", "data_source", "campaign", "ad_set"]].drop_duplicates().reset_index(drop=True)
dims["k"] = range(len(dims))
m = df.merge(dims, on=["channel", "data_source", "campaign", "ad_set"])
m["di"] = (pd.to_datetime(m["date"]) - pd.Timestamp(START)).dt.days
m = m.sort_values(["di", "k"])
payload = dict(
    start=START.isoformat(), ndays=len(DAYS),
    combos=dims[["channel", "data_source", "campaign", "ad_set"]].values.tolist(),
    d=m["di"].tolist(), k=m["k"].tolist(), imp=m["impressions"].tolist(), clk=m["clicks"].tolist(),
    sp=(m["spend"] * 100).round().astype(int).tolist(), vv=m["video_views"].tolist(), cv=m["conversions"].tolist(),
)
with open("data.json", "w") as f:
    json.dump(payload, f, separators=(",", ":"))

print(f"{len(df):,} rows, {len(dims)} source x campaign combos")
