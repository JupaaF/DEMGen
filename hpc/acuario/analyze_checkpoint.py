#!/usr/bin/env python3
"""Export a DEM checkpoint to VTU and calculate global packing descriptors."""

from __future__ import annotations

import argparse
import csv
from collections import deque
import json
import math
from pathlib import Path
from xml.sax.saxutils import escape

import numpy as np

import KratosMultiphysics as KM
import KratosMultiphysics.DEMApplication as DEM


MODEL_PART_NAMES = ("SpheresPart", "ContactPart")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("checkpoint_directory", type=Path)
    parser.add_argument("output_directory", type=Path)
    return parser.parse_args()


def load_model_part(
    checkpoint_directory: Path, name: str, label: str
) -> tuple[KM.Model, KM.ModelPart]:
    model = KM.Model()
    model_part = model.CreateModelPart(name)
    restart_path = checkpoint_directory / f"{name}__restart_files" / f"{name}_{label}"
    serializer = KM.FileSerializer(
        str(restart_path), KM.SerializerTraceType.SERIALIZER_NO_TRACE
    )
    serializer.Load(name, model_part)
    return model, model_part


def minimum_image(vector: np.ndarray, lengths: np.ndarray) -> np.ndarray:
    return vector - lengths * np.round(vector / lengths)


def j2(tensor: np.ndarray) -> float:
    symmetric = 0.5 * (tensor + tensor.T)
    deviator = symmetric - np.trace(symmetric) * np.eye(3) / 3.0
    return float(0.5 * np.sum(deviator * deviator))


def iterative_rattlers(
    adjacency: dict[int, set[int]], minimum_contacts: int
) -> set[int]:
    working = {particle_id: set(neighbors) for particle_id, neighbors in adjacency.items()}
    queue = deque(
        particle_id
        for particle_id, neighbors in working.items()
        if len(neighbors) < minimum_contacts
    )
    removed = set(queue)
    while queue:
        particle_id = queue.popleft()
        for neighbor_id in tuple(working[particle_id]):
            working[neighbor_id].discard(particle_id)
            if neighbor_id not in removed and len(working[neighbor_id]) < minimum_contacts:
                removed.add(neighbor_id)
                queue.append(neighbor_id)
        working[particle_id].clear()
    return removed


def scalar_values(values) -> str:
    return " ".join(f"{value:.17g}" if isinstance(value, float) else str(value) for value in values)


def tuple_values(values) -> str:
    return "\n".join(" ".join(f"{float(component):.17g}" for component in value) for value in values)


def data_array(
    name: str,
    values: str,
    vtk_type: str = "Float64",
    components: int | None = None,
    tuples: int | None = None,
) -> str:
    component_attribute = f' NumberOfComponents="{components}"' if components else ""
    tuple_attribute = f' NumberOfTuples="{tuples}"' if tuples else ""
    return (
        f'<DataArray type="{vtk_type}" Name="{escape(name)}"'
        f'{component_attribute}{tuple_attribute} format="ascii">\n{values}\n</DataArray>'
    )


def field_arrays(metrics: dict[str, object]) -> str:
    scalar_names = (
        "time_s",
        "cycle",
        "particle_count",
        "contact_count",
        "packing",
        "p_pa",
        "q_pa",
        "q_over_p",
        "mcn",
        "mcn_backbone_k2",
        "mcn_backbone_k3",
        "mcn_backbone_k4",
        "K_mean",
        "kd",
        "a",
    )
    arrays = []
    for name in scalar_names:
        vtk_type = "Int64" if name in {"cycle", "particle_count", "contact_count"} else "Float64"
        arrays.append(data_array(name, str(metrics[name]), vtk_type, tuples=1))
    for name in ("sigma_pa", "K", "Fabric"):
        arrays.append(
            data_array(name, tuple_values([np.asarray(metrics[name]).reshape(-1)]), components=9, tuples=1)
        )
    arrays.append(
        data_array("BoxBounds", scalar_values(metrics["box_bounds"]), components=6, tuples=1)
    )
    return "".join(arrays)


