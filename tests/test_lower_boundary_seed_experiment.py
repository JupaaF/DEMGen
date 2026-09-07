import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = (
    PROJECT_ROOT
    / "experiments"
    / "lower_boundary_seed_sensitivity"
    / "prepare_cases.py"
)
SPEC = importlib.util.spec_from_file_location("prepare_seed_cases", SCRIPT_PATH)
prepare_seed_cases = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(prepare_seed_cases)


class LowerBoundarySeedExperimentTests(unittest.TestCase):
    def test_prepares_consecutive_reproducible_single_point_cases(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / "cases"
            prepare_seed_cases.prepare_cases(
                PROJECT_ROOT / "uniform_hard_50kPa_0.625",
                output,
                3,
            )

            for seed in range(1, 4):
                case = output / f"seed_{seed:03d}"
                prepare_seed_cases.validate_case(case, seed)
                parameters = json.loads(
                    (case / "ParametersDEMGen.json").read_text()
                )
                self.assertEqual(
                    parameters["curve_generation"],
                    {
                        "mode": "stress_sweep",
                        "initial_density": 0.5,
                        "initial_stress": 1000.0,
                        "final_stress": 1000.0,
                        "number_of_steps": 1,
                    },
                )

            manifest = (root / "experiment_manifest.csv").read_text()
            self.assertEqual(len(manifest.splitlines()), 4)

    def test_refuses_to_overwrite_simulation_outputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / "cases"
            prepare_seed_cases.prepare_cases(
                PROJECT_ROOT / "uniform_hard_50kPa_0.625",
                output,
                1,
            )
            (output / "seed_001" / "generated_cases").mkdir()

            with self.assertRaisesRegex(RuntimeError, "Refusing to overwrite"):
                prepare_seed_cases.prepare_cases(
                    PROJECT_ROOT / "uniform_hard_50kPa_0.625",
                    output,
                    1,
                )


if __name__ == "__main__":
    unittest.main()
