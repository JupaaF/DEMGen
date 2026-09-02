# Cyclic stress-controlled method

This generator implements the pressure protocol requested from method III of
Santos et al. without using radius expansion. It creates each case with exactly
10,000 non-overlapping polydisperse particles at an initial solid fraction of
`0.05`, in a cubic three-dimensional periodic box. Final radii are sampled by
number from `random_variable_settings.possible_values` and
`relative_frequencies`. `radius_scale_multiplier` is intentionally ignored:
there is no radius-expansion stage in this method.

Select the generator and provide its three user-controlled values in Pa:

```json
{
  "generator_name": "cyclic_stress_controlled_method",
  "packing_num": 1,
  "cyclic_stress_controlled_method_parameters": {
    "target_packing_density": 0.625,
    "target_stress": 50000.0,
    "minimum_cycle_pressure": 10000.0
  }
}
```

The pressure order must satisfy:

```text
0 < minimum_cycle_pressure < target_stress < 200000 Pa
```

During each moving leg, the stress target given to the box servo is updated
every DEM step from the measured mean stress. Compression uses
`min(measured_stress + 10000 Pa, 200000 Pa)` and decompression uses
`max(measured_stress - 10000 Pa, minimum_cycle_pressure)`. The controller keeps
the final phase limit separately, so this moving setpoint cannot exceed either
cycle endpoint.

During compression, crossing `200000 Pa` latches the threshold and reduces the
maximum box-servo velocity from `10 m/s` to `0.1 m/s`. The servo remains active
at `200000 Pa` so that stress does not collapse while DEMGen waits for the stress
window and unbalanced force to stabilize. It then changes the servo target to
the current minimum pressure and restores the `10 m/s` limit. The same
slow-servo stabilization occurs during decompression after crossing the minimum
pressure; the next cycle then targets `200000 Pa`. Once the density is within
tolerance at a stable minimum, the box moves toward `target_stress` for the
final stable check.

Stability uses the existing DEMGen stress and unbalanced-force tolerances from
`random_particle_generation_parameters`. The effective stress tolerance is
`max(configured_absolute_tolerance, 0.005 * phase_pressure)`, so the default
`10 Pa` tolerance becomes `1000 Pa`, `10 Pa`, and `50 Pa` at `200 kPa`, `1 kPa`,
and `10 kPa`, respectively.
The packing succeeds when the stable final state satisfies
`abs(density - target_packing_density) <= 0.002`.

If the stable density at `target_stress` is too low, another cycle uses the same
minimum pressure. If it is too high, the minimum pressure is multiplied by
`0.9` before the next cycle. This method intentionally does not enforce
`minimum_mean_stress`. It stops with an error after 10,000 unsuccessful cycles.

Every value above is fixed by the requested protocol except `packing_num`, the
particle-radius distribution, `target_packing_density`, `target_stress`, and
`minimum_cycle_pressure`.
`ProjectParametersDEM.json.FinalTime` is fixed at `10000 s` for this method.
Reaching it before a successful stable state terminates the case with an error.

## Runtime settings

This method fixes `MaxTimeStep` at `1e-6 s`. The Rayleigh limit must be checked
against the smallest configured radius (`0.003 m` in the reference
distribution). The bounding-box servo is updated every DEM step and remains
limited to `10 m/s`.

Stress is sampled every step. Density is measured for progress output every
1000 steps and whenever a stable state is detected. The more expensive
unbalanced-force measurement runs only after the rolling stress window is
inside its phase tolerance. Console progress therefore remains available
without measuring every packing property at every servo update.
The unbalanced-force measurement uses a sphere enclosing the complete deformed
box, including its corners and a particle-radius margin, so all particles and
contacts contribute to the RMS force ratio.

Intermediate GiD/VTK writing and energy accounting are disabled while generating
the packing. Kratos requires `ContactMeshOption` and `PostStressStrainOption` to
remain enabled internally for the global stress measurement that drives the
servo; their intermediate result files are not written. The successful packing
is still written to `show_packing`.

## Checkpoints and restart

After every stable phase transition, the method serializes all DEM model parts,
the deformed box limits, and the cyclic-controller state. Only the latest valid
checkpoint is retained. If execution is interrupted, rerun DEMGen with the same
parameter file; the existing generated case is reused and resumes from that
checkpoint. A checkpoint whose cyclic settings differ from the current request
is rejected instead of being silently reused. A generated case without the
same particle-radius distribution metadata is regenerated instead of mixing a
monodisperse checkpoint with a polydisperse request.
