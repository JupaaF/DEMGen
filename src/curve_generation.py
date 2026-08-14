from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any, Mapping


SINGLE_POINT = "single_point"
STRESS_SWEEP = "stress_sweep"
DENSITY_SWEEP = "density_sweep"
SUPPORTED_MODES = (SINGLE_POINT, STRESS_SWEEP, DENSITY_SWEEP)


@dataclass(frozen=True)
class CurveGenerationSettings:
    mode: str
    initial_density: float
    final_density: float
    initial_stress: float
    final_stress: float
    number_of_steps: int

    @property
    def generation_density(self) -> float:
        return self.initial_density

    @property
    def stress_targets(self) -> tuple[float, ...]:
        if self.mode == SINGLE_POINT:
            return (self.final_stress,)
        return logarithmic_stress_targets(
            self.initial_stress,
            self.final_stress,
            self.number_of_steps,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_curve_generation_settings(
    parameters: Mapping[str, Any],
    project_parameters_path: str | Path,
) -> CurveGenerationSettings:
    with Path(project_parameters_path).open(encoding="utf-8") as parameter_file:
        project_parameters = json.load(parameter_file)

    target_stresses = project_parameters["BoundingBoxServoLoadingSettings"][
        "BoundingBoxServoLoadingStress"
    ]
    default_target_stress = sum(target_stresses) / len(target_stresses)
    return parse_curve_generation_settings(parameters, default_target_stress)


def parse_curve_generation_settings(
    parameters: Mapping[str, Any],
    default_target_stress: float,
) -> CurveGenerationSettings:
    generation = parameters["random_particle_generation_parameters"]
    minimum_stress = _positive_number(
        generation["minimum_mean_stress"],
        "random_particle_generation_parameters.minimum_mean_stress",
    )
    legacy_density = _density(
        generation["target_packing_density"],
        "random_particle_generation_parameters.target_packing_density",
    )

    raw_settings = parameters.get("curve_generation")
    if raw_settings is None:
        target_stress = max(
            _positive_number(default_target_stress, "ProjectParameters target stress"),
            minimum_stress,
        )
        return CurveGenerationSettings(
            mode=SINGLE_POINT,
            initial_density=legacy_density,
            final_density=legacy_density,
            initial_stress=target_stress,
            final_stress=target_stress,
            number_of_steps=1,
        )

    if not isinstance(raw_settings, Mapping):
        raise ValueError("curve_generation must be a JSON object.")

    mode = raw_settings.get("mode", SINGLE_POINT)
    if mode not in SUPPORTED_MODES:
        supported = ", ".join(SUPPORTED_MODES)
        raise ValueError(
            f"curve_generation.mode must be one of: {supported}. Got {mode!r}."
        )

    if mode == SINGLE_POINT:
        density = _density(
            raw_settings.get("target_density", legacy_density),
            "curve_generation.target_density",
        )
        target_stress = _stress_at_or_above_minimum(
            raw_settings.get("target_stress", default_target_stress),
            "curve_generation.target_stress",
            minimum_stress,
        )
        return CurveGenerationSettings(
            mode=mode,
            initial_density=density,
            final_density=density,
            initial_stress=target_stress,
            final_stress=target_stress,
            number_of_steps=1,
        )

    initial_density = _density(
        raw_settings.get("initial_density", legacy_density),
        "curve_generation.initial_density",
    )
    number_of_steps = _positive_integer(
        raw_settings.get("number_of_steps", 20),
        "curve_generation.number_of_steps",
    )
    initial_stress = _stress_at_or_above_minimum(
        raw_settings.get("initial_stress", minimum_stress),
        "curve_generation.initial_stress",
        minimum_stress,
    )

    if mode == STRESS_SWEEP:
        final_stress = _stress_at_or_above_minimum(
            _required(raw_settings, "final_stress"),
            "curve_generation.final_stress",
            minimum_stress,
        )
        if initial_stress == final_stress:
            raise ValueError(
                "A stress_sweep requires different initial_stress and final_stress values."
            )
        return CurveGenerationSettings(
            mode=mode,
            initial_density=initial_density,
            final_density=initial_density,
            initial_stress=initial_stress,
            final_stress=final_stress,
            number_of_steps=number_of_steps,
        )

    final_density = _density(
        _required(raw_settings, "final_density"),
        "curve_generation.final_density",
    )
    if final_density <= initial_density:
        raise ValueError(
            "A density_sweep requires final_density to be greater than initial_density."
        )
    fixed_stress = _stress_at_or_above_minimum(
        _required(raw_settings, "fixed_stress"),
        "curve_generation.fixed_stress",
        minimum_stress,
    )
    if fixed_stress < initial_stress:
        raise ValueError(
            "A density_sweep requires fixed_stress to be at least initial_stress."
        )
    return CurveGenerationSettings(
        mode=mode,
        initial_density=initial_density,
        final_density=final_density,
        initial_stress=initial_stress,
        final_stress=fixed_stress,
        number_of_steps=number_of_steps,
    )


def logarithmic_stress_targets(
    initial_stress: float,
    final_stress: float,
    number_of_steps: int,
) -> tuple[float, ...]:
    """Return both endpoints separated by the requested logarithmic intervals."""
    initial_stress = _positive_number(initial_stress, "initial_stress")
    final_stress = _positive_number(final_stress, "final_stress")
    number_of_steps = _positive_integer(number_of_steps, "number_of_steps")
    if initial_stress == final_stress:
        return (initial_stress,)
    ratio = (final_stress / initial_stress) ** (1.0 / number_of_steps)
    targets = [initial_stress * ratio**step for step in range(number_of_steps + 1)]
    targets[-1] = final_stress
    return tuple(targets)


def _required(settings: Mapping[str, Any], name: str) -> Any:
    if name not in settings:
        raise ValueError(f"curve_generation.{name} is required for this mode.")
    return settings[name]


def _density(value: Any, name: str) -> float:
    density = _number(value, name)
    if not 0.0 < density < 1.0:
        raise ValueError(f"{name} must be between 0 and 1. Got {density}.")
    return density


def _stress_at_or_above_minimum(value: Any, name: str, minimum: float) -> float:
    stress = _positive_number(value, name)
    if stress < minimum:
        raise ValueError(f"{name} must be at least minimum_mean_stress ({minimum} Pa).")
    return stress


def _positive_number(value: Any, name: str) -> float:
    number = _number(value, name)
    if number <= 0.0:
        raise ValueError(f"{name} must be greater than zero. Got {number}.")
    return number


def _number(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a number. Got {value!r}.")
    return float(value)


def _positive_integer(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{name} must be an integer greater than zero. Got {value!r}.")
    return value
