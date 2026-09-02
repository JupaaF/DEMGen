import math
import random
import unittest

from src.cyclic_stress_control import (
    CYCLIC_FINAL_TIME,
    CYCLIC_IMMEDIATE_STRESS_OFFSET,
    CYCLIC_SERVO_LOADING_FREQUENCY_STEPS,
    CYCLIC_SERVO_VELOCITY_MAX,
    CYCLIC_SETTLING_SERVO_VELOCITY_MAX,
    CYCLIC_TIME_STEP,
    DENSITY_TOLERANCE,
    HIGH_PRESSURE_PHASE,
    INITIAL_PACKING_DENSITY,
    LOW_PRESSURE_PHASE,
    MAXIMUM_CYCLE_PRESSURE,
    MAXIMUM_CYCLES,
    PARTICLE_COUNT,
    PARTICLE_RADIUS,
    STRESS_MEASUREMENT_FREQUENCY_STEPS,
    TARGET_STRESS_PHASE,
    CyclicStressControlledSettings,
    CyclicStressController,
    ParticleRadiusDistribution,
    cubic_box_length,
    cubic_box_length_from_radii,
    cycle_pressure_threshold_crossed,
    enclosing_measurement_sphere,
    generate_non_overlapping_periodic_positions,
    immediate_cycle_pressure_target,
    phase_stress_tolerance,
)


class CyclicStressControlledSettingsTests(unittest.TestCase):
    def test_uses_requested_fixed_time_step(self):
        self.assertEqual(CYCLIC_TIME_STEP, 1.0e-6)

    def test_uses_requested_final_time(self):
        self.assertEqual(CYCLIC_FINAL_TIME, 10_000.0)

    def test_updates_servo_and_stress_target_every_step(self):
        self.assertEqual(STRESS_MEASUREMENT_FREQUENCY_STEPS, 1)
        self.assertEqual(CYCLIC_SERVO_LOADING_FREQUENCY_STEPS, 1)

    def test_slows_servo_while_waiting_for_stability(self):
        self.assertEqual(CYCLIC_SERVO_VELOCITY_MAX, 10.0)
        self.assertEqual(CYCLIC_SETTLING_SERVO_VELOCITY_MAX, 0.1)

    def test_loads_public_inputs_and_keeps_protocol_constants_fixed(self):
        settings = CyclicStressControlledSettings.from_parameters(
            {
                "minimum_mean_stress": 1_000.0,
                "cyclic_stress_controlled_method_parameters": {
                    "target_packing_density": 0.625,
                    "target_stress": 50_000.0,
                    "minimum_cycle_pressure": 100.0,
                },
            }
        )

        self.assertEqual(settings.target_packing_density, 0.625)
        self.assertEqual(settings.target_stress, 50_000.0)
        self.assertEqual(settings.minimum_cycle_pressure, 100.0)
        self.assertEqual(settings.maximum_cycle_pressure, MAXIMUM_CYCLE_PRESSURE)
        self.assertEqual(settings.density_tolerance, DENSITY_TOLERANCE)
        self.assertEqual(settings.maximum_cycles, MAXIMUM_CYCLES)

    def test_rejects_pressures_outside_the_confirmed_order(self):
        for minimum, target in (
            (50_000.0, 50_000.0),
            (50_000.0, 40_000.0),
            (50_000.0, 200_000.0),
        ):
            with self.subTest(minimum=minimum, target=target):
                with self.assertRaisesRegex(ValueError, "Pressures must satisfy"):
                    CyclicStressControlledSettings(0.625, target, minimum)


