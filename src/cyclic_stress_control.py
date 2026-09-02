from __future__ import annotations

import bisect
from dataclasses import dataclass
import math
import random
from typing import Any, Mapping, Protocol, Sequence


PARTICLE_COUNT = 10_000
PARTICLE_RADIUS = 0.007
INITIAL_PACKING_DENSITY = 0.05
MAXIMUM_CYCLE_PRESSURE = 200_000.0
DENSITY_TOLERANCE = 0.002
MAXIMUM_CYCLES = 10_000
MINIMUM_PRESSURE_REDUCTION_FACTOR = 0.9
CYCLIC_TIME_STEP = 1.0e-6
CYCLIC_FINAL_TIME = 10_000.0
CYCLIC_SERVO_LOADING_FREQUENCY_STEPS = 1
CYCLIC_SERVO_VELOCITY_MAX = 10.0
CYCLIC_SETTLING_SERVO_VELOCITY_MAX = 0.1
CYCLIC_IMMEDIATE_STRESS_OFFSET = 10_000.0
STRESS_RELATIVE_TOLERANCE = 0.005
STRESS_MEASUREMENT_FREQUENCY_STEPS = 1
PROGRESS_REPORT_FREQUENCY_STEPS = 1_000
CHECKPOINT_STATE_FILENAME = "cyclic_stress_checkpoint.json"

HIGH_PRESSURE_PHASE = "high_pressure"
LOW_PRESSURE_PHASE = "low_pressure"
TARGET_STRESS_PHASE = "target_stress"


class RandomSource(Protocol):
    def uniform(self, lower: float, upper: float) -> float: ...


@dataclass(frozen=True)
class ParticleRadiusDistribution:
    """A discrete final-radius distribution sampled by number."""

    possible_values: tuple[float, ...]
    relative_frequencies: tuple[float, ...]

    def __post_init__(self) -> None:
        values = tuple(
            _positive_number(value, "particle radius")
            for value in self.possible_values
        )
        frequencies = tuple(
            _positive_number(frequency, "particle radius relative frequency")
            for frequency in self.relative_frequencies
        )
        if not values:
            raise ValueError("The particle radius distribution cannot be empty.")
        if len(values) != len(frequencies):
            raise ValueError(
                "Particle radius values and relative frequencies must have the "
                "same length."
            )
        object.__setattr__(self, "possible_values", values)
        object.__setattr__(self, "relative_frequencies", frequencies)

    @property
    def minimum_radius(self) -> float:
        return min(self.possible_values)

    @property
    def maximum_radius(self) -> float:
        return max(self.possible_values)

    def to_dict(self) -> dict[str, list[float]]:
        return {
            "possible_values": list(self.possible_values),
            "relative_frequencies": list(self.relative_frequencies),
        }

    def sample(
        self,
        particle_count: int = PARTICLE_COUNT,
        random_source: RandomSource | None = None,
    ) -> tuple[float, ...]:
        if isinstance(particle_count, bool) or not isinstance(particle_count, int):
            raise ValueError("particle_count must be a positive integer.")
        if particle_count <= 0:
            raise ValueError("particle_count must be a positive integer.")
        source = random_source if random_source is not None else random.Random()
        cumulative_frequencies: list[float] = []
        total_frequency = 0.0
        for frequency in self.relative_frequencies:
            total_frequency += frequency
            cumulative_frequencies.append(total_frequency)

        radii = []
        for _ in range(particle_count):
            draw = source.uniform(0.0, total_frequency)
            index = min(
                bisect.bisect_left(cumulative_frequencies, draw),
                len(self.possible_values) - 1,
            )
            radii.append(self.possible_values[index])
        return tuple(radii)


