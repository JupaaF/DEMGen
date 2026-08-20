"""Generate a 2D radius-expansion trajectory for the presentation."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from math import cos, pi, sin
from pathlib import Path


@dataclass
class Particle:
    x: float
    y: float
    vx: float = 0.0
    vy: float = 0.0


ROWS = 9
COLUMNS = 10
INITIAL_RADIUS = 0.023
FINAL_RADIUS = 0.046
EXPANSION_STEPS = 2_100
RELAXATION_STEPS = 600
TIME_STEP = 0.002
SAVE_EVERY = 20


def resolve_contacts(particles: list[Particle], radius: float) -> None:
    minimum_distance = 2.0 * radius
    for first_id, first in enumerate(particles):
        for second in particles[first_id + 1 :]:
            dx = second.x - first.x
            dy = second.y - first.y
            distance_squared = dx * dx + dy * dy
            if distance_squared >= minimum_distance * minimum_distance:
                continue

            distance = max(distance_squared**0.5, 1e-8)
            nx, ny = dx / distance, dy / distance
            overlap = minimum_distance - distance
            first.x -= nx * overlap * 0.5
            first.y -= ny * overlap * 0.5
            second.x += nx * overlap * 0.5
            second.y += ny * overlap * 0.5

            normal_speed = (second.vx - first.vx) * nx + (second.vy - first.vy) * ny
            if normal_speed < 0.0:
                impulse = -0.55 * normal_speed
                first.vx -= impulse * nx
                first.vy -= impulse * ny
                second.vx += impulse * nx
                second.vy += impulse * ny


def keep_inside(particle: Particle, radius: float) -> None:
    if particle.x - radius < 0.0:
        particle.x = radius
        particle.vx = abs(particle.vx) * 0.15
    elif particle.x + radius > 1.0:
        particle.x = 1.0 - radius
        particle.vx = -abs(particle.vx) * 0.15
    if particle.y - radius < 0.0:
        particle.y = radius
        particle.vy = abs(particle.vy) * 0.15
    elif particle.y + radius > 1.0:
        particle.y = 1.0 - radius
        particle.vy = -abs(particle.vy) * 0.15


def main() -> None:
    particles = [
        Particle(
            x=0.095 + column * 0.09 + (row % 2) * 0.018,
            y=0.10 + row * 0.10,
        )
        for row in range(ROWS)
        for column in range(COLUMNS)
    ]
    total_steps = EXPANSION_STEPS + RELAXATION_STEPS
    output_path = Path(__file__).with_name("radius_expansion_trajectory.txt")
    with output_path.open("w", newline="", encoding="utf-8") as trajectory_file:
        writer = csv.writer(trajectory_file)
        writer.writerow(["frame", "particle_id", "x", "y", "radius"])
        frame = 0
        for step in range(total_steps + 1):
            expansion_progress = min(step / EXPANSION_STEPS, 1.0)
            radius = INITIAL_RADIUS + (FINAL_RADIUS - INITIAL_RADIUS) * expansion_progress
            for particle_id, particle in enumerate(particles):
                # Weak agitation gives the particles room to rearrange while
                # their radii grow, without introducing a privileged direction.
                particle.vx = 0.992 * particle.vx + 0.55 * sin(0.021 * step + particle_id) * TIME_STEP
                particle.vy = 0.992 * particle.vy + 0.55 * cos(0.017 * step + 1.3 * particle_id) * TIME_STEP
                particle.x += particle.vx * TIME_STEP
                particle.y += particle.vy * TIME_STEP
                keep_inside(particle, radius)

            resolve_contacts(particles, radius)
            resolve_contacts(particles, radius)
            for particle in particles:
                keep_inside(particle, radius)

            if step % SAVE_EVERY == 0 or step == total_steps:
                for particle_id, particle in enumerate(particles):
                    writer.writerow([
                        frame,
                        particle_id,
                        f"{particle.x:.6f}",
                        f"{particle.y:.6f}",
                        f"{radius:.6f}",
                    ])
                frame += 1

    final_density = len(particles) * pi * FINAL_RADIUS**2
    print(f"Wrote {frame} frames for {len(particles)} particles; final 2D density = {final_density:.3f}")


if __name__ == "__main__":
    main()
