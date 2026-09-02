#!/usr/bin/env python3
"""Extract and plot cyclic-stress history from an Acuario Slurm log."""

from __future__ import annotations

import argparse
from bisect import bisect_left
import csv
import json
from pathlib import Path
import re


SIMULATION_TIME_PATTERN = re.compile(
    r"DEM:\s+Simulation time:\s+([0-9.eE+-]+)\s+seconds"
)
CYCLIC_SAMPLE_PATTERN = re.compile(
    r"\[cyclic_stress_controlled\]\s+"
    r"phase=(?P<phase>[^,]+),\s+"
    r"cycle=(?P<cycle>\d+),\s+"
    r"stress=(?P<stress>[0-9.eE+-]+)\s+Pa,.*?"
    r"density=(?P<density>[0-9.eE+-]+)(?:/[0-9.eE+-]+)?"
)
STABLE_ENDPOINT_PATTERN = re.compile(
    r"\[cyclic_stress_controlled\]\s+"
    r"stable after cycle threshold crossing:\s+"
    r"phase=(?P<phase>[^,]+),\s+"
    r"cycle=(?P<cycle>\d+),\s+"
    r"stress=(?P<stress>[0-9.eE+-]+)\s+Pa,\s+"
    r"density=(?P<density>[0-9.eE+-]+)"
)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("log", type=Path)
    parser.add_argument("checkpoint", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def nearest_time(
    line_number: int,
    anchor_lines: list[int],
    anchor_times: list[float],
) -> float:
    position = bisect_left(anchor_lines, line_number)
    candidates = []
    if position < len(anchor_lines):
        candidates.append(position)
    if position:
        candidates.append(position - 1)
    if not candidates:
        raise RuntimeError("The log contains no simulation-time markers.")
    closest = min(
        candidates,
        key=lambda index: abs(anchor_lines[index] - line_number),
    )
    return anchor_times[closest]


def extract_history(
    log_path: Path,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    anchors = []
    raw_samples = []
    raw_endpoints = []
    for line_number, line in enumerate(lines, start=1):
        time_match = SIMULATION_TIME_PATTERN.search(line)
        if time_match:
            anchors.append((line_number, float(time_match.group(1))))
        sample_match = CYCLIC_SAMPLE_PATTERN.search(line)
        if sample_match:
            raw_samples.append((line_number, sample_match.groupdict()))
        endpoint_match = STABLE_ENDPOINT_PATTERN.search(line)
        if endpoint_match:
            raw_endpoints.append((line_number, endpoint_match.groupdict()))

    if not anchors:
        raise RuntimeError("No simulation-time markers were found in the log.")
    if not raw_samples:
        raise RuntimeError("No cyclic stress/density samples were found in the log.")

    anchor_lines = [line for line, _ in anchors]
    anchor_times = [time for _, time in anchors]
    samples = []
    for line_number, values in raw_samples:
        stress_pa = float(values["stress"])
        samples.append(
            {
                "simulation_time_s": nearest_time(
                    line_number,
                    anchor_lines,
                    anchor_times,
                ),
                "pressure_pa": stress_pa,
                "pressure_kpa": stress_pa / 1000.0,
                "density": float(values["density"]),
                "phase": values["phase"],
                "cycle": int(values["cycle"]),
                "log_line": line_number,
            }
        )
    endpoints = []
    for line_number, values in raw_endpoints:
        stress_pa = float(values["stress"])
        endpoints.append(
            {
                "simulation_time_s": nearest_time(
                    line_number,
                    anchor_lines,
                    anchor_times,
                ),
                "pressure_pa": stress_pa,
                "pressure_kpa": stress_pa / 1000.0,
                "density": float(values["density"]),
                "phase": values["phase"],
                "cycle": int(values["cycle"]),
                "log_line": line_number,
            }
        )
    return samples, endpoints


def write_csv(samples: list[dict[str, object]], output_path: Path) -> None:
    with output_path.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=list(samples[0]))
        writer.writeheader()
        writer.writerows(samples)


def plot_history(
    samples: list[dict[str, object]],
    checkpoint: dict[str, object],
    output_path: Path,
    job_label: str,
    detail_label: str | None = None,
) -> None:
    import matplotlib.pyplot as plt

    settings = checkpoint["settings"]
    times = [sample["simulation_time_s"] for sample in samples]
    pressures = [sample["pressure_kpa"] for sample in samples]
    densities = [sample["density"] for sample in samples]

    figure, (pressure_axis, density_axis) = plt.subplots(
        2,
        1,
        figsize=(12, 7),
        sharex=True,
        constrained_layout=True,
    )
    pressure_axis.plot(times, pressures, color="#1976d2", linewidth=0.9)
    pressure_axis.set_yscale("log")
    pressure_axis.axhline(
        float(settings["target_stress"]) / 1000.0,
        color="#d32f2f",
        linestyle="--",
        linewidth=1.0,
        label="Target pressure",
    )
    pressure_axis.set_ylabel("Pressure [kPa]")
    pressure_axis.grid(alpha=0.25)
    pressure_axis.legend(loc="upper right")

    density_axis.plot(times, densities, color="#00897b", linewidth=0.9)
    density_axis.axhline(
        float(settings["target_packing_density"]),
        color="#d32f2f",
        linestyle="--",
        linewidth=1.0,
        label="Target density",
    )
    density_axis.set_xlabel("Simulation time [s]")
    density_axis.set_ylabel("Packing density [-]")
    density_axis.grid(alpha=0.25)
    density_axis.legend(loc="upper right")

    title = f"Cyclic stress-controlled packing — {job_label}"
    if detail_label:
        title += f" — {detail_label}"
    figure.suptitle(title)
    figure.savefig(output_path, dpi=200)
    plt.close(figure)


def plot_endpoint_density(
    endpoints: list[dict[str, object]],
    checkpoint: dict[str, object],
    output_path: Path,
    job_label: str,
) -> None:
    import matplotlib.pyplot as plt

    settings = checkpoint["settings"]
    target = float(settings["target_packing_density"])
    tolerance = float(settings["density_tolerance"])
    figure, axis = plt.subplots(figsize=(11, 5), constrained_layout=True)
    for phase, label, color in (
        ("high_pressure", "Stable at 200 kPa", "#1976d2"),
        ("low_pressure", "Stable at 1 kPa", "#f57c00"),
    ):
        phase_endpoints = [
            endpoint for endpoint in endpoints if endpoint["phase"] == phase
        ]
        axis.plot(
            [endpoint["cycle"] for endpoint in phase_endpoints],
            [endpoint["density"] for endpoint in phase_endpoints],
            marker="o",
            markersize=2.5,
            linewidth=1.0,
            label=label,
            color=color,
        )
    axis.axhspan(
        target - tolerance,
        target + tolerance,
        color="#43a047",
        alpha=0.15,
        label="Target tolerance",
    )
    axis.axhline(target, color="#d32f2f", linestyle="--", linewidth=1.0)
    axis.set_xlabel("Completed cycle")
    axis.set_ylabel("Stable packing density [-]")
    axis.set_title(f"Stable cycle endpoints — {job_label}")
    axis.grid(alpha=0.25)
    axis.legend()
    figure.savefig(output_path, dpi=200)
    plt.close(figure)


def main() -> None:
    arguments = parse_arguments()
    arguments.output_dir.mkdir(parents=True, exist_ok=True)
    checkpoint = json.loads(arguments.checkpoint.read_text(encoding="utf-8"))
    samples, endpoints = extract_history(arguments.log)
    csv_path = arguments.output_dir / "pressure_density_history.csv"
    endpoints_csv_path = arguments.output_dir / "stable_cycle_endpoints.csv"
    plot_path = arguments.output_dir / "pressure_density_vs_time.png"
    endpoints_plot_path = arguments.output_dir / "stable_density_vs_cycle.png"
    recent_plot_path = (
        arguments.output_dir / "pressure_density_recent_cycles.png"
    )
    write_csv(samples, csv_path)
    write_csv(endpoints, endpoints_csv_path)
    job_match = re.search(r"(\d+)", arguments.log.stem)
    job_label = f"job {job_match.group(1)}" if job_match else arguments.log.stem
    plot_history(samples, checkpoint, plot_path, job_label)
    latest_cycle = max(int(sample["cycle"]) for sample in samples)
    recent_samples = [
        sample
        for sample in samples
        if int(sample["cycle"]) >= max(0, latest_cycle - 9)
    ]
    plot_history(
        recent_samples,
        checkpoint,
        recent_plot_path,
        job_label,
        "last 10 cycles",
    )
    plot_endpoint_density(
        endpoints,
        checkpoint,
        endpoints_plot_path,
        job_label,
    )
    print(
        f"Wrote {len(samples)} samples spanning "
        f"{samples[0]['simulation_time_s']:.6f} to "
        f"{samples[-1]['simulation_time_s']:.6f} s."
    )
    print(csv_path)
    print(plot_path)
    print(endpoints_csv_path)
    print(endpoints_plot_path)
    print(recent_plot_path)


if __name__ == "__main__":
    main()