def write_particles_vtu(
    path: Path,
    nodes,
    adjacency: dict[int, set[int]],
    contact_ratios: dict[int, list[float]],
    rattlers: dict[int, set[int]],
    metrics: dict[str, object],
) -> None:
    ids = [node.Id for node in nodes]
    positions = [(node.X, node.Y, node.Z) for node in nodes]
    radii = [float(node.GetSolutionStepValue(KM.RADIUS)) for node in nodes]
    velocities = [node.GetSolutionStepValue(KM.VELOCITY) for node in nodes]
    angular_velocities = [node.GetSolutionStepValue(KM.ANGULAR_VELOCITY) for node in nodes]
    displacements = [node.GetSolutionStepValue(KM.DISPLACEMENT) for node in nodes]
    total_forces = [node.GetSolutionStepValue(KM.TOTAL_FORCES) for node in nodes]
    coordination = [len(adjacency[particle_id]) for particle_id in ids]
    mean_ratios = [
        float(np.mean(contact_ratios[particle_id])) if contact_ratios[particle_id] else 0.0
        for particle_id in ids
    ]
    max_ratios = [max(contact_ratios[particle_id], default=0.0) for particle_id in ids]
    point_data = [
        data_array("ParticleId", scalar_values(ids), "Int64"),
        data_array("Radius", scalar_values(radii)),
        data_array("Velocity", tuple_values(velocities), components=3),
        data_array("AngularVelocity", tuple_values(angular_velocities), components=3),
        data_array("Displacement", tuple_values(displacements), components=3),
        data_array("TotalForce", tuple_values(total_forces), components=3),
        data_array("CoordinationNumber", scalar_values(coordination), "Int32"),
    ]
    for threshold in (2, 3, 4):
        point_data.append(
            data_array(
                f"IsRattlerK{threshold}",
                scalar_values(int(particle_id in rattlers[threshold]) for particle_id in ids),
                "UInt8",
            )
        )
    point_data.extend(
        [
            data_array("MeanContactFtFn", scalar_values(mean_ratios)),
            data_array("MaxContactFtFn", scalar_values(max_ratios)),
        ]
    )
    count = len(nodes)
    cells = "".join(
        [
            data_array("connectivity", scalar_values(range(count)), "Int64"),
            data_array("offsets", scalar_values(range(1, count + 1)), "Int64"),
            data_array("types", scalar_values([1] * count), "UInt8"),
        ]
    )
    vtk = f'''<?xml version="1.0"?>
<VTKFile type="UnstructuredGrid" version="1.0" byte_order="LittleEndian">
  <UnstructuredGrid>
    <FieldData>{field_arrays(metrics)}</FieldData>
    <Piece NumberOfPoints="{count}" NumberOfCells="{count}">
      <PointData Scalars="Radius" Vectors="Velocity">{"".join(point_data)}</PointData>
      <CellData/>
      <Points>{data_array("Points", tuple_values(positions), components=3)}</Points>
      <Cells>{cells}</Cells>
    </Piece>
  </UnstructuredGrid>
</VTKFile>
'''
    path.write_text(vtk, encoding="utf-8")


