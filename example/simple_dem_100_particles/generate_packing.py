"""Genera un empaquetamiento DEM 2D de 100 discos en una caja cuadrada.

El cálculo usa relajación cuasiestática: los solapes entre discos y con las
paredes se corrigen iterativamente mientras los radios crecen hasta su valor
final.  Así se obtiene una configuración compacta sin depender de Kratos.
"""

from __future__ import annotations

import argparse
import csv
import math
import random
from pathlib import Path


NUMBER_OF_PARTICLES = 100
BOX_SIDE = 1.0
TARGET_PACKING_DENSITY = 0.75
MINIMUM_RADIUS = 0.042
MAXIMUM_RADIUS = 0.054
INITIAL_RADIUS_RATIO = 0.25
GROWTH_STEPS = 160
RELAXATION_ITERATIONS = 35
FINAL_RELAXATION_ITERATIONS = 3_000
SEED = 20260817


def final_radii(seed: int) -> list[float]:
    """Devuelve radios polidispersos, escalados a la densidad objetivo."""
    random_generator = random.Random(seed)
    unscaled_radii = [
        random_generator.uniform(MINIMUM_RADIUS, MAXIMUM_RADIUS)
        for _ in range(NUMBER_OF_PARTICLES)
    ]
    scale = math.sqrt(
        TARGET_PACKING_DENSITY
        * BOX_SIDE**2
        / (math.pi * sum(radius**2 for radius in unscaled_radii))
    )
    return [radius * scale for radius in unscaled_radii]


def initial_positions(initial_radii: list[float], seed: int) -> list[list[float]]:
    """Muestrea posiciones aleatorias uniformes sin imponer una retícula."""
    random_generator = random.Random(seed + 1)
    positions: list[list[float]] = []

    # El rechazo de candidatos demasiado próximos evita huecos macroscópicos
    # durante la compactación sin introducir filas o columnas artificiales.
    minimum_initial_distance = 0.06
    for radius in initial_radii:
        for _ in range(10_000):
            candidate = [
                random_generator.uniform(radius, BOX_SIDE - radius),
                random_generator.uniform(radius, BOX_SIDE - radius),
            ]
            if all(
                (candidate[0] - position[0]) ** 2 + (candidate[1] - position[1]) ** 2
                >= minimum_initial_distance**2
                for position in positions
            ):
                positions.append(candidate)
                break
        else:
            raise RuntimeError("No se pudo crear una distribución inicial uniforme")
    return positions


def relax(positions: list[list[float]], radii: list[float]) -> None:
    """Resuelve contactos disco-disco y disco-pared mediante amortiguamiento."""
    for first in range(NUMBER_OF_PARTICLES - 1):
        first_position = positions[first]
        for second in range(first + 1, NUMBER_OF_PARTICLES):
            second_position = positions[second]
            minimum_distance = radii[first] + radii[second]
            minimum_distance_squared = minimum_distance * minimum_distance
            dx = second_position[0] - first_position[0]
            dy = second_position[1] - first_position[1]
            distance_squared = dx * dx + dy * dy

            if distance_squared >= minimum_distance_squared:
                continue

            if distance_squared == 0.0:
                # Dirección determinista para un contacto degenerado.
                dx, dy = (1.0, 0.0) if (first + second) % 2 else (0.0, 1.0)
                distance = 1.0
            else:
                distance = math.sqrt(distance_squared)

            overlap = minimum_distance - distance
            correction = 0.5 * overlap / distance
            move_x = correction * dx
            move_y = correction * dy
            first_position[0] -= move_x
            first_position[1] -= move_y
            second_position[0] += move_x
            second_position[1] += move_y

    # Contactos con las cuatro paredes rígidas de la caja [0, 1] x [0, 1].
    for position, radius in zip(positions, radii):
        position[0] = min(max(position[0], radius), BOX_SIDE - radius)
        position[1] = min(max(position[1], radius), BOX_SIDE - radius)


def generate_packing(seed: int = SEED) -> tuple[list[list[float]], list[float]]:
    radii = final_radii(seed)
    positions = initial_positions([radius * INITIAL_RADIUS_RATIO for radius in radii], seed)
    for step in range(1, GROWTH_STEPS + 1):
        fraction = step / GROWTH_STEPS
        current_radii = [
            radius * (INITIAL_RADIUS_RATIO + fraction * (1.0 - INITIAL_RADIUS_RATIO))
            for radius in radii
        ]
        for _ in range(RELAXATION_ITERATIONS):
            relax(positions, current_radii)
    for _ in range(FINAL_RELAXATION_ITERATIONS):
        relax(positions, radii)
    return positions, radii


def validate(positions: list[list[float]], radii: list[float]) -> float:
    """Verifica límites y solapes, y devuelve la fracción de área ocupada."""
    tolerance = 1.0e-8
    for particle_id, ((x, y), radius) in enumerate(zip(positions, radii), start=1):
        if not (radius - tolerance <= x <= BOX_SIDE - radius + tolerance):
            raise RuntimeError(f"Partícula {particle_id} fuera de la caja en x")
        if not (radius - tolerance <= y <= BOX_SIDE - radius + tolerance):
            raise RuntimeError(f"Partícula {particle_id} fuera de la caja en y")

    for first in range(NUMBER_OF_PARTICLES - 1):
        for second in range(first + 1, NUMBER_OF_PARTICLES):
            dx = positions[second][0] - positions[first][0]
            dy = positions[second][1] - positions[first][1]
            if dx * dx + dy * dy < (radii[first] + radii[second] - tolerance) ** 2:
                raise RuntimeError(f"Solape entre partículas {first + 1} y {second + 1}")

    return math.pi * sum(radius**2 for radius in radii) / BOX_SIDE**2


def write_csv(positions: list[list[float]], radii: list[float], destination: Path) -> None:
    with destination.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(("particle_id", "x", "y", "radius"))
        for particle_id, ((x, y), radius) in enumerate(zip(positions, radii), start=1):
            writer.writerow((particle_id, f"{x:.12f}", f"{y:.12f}", f"{radius:.12f}"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Genera un packing DEM 2D de discos aleatorios.")
    parser.add_argument("--seed", type=int, default=SEED, help="Semilla aleatoria reproducible.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).with_name("particles_100_square.csv"),
        help="Ruta del CSV de salida.",
    )
    arguments = parser.parse_args()

    output_file = arguments.output
    final_positions, radii = generate_packing(arguments.seed)
    packing_density = validate(final_positions, radii)
    write_csv(final_positions, radii, output_file)
    print(f"Archivo creado: {output_file}")
    print(f"Semilla: {arguments.seed}")
    print(f"Caja cuadrada: {BOX_SIDE} x {BOX_SIDE}")
    print(f"Partículas: {NUMBER_OF_PARTICLES}; densidad de empaquetamiento: {packing_density:.3f}")