@dataclass(frozen=True)
class CyclicStressControlledSettings:
    target_packing_density: float
    target_stress: float
    minimum_cycle_pressure: float
    maximum_cycle_pressure: float = MAXIMUM_CYCLE_PRESSURE
    density_tolerance: float = DENSITY_TOLERANCE
    maximum_cycles: int = MAXIMUM_CYCLES
    minimum_pressure_reduction_factor: float = MINIMUM_PRESSURE_REDUCTION_FACTOR

    def __post_init__(self) -> None:
        target_density = _number(
            self.target_packing_density,
            "target_packing_density",
        )
        if not 0.0 < target_density < 1.0:
            raise ValueError("target_packing_density must be between 0 and 1.")

        minimum_pressure = _positive_number(
            self.minimum_cycle_pressure,
            "minimum_cycle_pressure",
        )
        target_stress = _positive_number(self.target_stress, "target_stress")
        maximum_pressure = _positive_number(
            self.maximum_cycle_pressure,
            "maximum_cycle_pressure",
        )
        if not minimum_pressure < target_stress < maximum_pressure:
            raise ValueError(
                "Pressures must satisfy 0 < minimum_cycle_pressure < "
                "target_stress < maximum_cycle_pressure."
            )
        if self.density_tolerance != DENSITY_TOLERANCE:
            raise ValueError(f"density_tolerance is fixed at {DENSITY_TOLERANCE}.")
        if self.maximum_cycles != MAXIMUM_CYCLES:
            raise ValueError(f"maximum_cycles is fixed at {MAXIMUM_CYCLES}.")
        if self.minimum_pressure_reduction_factor != MINIMUM_PRESSURE_REDUCTION_FACTOR:
            raise ValueError(
                "minimum_pressure_reduction_factor is fixed at "
                f"{MINIMUM_PRESSURE_REDUCTION_FACTOR}."
            )

    @classmethod
    def from_parameters(
        cls,
        parameters: Mapping[str, Any],
    ) -> CyclicStressControlledSettings:
        name = "cyclic_stress_controlled_method_parameters"
        raw_settings = parameters.get(name)
        if not isinstance(raw_settings, Mapping):
            raise ValueError(f"{name} must be a JSON object.")
        return cls(
            target_packing_density=_required(raw_settings, "target_packing_density"),
            target_stress=_required(raw_settings, "target_stress"),
            minimum_cycle_pressure=_required(
                raw_settings,
                "minimum_cycle_pressure",
            ),
        )

    def to_dict(self) -> dict[str, float | int]:
        return {
            "target_packing_density": self.target_packing_density,
            "target_stress": self.target_stress,
            "minimum_cycle_pressure": self.minimum_cycle_pressure,
            "maximum_cycle_pressure": self.maximum_cycle_pressure,
            "density_tolerance": self.density_tolerance,
            "maximum_cycles": self.maximum_cycles,
            "minimum_pressure_reduction_factor": (
                self.minimum_pressure_reduction_factor
            ),
        }


