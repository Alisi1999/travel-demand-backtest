"""Run with python check_statsmodels.py after installing statsmodels==0.14.6."""
import csv
from pathlib import Path
from statistics import mean

import numpy as np
from statsmodels.tsa.holtwinters import ExponentialSmoothing

ROOT = Path(__file__).resolve().parent


def main():
    with (ROOT / 'data/passengers.csv').open() as source:
        observations = list(csv.DictReader(source))
    values = np.array([float(row['passengers_thousands']) for row in observations])
    month_index = {row['month']: i for i, row in enumerate(observations)}
    with (ROOT / 'backtest.csv').open() as source:
        cases = [row for row in csv.DictReader(source) if row['model'] == 'growth_adjusted']

    errors = {}
    predictions = {}
    for row in cases:
        end = month_index[row['last_observed']] + 1
        horizon = int(row['horizon_months'])
        if month_index[row['target']] != end + horizon - 1:
            raise ValueError('Forecast target is misaligned')
        if end not in predictions:
            fit = ExponentialSmoothing(np.log(values[:end]), trend='add', seasonal='add',
                                       seasonal_periods=12, initialization_method='estimated').fit()
            predictions[end] = np.exp(fit.forecast(3))
        actual = values[end + horizon - 1]
        errors.setdefault(horizon, []).append(abs(actual - predictions[end][horizon - 1]))
    for horizon, misses in sorted(errors.items()):
        print(f'{horizon} month | {len(misses)} origins | MAE {mean(misses):.2f} thousand passengers')


if __name__ == '__main__':
    main()
