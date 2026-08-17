# IRESR point and curve generation

The `improved_radius_expansion_with_servo_control_method` accepts an optional
top-level `curve_generation` object in `ParametersDEMGen.json`. If this object
is omitted, DEMGen keeps the previous `single_point` behavior: density comes
from `random_particle_generation_parameters.target_packing_density` and stress
comes from `ProjectParametersDEM.json`.

All stresses are positive values in Pa. A configured stress cannot be lower
than `random_particle_generation_parameters.minimum_mean_stress`.

## Single point

```json
"curve_generation": {
    "mode": "single_point",
    "target_density": 0.625,
    "target_stress": 50000.0
}
```

The existing `packing_density_delta_list` retry strategy remains active in this
mode.

## Fractional zigzag point

```json
"curve_generation": {
    "mode": "zigzag_point",
    "initial_density": 0.58,
    "initial_stress": 100000000.0,
    "target_density": 0.60,
    "target_stress": 400000000.0,
    "step_fraction": 0.5,
    "maximum_iterations": 20
}
```

The search alternates a stress correction followed by an ascending density
correction. `step_fraction` is the fraction of the remaining error corrected
by each leg. Stress advances logarithmically while density advances linearly:

```text
next_stress = current_stress * (target_stress / current_stress) ** step_fraction
next_density = current_density + step_fraction * (target_density - current_density)
```

The controlled stress normally supplies `current_stress`. If the measured
stress crosses the final target, the next leg starts from that measurement so
the stress correction can reverse direction. Density corrections never
descend, so `target_density` must be greater than `initial_density`.

The search stops when both existing packing-density and mean-stress tolerances
are satisfied. It fails instead of looping indefinitely if
`maximum_iterations` stress corrections are exhausted. `step_fraction`
defaults to `0.5`, `maximum_iterations` defaults to `20`, and only the final
packing/checkpoint is saved.

## Constant-density stress sweep

```json
"curve_generation": {
    "mode": "stress_sweep",
    "initial_density": 0.625,
    "initial_stress": 1000.0,
    "final_stress": 200000.0,
    "number_of_steps": 20
}
```

The pressure targets are always logarithmically spaced. `number_of_steps` is
the number of intervals, so both endpoints are saved and the example produces
21 curve points. Reverse the two stress values to obtain the upper boundary:

```json
"curve_generation": {
    "mode": "stress_sweep",
    "initial_density": 0.625,
    "initial_stress": 200000.0,
    "final_stress": 1000.0,
    "number_of_steps": 20
}
```

Density is set by the initial packing and is not actively controlled during
the pressure sweep. It can therefore vary slightly along the curve.

## Cyclic stress

```json
"curve_generation": {
    "mode": "cyclic_stress",
    "initial_density": 0.625,
    "minimum_stress": 12500.0,
    "maximum_stress": 50000.0,
    "number_of_cycles": 3
}
```

DEMGen first stabilizes and saves the packing at `minimum_stress`. Each complete
cycle then compresses to `maximum_stress` and decompresses back to
`minimum_stress`. Thus, the example follows seven stable targets:

```text
12500, 50000, 12500, 50000, 12500, 50000, 12500 Pa
```

Both stress limits must be at least `minimum_mean_stress`, `maximum_stress`
must be greater than `minimum_stress`, and `number_of_cycles` must be a positive
integer. Density is initialized from `initial_density` but is not controlled
during cycling; it changes naturally as the servo compresses and decompresses
the box.

Every stable endpoint is saved. For example, the first cycle produces:

```text
inletPGDEM_cycle_000_minimum.mdpa
inletPGDEM_cycle_001_maximum.mdpa
inletPGDEM_cycle_001_minimum.mdpa
```

## Constant-stress ascending density sweep

```json
"curve_generation": {
    "mode": "density_sweep",
    "initial_density": 0.625,
    "final_density": 0.65,
    "initial_stress": 1000.0,
    "fixed_stress": 20000.0,
    "number_of_steps": 20
}
```

DEMGen first follows a logarithmic pressure ramp from `initial_stress` to
`fixed_stress`. The ramp uses `number_of_steps` intervals but does not save
packing checkpoints. Once the fixed stress is stable, DEMGen saves the first
vertical-curve point and increases density using the original successive
zero-friction phases. Only ascending density sweeps are supported.

## Outputs

Every selected curve point produces:

- An `inletPGDEM_*.mdpa` packing in the generated case directory.
- A row in `stress_tensor_save.txt`.
- A complete GiD result at the checkpoint time.

The final packing is also written to `show_packing/inletPGDEM.mdpa`. The saved
state rows contain, in order: time, mean stress, density, full stress tensor,
mean coordination number, conductivity tensor and trace, mean tangential
stress, tangential stress tensor, shear stress, fabric tensor, and the second
invariant of its deviatoric tensor.

For `zigzag_point`, intermediate legs are not selected curve points: only the
final `inletPGDEM_target.mdpa`, measurement row, and GiD checkpoint are written.

## Small-simulation validation suite

The integration suite runs the public DEMGen command against six deterministic
cases: single point, zigzag point, ascending stress sweep, descending stress
sweep, ascending density sweep, and cyclic stress. The single-point and stress-sweep cases
target density `0.60` with 248 particles. The zigzag case climbs from `0.58` to
`0.60` with 240 particles, and the vertical case climbs from `0.59` to `0.60`
with 244 particles. Every case uses an isolated temporary directory. Run it in
an environment where Kratos DEM is available:

```bash
DEMGEN_RUN_SIMULATION_TESTS=1 python3 -m unittest tests.test_curve_generation_simulations -v
```

The tests validate successful completion, logarithmic target order, the
fractional zigzag target, checkpoint MDPA files, GiD results, all 44 measured
values, increasing density, cyclic extrema, and the absence of intermediate
zigzag packings.
The environment variable keeps these simulations out of the fast default
unit-test run.