class CyclicStressController:
    """Switch cyclic targets after each crossed threshold has settled."""

    def __init__(self, settings: CyclicStressControlledSettings) -> None:
        self.settings = settings
        self.phase = HIGH_PRESSURE_PHASE
        self.target_pressure = settings.maximum_cycle_pressure
        self.minimum_cycle_pressure = settings.minimum_cycle_pressure
        self.completed_cycles = 0
        self.succeeded = False
        self.failed = False
        self.failure_message: str | None = None

    def to_state(self) -> dict[str, Any]:
        return {
            "phase": self.phase,
            "target_pressure": self.target_pressure,
            "minimum_cycle_pressure": self.minimum_cycle_pressure,
            "completed_cycles": self.completed_cycles,
            "succeeded": self.succeeded,
            "failed": self.failed,
            "failure_message": self.failure_message,
        }

    @classmethod
    def from_state(
        cls,
        settings: CyclicStressControlledSettings,
        state: Mapping[str, Any],
    ) -> CyclicStressController:
        controller = cls(settings)
        phase = state.get("phase")
        if phase not in {
            HIGH_PRESSURE_PHASE,
            LOW_PRESSURE_PHASE,
            TARGET_STRESS_PHASE,
        }:
            raise ValueError("Checkpoint contains an invalid controller phase.")
        minimum_pressure = _positive_number(
            state.get("minimum_cycle_pressure"),
            "checkpoint minimum_cycle_pressure",
        )
        completed_cycles = state.get("completed_cycles")
        if (
            isinstance(completed_cycles, bool)
            or not isinstance(completed_cycles, int)
            or not 0 <= completed_cycles <= settings.maximum_cycles
        ):
            raise ValueError("Checkpoint contains an invalid completed cycle count.")
        expected_pressure = {
            HIGH_PRESSURE_PHASE: settings.maximum_cycle_pressure,
            LOW_PRESSURE_PHASE: minimum_pressure,
            TARGET_STRESS_PHASE: settings.target_stress,
        }[phase]
        target_pressure = _positive_number(
            state.get("target_pressure"),
            "checkpoint target_pressure",
        )
        if not math.isclose(target_pressure, expected_pressure):
            raise ValueError(
                "Checkpoint target pressure is inconsistent with its phase."
            )
        succeeded = state.get("succeeded", False)
        failed = state.get("failed", False)
        if not isinstance(succeeded, bool) or not isinstance(failed, bool):
            raise ValueError("Checkpoint completion flags must be booleans.")
        if succeeded or failed:
            raise ValueError("Only an active controller checkpoint can be resumed.")

        controller.phase = phase
        controller.target_pressure = target_pressure
        controller.minimum_cycle_pressure = minimum_pressure
        controller.completed_cycles = completed_cycles
        controller.failure_message = None
        return controller

    def register_stable_cycle_threshold(
        self,
        packing_density: float,
    ) -> float | None:
        if self.succeeded or self.failed:
            raise RuntimeError("The cyclic stress controller has already finished.")

        packing_density = _number(packing_density, "packing_density")
        if self.phase == HIGH_PRESSURE_PHASE:
            return self._change_phase(
                LOW_PRESSURE_PHASE,
                self.minimum_cycle_pressure,
            )

        if self.phase != LOW_PRESSURE_PHASE:
            raise RuntimeError(
                "A cycle threshold can only be registered during a high- or "
                "low-pressure phase."
            )

        self.completed_cycles += 1
        density_error = packing_density - self.settings.target_packing_density
        if abs(density_error) <= self.settings.density_tolerance:
            return self._change_phase(
                TARGET_STRESS_PHASE,
                self.settings.target_stress,
            )

        if self.completed_cycles >= self.settings.maximum_cycles:
            self.failed = True
            self.failure_message = (
                "The system did not reach the requested density within "
                f"{self.settings.maximum_cycles} cycles."
            )
            return None

        if density_error > self.settings.density_tolerance:
            if not self._reduce_minimum_cycle_pressure():
                return None

        return self._change_phase(
            HIGH_PRESSURE_PHASE,
            self.settings.maximum_cycle_pressure,
        )

    def register_stable_state(self, packing_density: float) -> float | None:
        if self.succeeded or self.failed:
            raise RuntimeError("The cyclic stress controller has already finished.")
        if self.phase != TARGET_STRESS_PHASE:
            raise RuntimeError(
                "Stable states are only evaluated during the final target-stress "
                "phase."
            )

        packing_density = _number(packing_density, "packing_density")
        density_error = packing_density - self.settings.target_packing_density
        if abs(density_error) <= self.settings.density_tolerance:
            self.succeeded = True
            return None

        if self.completed_cycles >= self.settings.maximum_cycles:
            self.failed = True
            self.failure_message = (
                "The system did not reach the requested stable density and "
                f"stress within {self.settings.maximum_cycles} cycles."
            )
            return None

        if density_error > self.settings.density_tolerance:
            if not self._reduce_minimum_cycle_pressure():
                return None

        return self._change_phase(
            HIGH_PRESSURE_PHASE,
            self.settings.maximum_cycle_pressure,
        )

    def _reduce_minimum_cycle_pressure(self) -> bool:
        reduced_pressure = (
            self.minimum_cycle_pressure
            * self.settings.minimum_pressure_reduction_factor
        )
        if reduced_pressure <= 0.0:
            self.failed = True
            self.failure_message = (
                "The minimum cycle pressure became numerically zero before "
                "the requested density was reached."
            )
            return False
        self.minimum_cycle_pressure = reduced_pressure
        return True

    def _change_phase(self, phase: str, target_pressure: float) -> float:
        self.phase = phase
        self.target_pressure = target_pressure
        return target_pressure


def cycle_pressure_threshold_crossed(
    phase: str,
    measured_stress: float,
    target_pressure: float,
) -> bool:
    stress = _number(measured_stress, "measured_stress")
    pressure = _positive_number(target_pressure, "target_pressure")
    if phase == HIGH_PRESSURE_PHASE:
        return stress >= pressure
    if phase == LOW_PRESSURE_PHASE:
        return stress <= pressure
    return False


