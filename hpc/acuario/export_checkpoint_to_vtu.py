#!/usr/bin/env python3
"""Export a cyclic-stress Kratos checkpoint as a ParaView VTU file."""

from __future__ import annotations

import argparse
from collections import deque
import json
from pathlib import Path

import numpy as np

import KratosMultiphysics as KM
import KratosMultiphysics.DEMApplication as DEM


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("checkpoint_directory", type=Path)
    parser.add_argument("output", type=Path)
    return parser.parse_args()


def load_model_part(
    checkpoint_directory: Path,
    name: str,
    label: str,
) -> tuple[KM.Model, KM.ModelPart]:
    model = KM.Model()
    model_part = model.CreateModelPart(name)
    restart_path = (
        checkpoint_directory
        / f"{name}__restart_files"
        / f"{name}_{label}"
    )
    serializer = KM.FileSerializer(
        str(restart_path),
        KM.SerializerTraceType.SERIALIZER_NO_TRACE,
    )
    serializer.Load(name, model_part)
    return model, model_part


def iterative_rattlers(
    adjacency: dict[int, set[int]],
    minimum_contacts: int,
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
            if (
                neighbor_id not in removed
                and len(working[neighbor_id]) < minimum_contacts
            ):
                removed.add(neighbor_id)
                queue.append(neighbor_id)
        working[particle_id].clear()
    return removed


def scalar_values(values) -> str:
    return " ".join(str(value) for value in values)


def vector_values(values) -> str:
    return "\n".join(" ".join(str(component) for component in value) for value in values)


def data_array(
    name: str,
    values: str,
    vtk_type: str = "Float64",
    components: int | None = None,
    tuples: int | None = None,
) -> str:
    component_attribute = (
        f' NumberOfComponents="{components}"' if components is not None else ""
    )
    tuple_attribute = f' NumberOfTuples="{tuples}"' if tuples is not None else ""
    return (
        f'<DataArray type="{vtk_type}" Name="{name}"'
        f'{component_attribute}{tuple_attribute} format="ascii">'
        f'\n{values}\n</DataArray>'
    )


def main() -> None:
    arguments = parse_arguments()
    checkpoint = json.loads(
        (arguments.checkpoint_directory / "cyclic_stress_checkpoint.json").read_text(
            encoding="utf-8"
        )
    )
    label = checkpoint["restart_label"]
    spheres_model, spheres = load_model_part(
        arguments.checkpoint_directory,
        "SpheresPart",
        label,
    )
    contacts_model, contacts = load_model_part(
        arguments.checkpoint_directory,
        "ContactPart",
        label,
    )

    nodes = sorted(spheres.Nodes, key=lambda node: node.Id)
    particle_ids = [node.Id for node in nodes]
    adjacency = {particle_id: set() for particle_id in particle_ids}
    contact_ratios = {particle_id: [] for particle_id in particle_ids}

    for element in contacts.Elements:
        total_force = np.asarray(
            element.GetValue(DEM.GLOBAL_CONTACT_FORCE),
            dtype=float,
        )
        tangential_force = np.asarray(
            element.GetValue(DEM.GLOBAL_CONTACT_FORCE_TANGENTIAL),
            dtype=float,
        )
        normal_magnitude = np.linalg.norm(total_force - tangential_force)
        if normal_magnitude <= 1.0e-14:
            continue
        ratio = float(np.linalg.norm(tangential_force) / normal_magnitude)
        first_id = element.GetGeometry()[0].Id
        second_id = element.GetGeometry()[1].Id
        if first_id == second_id:
            continue
        adjacency[first_id].add(second_id)
        adjacency[second_id].add(first_id)
        contact_ratios[first_id].append(ratio)
        contact_ratios[second_id].append(ratio)

    rattlers_k2 = iterative_rattlers(adjacency, 2)
    rattlers_k3 = iterative_rattlers(adjacency, 3)
    rattlers_k4 = iterative_rattlers(adjacency, 4)

    positions = [(node.X, node.Y, node.Z) for node in nodes]
    radii = [node.GetSolutionStepValue(KM.RADIUS) for node in nodes]
    velocities = [node.GetSolutionStepValue(KM.VELOCITY) for node in nodes]
    angular_velocities = [
        node.GetSolutionStepValue(KM.ANGULAR_VELOCITY) for node in nodes
    ]
    displacements = [
        node.GetSolutionStepValue(KM.DISPLACEMENT) for node in nodes
    ]
    total_forces = [node.GetSolutionStepValue(KM.TOTAL_FORCES) for node in nodes]
    coordination = [len(adjacency[particle_id]) for particle_id in particle_ids]
    mean_contact_ratio = [
        float(np.mean(contact_ratios[particle_id]))
        if contact_ratios[particle_id]
        else 0.0
        for particle_id in particle_ids
    ]
    maximum_contact_ratio = [
        max(contact_ratios[particle_id], default=0.0)
        for particle_id in particle_ids
    ]

    point_data = [
        data_array("ParticleId", scalar_values(particle_ids), "Int64"),
        data_array("Radius", scalar_values(radii)),
        data_array("Velocity", vector_values(velocities), components=3),
        data_array(
            "AngularVelocity",
            vector_values(angular_velocities),
            components=3,
        ),
        data_array("Displacement", vector_values(displacements), components=3),
        data_array("TotalForce", vector_values(total_forces), components=3),
        data_array("CoordinationNumber", scalar_values(coordination), "Int32"),
        data_array(
            "IsRattlerK2",
            scalar_values(int(particle_id in rattlers_k2) for particle_id in particle_ids),
            "UInt8",
        ),
        data_array(
            "IsRattlerK3",
            scalar_values(int(particle_id in rattlers_k3) for particle_id in particle_ids),
            "UInt8",
        ),
        data_array(
            "IsRattlerK4",
            scalar_values(int(particle_id in rattlers_k4) for particle_id in particle_ids),
            "UInt8",
        ),
        data_array("MeanContactFtFn", scalar_values(mean_contact_ratio)),
        data_array("MaxContactFtFn", scalar_values(maximum_contact_ratio)),
    ]

    number_of_particles = len(nodes)
    bounds = checkpoint["box_bounds"]
    box_values = [
        bounds["BoundingBoxMinX"],
        bounds["BoundingBoxMaxX"],
        bounds["BoundingBoxMinY"],
        bounds["BoundingBoxMaxY"],
        bounds["BoundingBoxMinZ"],
        bounds["BoundingBoxMaxZ"],
    ]
    field_data = [
        data_array("TimeValue", str(checkpoint["time"]), tuples=1),
        data_array(
            "BoxBounds",
            scalar_values(box_values),
            components=6,
            tuples=1,
        ),
    ]
    cells = [
        data_array(
            "connectivity",
            scalar_values(range(number_of_particles)),
            "Int64",
        ),
        data_array(
            "offsets",
            scalar_values(range(1, number_of_particles + 1)),
            "Int64",
        ),
        data_array(
            "types",
            scalar_values([1] * number_of_particles),
            "UInt8",
        ),
    ]

    vtk = f'''<?xml version="1.0"?>
<VTKFile type="UnstructuredGrid" version="1.0" byte_order="LittleEndian">
  <UnstructuredGrid>
    <FieldData>{''.join(field_data)}</FieldData>
    <Piece NumberOfPoints="{number_of_particles}" NumberOfCells="{number_of_particles}">
      <PointData Scalars="Radius" Vectors="Velocity">{''.join(point_data)}</PointData>
      <CellData/>
      <Points>{data_array("Points", vector_values(positions), components=3)}</Points>
      <Cells>{''.join(cells)}</Cells>
    </Piece>
  </UnstructuredGrid>
</VTKFile>
'''
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(vtk, encoding="utf-8")
    print(f"Exported {number_of_particles} particles to {arguments.output}")
    print(
        f"Rattlers: k2={len(rattlers_k2)}, "
        f"k3={len(rattlers_k3)}, k4={len(rattlers_k4)}"
    )


if __name__ == "__main__":
    main()
