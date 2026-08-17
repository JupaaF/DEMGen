import unittest

from src.curve_generation import (
    CYCLIC_STRESS,
    DENSITY_SWEEP,
    SINGLE_POINT,
    STRESS_SWEEP,
    ZIGZAG_POINT,
    logarithmic_stress_targets,
    parse_curve_generation_settings,
)


def input_parameters(curve_generation=None):
    parameters = {
        "random_particle_generation_parameters": {
            "target_packing_density": 0.64,
            "minimum_mean_stress": 1000.0,
        }
    }
    if curve_generation is not None:
        parameters["curve_generation"] = curve_generation
    return parameters


class CurveGenerationSettingsTests(unittest.TestCase):
    def test_cyclic_stress_repeats_both_stable_extremes_for_each_cycle(self):
        settings = parse_curve_generation_settings(
            input_parameters(
                {
                    "mode": CYCLIC_STRESS,
                    "initial_density": 0.625,
                    "minimum_stress": 12500.0,
                    "maximum_stress": 50000.0,
                    "number_of_cycles": 3,
                }
            ),
            5000.0,
        )

        self.assertEqual(settings.mode, CYCLIC_STRESS)
        self.assertEqual(settings.generation_density, 0.625)
        self.assertEqual(settings.number_of_cycles, 3)
        self.assertEqual(
            settings.stress_targets,
            (12500.0, 50000.0, 12500.0, 50000.0, 12500.0, 50000.0, 12500.0),
        )

    def test_cyclic_stress_rejects_invalid_extremes_and_cycle_count(self):
        invalid_settings = (
            {
                "mode": CYCLIC_STRESS,
                "minimum_stress": 50000.0,
                "maximum_stress": 12500.0,
                "number_of_cycles": 1,
            },
            {
                "mode": CYCLIC_STRESS,
                "minimum_stress": 12500.0,
                "maximum_stress": 50000.0,
                "number_of_cycles": 0,
            },
        )

        for settings in invalid_settings:
            with self.subTest(settings=settings):
                with self.assertRaises(ValueError):
                    parse_curve_generation_settings(
                        input_parameters(settings),
                        5000.0,
                    )

    def test_missing_configuration_preserves_single_point_behavior(self):
        settings = parse_curve_generation_settings(input_parameters(), 5000.0)

        self.assertEqual(settings.mode, SINGLE_POINT)
        self.assertEqual(settings.initial_density, 0.64)
        self.assertEqual(settings.final_density, 0.64)
        self.assertEqual(settings.stress_targets, (5000.0,))

    def test_explicit_single_point_uses_curve_targets(self):
        settings = parse_curve_generation_settings(
            input_parameters(
                {
                    "mode": SINGLE_POINT,
                    "target_density": 0.625,
                    "target_stress": 50000.0,
                }
            ),
            5000.0,
        )

        self.assertEqual(settings.generation_density, 0.625)
        self.assertEqual(settings.stress_targets, (50000.0,))

    def test_zigzag_point_uses_fractional_targets(self):
        settings = parse_curve_generation_settings(
            input_parameters(
                {
                    "mode": ZIGZAG_POINT,
                    "initial_density": 0.5,
                    "initial_stress": 1000.0,
                    "target_density": 0.6,
                    "target_stress": 100000.0,
                    "step_fraction": 0.5,
                    "maximum_iterations": 20,
                }
            ),
            5000.0,
        )

        self.assertEqual(settings.mode, ZIGZAG_POINT)
        self.assertEqual(settings.generation_density, 0.5)
        self.assertEqual(settings.final_density, 0.6)
        self.assertEqual(settings.stress_targets, (10000.0,))
        self.assertEqual(settings.step_fraction, 0.5)
        self.assertEqual(settings.maximum_iterations, 20)

    def test_zigzag_point_supports_descending_stress_corrections(self):
        settings = parse_curve_generation_settings(
            input_parameters(
                {
                    "mode": ZIGZAG_POINT,
                    "initial_density": 0.5,
                    "initial_stress": 100000.0,
                    "target_density": 0.6,
                    "target_stress": 1000.0,
                    "step_fraction": 0.5,
                }
            ),
            5000.0,
        )

        self.assertEqual(settings.stress_targets, (10000.0,))

    def test_zigzag_point_rejects_nonascending_density(self):
        with self.assertRaisesRegex(ValueError, "target_density"):
            parse_curve_generation_settings(
                input_parameters(
                    {
                        "mode": ZIGZAG_POINT,
                        "initial_density": 0.6,
                        "initial_stress": 1000.0,
                        "target_density": 0.6,
                        "target_stress": 10000.0,
                    }
                ),
                5000.0,
            )

    def test_zigzag_point_rejects_invalid_step_fraction(self):
        for fraction in (0.0, 1.0):
            with self.subTest(fraction=fraction):
                with self.assertRaisesRegex(ValueError, "step_fraction"):
                    parse_curve_generation_settings(
                        input_parameters(
                            {
                                "mode": ZIGZAG_POINT,
                                "initial_density": 0.5,
                                "initial_stress": 1000.0,
                                "target_density": 0.6,
                                "target_stress": 10000.0,
                                "step_fraction": fraction,
                            }
                        ),
                        5000.0,
                    )

    def test_stress_sweep_supports_both_directions(self):
        lower = parse_curve_generation_settings(
            input_parameters(
                {
                    "mode": STRESS_SWEEP,
                    "initial_density": 0.625,
                    "initial_stress": 1000.0,
                    "final_stress": 200000.0,
                    "number_of_steps": 20,
                }
            ),
            5000.0,
        )
        upper = parse_curve_generation_settings(
            input_parameters(
                {
                    "mode": STRESS_SWEEP,
                    "initial_density": 0.625,
                    "initial_stress": 200000.0,
                    "final_stress": 1000.0,
                    "number_of_steps": 20,
                }
            ),
            5000.0,
        )

        self.assertEqual(lower.mode, STRESS_SWEEP)
        self.assertEqual(len(lower.stress_targets), 21)
        self.assertEqual(lower.stress_targets[0], 1000.0)
        self.assertEqual(lower.stress_targets[-1], 200000.0)
        self.assertEqual(upper.stress_targets[0], 200000.0)
        self.assertEqual(upper.stress_targets[-1], 1000.0)
        self.assertTrue(
            all(
                left > right
                for left, right in zip(upper.stress_targets, upper.stress_targets[1:])
            )
        )

    def test_density_sweep_uses_logarithmic_preparation_ramp(self):
        settings = parse_curve_generation_settings(
            input_parameters(
                {
                    "mode": DENSITY_SWEEP,
                    "initial_density": 0.625,
                    "final_density": 0.65,
                    "initial_stress": 1000.0,
                    "fixed_stress": 20000.0,
                    "number_of_steps": 10,
                }
            ),
            5000.0,
        )

        self.assertEqual(settings.mode, DENSITY_SWEEP)
        self.assertEqual(settings.final_density, 0.65)
        self.assertEqual(len(settings.stress_targets), 11)
        self.assertEqual(settings.stress_targets[0], 1000.0)
        self.assertEqual(settings.stress_targets[-1], 20000.0)

    def test_density_sweep_rejects_a_descending_density(self):
        with self.assertRaisesRegex(ValueError, "final_density"):
            parse_curve_generation_settings(
                input_parameters(
                    {
                        "mode": DENSITY_SWEEP,
                        "initial_density": 0.65,
                        "final_density": 0.625,
                        "fixed_stress": 20000.0,
                    }
                ),
                5000.0,
            )

    def test_density_sweep_can_start_at_its_fixed_stress(self):
        settings = parse_curve_generation_settings(
            input_parameters(
                {
                    "mode": DENSITY_SWEEP,
                    "initial_density": 0.625,
                    "final_density": 0.65,
                    "initial_stress": 1000.0,
                    "fixed_stress": 1000.0,
                }
            ),
            5000.0,
        )

        self.assertEqual(settings.stress_targets, (1000.0,))

    def test_targets_are_logarithmically_spaced(self):
        targets = logarithmic_stress_targets(1000.0, 100000.0, 2)

        self.assertEqual(targets, (1000.0, 10000.0, 100000.0))

    def test_stress_below_minimum_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "minimum_mean_stress"):
            parse_curve_generation_settings(
                input_parameters(
                    {
                        "mode": SINGLE_POINT,
                        "target_density": 0.64,
                        "target_stress": 500.0,
                    }
                ),
                5000.0,
            )


if __name__ == "__main__":
    unittest.main()