def immediate_cycle_pressure_target(
    phase: str,
    measured_stress: float,
    minimum_pressure: float,
    maximum_pressure: float,
    stress_offset: float = CYCLIC_IMMEDIATE_STRESS_OFFSET,
) -> float:
    if phase not in {HIGH_PRESSURE_PHASE, LOW_PRESSURE_PHASE}:
        raise ValueError("An immediate cycle target requires a cyclic phase.")
    stress = _number(measured_stress, "measured_stress")
    minimum = _positive_number(minimum_pressure, "minimum_pressure")
    maximum = _positive_number(maximum_pressure, "maximum_pressure")
    if maximum <= minimum:
        raise ValueError("maximum_pressure must be greater than minimum_pressure.")
    offset = _positive_number(stress_offset, "stress_offset")
    requested_pressure = (
        stress + offset
        if phase == HIGH_PRESSURE_PHASE
        else stress - offset
    )
    return min(max(requested_pressure, minimum), maximum)


def cubic_box_length(
    particle_count: int = PARTICLE_COUNT,
    particle_radius: float = PARTICLE_RADIUS,
    packing_density: float = INITIAL_PACKING_DENSITY,
) -> float:
    if isinstance(particle_count, bool) or not isinstance(particle_count, int):
        raise ValueError("particle_count must be a positive integer.")
    if particle_count <= 0:
        raise ValueError("particle_count must be a positive integer.")
    radius = _positive_number(particle_radius, "particle_radius")
    density = _number(packing_density, "packing_density")
    if not 0.0 < density < 1.0:
        raise ValueError("packing_density must be between 0 and 1.")
    solid_volume = particle_count * 4.0 / 3.0 * math.pi * radius**3
    return (solid_volume / density) ** (1.0 / 3.0)


def cubic_box_length_from_radii(
    particle_radii: Sequence[float],
    packing_density: float = INITIAL_PACKING_DENSITY,
) -> float:
    radii = _validated_particle_radii(particle_radii)
    density = _number(packing_density, "packing_density")
    if not 0.0 < density < 1.0:
        raise ValueError("packing_density must be between 0 and 1.")
    solid_volume = sum(4.0 / 3.0 * math.pi * radius**3 for radius in radii)
    return (solid_volume / density) ** (1.0 / 3.0)


def enclosing_measurement_sphere(
    minimum: Sequence[float],
    maximum: Sequence[float],
    maximum_particle_radius: float,
) -> tuple[tuple[float, float, float], float]:
    if len(minimum) != 3 or len(maximum) != 3:
        raise ValueError("Box bounds must contain exactly three coordinates.")
    minimum_coordinates = tuple(
        _number(value, "minimum box coordinate") for value in minimum
    )
    maximum_coordinates = tuple(
        _number(value, "maximum box coordinate") for value in maximum
    )
    if any(
        lower >= upper
        for lower, upper in zip(minimum_coordinates, maximum_coordinates)
    ):
        raise ValueError("Every maximum box coordinate must exceed its minimum.")
    particle_radius = _positive_number(
        maximum_particle_radius,
        "maximum_particle_radius",
    )
    center = tuple(
        0.5 * (lower + upper)
        for lower, upper in zip(minimum_coordinates, maximum_coordinates)
    )
    half_lengths = tuple(
        0.5 * (upper - lower)
        for lower, upper in zip(minimum_coordinates, maximum_coordinates)
    )
    half_diagonal = math.sqrt(sum(length**2 for length in half_lengths))
    # Kratos includes a particle only when distance < measurement_radius - r.
    # Two radii of padding keep that strict inequality true at box corners.
    measurement_radius = half_diagonal + 2.0 * particle_radius
    return center, measurement_radius


def phase_stress_tolerance(
    target_pressure: float,
    absolute_tolerance: float,
) -> float:
    pressure = _positive_number(target_pressure, "target_pressure")
    tolerance = _positive_number(absolute_tolerance, "absolute_tolerance")
    return max(tolerance, STRESS_RELATIVE_TOLERANCE * pressure)


