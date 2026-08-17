import json
import os
from pathlib import Path
import signal
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
STUDY_CASE_DIR = Path(
    os.environ.get(
        "DEMGEN_STUDY_CASE_DIR",
        "/home/juan-pablo/Documents/Resultados DEMGen/study_cases/"
        "a_normal_case/uniform_hard_50kPa_0.625",
    )
)
RUN_SIMULATIONS = os.environ.get("DEMGEN_RUN_SIMULATION_TESTS") == "1"
STRICT_STRESS_TOLERANCE = 10.0
TARGET_DENSITY = 0.625
REDUCED_DOMAIN_LENGTH = 0.084


@unittest.skipUnless(
    RUN_SIMULATIONS,
    "Set DEMGEN_RUN_SIMULATION_TESTS=1 to run the Kratos simulation suite.",
)
class CurveGenerationSimulationTests(unittest.TestCase):
    def test_cyclic_stress_saves_every_stable_minimum_and_maximum(self):
        with self.run_simulation(
            {
                "mode": "cyclic_stress",
                "initial_density": TARGET_DENSITY,
                "minimum_stress": 12500.0,
                "maximum_stress": 50000.0,
                "number_of_cycles": 1,
            },
            density_tolerance=0.0001,
        ) as case_dir:
            self.assert_successful_case(case_dir)
            self.assertEqual(
                self.target_sequence(case_dir),
                [12500.0, 50000.0, 12500.0],
            )
            self.assertEqual(self.checkpoint_rows(case_dir), 3)
            for output_name in (
                "inletPGDEM_cycle_000_minimum.mdpa",
                "inletPGDEM_cycle_001_maximum.mdpa",
                "inletPGDEM_cycle_001_minimum.mdpa",
            ):
                self.assertTrue((case_dir / output_name).is_file())
            self.assert_checkpoint_stresses(
                case_dir,
                [12500.0, 50000.0, 12500.0],
                STRICT_STRESS_TOLERANCE,
            )
            self.assert_complete_measurements(case_dir)
            self.assert_gid_checkpoints(case_dir)

    def test_single_point_writes_one_complete_checkpoint(self):
        with self.run_simulation(
            {
                "mode": "single_point",
                "target_density": TARGET_DENSITY,
                "target_stress": 50000.0,
            },
            density_tolerance=0.0001,
        ) as case_dir:
            self.assert_successful_case(case_dir)
            self.assertEqual(self.checkpoint_rows(case_dir), 1)
            self.assertTrue((case_dir / "inletPGDEM_target.mdpa").is_file())
            self.assert_density_near_sixty_two_percent(case_dir)
            self.assert_checkpoint_stresses(
                case_dir,
                [50000.0],
                STRICT_STRESS_TOLERANCE,
            )
            self.assert_complete_measurements(case_dir)
            self.assert_gid_checkpoints(case_dir)

    def test_zigzag_point_saves_only_the_final_fractional_search_result(self):
        with self.run_simulation(
            {
                "mode": "zigzag_point",
                "initial_density": 0.605,
                "initial_stress": 12500.0,
                "target_density": TARGET_DENSITY,
                "target_stress": 50000.0,
                "step_fraction": 0.5,
                "maximum_iterations": 20,
            },
            density_tolerance=0.0001,
        ) as case_dir:
            self.assert_successful_case(case_dir)
            targets = self.target_sequence(case_dir)
            self.assertEqual(targets[0], 25000.0)
            self.assertEqual(targets[-1], 50000.0)
            self.assertGreaterEqual(len(targets), 2)
            self.assertEqual(self.checkpoint_rows(case_dir), 1)
            self.assertTrue((case_dir / "inletPGDEM_target.mdpa").is_file())
            self.assertFalse(list(case_dir.glob("inletPGDEM_density_*.mdpa")))
            self.assertFalse(list(case_dir.glob("inletPGDEM_[0-9]*.mdpa")))
            self.assert_density_near_sixty_two_percent(case_dir)
            self.assert_checkpoint_stresses(
                case_dir,
                [50000.0],
                STRICT_STRESS_TOLERANCE,
            )
            self.assert_complete_measurements(case_dir)
            self.assert_gid_checkpoints(case_dir)

    def test_ascending_stress_sweep_saves_every_logarithmic_target(self):
        with self.run_simulation(
            {
                "mode": "stress_sweep",
                "initial_density": TARGET_DENSITY,
                "initial_stress": 12500.0,
                "final_stress": 50000.0,
                "number_of_steps": 2,
            },
            density_tolerance=0.0001,
        ) as case_dir:
            self.assert_successful_case(case_dir)
            self.assertEqual(
                self.target_sequence(case_dir),
                [12500.0, 25000.0, 50000.0],
            )
            self.assertEqual(self.checkpoint_rows(case_dir), 3)
            for target in (12500, 25000, 50000):
                self.assertTrue((case_dir / f"inletPGDEM_{target}.mdpa").is_file())
            self.assert_density_near_sixty_two_percent(case_dir)
            self.assert_checkpoint_stresses(
                case_dir,
                [12500.0, 25000.0, 50000.0],
                STRICT_STRESS_TOLERANCE,
            )
            self.assert_complete_measurements(case_dir)
            self.assert_gid_checkpoints(case_dir)

    def test_descending_stress_sweep_saves_targets_in_reverse_order(self):
        with self.run_simulation(
            {
                "mode": "stress_sweep",
                "initial_density": TARGET_DENSITY,
                "initial_stress": 50000.0,
                "final_stress": 12500.0,
                "number_of_steps": 2,
            },
            density_tolerance=0.0001,
        ) as case_dir:
            self.assert_successful_case(case_dir)
            self.assertEqual(
                self.target_sequence(case_dir),
                [50000.0, 25000.0, 12500.0],
            )
            self.assertEqual(self.checkpoint_rows(case_dir), 3)
            self.assert_density_near_sixty_two_percent(case_dir)
            self.assert_checkpoint_stresses(
                case_dir,
                [50000.0, 25000.0, 12500.0],
                STRICT_STRESS_TOLERANCE,
            )
            self.assert_complete_measurements(case_dir)
            self.assert_gid_checkpoints(case_dir)

    def test_density_sweep_saves_only_the_ascending_vertical_curve(self):
        with self.run_simulation(
            {
                "mode": "density_sweep",
                "initial_density": 0.615,
                "final_density": TARGET_DENSITY,
                "initial_stress": 12500.0,
                "fixed_stress": 50000.0,
                "number_of_steps": 1,
            },
            density_tolerance=0.0001,
        ) as case_dir:
            self.assert_successful_case(case_dir)
            self.assertEqual(
                self.target_sequence(case_dir),
                [12500.0, 50000.0],
            )
            density_packings = sorted(case_dir.glob("inletPGDEM_density_*.mdpa"))
            self.assertGreaterEqual(len(density_packings), 2)
            self.assertEqual(len(density_packings), self.checkpoint_rows(case_dir))
            self.assertFalse((case_dir / "inletPGDEM_12500.mdpa").exists())
            self.assertFalse((case_dir / "inletPGDEM_50000.mdpa").exists())

            densities = self.checkpoint_densities(case_dir)
            self.assertGreater(densities[-1], densities[0])
            self.assertGreaterEqual(densities[-1], 0.623)
            self.assert_density_near_sixty_two_percent(case_dir)
            self.assert_checkpoint_stresses(
                case_dir,
                [50000.0] * len(density_packings),
                STRICT_STRESS_TOLERANCE,
            )
            self.assert_complete_measurements(case_dir)
            self.assert_gid_checkpoints(case_dir)

    def run_simulation(
        self,
        curve_generation,
        density_tolerance=1.0,
        stress_tolerance=STRICT_STRESS_TOLERANCE,
        timeout=3600,
    ):
        temporary_case = tempfile.TemporaryDirectory(prefix="demgen-curve-test-")
        run_dir = Path(temporary_case.name)
        self.addCleanup(temporary_case.cleanup)

        parameters = json.loads(
            (STUDY_CASE_DIR / "ParametersDEMGen.json").read_text(encoding="utf-8")
        )
        parameters.update(
            {
                "packing_num": 1,
                "domain_length_x": REDUCED_DOMAIN_LENGTH,
                "domain_length_y": REDUCED_DOMAIN_LENGTH,
                "domain_length_z": REDUCED_DOMAIN_LENGTH,
                "packing_charcterization_option": False,
                "curve_generation": curve_generation,
            }
        )
        generation = parameters["random_particle_generation_parameters"]
        generation.update(
            {
                "target_packing_density": TARGET_DENSITY,
                "tolerance_of_packing_density": density_tolerance,
                "tolerance_of_target_mean_stress": stress_tolerance,
            }
        )
        if curve_generation["mode"] != "single_point":
            generation["packing_density_delta_list"] = [0.0]
        generation["random_variable_settings"].update(
            {
                "do_use_seed": True,
                "seed": 1,
            }
        )
        parameters_path = run_dir / "ParametersDEMGen.json"
        parameters_path.write_text(json.dumps(parameters, indent=2), encoding="utf-8")

        project_parameters = json.loads(
            (STUDY_CASE_DIR / "ProjectParametersDEM.json").read_text(encoding="utf-8")
        )
        project_parameters.update(
            {
                "BoundingBoxMaxX": REDUCED_DOMAIN_LENGTH / 2,
                "BoundingBoxMaxY": REDUCED_DOMAIN_LENGTH / 2,
                "BoundingBoxMaxZ": REDUCED_DOMAIN_LENGTH / 2,
                "BoundingBoxMinX": -REDUCED_DOMAIN_LENGTH / 2,
                "BoundingBoxMinY": -REDUCED_DOMAIN_LENGTH / 2,
                "BoundingBoxMinZ": -REDUCED_DOMAIN_LENGTH / 2,
                "MaxTimeStep": 5e-7,
                "FinalTime": 2.5e-4,
                "GraphExportFreq": 2.5e-4,
                "VelTrapGraphExportFreq": 2.5e-4,
                "OutputTimeStep": 2.5e-4,
            }
        )
        (run_dir / "ProjectParametersDEM.json").write_text(
            json.dumps(project_parameters, indent=2),
            encoding="utf-8",
        )
        shutil.copyfile(
            STUDY_CASE_DIR / "MaterialsDEM.json",
            run_dir / "MaterialsDEM.json",
        )

        environment = os.environ.copy()
        environment["OMP_NUM_THREADS"] = "1"
        print(
            "\n[simulation-suite] starting "
            f"mode={curve_generation['mode']} with {curve_generation}",
            flush=True,
        )
        process = subprocess.Popen(
            [
                sys.executable,
                PROJECT_ROOT / "src" / "DEMGen_framework_main.py",
                parameters_path,
            ],
            cwd=PROJECT_ROOT,
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        output_lines = []

        def relay_progress():
            for line in process.stdout:
                output_lines.append(line)
                if "[curve_generation]" in line:
                    print(line, end="", flush=True)

        output_reader = threading.Thread(target=relay_progress, daemon=True)
        output_reader.start()
        try:
            process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            output_reader.join(timeout=5)
            output = "".join(output_lines)
            self.fail(
                f"DEMGen exceeded the {timeout}-second timeout.\n{output[-12000:]}"
            )

        output_reader.join(timeout=5)
        if process.stdout is not None:
            process.stdout.close()
        output = "".join(output_lines)
        (run_dir / "simulation.log").write_text(output, encoding="utf-8")
        if process.returncode != 0:
            self.fail(
                f"DEMGen exited with {process.returncode}.\n{output[-12000:]}"
            )
        print(
            f"[simulation-suite] completed mode={curve_generation['mode']}",
            flush=True,
        )

        case_dir = run_dir / "generated_cases" / "case_1"
        return _CaseDirectory(temporary_case, case_dir)

    def assert_successful_case(self, case_dir):
        if not (case_dir / "success.txt").is_file():
            simulation_log = case_dir.parents[1] / "simulation.log"
            generated_files = "\n".join(
                str(path.relative_to(case_dir))
                for path in sorted(case_dir.rglob("*"))
                if path.is_file()
            )
            self.fail(
                "The simulation did not create success.txt.\n"
                f"Generated files:\n{generated_files}\n\n"
                + simulation_log.read_text(encoding="utf-8")[-12000:]
            )
        self.assertTrue((case_dir / "show_packing" / "inletPGDEM.mdpa").is_file())
        gid_files = list((case_dir / "inletPG_Post_Files").glob("*"))
        self.assertTrue(gid_files, "The simulation did not produce GiD results.")
        self.assertGreaterEqual(self.particle_count(case_dir), 200)
        self.assertLessEqual(self.particle_count(case_dir), 700)

    def checkpoint_rows(self, case_dir):
        return len(
            (case_dir / "stress_tensor_save.txt").read_text(encoding="utf-8").splitlines()
        )

    def checkpoint_densities(self, case_dir):
        return [
            float(row.split()[2])
            for row in (case_dir / "stress_tensor_save.txt")
            .read_text(encoding="utf-8")
            .splitlines()
        ]

    def checkpoint_stresses(self, case_dir):
        return [
            float(row.split()[1])
            for row in (case_dir / "stress_tensor_save.txt")
            .read_text(encoding="utf-8")
            .splitlines()
        ]

    def assert_checkpoint_stresses(self, case_dir, targets, tolerance):
        stresses = self.checkpoint_stresses(case_dir)
        self.assertEqual(len(stresses), len(targets))
        for measured, target in zip(stresses, targets):
            self.assertLessEqual(abs(measured - target), tolerance)

    def assert_density_near_sixty_two_percent(self, case_dir):
        for density in self.checkpoint_densities(case_dir):
            self.assertGreaterEqual(density, 0.60)
            self.assertLessEqual(density, 0.635)

    def target_sequence(self, case_dir):
        targets = [
            float(line.split()[1])
            for line in (case_dir / "target_stress.txt")
            .read_text(encoding="utf-8")
            .splitlines()
        ]
        sequence = []
        for target in targets:
            if not sequence or target != sequence[-1]:
                sequence.append(target)
        return sequence

    def assert_complete_measurements(self, case_dir):
        rows = (
            (case_dir / "stress_tensor_save.txt")
            .read_text(encoding="utf-8")
            .splitlines()
        )
        self.assertTrue(rows)
        self.assertTrue(all(len(row.split()) == 44 for row in rows))

    def assert_gid_checkpoints(self, case_dir):
        gid_results = list((case_dir / "inletPG_Post_Files").glob("*.post.res"))
        self.assertGreaterEqual(len(gid_results), self.checkpoint_rows(case_dir))

    def particle_count(self, case_dir):
        lines = (case_dir / "inletPGDEM_ini.mdpa").read_text(encoding="utf-8").splitlines()
        begin = lines.index("Begin Nodes") + 1
        end = lines.index("End Nodes")
        return end - begin


class _CaseDirectory:
    def __init__(self, temporary_case, case_dir):
        self.temporary_case = temporary_case
        self.case_dir = case_dir

    def __enter__(self):
        return self.case_dir

    def __exit__(self, exc_type, exc_value, traceback):
        self.temporary_case.cleanup()