def write_contacts_vtu(
    path: Path, contact_records: list[dict[str, object]], metrics: dict[str, object]
) -> None:
    positions = []
    for record in contact_records:
        positions.extend((record["point_0"], record["point_1_unwrapped"]))
    count = len(contact_records)
    cell_data = [
        data_array("ContactId", scalar_values(record["id"] for record in contact_records), "Int64"),
        data_array("ParticleId0", scalar_values(record["particle_0"] for record in contact_records), "Int64"),
        data_array("ParticleId1", scalar_values(record["particle_1"] for record in contact_records), "Int64"),
        data_array("BranchVector", tuple_values(record["branch"] for record in contact_records), components=3),
        data_array("BranchLength", scalar_values(record["length"] for record in contact_records)),
        data_array("ContactNormal", tuple_values(record["normal"] for record in contact_records), components=3),
        data_array("ContactForce", tuple_values(record["force"] for record in contact_records), components=3),
        data_array("NormalForce", scalar_values(record["normal_force"] for record in contact_records)),
        data_array("TangentialForce", tuple_values(record["tangential_force"] for record in contact_records), components=3),
        data_array("TangentialForceMagnitude", scalar_values(record["tangential_magnitude"] for record in contact_records)),
        data_array("FtOverFn", scalar_values(record["force_ratio"] for record in contact_records)),
        data_array("ContactArea", scalar_values(record["area"] for record in contact_records)),
        data_array("CrossesPeriodicBoundary", scalar_values(record["periodic"] for record in contact_records), "UInt8"),
    ]
    cells = "".join(
        [
            data_array("connectivity", scalar_values(range(2 * count)), "Int64"),
            data_array("offsets", scalar_values(range(2, 2 * count + 1, 2)), "Int64"),
            data_array("types", scalar_values([3] * count), "UInt8"),
        ]
    )
    vtk = f'''<?xml version="1.0"?>
<VTKFile type="UnstructuredGrid" version="1.0" byte_order="LittleEndian">
  <UnstructuredGrid>
    <FieldData>{field_arrays(metrics)}</FieldData>
    <Piece NumberOfPoints="{2 * count}" NumberOfCells="{count}">
      <PointData/>
      <CellData Scalars="NormalForce" Vectors="ContactForce">{"".join(cell_data)}</CellData>
      <Points>{data_array("Points", tuple_values(positions), components=3)}</Points>
      <Cells>{cells}</Cells>
    </Piece>
  </UnstructuredGrid>
</VTKFile>
'''
    path.write_text(vtk, encoding="utf-8")


def backbone_mcn(adjacency: dict[int, set[int]], removed: set[int]) -> float:
    retained = set(adjacency) - removed
    if not retained:
        return 0.0
    retained_edges_twice = sum(len(adjacency[node] & retained) for node in retained)
    return retained_edges_twice / len(retained)