def generate_non_overlapping_periodic_positions(
    *,
    particle_count: int = PARTICLE_COUNT,
    particle_radius: float = PARTICLE_RADIUS,
    particle_radii: Sequence[float] | None = None,
    packing_density: float = INITIAL_PACKING_DENSITY,
    random_source: RandomSource | None = None,
    maximum_attempts_per_particle: int = 10_000,
) -> tuple[tuple[float, float, float], ...]:
    """Place spheres randomly without overlap in a periodic cubic box."""
    if particle_radii is None:
        if isinstance(particle_count, bool) or not isinstance(particle_count, int):
            raise ValueError("particle_count must be a positive integer.")
        if particle_count <= 0:
            raise ValueError("particle_count must be a positive integer.")
        radius = _positive_number(particle_radius, "particle_radius")
        radii = (radius,) * particle_count
    else:
        radii = _validated_particle_radii(particle_radii)

    box_length = cubic_box_length_from_radii(radii, packing_density)
    maximum_diameter = 2.0 * max(radii)
    cells_per_axis = max(1, int(box_length / maximum_diameter))
    cell_length = box_length / cells_per_axis
    half_length = 0.5 * box_length
    source = random_source if random_source is not None else random.Random()

    cells: dict[tuple[int, int, int], list[int]] = {}
    positions: list[tuple[float, float, float]] = []

    for particle_index, candidate_radius in enumerate(radii):
        for _ in range(maximum_attempts_per_particle):
            candidate = (
                source.uniform(-half_length, half_length),
                source.uniform(-half_length, half_length),
                source.uniform(-half_length, half_length),
            )
            cell = _cell_index(
                candidate,
                half_length,
                cell_length,
                cells_per_axis,
            )
            if _has_periodic_overlap(
                candidate,
                cell,
                positions,
                cells,
                box_length,
                cells_per_axis,
                candidate_radius,
                radii,
            ):
                continue

            positions.append(candidate)
            cells.setdefault(cell, []).append(particle_index)
            break
        else:
            raise RuntimeError(
                "Could not place particle "
                f"{particle_index + 1} without overlap after "
                f"{maximum_attempts_per_particle} attempts."
            )

    return tuple(positions)


def _cell_index(
    position: tuple[float, float, float],
    half_length: float,
    cell_length: float,
    cells_per_axis: int,
) -> tuple[int, int, int]:
    return tuple(
        min(cells_per_axis - 1, int((coordinate + half_length) / cell_length))
        for coordinate in position
    )


def _has_periodic_overlap(
    candidate: tuple[float, float, float],
    cell: tuple[int, int, int],
    positions: list[tuple[float, float, float]],
    cells: dict[tuple[int, int, int], list[int]],
    box_length: float,
    cells_per_axis: int,
    candidate_radius: float,
    particle_radii: Sequence[float],
) -> bool:
    neighboring_cells = {
        (
            (cell[0] + offset_x) % cells_per_axis,
            (cell[1] + offset_y) % cells_per_axis,
            (cell[2] + offset_z) % cells_per_axis,
        )
        for offset_x in (-1, 0, 1)
        for offset_y in (-1, 0, 1)
        for offset_z in (-1, 0, 1)
    }
    for neighboring_cell in neighboring_cells:
        for particle_index in cells.get(neighboring_cell, ()):
            position = positions[particle_index]
            distance_squared = sum(
                min(abs(left - right), box_length - abs(left - right)) ** 2
                for left, right in zip(candidate, position)
            )
            minimum_distance = candidate_radius + particle_radii[particle_index]
            if distance_squared < minimum_distance**2:
                return True
    return False


def _validated_particle_radii(
    particle_radii: Sequence[float],
) -> tuple[float, ...]:
    if isinstance(particle_radii, (str, bytes)):
        raise ValueError("particle_radii must be a non-empty sequence.")
    radii = tuple(
        _positive_number(radius, "particle radius") for radius in particle_radii
    )
    if not radii:
        raise ValueError("particle_radii must be a non-empty sequence.")
    return radii


def _required(settings: Mapping[str, Any], name: str) -> Any:
    if name not in settings:
        raise ValueError(
            "cyclic_stress_controlled_method_parameters."
            f"{name} is required."
        )
    return settings[name]


def _positive_number(value: Any, name: str) -> float:
    number = _number(value, name)
    if number <= 0.0:
        raise ValueError(f"{name} must be greater than zero.")
    return number


def _number(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a number. Got {value!r}.")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{name} must be finite.")
    return number
