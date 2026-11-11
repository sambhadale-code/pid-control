import unittest

import numpy as np

from src.pid_assignment import (
    PIDController,
    plot_ziegler_nichols,
    simulate_mass_spring,
    simulate_three_poles,
    step_metrics,
)


class PIDAssignmentTests(unittest.TestCase):
    def test_p_only_equilibrium_matches_spring_balance(self):
        time, position, _ = simulate_mass_spring(20.0, 0.0, 0.0, total_time=8.0)
        self.assertAlmostEqual(position[-1], 0.5, places=3)
        self.assertAlmostEqual(step_metrics(time, position)["steady_state_error_m"], 0.5, places=3)

    def test_pid_removes_steady_state_error(self):
        _, position, _ = simulate_mass_spring(
            20.0, 30.0, 5.0, total_time=8.0
        )
        self.assertLess(abs(1.0 - position[-1]), 1e-3)

    def test_sensor_noise_is_reproducible_with_fixed_seed(self):
        first = simulate_mass_spring(
            20.0, 30.0, 5.0, sensor_noise_mm=1.0, random_seed=42, total_time=2.0
        )
        repeated = simulate_mass_spring(
            20.0, 30.0, 5.0, sensor_noise_mm=1.0, random_seed=42, total_time=2.0
        )
        different_seed = simulate_mass_spring(
            20.0, 30.0, 5.0, sensor_noise_mm=1.0, random_seed=7, total_time=2.0
        )
        np.testing.assert_array_equal(first[1], repeated[1])
        self.assertFalse(np.array_equal(first[1], different_seed[1]))

    def test_conditional_integration_reduces_windup_overshoot(self):
        _, naive, _ = simulate_mass_spring(
            80.0, 100.0, 0.0, actuator_limit=30.0, total_time=8.0,
            anti_windup=False,
        )
        _, protected, _ = simulate_mass_spring(
            80.0, 100.0, 0.0, actuator_limit=30.0, total_time=8.0,
            anti_windup=True,
        )
        self.assertLess(np.max(protected), np.max(naive))

    def test_derivative_on_measurement_avoids_step_kick(self):
        measurement_derivative = PIDController(4.0, 0.0, 0.5, 0.01)
        error_derivative = PIDController(
            4.0, 0.0, 0.5, 0.01, derivative_on_measurement=False
        )
        self.assertAlmostEqual(measurement_derivative.update(1.0, 0.0), 4.0)
        self.assertAlmostEqual(error_derivative.update(1.0, 0.0), 4.0)
        measurement_derivative.update(1.0, 0.0)
        error_derivative.update(0.0, 0.0)
        self.assertAlmostEqual(measurement_derivative.update(1.0, 0.0), 4.0)
        self.assertAlmostEqual(error_derivative.update(1.0, 0.0), 54.0)

    def test_metrics_use_final_response_for_rise_and_settling(self):
        time = np.arange(0.0, 4.1, 0.1)
        response = 0.5 * (1.0 - np.exp(-time))
        metrics = step_metrics(time, response)
        self.assertGreater(metrics["rise_time_s"], 0.0)
        self.assertTrue(np.isfinite(metrics["settling_time_s"]))
        self.assertAlmostEqual(
            metrics["steady_state_error_m"], 1.0 - response[-1], places=12
        )

    def test_three_pole_model_and_zn_refinement(self):
        _, output = simulate_three_poles(2.4, 0.6, 1.8)
        self.assertAlmostEqual(output[-1], 1.0, places=2)
        result = plot_ziegler_nichols()
        self.assertAlmostEqual(result["Ku"], 8.0)
        self.assertAlmostEqual(result["Pu_s"], 2 * np.pi / np.sqrt(3.0), places=5)
        self.assertLess(
            result["refined_overshoot_percent"], result["overshoot_percent"]
        )


if __name__ == "__main__":
    unittest.main()
