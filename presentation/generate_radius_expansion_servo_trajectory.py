"""Solve a gravity-free 2D DEM radius-expansion/servo trajectory for Manim."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from math import cos, pi, sin, sqrt
from pathlib import Path
from random import Random


@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    fx: float = 0.0
    fy: float = 0.0


PARTICLE_COUNT = 90
NOMINAL_RADIUS = 0.051
SCALED_RADIUS = NOMINAL_RADIUS * 0.5
PREPARATION_STEPS = 2_500
REDUCTION_STEPS = 500
EXPANSION_STEPS = 2_600
SERVO_STEPS = 3_000
TIME_STEP = 0.0005
SAVE_EVERY = 20
CONTACT_STIFFNESS = 4_000.0
NORMAL_DAMPING = 20.0
TANGENTIAL_DAMPING = 3.0
VELOCITY_DAMPING = 0.999
SERVO_TARGET_STRESS = 5.0
STRESS_TO_KPA = 0.040
SERVO_GAIN = 0.00002
MINIMUM_SIDE = 0.890
RANDOM_SEED = 20260821


def random_particles() -> list[Particle]:
    """Create a reproducible random cloud; no lattice is used as a seed."""
    generator = Random(RANDOM_SEED)
    particles: list[Particle] = []
    minimum_seed_distance = 0.032
    while len(particles) < PARTICLE_COUNT:
        x = generator.uniform(NOMINAL_RADIUS, 1.0 - NOMINAL_RADIUS)
        y = generator.uniform(NOMINAL_RADIUS, 1.0 - NOMINAL_RADIUS)
        if any((x - particle.x) ** 2 + (y - particle.y) ** 2 < minimum_seed_distance**2 for particle in particles):
            continue
        particles.append(
            Particle(
                x=x,
                y=y,
                vx=generator.uniform(-0.12, 0.12),
                vy=generator.uniform(-0.12, 0.12),
            )
        )
    return particles


def reset_forces(particles: list[Particle]) -> None:
    for particle in particles:
        particle.fx = 0.0
        particle.fy = 0.0


def accumulate_contact_forces(particles: list[Particle], radius: float, friction: float) -> None:
    """Linear spring-dashpot contacts plus a Coulomb-limited tangential force."""
    contact_distance = 2.0 * radius
    for first_id, first in enumerate(particles):
        for second_id, second in enumerate(particles[first_id + 1 :], first_id + 1):
            dx, dy = second.x - first.x, second.y - first.y
            distance_squared = dx * dx + dy * dy
            if distance_squared >= contact_distance**2:
                continue

            distance = max(sqrt(distance_squared), 1e-10)
            if distance < 1e-8:
                angle = 1.91 * (first_id + second_id + 1)
                nx, ny = cos(angle), sin(angle)
            else:
                nx, ny = dx / distance, dy / distance
            overlap = contact_distance - distance
            relative_vx, relative_vy = second.vx - first.vx, second.vy - first.vy
            normal_speed = relative_vx * nx + relative_vy * ny
            normal_force = max(0.0, CONTACT_STIFFNESS * overlap - NORMAL_DAMPING * normal_speed)
            tangent_vx = relative_vx - normal_speed * nx
            tangent_vy = relative_vy - normal_speed * ny
            tangent_speed = sqrt(tangent_vx * tangent_vx + tangent_vy * tangent_vy)
            tangent_force = min(friction * normal_force, TANGENTIAL_DAMPING * tangent_speed)
            if tangent_speed > 1e-12:
                tangent_x = -tangent_force * tangent_vx / tangent_speed
                tangent_y = -tangent_force * tangent_vy / tangent_speed
            else:
                tangent_x = tangent_y = 0.0
            force_x, force_y = normal_force * nx + tangent_x, normal_force * ny + tangent_y
            first.fx -= force_x
            first.fy -= force_y
            second.fx += force_x
            second.fy += force_y


def accumulate_wall_forces(
    particles: list[Particle], radius: float, left: float, right: float, bottom: float, top: float, friction: float
) -> float:
    """Apply spring-dashpot wall contacts and return their total normal reaction."""
    reaction = 0.0
    for particle in particles:
        wall_contacts = (
            (left + radius - particle.x, 1.0, 0.0, particle.vx, particle.vy),
            (particle.x - (right - radius), -1.0, 0.0, -particle.vx, particle.vy),
            (bottom + radius - particle.y, 0.0, 1.0, particle.vy, particle.vx),
            (particle.y - (top - radius), 0.0, -1.0, -particle.vy, particle.vx),
        )
        for overlap, nx, ny, normal_speed, tangent_speed in wall_contacts:
            if overlap <= 0.0:
                continue
            normal_force = max(0.0, CONTACT_STIFFNESS * overlap - NORMAL_DAMPING * normal_speed)
            tangent_force = min(friction * normal_force, TANGENTIAL_DAMPING * abs(tangent_speed))
            tangent_sign = -1.0 if tangent_speed > 0.0 else 1.0
            particle.fx += normal_force * nx - tangent_force * ny * tangent_sign
            particle.fy += normal_force * ny + tangent_force * nx * tangent_sign
            reaction += normal_force
    return reaction


def integrate(particles: list[Particle], radius: float, left: float, right: float, bottom: float, top: float) -> None:
    for particle in particles:
        # No gravitational acceleration is added: all motion comes from contacts.
        particle.vx = (particle.vx + particle.fx * TIME_STEP) * VELOCITY_DAMPING
        particle.vy = (particle.vy + particle.fy * TIME_STEP) * VELOCITY_DAMPING
        particle.x += particle.vx * TIME_STEP
        particle.y += particle.vy * TIME_STEP
        # The force model handles wall reactions.  Keep a particle inside the
        # physical box without erasing the overlap that creates that reaction.
        particle.x = min(right, max(left, particle.x))
        particle.y = min(top, max(bottom, particle.y))


def dem_step(
    particles: list[Particle], radius: float, left: float, right: float, bottom: float, top: float, friction: float
) -> float:
    reset_forces(particles)
    accumulate_contact_forces(particles, radius, friction)
    wall_reaction = accumulate_wall_forces(particles, radius, left, right, bottom, top, friction)
    integrate(particles, radius, left, right, bottom, top)
    return wall_reaction


def main() -> None:
    particles = random_particles()
    # Relax the random normal-radius cloud with DEM before its first snapshot.
    for _ in range(PREPARATION_STEPS):
        dem_step(particles, NOMINAL_RADIUS, 0.0, 1.0, 0.0, 1.0, friction=0.0)

    output_path = Path(__file__).with_name("radius_expansion_servo_trajectory.txt")
    with output_path.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.writer(output_file)
        writer.writerow(
            ["frame", "phase", "particle_id", "x", "y", "radius", "left", "right", "bottom", "top", "stress_kpa", "friction"]
        )
        frame = 0

        def write_frame(
            phase: str, radius: float, left: float, right: float, bottom: float, top: float, stress_kpa: float, friction: float
        ) -> None:
            nonlocal frame
            for particle_id, particle in enumerate(particles):
                writer.writerow(
                    [
                        frame,
                        phase,
                        particle_id,
                        f"{particle.x:.6f}",
                        f"{particle.y:.6f}",
                        f"{radius:.6f}",
                        f"{left:.6f}",
                        f"{right:.6f}",
                        f"{bottom:.6f}",
                        f"{top:.6f}",
                        f"{stress_kpa:.6f}",
                        f"{friction:.2f}",
                    ]
                )
            frame += 1

        write_frame("nominal", NOMINAL_RADIUS, 0.0, 1.0, 0.0, 1.0, 0.0, friction=0.60)

        for step in range(1, REDUCTION_STEPS + 1):
            progress = step / REDUCTION_STEPS
            radius = NOMINAL_RADIUS + (SCALED_RADIUS - NOMINAL_RADIUS) * progress
            dem_step(particles, radius, 0.0, 1.0, 0.0, 1.0, friction=0.0)
            if step % SAVE_EVERY == 0 or step == REDUCTION_STEPS:
                write_frame("reduction", radius, 0.0, 1.0, 0.0, 1.0, 0.0, friction=0.0)

        for step in range(1, EXPANSION_STEPS + 1):
            progress = step / EXPANSION_STEPS
            radius = SCALED_RADIUS + (NOMINAL_RADIUS - SCALED_RADIUS) * progress
            dem_step(particles, radius, 0.0, 1.0, 0.0, 1.0, friction=0.0)
            if step % SAVE_EVERY == 0 or step == EXPANSION_STEPS:
                write_frame("expansion", radius, 0.0, 1.0, 0.0, 1.0, 0.0, friction=0.0)

        side = 1.0
        measured_stress = 0.0
        for step in range(1, SERVO_STEPS + 1):
            left = bottom = (1.0 - side) / 2
            right = top = 1.0 - left
            wall_reaction = dem_step(particles, NOMINAL_RADIUS, left, right, bottom, top, friction=0.60)
            measured_stress = STRESS_TO_KPA * wall_reaction / (4.0 * side)
            # Stress error closes or opens all walls symmetrically: a servo controller.
            side = min(1.0, max(MINIMUM_SIDE, side - SERVO_GAIN * (SERVO_TARGET_STRESS - measured_stress)))
            if step % SAVE_EVERY == 0 or step == SERVO_STEPS:
                write_frame("servo", NOMINAL_RADIUS, left, right, bottom, top, measured_stress, friction=0.60)

    final_density = len(particles) * pi * NOMINAL_RADIUS**2 / side**2
    print(
        f"Wrote {frame} frames for {len(particles)} particles; final density = {final_density:.3f}; "
        f"final stress = {measured_stress:.3f} kPa; final side = {side:.3f}"
    )


if __name__ == "__main__":
    main()