class CyclicStressControllerTests(unittest.TestCase):
    def setUp(self):
        self.settings = CyclicStressControlledSettings(
            target_packing_density=0.625,
            target_stress=50_000.0,
            minimum_cycle_pressure=10_000.0,
        )

    def test_one_cycle_visits_high_low_and_final_target_before_succeeding(self):
        controller = CyclicStressController(self.settings)

        self.assertEqual(controller.phase, HIGH_PRESSURE_PHASE)
        self.assertEqual(controller.target_pressure, 200_000.0)
        self.assertEqual(
            controller.register_stable_cycle_threshold(0.60),
            10_000.0,
        )
        self.assertEqual(controller.phase, LOW_PRESSURE_PHASE)
        self.assertEqual(
            controller.register_stable_cycle_threshold(0.626),
            50_000.0,
        )
        self.assertEqual(controller.phase, TARGET_STRESS_PHASE)
        self.assertIsNone(controller.register_stable_state(0.6269))

        self.assertTrue(controller.succeeded)
        self.assertEqual(controller.completed_cycles, 1)

    def test_density_below_target_starts_another_cycle_at_same_minimum(self):
        controller = CyclicStressController(self.settings)

        controller.register_stable_cycle_threshold(0.60)
        next_pressure = controller.register_stable_cycle_threshold(0.6229)

        self.assertEqual(next_pressure, 200_000.0)
        self.assertEqual(controller.minimum_cycle_pressure, 10_000.0)
        self.assertEqual(controller.phase, HIGH_PRESSURE_PHASE)

    def test_density_above_target_reduces_minimum_pressure_by_ten_percent(self):
        controller = CyclicStressController(self.settings)

        controller.register_stable_cycle_threshold(0.60)
        next_pressure = controller.register_stable_cycle_threshold(0.6271)

        self.assertEqual(next_pressure, 200_000.0)
        self.assertEqual(controller.minimum_cycle_pressure, 9_000.0)

    def test_fails_after_the_ten_thousandth_unsuccessful_cycle(self):
        controller = CyclicStressController(self.settings)

        for _ in range(MAXIMUM_CYCLES):
            controller.register_stable_cycle_threshold(0.60)
            result = controller.register_stable_cycle_threshold(0.62)

        self.assertIsNone(result)
        self.assertTrue(controller.failed)
        self.assertEqual(controller.completed_cycles, MAXIMUM_CYCLES)

    def test_restores_an_active_controller_checkpoint(self):
        controller = CyclicStressController(self.settings)
        controller.register_stable_cycle_threshold(0.60)
        controller.register_stable_cycle_threshold(0.626)

        restored = CyclicStressController.from_state(
            self.settings,
            controller.to_state(),
        )

        self.assertEqual(restored.phase, TARGET_STRESS_PHASE)
        self.assertEqual(restored.target_pressure, 50_000.0)
        self.assertEqual(restored.completed_cycles, 1)
        self.assertEqual(restored.minimum_cycle_pressure, 10_000.0)

    def test_rejects_checkpoint_with_pressure_inconsistent_with_phase(self):
        state = CyclicStressController(self.settings).to_state()
        state["target_pressure"] = 123.0

        with self.assertRaisesRegex(ValueError, "inconsistent"):
            CyclicStressController.from_state(self.settings, state)

    def test_rejects_stable_state_outside_final_target_phase(self):
        controller = CyclicStressController(self.settings)

        with self.assertRaisesRegex(RuntimeError, "final target-stress"):
            controller.register_stable_state(0.625)


class CycleThresholdTests(unittest.TestCase):
    def test_immediate_target_stays_ten_kilopascals_ahead_of_stress(self):
        minimum_pressure = 1_000.0
        maximum_pressure = 200_000.0

        self.assertEqual(CYCLIC_IMMEDIATE_STRESS_OFFSET, 10_000.0)
        self.assertEqual(
            immediate_cycle_pressure_target(
                HIGH_PRESSURE_PHASE,
                1_000.0,
                minimum_pressure,
                maximum_pressure,
            ),
            11_000.0,
        )
        self.assertEqual(
            immediate_cycle_pressure_target(
                LOW_PRESSURE_PHASE,
                200_000.0,
                minimum_pressure,
                maximum_pressure,
            ),
            190_000.0,
        )

    def test_immediate_target_is_clipped_at_cycle_limits(self):
        self.assertEqual(
            immediate_cycle_pressure_target(
                HIGH_PRESSURE_PHASE,
                195_000.0,
                1_000.0,
                200_000.0,
            ),
            200_000.0,
        )
        self.assertEqual(
            immediate_cycle_pressure_target(
                LOW_PRESSURE_PHASE,
                5_000.0,
                1_000.0,
                200_000.0,
            ),
            1_000.0,
        )

    def test_high_threshold_requires_stress_at_or_above_maximum(self):
        self.assertFalse(
            cycle_pressure_threshold_crossed(
                HIGH_PRESSURE_PHASE,
                199_999.0,
                200_000.0,
            )
        )
        self.assertTrue(
            cycle_pressure_threshold_crossed(
                HIGH_PRESSURE_PHASE,
                200_000.0,
                200_000.0,
            )
        )

    def test_low_threshold_requires_stress_at_or_below_minimum(self):
        self.assertFalse(
            cycle_pressure_threshold_crossed(
                LOW_PRESSURE_PHASE,
                10_001.0,
                10_000.0,
            )
        )
        self.assertTrue(
            cycle_pressure_threshold_crossed(
                LOW_PRESSURE_PHASE,
                10_000.0,
                10_000.0,
            )
        )

