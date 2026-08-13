from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator


_SUPPORTED_GROUPS = ("Body", "Joint")


@dataclass(frozen=True, slots=True)
class SphericalParticle:
    """A spherical DEM particle independent from Kratos and MDPA."""

    node_id: int
    element_id: int
    position: tuple[float, float, float]
    radius: float
    group: str = "Body"

    def __post_init__(self) -> None:
        if (
            isinstance(self.node_id, bool)
            or not isinstance(self.node_id, int)
            or self.node_id <= 0
        ):
            raise ValueError("node_id must be a positive integer.")
        if (
            isinstance(self.element_id, bool)
            or not isinstance(self.element_id, int)
            or self.element_id <= 0
        ):
            raise ValueError("element_id must be a positive integer.")
        if len(self.position) != 3:
            raise ValueError("position must contain exactly three coordinates.")

        position = tuple(float(coordinate) for coordinate in self.position)
        if not all(math.isfinite(coordinate) for coordinate in position):
            raise ValueError("position coordinates must be finite.")

        radius = float(self.radius)
        if not math.isfinite(radius) or radius <= 0.0:
            raise ValueError("radius must be a positive finite number.")
        if self.group not in _SUPPORTED_GROUPS:
            raise ValueError(
                f"group must be one of {', '.join(_SUPPORTED_GROUPS)}."
            )

        object.__setattr__(self, "position", position)
        object.__setattr__(self, "radius", radius)

    @property
    def volume(self) -> float:
        return 4.0 / 3.0 * math.pi * self.radius**3


class ParticlePacking:
    """A validated collection of spherical particles with MDPA persistence."""

    def __init__(self, particles: Iterable[SphericalParticle] = ()) -> None:
        self._particles: list[SphericalParticle] = []
        self._node_ids: set[int] = set()
        self._element_ids: set[int] = set()
        for particle in particles:
            self.add(particle)

    def __iter__(self) -> Iterator[SphericalParticle]:
        return iter(self._particles)

    def __len__(self) -> int:
        return len(self._particles)

    def add(self, particle: SphericalParticle) -> None:
        if not isinstance(particle, SphericalParticle):
            raise TypeError(
                "ParticlePacking only accepts SphericalParticle instances."
            )
        if particle.node_id in self._node_ids:
            raise ValueError(f"Duplicate particle node_id: {particle.node_id}.")
        if particle.element_id in self._element_ids:
            raise ValueError(
                f"Duplicate particle element_id: {particle.element_id}."
            )

        self._particles.append(particle)
        self._node_ids.add(particle.node_id)
        self._element_ids.add(particle.element_id)

    def total_solid_volume(self) -> float:
        return sum(particle.volume for particle in self._particles)

    def scaled_radii(self, multiplier: float) -> ParticlePacking:
        multiplier = float(multiplier)
        if not math.isfinite(multiplier) or multiplier <= 0.0:
            raise ValueError("radius multiplier must be a positive finite number.")

        return ParticlePacking(
            SphericalParticle(
                node_id=particle.node_id,
                element_id=particle.element_id,
                position=particle.position,
                radius=particle.radius * multiplier,
                group=particle.group,
            )
            for particle in self._particles
        )

    @classmethod
    def from_mdpa(cls, path: str | Path) -> ParticlePacking:
        path = Path(path)
        nodes: dict[int, tuple[float, float, float]] = {}
        element_ids: dict[int, int] = {}
        radii: dict[int, float] = {}
        groups: dict[int, str] = {}

        section: str | None = None
        submodel_group: str | None = None

        with path.open("r", encoding="utf-8") as mdpa_file:
            for line_number, line in enumerate(mdpa_file, start=1):
                values = line.split()
                if not values or values[0].startswith("//"):
                    continue

                if values[:2] == ["Begin", "SubModelPart"]:
                    submodel_group = _group_from_submodel_part(values, path, line_number)
                    section = None
                    continue
                if values[:2] == ["End", "SubModelPart"]:
                    submodel_group = None
                    section = None
                    continue

                if values[:2] == ["Begin", "SubModelPartNodes"]:
                    section = "group_nodes" if submodel_group is not None else "skip"
                    continue
                if values[:2] == ["End", "SubModelPartNodes"]:
                    section = None
                    continue

                if values[:2] == ["Begin", "Nodes"]:
                    section = "nodes"
                    continue
                if values[:2] == ["End", "Nodes"]:
                    section = None
                    continue

                if values[:2] == ["Begin", "Elements"]:
                    section = (
                        "elements"
                        if len(values) >= 3 and values[2].startswith("SphericParticle3D")
                        else "skip"
                    )
                    continue
                if values[:2] == ["End", "Elements"]:
                    section = None
                    continue

                if values[:3] == ["Begin", "NodalData", "RADIUS"]:
                    section = "radii"
                    continue
                if values[:2] == ["Begin", "NodalData"]:
                    section = "skip"
                    continue
                if values[:2] == ["End", "NodalData"]:
                    section = None
                    continue

                try:
                    if section == "nodes":
                        node_id = int(values[0])
                        _store_unique(
                            nodes,
                            node_id,
                            (float(values[1]), float(values[2]), float(values[3])),
                            "node",
                        )
                    elif section == "elements":
                        element_id = int(values[0])
                        node_id = int(values[2])
                        _store_unique(
                            element_ids,
                            node_id,
                            element_id,
                            "element for node",
                        )
                    elif section == "radii":
                        node_id = int(values[0])
                        _store_unique(
                            radii,
                            node_id,
                            float(values[2]),
                            "radius for node",
                        )
                    elif section == "group_nodes":
                        groups[int(values[0])] = submodel_group or "Body"
                except (IndexError, ValueError) as error:
                    raise ValueError(
                        f"Invalid MDPA particle data at {path}:{line_number}."
                    ) from error

        node_ids = set(nodes)
        _require_same_ids(path, node_ids, set(element_ids), "elements")
        _require_same_ids(path, node_ids, set(radii), "radii")

        return cls(
            SphericalParticle(
                node_id=node_id,
                element_id=element_ids[node_id],
                position=nodes[node_id],
                radius=radii[node_id],
                group=groups.get(node_id, "Body"),
            )
            for node_id in sorted(node_ids)
        )

    def write_mdpa(self, path: str | Path, *, cohesive: bool = False) -> None:
        path = Path(path)
        particles = sorted(self._particles, key=lambda particle: particle.node_id)

        with path.open("w", encoding="utf-8") as mdpa_file:
            mdpa_file.write(
                "Begin ModelPartData\n"
                "End ModelPartData\n\n"
                "Begin Properties 0\n"
                "End Properties\n\n"
            )
            mdpa_file.write("Begin Nodes\n")
            for particle in particles:
                x, y, z = particle.position
                mdpa_file.write(f"{particle.node_id} {x} {y} {z}\n")
            mdpa_file.write("End Nodes\n\n")

            mdpa_file.write("Begin Elements SphericParticle3D\n")
            for particle in particles:
                mdpa_file.write(
                    f"{particle.element_id} 0 {particle.node_id}\n"
                )
            mdpa_file.write("End Elements\n\n")

            mdpa_file.write("Begin NodalData RADIUS\n")
            for particle in particles:
                mdpa_file.write(
                    f"{particle.node_id} 0 {particle.radius}\n"
                )
            mdpa_file.write("End NodalData\n\n")

            if cohesive:
                mdpa_file.write("Begin NodalData COHESIVE_GROUP\n")
                for particle in particles:
                    mdpa_file.write(f"{particle.node_id} 0 1\n")
                mdpa_file.write("End NodalData\n\n")
                mdpa_file.write("Begin NodalData SKIN_SPHERE\n")
                mdpa_file.write("End NodalData\n\n")

            for group in _SUPPORTED_GROUPS:
                group_particles = [
                    particle for particle in particles if particle.group == group
                ]
                if group_particles:
                    _write_submodel_part(mdpa_file, group, group_particles)


