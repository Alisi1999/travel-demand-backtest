"""Rolling-origin monthly passenger forecasts. Run with Python 3.10+."""
import csv
import math
import statistics
from pathlib import Path

from scipy.optimize import minimize

ROOT = Path(__file__).resolve().parent


def last_month(history, month):
    return history[-1]


def fit_holt_winters(history):
    """Additive Holt-Winters on log counts, with a 12-month seasonal period."""
    logs = [math.log(value) for value in history]
    initial_level = statistics.mean(logs[:12])
    initial_trend = (statistics.mean(logs[12:24]) - initial_level) / 12
    initial_season = [value - initial_level - (i - 5.5) * initial_trend
                      for i, value in enumerate(logs[:12])]

    def smooth(params):
        alpha, beta, gamma = params
        level = initial_level + 5.5 * initial_trend
        trend = initial_trend
        season = initial_season.copy()
        loss = 0.0
        for i in range(12, len(logs)):
            slot = i % 12
            predicted_level = level + trend
            error = logs[i] - predicted_level - season[slot]
            if i >= 24:
                loss += error ** 2
            previous_level = level
            level = predicted_level + alpha * error
            trend = (1 - beta) * trend + beta * (level - previous_level)
            season[slot] += gamma * (logs[i] - level - season[slot])
        return loss, level, trend, season

    result = minimize(lambda x: smooth(x)[0], (0.3, 0.1, 0.2),
                      method="L-BFGS-B", bounds=[(0.001, 0.999)] * 3)
    if not result.success:
        raise RuntimeError(f"Holt-Winters optimisation failed: {result.message}")
    _, level, trend, season = smooth(result.x)
    return {h: math.exp(level + h * trend + season[(len(history) + h - 1) % 12])
            for h in (1, 3)}


def seasonal(history, month):
    return history[-12 + month]


def growth_adjusted(history, month):
    """Apply the most recent year-over-year growth factor to last year's month."""
    ratio = sum(history[-12:]) / sum(history[-24:-12])
    return seasonal(history, month) * ratio


def log_trend(history, month):
    """Fit a shared log-linear trend and 12 monthly intercepts by least squares."""
    groups = [list(range(m, len(history), 12)) for m in range(12)]
    logs = [math.log(v) for v in history]
    numerator = denominator = 0
    for group in groups:
        center = statistics.mean(group)
        numerator += sum((i - center) * logs[i] for i in group)
        denominator += sum((i - center) ** 2 for i in group)
    slope = numerator / denominator
    target = len(history) + month
    group = groups[target % 12]
    intercept = statistics.mean(logs[i] - slope * i for i in group)
    return math.exp(intercept + slope * target)


def evaluate(values, dates):
    for origin in range(60, len(values) - 2):
        history = values[:origin]
        smoothed = fit_holt_winters(history)
        for horizon in (1, 3):
            target = origin + horizon - 1
            for model in (seasonal, last_month, growth_adjusted, log_trend):
                prediction = model(history, horizon - 1)
                yield [dates[origin - 1], dates[target], horizon, model.__name__,
                       values[target], round(prediction, 4)]
            yield [dates[origin - 1], dates[target], horizon, "holt_winters",
                   values[target], round(smoothed[horizon], 4)]


def main():
    with (ROOT / 'data/passengers.csv').open() as source:
        records = list(csv.DictReader(source))
    rows = list(evaluate([int(r['passengers_thousands']) for r in records],
                         [r['month'] for r in records]))
    with (ROOT / 'backtest.csv').open('w', newline='') as out:
        writer = csv.writer(out)
        writer.writerow(['last_observed', 'target', 'horizon_months', 'model',
                         'actual_thousands', 'forecast_thousands'])
        writer.writerows(rows)
    for horizon in (1, 3):
        for name in ('seasonal', 'last_month', 'growth_adjusted', 'log_trend', 'holt_winters'):
            errors = [r[5] - r[4] for r in rows if r[2:4] == [horizon, name]]
            print(f'{horizon} month | {name:16} | MAE {statistics.mean(map(abs, errors)):.2f}'
                  f' | bias {statistics.mean(errors):+.2f}')


if __name__ == '__main__':
    main()