def analyse(checkpoint_directory: Path) -> tuple[dict[str, object], list, dict, dict, dict, list]:
    checkpoint = json.loads(
        (checkpoint_directory / "cyclic_stress_checkpoint.json").read_text(encoding="utf-8")
    )
    label = checkpoint["restart_label"]
    _, spheres = load_model_part(checkpoint_directory, "SpheresPart", label)
    _, contacts = load_model_part(checkpoint_directory, "ContactPart", label)
    nodes = sorted(spheres.Nodes, key=lambda node: node.Id)
    adjacency = {node.Id: set() for node in nodes}
    contact_ratios = {node.Id: [] for node in nodes}

    bounds = checkpoint["box_bounds"]
    box_bounds = [
        bounds["BoundingBoxMinX"], bounds["BoundingBoxMaxX"],
        bounds["BoundingBoxMinY"], bounds["BoundingBoxMaxY"],
        bounds["BoundingBoxMinZ"], bounds["BoundingBoxMaxZ"],
    ]
    lengths = np.array(
        [box_bounds[1] - box_bounds[0], box_bounds[3] - box_bounds[2], box_bounds[5] - box_bounds[4]]
    )
    box_volume = float(np.prod(lengths))
    sigma = np.zeros((3, 3))
    conductivity = np.zeros((3, 3))
    fabric = np.zeros((3, 3))
    records = []

    for element in contacts.Elements:
        geometry = element.GetGeometry()
        point_0 = np.array([geometry[0].X, geometry[0].Y, geometry[0].Z])
        point_1 = np.array([geometry[1].X, geometry[1].Y, geometry[1].Z])
        raw_branch = point_0 - point_1
        branch = minimum_image(raw_branch, lengths)
        branch_length = float(np.linalg.norm(branch))
        if branch_length == 0.0:
            continue
        normal = branch / branch_length
        force = np.asarray(element.GetValue(DEM.GLOBAL_CONTACT_FORCE), dtype=float)
        tangential = np.asarray(
            element.GetValue(DEM.GLOBAL_CONTACT_FORCE_TANGENTIAL), dtype=float
        )
        normal_magnitude = float(np.linalg.norm(force - tangential))
        tangential_magnitude = float(np.linalg.norm(tangential))
        force_ratio = tangential_magnitude / normal_magnitude if normal_magnitude > 1e-14 else 0.0
        radius_0 = float(geometry[0].GetSolutionStepValue(KM.RADIUS))
        radius_1 = float(geometry[1].GetSolutionStepValue(KM.RADIUS))
        area_argument = max(
            4.0 * radius_0**2 * branch_length**2
            - (radius_0**2 + branch_length**2 - radius_1**2) ** 2,
            0.0,
        )
        contact_radius = math.sqrt(area_argument) / (2.0 * branch_length)
        area = math.pi * contact_radius**2

        first_id, second_id = geometry[0].Id, geometry[1].Id
        if first_id != second_id:
            adjacency[first_id].add(second_id)
            adjacency[second_id].add(first_id)
            contact_ratios[first_id].append(force_ratio)
            contact_ratios[second_id].append(force_ratio)
        sigma += np.outer(force, branch)
        fabric += np.outer(normal, normal)
        conductivity += area * branch_length * np.outer(normal, normal)
        records.append(
            {
                "id": element.Id,
                "particle_0": first_id,
                "particle_1": second_id,
                "point_0": point_0,
                "point_1_unwrapped": point_0 - branch,
                "branch": branch,
                "length": branch_length,
                "normal": normal,
                "force": force,
                "normal_force": normal_magnitude,
                "tangential_force": tangential,
                "tangential_magnitude": tangential_magnitude,
                "force_ratio": force_ratio,
                "area": area,
                "periodic": int(not np.allclose(raw_branch, branch, rtol=0.0, atol=1e-12)),
            }
        )

    contact_count = len(records)
    sigma /= box_volume
    conductivity /= box_volume
    fabric /= contact_count
    particle_volume = sum(
        4.0 * math.pi * float(node.GetSolutionStepValue(KM.RADIUS)) ** 3 / 3.0
        for node in nodes
    )
    rattlers = {threshold: iterative_rattlers(adjacency, threshold) for threshold in (2, 3, 4)}
    p = float(np.trace(sigma) / 3.0)
    q = math.sqrt(3.0 * j2(sigma))
    kd = math.sqrt(3.0 * j2(conductivity))
    anisotropy = math.sqrt(3.0 * j2(fabric))
    metrics = {
        "checkpoint_label": label,
        "time_s": float(checkpoint["time"]),
        "cycle": int(checkpoint["controller"]["completed_cycles"]),
        "phase_after_checkpoint": checkpoint["controller"]["phase"],
        "state_at_checkpoint": "high_pressure" if checkpoint["controller"]["phase"] == "low_pressure" else "low_pressure",
        "particle_count": len(nodes),
        "contact_count": contact_count,
        "periodic_contact_count": sum(record["periodic"] for record in records),
        "box_lengths_m": lengths.tolist(),
        "box_bounds": box_bounds,
        "box_volume_m3": box_volume,
        "particle_volume_m3": particle_volume,
        "packing": particle_volume / box_volume,
        "mcn": 2.0 * contact_count / len(nodes),
        "mcn_backbone_k2": backbone_mcn(adjacency, rattlers[2]),
        "mcn_backbone_k3": backbone_mcn(adjacency, rattlers[3]),
        "mcn_backbone_k4": backbone_mcn(adjacency, rattlers[4]),
        "rattler_count_k2": len(rattlers[2]),
        "rattler_count_k3": len(rattlers[3]),
        "rattler_count_k4": len(rattlers[4]),
        "sigma_pa": sigma.tolist(),
        "sigma_symmetric_pa": (0.5 * (sigma + sigma.T)).tolist(),
        "sigma_antisymmetric_norm_pa": float(np.linalg.norm(0.5 * (sigma - sigma.T))),
        "p_pa": p,
        "J2_sigma_pa2": j2(sigma),
        "q_pa": q,
        "q_over_p": q / p if p else None,
        "K": conductivity.tolist(),
        "K_mean": float(np.trace(conductivity) / 3.0),
        "J2_K": j2(conductivity),
        "kd": kd,
        "Fabric": fabric.tolist(),
        "J2_Fabric": j2(fabric),
        "a": anisotropy,
        "principal_sigma_pa": np.linalg.eigvalsh(0.5 * (sigma + sigma.T)).tolist(),
        "principal_K": np.linalg.eigvalsh(conductivity).tolist(),
        "principal_Fabric": np.linalg.eigvalsh(fabric).tolist(),
    }
    return metrics, nodes, adjacency, contact_ratios, rattlers, records