class UnbalancedForceMeasurementTests(unittest.TestCase):
    def test_measurement_sphere_contains_every_particle_in_the_box(self):
        minimum = (-2.0, -3.0, -4.0)
        maximum = (2.0, 3.0, 4.0)
        particle_radius = 0.007

        center, measurement_radius = enclosing_measurement_sphere(
            minimum,
            maximum,
            particle_radius,
        )

        for x in (minimum[0], maximum[0]):
            for y in (minimum[1], maximum[1]):
                for z in (minimum[2], maximum[2]):
                    corner_distance = math.dist(center, (x, y, z))
                    self.assertLess(
                        corner_distance,
                        measurement_radius - particle_radius,
                    )


class StressToleranceTests(unittest.TestCase):
    def test_uses_half_percent_relative_tolerance_at_each_phase(self):
        self.assertEqual(phase_stress_tolerance(200_000.0, 10.0), 1_000.0)
        self.assertEqual(phase_stress_tolerance(10_000.0, 10.0), 50.0)
        self.assertEqual(phase_stress_tolerance(1_000.0, 10.0), 10.0)


class InitialPackingGeometryTests(unittest.TestCase):
    def test_box_length_gives_exactly_the_paper_initial_density(self):
        length = cubic_box_length()
        solid_volume = (
            PARTICLE_COUNT * 4.0 / 3.0 * math.pi * PARTICLE_RADIUS**3
        )

        self.assertAlmostEqual(
            solid_volume / length**3,
            INITIAL_PACKING_DENSITY,
        )
        self.assertAlmostEqual(length, 0.6598890294362815)

    def test_random_positions_do_not_overlap_across_periodic_boundaries(self):
        radius = 0.007
        positions = generate_non_overlapping_periodic_positions(
            particle_count=250,
            particle_radius=radius,
            packing_density=0.05,
            random_source=random.Random(7),
        )
        length = cubic_box_length(250, radius, 0.05)

        for index, left in enumerate(positions):
            for right in positions[index + 1 :]:
                distance_squared = sum(
                    min(abs(a - b), length - abs(a - b)) ** 2
                    for a, b in zip(left, right)
                )
                self.assertGreaterEqual(distance_squared, (2.0 * radius) ** 2)

    def test_polydisperse_box_has_the_requested_initial_density(self):
        radii = (0.003, 0.004, 0.005, 0.006, 0.007)
        length = cubic_box_length_from_radii(radii, 0.05)
        solid_volume = sum(4.0 / 3.0 * math.pi * radius**3 for radius in radii)

        self.assertAlmostEqual(solid_volume / length**3, 0.05)

    def test_polydisperse_positions_do_not_overlap_periodically(self):
        radii = tuple(0.003 + index % 5 * 0.001 for index in range(250))
        positions = generate_non_overlapping_periodic_positions(
            particle_radii=radii,
            packing_density=0.05,
            random_source=random.Random(11),
        )
        length = cubic_box_length_from_radii(radii, 0.05)

        for index, (left, left_radius) in enumerate(zip(positions, radii)):
            for right, right_radius in zip(
                positions[index + 1 :],
                radii[index + 1 :],
            ):
                distance_squared = sum(
                    min(abs(a - b), length - abs(a - b)) ** 2
                    for a, b in zip(left, right)
                )
                self.assertGreaterEqual(
                    distance_squared,
                    (left_radius + right_radius) ** 2,
                )


class ParticleRadiusDistributionTests(unittest.TestCase):
    def test_samples_only_configured_final_radii(self):
        distribution = ParticleRadiusDistribution(
            (0.003, 0.005, 0.007),
            (1.0, 2.0, 1.0),
        )

        radii = distribution.sample(500, random.Random(4))

        self.assertEqual(len(radii), 500)
        self.assertTrue(set(radii) <= {0.003, 0.005, 0.007})
        self.assertEqual(distribution.minimum_radius, 0.003)
        self.assertEqual(distribution.maximum_radius, 0.007)

    def test_rejects_mismatched_values_and_frequencies(self):
        with self.assertRaisesRegex(ValueError, "same length"):
            ParticleRadiusDistribution((0.003, 0.007), (1.0,))


if __name__ == "__main__":
    unittest.main()
