import unittest
from forecast import evaluate, fit_holt_winters, last_month, growth_adjusted, log_trend, seasonal


class ForecastTests(unittest.TestCase):
    def test_constant_demand(self):
        for model in (seasonal, last_month, growth_adjusted, log_trend):
            for ahead in (0, 2):
                self.assertAlmostEqual(model([250] * 60, ahead), 250)

    def test_smoothing_constant(self):
        for value in fit_holt_winters([250] * 60).values():
            self.assertAlmostEqual(value, 250)

    def test_forecasts_ignore_future_changes(self):
        values = list(range(100, 170))
        dates = list(range(70))
        original = list(evaluate(values, dates))[:10]
        changed = list(evaluate(values[:60] + [999] * 10, dates))[:10]
        self.assertEqual([r[5] for r in original], [r[5] for r in changed])
        self.assertEqual({r[1] for r in original}, {60, 62})