def write_summary_files(output: Path, metrics: dict[str, object]) -> None:
    (output / "checkpoint_metrics.json").write_text(
        json.dumps(metrics, indent=2) + "\n", encoding="utf-8"
    )
    with (output / "checkpoint_metrics.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(("metric", "value", "unit"))
        units = {
            "time_s": "s", "p_pa": "Pa", "q_pa": "Pa", "J2_sigma_pa2": "Pa^2",
            "box_volume_m3": "m^3", "particle_volume_m3": "m^3",
        }
        scalar_names = (
            "time_s", "cycle", "particle_count", "contact_count", "periodic_contact_count",
            "packing", "mcn", "mcn_backbone_k2", "mcn_backbone_k3", "mcn_backbone_k4",
            "rattler_count_k2", "rattler_count_k3", "rattler_count_k4", "p_pa",
            "J2_sigma_pa2", "q_pa", "q_over_p", "K_mean", "J2_K", "kd", "J2_Fabric", "a",
        )
        for name in scalar_names:
            writer.writerow((name, metrics[name], units.get(name, "-")))
    for name, unit in (("sigma_pa", "Pa"), ("K", "-"), ("Fabric", "-")):
        tensor = np.asarray(metrics[name])
        with (output / f"tensor_{name}.csv").open("w", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream)
            writer.writerow((f"{name} [{unit}]", "x", "y", "z"))
            for label, row in zip(("x", "y", "z"), tensor):
                writer.writerow((label, *row))


def write_report(output: Path, metrics: dict[str, object]) -> None:
    def matrix(name: str) -> str:
        tensor = np.asarray(metrics[name])
        return "\n".join(
            "| " + label + " | " + " | ".join(f"{value:.8g}" for value in row) + " |"
            for label, row in zip(("x", "y", "z"), tensor)
        )

    text = f"""# Análisis del checkpoint 266758

- Checkpoint: `{metrics['checkpoint_label']}`; ciclo {metrics['cycle']}; t = {metrics['time_s']:.12g} s.
- Estado guardado: extremo de **alta presión**; la fase registrada después del checkpoint es `{metrics['phase_after_checkpoint']}`.
- Partículas: {metrics['particle_count']}; contactos: {metrics['contact_count']} ({metrics['periodic_contact_count']} cruzan una frontera periódica).

## Resultados escalares

| Magnitud | Valor |
|---|---:|
| p | {metrics['p_pa']:.8g} Pa |
| packing | {metrics['packing']:.8g} |
| MCN = 2 Nc/Np | {metrics['mcn']:.8g} |
| MCN backbone k=2 | {metrics['mcn_backbone_k2']:.8g} |
| MCN backbone k=3 | {metrics['mcn_backbone_k3']:.8g} |
| MCN backbone k=4 | {metrics['mcn_backbone_k4']:.8g} |
| K medio = tr(K)/3 | {metrics['K_mean']:.8g} |
| q = sqrt(3 J2(sigma)) | {metrics['q_pa']:.8g} Pa |
| q/p | {metrics['q_over_p']:.8g} |
| kd = sqrt(3 J2(K)) | {metrics['kd']:.8g} |
| a = sqrt(3 J2(Fabric)) | {metrics['a']:.8g} |

## Tensores

Convención: `J2(T) = 1/2 dev(sym(T)):dev(sym(T))`. La tensión usa la suma de Love-Weber `sigma = (1/V) sum(f ⊗ l)` y vectores rama de imagen mínima. `K = (1/V) sum(A l n ⊗ n)`. `Fabric = (1/Nc) sum(n ⊗ n)`.

### sigma [Pa]

| | x | y | z |
|---|---:|---:|---:|
{matrix('sigma_pa')}

### K [-]

| | x | y | z |
|---|---:|---:|---:|
{matrix('K')}

### Fabric [-]

| | x | y | z |
|---|---:|---:|---:|
{matrix('Fabric')}

## Lectura

La tensión es casi isotrópica: `q/p = {metrics['q_over_p']:.4g}`. La anisotropía geométrica también es pequeña (`a = {metrics['a']:.4g}`), y la anisotropía de conductividad geométrica es `kd = {metrics['kd']:.4g}`. El packing calculado directamente de los radios y del volumen de la caja es {metrics['packing']:.6f}.

Los VTU contienen las mismas magnitudes globales en `FieldData`. El fichero de partículas permite colorear por radio, coordinación, rattlers y `Ft/Fn`; el de contactos permite colorear las cadenas por fuerza normal, tangencial o `Ft/Fn`.
"""
    (output / "report.md").write_text(text, encoding="utf-8")


def write_plot(output: Path, metrics: dict[str, object]) -> None:
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 3, figsize=(12, 3.8), constrained_layout=True)
    names = ("sigma", "K", "Fabric")
    principal_names = ("principal_sigma_pa", "principal_K", "principal_Fabric")
    scales = (1000.0, 1.0, 1.0)
    units = ("kPa", "-", "-")
    for axis, name, principal_name, scale, unit in zip(axes, names, principal_names, scales, units):
        values = np.asarray(metrics[principal_name]) / scale
        axis.bar(("1", "2", "3"), values, color=("#4477AA", "#66CCEE", "#228833"))
        axis.set_title(f"Valores principales de {name}")
        axis.set_xlabel("Dirección principal")
        axis.set_ylabel(unit)
        axis.grid(axis="y", alpha=0.25)
    fig.suptitle(f"Checkpoint 266758 · ciclo {metrics['cycle']} · alta presión")
    fig.savefig(output / "principal_values.png", dpi=180)
    plt.close(fig)