def _group_from_submodel_part(
    values: list[str], path: Path, line_number: int
) -> str | None:
    if len(values) < 3 or not values[2].startswith("DEMParts_"):
        return None
    group = values[2].removeprefix("DEMParts_")
    if group not in _SUPPORTED_GROUPS:
        raise ValueError(
            f"Unsupported particle group {group!r} at {path}:{line_number}."
        )
    return group


def _store_unique(mapping, key, value, description: str) -> None:
    if key in mapping:
        raise ValueError(f"Duplicate {description} id: {key}.")
    mapping[key] = value


def _require_same_ids(
    path: Path, node_ids: set[int], actual_ids: set[int], description: str
) -> None:
    if actual_ids == node_ids:
        return
    missing = sorted(node_ids - actual_ids)
    unexpected = sorted(actual_ids - node_ids)
    raise ValueError(
        f"MDPA {path} has inconsistent {description}; "
        f"missing node ids={missing}, unexpected node ids={unexpected}."
    )


def _write_submodel_part(mdpa_file, group: str, particles) -> None:
    mdpa_file.write(f"Begin SubModelPart DEMParts_{group}\n")
    mdpa_file.write("Begin SubModelPartNodes\n")
    for particle in particles:
        mdpa_file.write(f"{particle.node_id}\n")
    mdpa_file.write("End SubModelPartNodes\n")
    mdpa_file.write("Begin SubModelPartElements\n")
    for particle in particles:
        mdpa_file.write(f"{particle.element_id}\n")
    mdpa_file.write("End SubModelPartElements\n")
    mdpa_file.write("Begin SubModelPartConditions\n")
    mdpa_file.write("End SubModelPartConditions\n")
    mdpa_file.write("End SubModelPart\n\n")
