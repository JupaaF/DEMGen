"""Generate 2D DEM-like data for the isotropic-compression presentation.

Particles receive small, repeatedly changing forces while all four box walls
move towards the centre.  The output is plain text so the slide can replay the
same positions without needing a Kratos run during rendering.
"""

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
RADIUS = 0.035
RELAXATION_STEPS = 450
COMPRESSION_STEPS = 1_800
TIME_STEP = 0.002
SAVE_EVERY = 20
TARGET_LEFT = 0.16
TARGET_RIGHT = 0.84
TARGET_BOTTOM = 0.16
TARGET_TOP = 0.84


def resolve_contacts(particles: list[Particle]) -> None:
    for first_id, first in enumerate(particles):
        for second in particles[first_id + 1 :]:
            dx = second.x - first.x
            dy = second.y - first.y
            distance_squared = dx * dx + dy * dy
            minimum_distance = 2.0 * RADIUS
            if distance_squared >= minimum_distance * minimum_distance:
                continue

            distance = max(distance_squared**0.5, 1e-8)
            nx, ny = dx / distance, dy / distance
            overlap = minimum_distance - distance
            first.x -= nx * overlap * 0.5
            first.y -= ny * overlap * 0.5
            second.x += nx * overlap * 0.5
            second.y += ny * overlap * 0.5

            relative_speed = (second.vx - first.vx) * nx + (second.vy - first.vy) * ny
            if relative_speed < 0.0:
                impulse = -0.58 * relative_speed
                first.vx -= impulse * nx
                first.vy -= impulse * ny
                second.vx += impulse * nx
                second.vy += impulse * ny


def keep_inside(particle: Particle, left: float, right: float, bottom: float, top: float) -> None:
    if particle.x - RADIUS < left:
        particle.x = left + RADIUS
        particle.vx = abs(particle.vx) * 0.2
    elif particle.x + RADIUS > right:
        particle.x = right - RADIUS
        particle.vx = -abs(particle.vx) * 0.2
    if particle.y - RADIUS < bottom:
        particle.y = bottom + RADIUS
        particle.vy = abs(particle.vy) * 0.2
    elif particle.y + RADIUS > top:
        particle.y = top - RADIUS
        particle.vy = -abs(particle.vy) * 0.2


def main() -> None:
    particles = [
        Particle(
            x=0.09 + column * 0.092 + (row % 2) * 0.018,
            y=0.10 + row * 0.095,
        )
        for row in range(ROWS)
        for column in range(COLUMNS)
    ]
    output_path = Path(__file__).with_name("isotropic_compression_trajectory.txt")
    with output_path.open("w", newline="", encoding="utf-8") as trajectory_file:
        writer = csv.writer(trajectory_file)
        writer.writerow(["frame", "particle_id", "x", "y", "radius", "left", "right", "bottom", "top"])
        frame = 0
        total_steps = RELAXATION_STEPS + COMPRESSION_STEPS
        for step in range(total_steps + 1):
            compression_progress = max(0.0, (step - RELAXATION_STEPS) / COMPRESSION_STEPS)
            left = TARGET_LEFT * compression_progress
            right = 1.0 + (TARGET_RIGHT - 1.0) * compression_progress
            bottom = TARGET_BOTTOM * compression_progress
            top = 1.0 + (TARGET_TOP - 1.0) * compression_progress

            for particle_id, particle in enumerate(particles):
                # Deterministic, changing force directions mimic the random
                # external forces used before and during compression.
                force_x = 0.85 * sin(0.018 * step + particle_id * 1.71)
                force_y = 0.85 * cos(0.023 * step + particle_id * 1.37)
                particle.vx = 0.992 * particle.vx + force_x * TIME_STEP
                particle.vy = 0.992 * particle.vy + force_y * TIME_STEP
                particle.x += particle.vx * TIME_STEP
                particle.y += particle.vy * TIME_STEP
                keep_inside(particle, left, right, bottom, top)

            # Two passes provide stable contacts as the boundaries close.
            resolve_contacts(particles)
            resolve_contacts(particles)
            for particle in particles:
                keep_inside(particle, left, right, bottom, top)

            if step % SAVE_EVERY == 0 or step == total_steps:
                for particle_id, particle in enumerate(particles):
                    writer.writerow([
                        frame,
                        particle_id,
                        f"{particle.x:.6f}",
                        f"{particle.y:.6f}",
                        f"{RADIUS:.6f}",
                        f"{left:.6f}",
                        f"{right:.6f}",
                        f"{bottom:.6f}",
                        f"{top:.6f}",
                    ])
                frame += 1

    final_density = len(particles) * pi * RADIUS**2 / ((right - left) * (top - bottom))
    print(f"Wrote {frame} frames for {len(particles)} particles; final 2D density = {final_density:.3f}")


if __name__ == "__main__":
    main()