def main() -> None:
    arguments = parse_arguments()
    arguments.output_directory.mkdir(parents=True, exist_ok=True)
    metrics, nodes, adjacency, ratios, rattlers, contacts = analyse(
        arguments.checkpoint_directory
    )
    particles_path = arguments.output_directory / "particles.vtu"
    contacts_path = arguments.output_directory / "contacts.vtu"
    write_particles_vtu(particles_path, nodes, adjacency, ratios, rattlers, metrics)
    write_contacts_vtu(contacts_path, contacts, metrics)
    collection = f'''<?xml version="1.0"?>
<VTKFile type="Collection" version="0.1" byte_order="LittleEndian">
  <Collection>
    <DataSet timestep="{metrics['time_s']}" group="particles" part="0" file="particles.vtu"/>
    <DataSet timestep="{metrics['time_s']}" group="contacts" part="1" file="contacts.vtu"/>
  </Collection>
</VTKFile>
'''
    (arguments.output_directory / "checkpoint.pvd").write_text(collection, encoding="utf-8")
    write_summary_files(arguments.output_directory, metrics)
    write_report(arguments.output_directory, metrics)
    write_plot(arguments.output_directory, metrics)
    print(json.dumps({key: metrics[key] for key in ("cycle", "packing", "p_pa", "mcn", "q_pa", "q_over_p", "K_mean", "kd", "a")}, indent=2))


if __name__ == "__main__":
    main()
