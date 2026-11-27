"""Draw actual passengers vs one-month-ahead forecasts from backtest.csv.

Usage: python plot_forecast.py  (standard library only; writes report/forecast_one_month.svg)
"""
import csv
from pathlib import Path

ROOT = Path(__file__).parent
MODELS = [  # (model, legend label, colour, dash pattern)
    ("holt_winters", "Holt-Winters (log counts)", "#1f77b4", ""),
    ("growth_adjusted", "Same month last year, growth-adjusted", "#ff7f0e", "4,2"),
]
# Largest one-month Holt-Winters misses: label text, label x offset (months), label y (thousands)
MARKED = {
    "1958-08": ("Aug 1958: forecast 469k, actual 505k", -20, 580),
    "1960-03": ("Mar 1960: forecast 466k, actual 419k", -22, 250),
}
W, H, LEFT, RIGHT, TOP, BOTTOM = 860, 400, 60, 15, 40, 40
Y_MIN, Y_MAX = 150, 650


def load(horizon=1):
    actual, forecasts = {}, {m: {} for m, *_ in MODELS}
    with open(ROOT / "backtest.csv", newline="") as f:
        for row in csv.DictReader(f):
            if int(row["horizon_months"]) != horizon:
                continue
            actual[row["target"]] = float(row["actual_thousands"])
            if row["model"] in forecasts:
                forecasts[row["model"]][row["target"]] = float(row["forecast_thousands"])
    return actual, forecasts


def main():
    actual, forecasts = load()
    months = sorted(actual)
    sx = lambda i: LEFT + i * (W - LEFT - RIGHT) / (len(months) - 1)
    sy = lambda v: TOP + (Y_MAX - v) * (H - TOP - BOTTOM) / (Y_MAX - Y_MIN)
    line = lambda values: " ".join(f"{sx(i):.1f},{sy(v):.1f}" for i, v in enumerate(values))

    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
           'font-family="Arial, Helvetica, sans-serif" font-size="12">',
           f'<rect width="{W}" height="{H}" fill="white"/>',
           f'<text x="{W / 2}" y="22" text-anchor="middle" font-size="15">'
           'One-month-ahead forecasts vs actual, 82 rolling origins</text>']
    for v in range(200, Y_MAX + 1, 100):  # horizontal grid and y labels
        svg.append(f'<line x1="{LEFT}" x2="{W - RIGHT}" y1="{sy(v):.1f}" y2="{sy(v):.1f}" stroke="#ddd"/>')
        svg.append(f'<text x="{LEFT - 6}" y="{sy(v) + 4:.1f}" text-anchor="end">{v}</text>')
    for i, m in enumerate(months):  # year labels
        if m.endswith("-01"):
            svg.append(f'<text x="{sx(i):.1f}" y="{H - BOTTOM + 18}" text-anchor="middle">{m[:4]}</text>')
    svg.append(f'<text transform="translate(16,{(TOP + H - BOTTOM) / 2}) rotate(-90)" text-anchor="middle">'
               'Passengers (thousands)</text>')
    svg.append(f'<polyline points="{line(actual[m] for m in months)}" fill="none" stroke="black" stroke-width="2"/>')
    for model, _, colour, dash in MODELS:
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        svg.append(f'<polyline points="{line(forecasts[model][m] for m in months)}" fill="none" '
                   f'stroke="{colour}" stroke-width="1.5"{dash_attr}/>')
    for month, (text, dx, y) in MARKED.items():
        i = months.index(month)
        px, py = sx(i), sy(forecasts["holt_winters"][month])
        tx, ty = sx(i + dx), sy(y)
        start_y = ty + 4 if ty < py else ty - 13  # leave the label from below or above, never through it
        svg.append(f'<line x1="{tx + 100:.1f}" y1="{start_y:.1f}" x2="{px:.1f}" y2="{py:.1f}" stroke="black"/>')
        svg.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="3" fill="none" stroke="black"/>')
        svg.append(f'<text x="{tx:.1f}" y="{ty:.1f}" font-size="11">{text}</text>')
    legend = [("Actual", "black", "")] + [(label, colour, dash) for _, label, colour, dash in MODELS]
    for k, (label, colour, dash) in enumerate(legend):
        y = TOP + 14 + 16 * k
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        svg.append(f'<line x1="{LEFT + 10}" x2="{LEFT + 34}" y1="{y}" y2="{y}" stroke="{colour}" stroke-width="2"{dash_attr}/>')
        svg.append(f'<text x="{LEFT + 40}" y="{y + 4}" font-size="11">{label}</text>')
    svg.append("</svg>")

    out = ROOT / "report" / "forecast_one_month.svg"
    out.write_text("\n".join(svg) + "\n", encoding="utf-8")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
