# Travel demand forecasting with rolling backtests

Which forecast would you use for next month’s passenger demand, and would you make the same choice three months ahead? Compare five transparent models at one- and three-month horizons on 144 monthly observations from the historical AirPassengers series (1949–1960). Counts are in thousands of passengers.

## Results

Mean absolute error (MAE), in thousands of passengers, across 82 common forecast origins per horizon:

| Model | One month ahead | Three months ahead |
|---|---:|---:|
| Same month last year | 36.50 | 36.98 |
| Last observed month | 33.39 | 67.61 |
| Same month last year, adjusted for recent annual growth | 14.22 | 16.67 |
| Log-linear trend with calendar-month effects | 20.01 | 21.23 |
| Holt-Winters on log counts | **10.67** | **14.72** |

The project’s Holt-Winters fit scored lowest in this backtest. An independent statsmodels cross-check supplied during review scored 11.28 at one month and 17.00 at three months. Both fits beat growth adjustment at one month. At three months the ranking reverses across implementations, so the evidence for preferring Holt-Winters there is sensitive to fitting choices. One month ahead it missed by about 10,670 passengers on average, compared with 14,220 for growth adjustment. Last month’s value beat last year’s at one month ahead but performed worst at three months. That reversal matters when choosing a planning horizon.

## Forecast review

Open [Forecast-review.rdl](report/Forecast-review.rdl) in Power BI Report Builder. This one-page paginated report is a snapshot. Run `python report/build.py` after updating the CSV to regenerate its MAE table. The separate statsmodels comparison is reviewer-reported.

March 1960 was the project's largest one-month Holt-Winters miss. From February’s 391 thousand passengers, the forecast implied a rise of about 75 thousand. The observed rise was only 28 thousand, to 419 thousand. The model anticipated the direction but overstated the rebound. August 1958 missed in the other direction (469 thousand forecast against 505 thousand actual). The series alone cannot establish what caused either miss.

## Reproduce

Tested with Python 3.12 and SciPy 1.17.0.

```sh
python -m pip install -r requirements.txt
python -m unittest -v
python forecast.py
```

Open backtest.csv in Excel or Power BI. Filter to one horizon and draw actual and forecast by target month, with one model selected. The actual repeats across models; summing it across model rows would count demand five times.

## Evaluation design

Start with five years of observations. At each month-end, refit using only observations available at that origin. Forecast the next month and the third month ahead. Restrict both horizons to origins with both outcomes available. All five models see identical history. Growth adjustment multiplies last year's corresponding month by the ratio of the two latest complete twelve-month totals. The log-trend model fits a common slope after removing month-specific intercepts and exponentiates predictions directly.

These retrospective results describe one historical series. Overlapping training windows produce correlated forecast errors. The models have no fares, capacity constraints, holidays or disruption indicators. Comparing these models here does not establish performance on contemporary demand.

## Data and authorship

[AirPassengers dataset documentation](https://stat.ethz.ch/R-manual/R-devel/library/datasets/html/AirPassengers.html) · [CSV source](https://github.com/jbrownlee/Datasets/blob/master/airline-passengers.csv). The bundled CSV retains the observations and uses descriptive column names.

Initial implementation and analysis prepared with Codex assistance.

## Smoothing specification

The Holt-Winters implementation fits additive level, trend and 12 monthly effects on log passenger counts. SciPy fits three smoothing coefficients at each forecast origin by minimizing one-step squared log errors after the first two years. Forecasts are exponentiated directly. The last-month model repeats the latest observed count at either horizon.
