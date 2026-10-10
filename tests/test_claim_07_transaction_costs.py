"""Independent tests for claim 7 (transaction costs), using answers worked out by hand."""

import ast
import unittest

import numpy as np

from checks.claim_07_transaction_costs import (
    TARGET, calls_with_keyword, load_function, loop_values, module_level_list,
)

execute_rebalance = load_function(TARGET / "portfolio_backtest.py", "execute_rebalance")


class HandCalculatedCases(unittest.TestCase):
    def test_zero_cost_changes_nothing(self):
        out = execute_rebalance(np.array([60.0, 40.0]), 0.0, np.array([0.5, 0.5]), cost_bps=0)
        self.assertAlmostEqual(out["Portfolio value"], 100.0, places=10)
        self.assertEqual(out["Transaction cost"], 0.0)

    def test_first_purchase_from_cash(self):
        # Buy with all cash V. Cost c on the amount bought: V' + cV' = V, so V' = V/(1+c).
        c = 10 / 10000
        out = execute_rebalance(np.zeros(2), 100000.0, np.array([0.3, 0.7]), cost_bps=10)
        self.assertAlmostEqual(out["Portfolio value"], 100000.0 / (1 + c), places=6)
        self.assertAlmostEqual(out["Transaction cost"], c * out["Portfolio value"], places=6)
        self.assertAlmostEqual(out["Turnover"], 1.0, places=12)

    def test_full_switch_from_one_asset_to_another(self):
        # Sell V of A and buy V' of B. Cost c(V + V'): V' + c(V + V') = V, so V' = V(1-c)/(1+c).
        c = 5 / 10000
        out = execute_rebalance(np.array([100.0, 0.0]), 0.0, np.array([0.0, 1.0]), cost_bps=5)
        self.assertAlmostEqual(out["Portfolio value"], 100.0 * (1 - c) / (1 + c), places=9)
        self.assertAlmostEqual(out["Traded value"], 100.0 + out["Portfolio value"], places=9)
        self.assertAlmostEqual(out["Turnover"], 2.0, places=12)

    def test_no_trade_costs_nothing(self):
        out = execute_rebalance(np.array([30.0, 70.0]), 0.0, np.array([0.3, 0.7]), cost_bps=10)
        self.assertAlmostEqual(out["Transaction cost"], 0.0, places=10)
        self.assertAlmostEqual(out["Portfolio value"], 100.0, places=10)


class Properties(unittest.TestCase):
    def test_accounting_identity_and_cost_formula_on_random_portfolios(self):
        rng = np.random.default_rng(0)
        for _ in range(1000):
            n = int(rng.integers(2, 9))
            values = rng.uniform(0, 1000, n)
            cash = float(rng.uniform(0, 500))
            weights = rng.dirichlet(np.ones(n))
            bps = float(rng.choice([0, 5, 10, 50]))
            out = execute_rebalance(values, cash, weights, cost_bps=bps)
            before = values.sum() + cash
            self.assertAlmostEqual(out["Portfolio value"] + out["Transaction cost"], before, delta=1e-8 * before)
            self.assertAlmostEqual(out["Transaction cost"], bps / 10000 * np.abs(out["Asset values"] - values).sum(),
                                   delta=1e-8 * before)
            np.testing.assert_allclose(out["Asset values"], out["Portfolio value"] * weights, rtol=1e-12)

    def test_higher_cost_rate_means_higher_cost_and_lower_value(self):
        values, weights = np.array([70.0, 30.0]), np.array([0.2, 0.8])
        outs = [execute_rebalance(values, 0.0, weights, cost_bps=b) for b in (0, 5, 10)]
        costs = [o["Transaction cost"] for o in outs]
        finals = [o["Portfolio value"] for o in outs]
        self.assertTrue(costs[0] < costs[1] < costs[2])
        self.assertTrue(finals[0] > finals[1] > finals[2])

    def test_invalid_inputs_are_rejected(self):
        good = dict(asset_values=np.array([50.0, 50.0]), cash=0.0, target_weights=np.array([0.5, 0.5]))
        for bad in ({"cost_bps": -1}, {"cost_bps": 10000}, {"cost_bps": float("nan")},
                    {"target_weights": np.array([0.7, 0.7])}, {"target_weights": np.array([1.2, -0.2])},
                    {"asset_values": np.array([-1.0, 101.0])}, {"cash": -5.0}):
            with self.assertRaises(ValueError):
                execute_rebalance(**{**good, "cost_bps": 5, **bad})


class KnownValidationGaps(unittest.TestCase):
    """I preserve current-bug evidence; passing does not approve the behaviour."""
    def test_current_near_unit_weights_are_accepted_and_overallocate(self):
        weights = np.array([0.5, 0.500009])
        out = execute_rebalance(np.array([60., 40.]), 0., weights, cost_bps=10)
        self.assertGreater(weights.sum(), 1.)
        self.assertGreater(out["Asset values"].sum() - out["Portfolio value"], 1e-5)

    def test_current_matrix_weights_are_accepted_and_change_cost(self):
        values = np.array([60., 40.])
        flat = execute_rebalance(values, 0., np.array([.5, .5]), cost_bps=10)
        matrix = execute_rebalance(values, 0., np.array([[.5], [.5]]), cost_bps=10)
        self.assertEqual(matrix["Asset values"].shape, (2, 1))
        self.assertGreater(matrix["Transaction cost"], flat["Transaction cost"])


class CallChain(unittest.TestCase):
    """The cost rate must reach execute_rebalance in every backtest that reports results."""

    def test_backtest_benchmarks_and_robustness_pass_the_cost_rate(self):
        for file in ("portfolio_backtest.py", "portfolio_benchmarks.py"):
            self.assertTrue(calls_with_keyword(TARGET / file, "execute_rebalance", "cost_bps"), file)
        self.assertTrue(calls_with_keyword(TARGET / "portfolio_robustness.py", "run_backtest", "cost_bps"))

    def test_cost_scenarios_and_scenario_counts(self):
        backtest = TARGET / "portfolio_backtest.py"
        benchmarks = TARGET / "portfolio_benchmarks.py"
        scenarios = ast.literal_eval(module_level_list(backtest, "cost_scenarios"))
        self.assertEqual(scenarios, [0, 5, 10])
        self.assertEqual(loop_values(benchmarks, "cost_bps"), [0, 5, 10])
        methods = module_level_list(backtest, "COVARIANCE_METHODS")
        self.assertEqual(len(methods.keys), 5)
        self.assertEqual(len(methods.keys) * len(scenarios), 15)   # optimized scenarios
        benchmark_dict = module_level_list(benchmarks, "benchmarks")
        self.assertEqual(len(benchmark_dict.keys) * len(scenarios), 9)  # benchmark scenarios

    def test_robustness_analysis_uses_ten_basis_points(self):
        self.assertEqual(ast.literal_eval(module_level_list(TARGET / "portfolio_robustness.py", "COST_BPS")), 10)


if __name__ == "__main__":
    unittest.main()
