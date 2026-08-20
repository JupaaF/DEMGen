"""Generate a compact 2D granular-deposition trajectory for the presentation.

The output is intentionally plain text so Manim can animate the same particle
positions without depending on Kratos while rendering the slides.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from math import floor
from pathlib import Path


@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    radius: float
    release_step: int


WIDTH = 1.0
HEIGHT = 0.8
DT = 0.002
STEPS = 3_600
SAVE_EVERY = 30
GRAVITY = 4.5
RESTITUTION = 0.16
RADIUS = 0.037
PARTICLE_COUNT = 145


def collision_with_walls(particle: Particle) -> None:
    if particle.x - particle.radius < 0.0:
        particle.x = particle.radius
        particle.vx = abs(particle.vx) * RESTITUTION
    elif particle.x + particle.radius > WIDTH:
        particle.x = WIDTH - particle.radius
        particle.vx = -abs(particle.vx) * RESTITUTION

    if particle.y - particle.radius < 0.0:
        particle.y = particle.radius
        particle.vy = abs(particle.vy) * RESTITUTION
        particle.vx *= 0.82  # friction against the bottom wall


def resolve_particle_contacts(particles: list[Particle], active: list[int]) -> None:
    cell_size = 2.0 * max(particles[particle_id].radius for particle_id in active)
    cells = {}
    for particle_id in active:
        particle = particles[particle_id]
        cell = (floor(particle.x / cell_size), floor(particle.y / cell_size))
        cells.setdefault(cell, []).append(particle_id)

    for first_id in active:
        first = particles[first_id]
        cell_x = floor(first.x / cell_size)
        cell_y = floor(first.y / cell_size)
        for neighbour_x in range(cell_x - 1, cell_x + 2):
            for neighbour_y in range(cell_y - 1, cell_y + 2):
                for second_id in cells.get((neighbour_x, neighbour_y), []):
                    if second_id <= first_id:
                        continue
                    second = particles[second_id]
                    dx = second.x - first.x
                    dy = second.y - first.y
                    minimum_distance = first.radius + second.radius
                    distance_squared = dx * dx + dy * dy
                    if distance_squared >= minimum_distance * minimum_distance:
                        continue

                    distance = max(distance_squared**0.5, 1e-8)
                    nx, ny = dx / distance, dy / distance
                    overlap = minimum_distance - distance
                    # Equal-mass positional correction keeps discs from interpenetrating.
                    first.x -= nx * overlap * 0.5
                    first.y -= ny * overlap * 0.5
                    second.x += nx * overlap * 0.5
                    second.y += ny * overlap * 0.5

                    relative_normal_velocity = (second.vx - first.vx) * nx + (second.vy - first.vy) * ny
                    if relative_normal_velocity < 0.0:
                        impulse = -(1.0 + RESTITUTION) * relative_normal_velocity * 0.5
                        first.vx -= impulse * nx
                        first.vy -= impulse * ny
                        second.vx += impulse * nx
                        second.vy += impulse * ny

                    # A little tangential dissipation gives a visibly settling pile.
                    first.vx *= 0.997
                    first.vy *= 0.997
                    second.vx *= 0.997
                    second.vy *= 0.997


def main() -> None:
    particles = [
        Particle(
            x=0.33 + 0.34 * ((particle_id * 37) % 101) / 100,
            y=0.99 + 0.025 * (particle_id % 3),
            vx=(particle_id % 5 - 2) * 0.055,
            vy=-0.10,
            radius=RADIUS * (0.92 + 0.04 * (particle_id % 4)),
            release_step=particle_id * 15,
        )
        for particle_id in range(PARTICLE_COUNT)
    ]

    output_path = Path(__file__).with_name("gravitational_deposition_trajectory.txt")
    with output_path.open("w", newline="", encoding="utf-8") as trajectory_file:
        writer = csv.writer(trajectory_file)
        writer.writerow(["frame", "particle_id", "x", "y", "radius", "active"])
        frame = 0
        for step in range(STEPS + 1):
            active = [particle_id for particle_id, particle in enumerate(particles) if step >= particle.release_step]
            for particle_id in active:
                particle = particles[particle_id]
                particle.vy -= GRAVITY * DT
                particle.x += particle.vx * DT
                particle.y += particle.vy * DT
                collision_with_walls(particle)

            # Two passes make simultaneous contacts settle more convincingly.
            resolve_particle_contacts(particles, active)
            resolve_particle_contacts(particles, active)
            for particle_id in active:
                collision_with_walls(particles[particle_id])

            if step % SAVE_EVERY == 0:
                for particle_id, particle in enumerate(particles):
                    writer.writerow([
                        frame,
                        particle_id,
                        f"{particle.x:.6f}",
                        f"{particle.y:.6f}",
                        f"{particle.radius:.6f}",
                        int(step >= particle.release_step),
                    ])
                frame += 1


if __name__ == "__main__":
    main()
