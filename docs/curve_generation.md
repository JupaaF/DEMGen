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

## Small-simulation validation suite

The integration suite runs the public DEMGen command against four deterministic
cases: single point, ascending stress sweep, descending stress sweep, and
ascending density sweep. The single-point and stress-sweep cases target density
`0.60` with 248 particles. The vertical case climbs from `0.59` to `0.60` with
244 particles. Every case uses an isolated temporary directory. Run it in an
environment where Kratos DEM is available:

```bash
DEMGEN_RUN_SIMULATION_TESTS=1 python3 -m unittest tests.test_curve_generation_simulations -v
```

The tests validate successful completion, logarithmic target order, checkpoint
MDPA files, GiD results, all 44 measured values, and increasing density on the
vertical curve. The environment variable keeps these simulations out of the
fast default unit-test run.
