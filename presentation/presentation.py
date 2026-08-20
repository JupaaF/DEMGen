import csv
from pathlib import Path

from manim import *  # or: from manimlib import *

from manim_slides import Slide

class DEMGenPresentation(Slide):


    def construct(self):
        main_title = Tex("Mobility to Utrecht", font_size=100)
        subtitle = Tex("How does ", "DEMGen", " work?", font_size=100)
        subtitle[1].set_color("#C6A64B")
        subtitle.next_to(main_title, DOWN*1.2)
        VGroup(main_title, subtitle).shift(UP * 1.5)
        
        name = Tex("Fernandez Juan Pablo", font_size=50)
        date = Tex("01/08 - 31/08", font_size=50)
        
        #Align the date with the lower edge of the screen
        date.to_edge(DOWN + LEFT)
        name.to_edge(DOWN + LEFT)
        name.shift(UP * 0.7)
        
        
        self.wait(1)   
        self.play(FadeIn(main_title))
        self.wait(0.5)
        self.play(FadeIn(subtitle))
        self.wait(2)
        self.play(FadeIn(name), FadeIn(date))
        
        self.next_slide()
        
        self.play(FadeOut(main_title), FadeOut(subtitle[0]), FadeOut(subtitle[2]), 
                  FadeOut(name), FadeOut(date), run_time=1)
        self.play(subtitle[1].animate.scale(0.65).to_edge(UP + LEFT), run_time=1.5)
        
        outline = Tex(": Outline", font_size=65).next_to(subtitle[1], 0.7*RIGHT)
        self.play(Create(outline), run_time=0.5)
        
        #Crear los items con arrows
        
        subitems_outline = [Tex("What is DEMGen?", font_size=50), 
                   Tex("What methods does it use?", font_size=50), 
                   Tex("Deep dive: IRESR", font_size=50), 
                   Tex("New method: Tapping", font_size=50), 
                   Tex("Conclusions", font_size=50)]
        arrows_outline = []
        for i, titulo in enumerate(subitems_outline):
            arrow = Arrow(start=subtitle[1].get_left() + DOWN*(i+2) + 0.5*RIGHT, 
                          end=subtitle[1].get_left() + DOWN*(i+2) + RIGHT, 
                          color="#C6A64B", buff = 0)
            arrows_outline.append(arrow)
            titulo.next_to(arrow, RIGHT)
        
        self.play(
            *[Create(arrow) for arrow in arrows_outline],
            *[Write(titulo) for titulo in subitems_outline],
            run_time=1.5,
        )
        
        self.next_slide()
        #FadeOut todos los subitems y arrows, excepto el primero
        self.play(FadeOut(outline),FadeOut(subtitle[1]), 
                  *[FadeOut(titulo) for titulo in subitems_outline[1:]], 
                  *[FadeOut(arrow) for arrow in arrows_outline[1:]], 
                  run_time=1)
        
        title_slide3 = Title("What is DEMGen?", font_size=55).to_edge(UP)
        self.play(Transform(subitems_outline[0], title_slide3), FadeOut(arrows_outline[0]), run_time=0.5)
        
        packing_side_length = 5.6
        square = Square(side_length=packing_side_length, color=WHITE).shift(DOWN * 0.25)

        csv_path = (
            Path(__file__).resolve().parents[1]
            / "example"
            / "simple_dem_100_particles"
            / "particles_100_square.csv"
        )
        with csv_path.open(newline="", encoding="utf-8") as csv_file:
            particles = list(csv.DictReader(csv_file))

        lower_left = square.get_corner(DL)
        particle_circles = VGroup()
        for particle in particles:
            x = float(particle["x"])
            y = float(particle["y"])
            radius = float(particle["radius"])
            center = lower_left + RIGHT * (x * packing_side_length) + UP * (y * packing_side_length)
            particle_circles.add(
                Circle(
                    radius=radius * packing_side_length,
                    stroke_color=BLACK,
                    stroke_width=0.6,
                    fill_color="#C6A64B",
                    fill_opacity=0.92,
                ).move_to(center)
            )

        self.play(Create(square))
        self.play(
            LaggedStart(*[FadeIn(circle, scale=0.7) for circle in particle_circles], lag_ratio=0.015),
            run_time=2.5,
        )
        self.next_slide()
        
        self.play(VGroup(square, particle_circles).animate.to_edge(LEFT).scale(0.7), run_time=1.5)
        flecha_density = CurvedArrow(
            start_point=square.get_right()+ UP,
            end_point=square.get_right() + RIGHT * 2.5 + UP * 2,
            angle=-PI / 3,
            color=YELLOW,
        )
        tex_density = Tex("Density $\\phi$ = 0.75", font_size=50).next_to(flecha_density.get_end(), RIGHT)
        self.play(Create(flecha_density), run_time=0.5)
        self.play(Create(tex_density), run_time=0.5)
        self.wait()
        self.next_slide()
        
        flecha_MCN = CurvedArrow(
                    start_point=square.get_right() + UP * (1 / 3),
                    end_point=square.get_right() + RIGHT * 2.5 + UP * (2 / 3),
                    angle=-PI / 3,
                    color=YELLOW,
                )
        tex_MCN = Tex("MCN = 3.4", font_size=50).next_to(flecha_MCN.get_end(), RIGHT)
        self.play(Create(flecha_MCN), run_time=0.5)
        self.play(Create(tex_MCN), run_time=0.5)
        self.wait()
        
        self.next_slide()
        
        flecha_stress = CurvedArrow(
                    start_point=square.get_right() + DOWN * (1 / 3),
                    end_point=square.get_right() + RIGHT * 2.5 + DOWN * (2 / 3),
                    angle=PI / 3,
                    color=YELLOW,
                )
        tex_stress = Tex("Stress $\\sigma$ = 10 kPa", font_size=50).next_to(flecha_stress.get_end(), RIGHT)
        self.play(Create(flecha_stress), run_time=0.5)
        self.play(Create(tex_stress), run_time=0.5)
        self.wait()
        
        self.next_slide()
        
        flecha_thermal_conductivity = CurvedArrow(
                            start_point=square.get_right() + DOWN,
                            end_point=square.get_right() + RIGHT * 2.5 + 2 * DOWN,
                            angle=PI / 3,
                            color=YELLOW,
                        )
        tex_thermal_conductivity = Tex("Cond. $\\lambda$ = 1.5 W/(m$\\cdot$K)", font_size=50).next_to(flecha_thermal_conductivity.get_end(), RIGHT)
        self.play(Create(flecha_thermal_conductivity), run_time=0.5)
        self.play(Create(tex_thermal_conductivity), run_time=0.5)
        self.wait()
        self.next_slide()

        second_square = Square(side_length=packing_side_length, color=WHITE).shift(DOWN * 0.25)
        second_csv_path = (
            Path(__file__).resolve().parents[1]
            / "example"
            / "simple_dem_100_particles"
            / "particles_100_square_seed_20260818.csv"
        )
        with second_csv_path.open(newline="", encoding="utf-8") as csv_file:
            second_particles = list(csv.DictReader(csv_file))

        second_lower_left = second_square.get_corner(DL)
        second_particle_circles = VGroup()
        for particle in second_particles:
            x = float(particle["x"])
            y = float(particle["y"])
            radius = float(particle["radius"])
            center = (
                second_lower_left
                + RIGHT * (x * packing_side_length)
                + UP * (y * packing_side_length)
            )
            second_particle_circles.add(
                Circle(
                    radius=radius * packing_side_length,
                    stroke_color=BLACK,
                    stroke_width=0.6,
                    fill_color="#C6A64B",
                    fill_opacity=0.92,
                ).move_to(center)
            )
        
        second_packing = VGroup(second_square, second_particle_circles)
        second_packing.to_edge(LEFT).scale(0.7)
        second_packing.shift(LEFT * 12)
        self.add(second_packing)

        objects_to_remove = [
            mobject
            for mobject in self.mobjects
            if mobject is not subitems_outline[0] and mobject is not second_packing
        ]
        self.play(
            *[mobject.animate.shift(RIGHT * 15) for mobject in objects_to_remove],
            second_packing.animate.shift(RIGHT * 12),
            run_time=1.2,
        )
        self.remove(*objects_to_remove)
        self.wait()
        self.next_slide()
                
        flecha_density = CurvedArrow(
            start_point=second_square.get_right()+ UP,
            end_point=second_square.get_right() + RIGHT * 2.5 + UP * 2,
            angle=-PI / 3,
            color=YELLOW,
        )
        tex_density = Tex("Density $\\phi$ = 0.75", font_size=50).next_to(flecha_density.get_end(), RIGHT)
        
        flecha_MCN = CurvedArrow(
                    start_point=second_square.get_right() + UP * (1 / 3),
                    end_point=second_square.get_right() + RIGHT * 2.5 + UP * (2 / 3),
                    angle=-PI / 3,
                    color=YELLOW,
                )
        tex_MCN = Tex("MCN = 3.4", font_size=50).next_to(flecha_MCN.get_end(), RIGHT)
        self.play(Create(flecha_MCN),Create(flecha_density), run_time=0.5)
        self.play(Create(tex_MCN),Create(tex_density), run_time=0.5)
        self.wait()
        
        self.next_slide()
        
        flecha_stress = CurvedArrow(
                    start_point=second_square.get_right() + DOWN * (1 / 3),
                    end_point=second_square.get_right() + RIGHT * 2.5 + DOWN * (2 / 3),
                    angle=PI / 3,
                    color=YELLOW,
                )
        tex_stress = Tex("Stress $\\sigma$ = 20 kPa", font_size=50).next_to(flecha_stress.get_end(), RIGHT)
        
        flecha_thermal_conductivity = CurvedArrow(
                            start_point=second_square.get_right() + DOWN,
                            end_point=second_square.get_right() + RIGHT * 2.5 + 2 * DOWN,
                            angle=PI / 3,
                            color=YELLOW,
                        )
        tex_thermal_conductivity = Tex("Cond. $\\lambda$ = 1.2 W/(m$\\cdot$K)", font_size=50).next_to(flecha_thermal_conductivity.get_end(), RIGHT)
        self.play(Create(flecha_thermal_conductivity),Create(flecha_stress), run_time=0.5)
        self.play(Create(tex_thermal_conductivity),Create(tex_stress), run_time=0.5)
        self.wait()
        self.next_slide()
        
        objects_to_remove = [
            mobject
            for mobject in self.mobjects
            if mobject is not subitems_outline[0]
        ]
        self.play(
            *[mobject.animate.shift(RIGHT * 15) for mobject in objects_to_remove],
            run_time=1.2,
        )
        
        logo_path = Path(__file__).resolve().parents[1] / "docs" / "images" / "LOGO1-transparent.png"
        logo = ImageMobject(logo_path)
        logo.scale(0.6)
        self.play(FadeIn(logo))
        
        self.next_slide()
        
        self.play(FadeOut(logo), run_time=1)
        self.remove(*objects_to_remove)

        packing_directory = (
            Path(__file__).resolve().parents[1] / "example" / "simple_dem_100_particles"
        )
        packing_files = (
            "particles_100_square.csv",
            "particles_100_square_seed_20260818.csv",
            "particles_100_square_seed_20260819.csv",
        )
        comparison_packings = VGroup()

        for i, (filename, target_x) in enumerate(zip(packing_files, (-3.8, 0.0, 3.8))):
            comparison_square = Square(side_length=packing_side_length, color=WHITE).shift(DOWN * 0.25)
            with (packing_directory / filename).open(newline="", encoding="utf-8") as csv_file:
                comparison_particles = list(csv.DictReader(csv_file))

            lower_left = comparison_square.get_corner(DL)
            comparison_circles = VGroup()
            for particle in comparison_particles:
                x = float(particle["x"])
                y = float(particle["y"])
                radius = float(particle["radius"])
                center = (
                    lower_left
                    + RIGHT * (x * packing_side_length)
                    + UP * (y * packing_side_length)
                )
                comparison_circles.add(
                    Circle(
                        radius=radius * packing_side_length,
                        stroke_color=BLACK,
                        stroke_width=0.6,
                        fill_color="#C6A64B",
                        fill_opacity=0.92,
                    ).move_to(center)
                )

            comparison_packing = VGroup(comparison_square, comparison_circles)
            comparison_packing.scale(0.60).move_to([target_x, -0.25, 0])
            comparison_label = Tex(f"($\\rho_{i+1}$, $\\sigma_{i+1}$)", font_size=40).next_to(
                comparison_packing,
                DOWN,
                buff=0.25,
            )
            comparison_packings.add(VGroup(comparison_packing, comparison_label))

        comparison_packings.shift(RIGHT * 15)
        self.add(comparison_packings)
        self.play(comparison_packings.animate.shift(LEFT * 15), run_time=1.5)
        self.next_slide()
        
        self.play(comparison_packings.animate.shift(RIGHT * 15), run_time=1.5)
        objects_to_remove = [
            mobject
            for mobject in self.mobjects
            if mobject is not subitems_outline[0]
        ]
        self.remove(*objects_to_remove)
        
        outline_title = Tex("DEMGen", ": Outline", font_size=65).to_edge(UP + LEFT)
        outline_title[0].set_color("#C6A64B")
        outline_labels = (
            "What is DEMGen?",
            "What methods does it use?",
            "Deep dive: IRESR",
            "New method: Tapping",
            "Conclusions",
        )
        outline_arrows = []
        outline_texts = []
        for index, label in enumerate(outline_labels):
            arrow = Arrow(
                start=outline_title.get_left() + DOWN * (index + 2) + RIGHT * 0.5,
                end=outline_title.get_left() + DOWN * (index + 2) + RIGHT,
                color="#C6A64B",
                buff=0,
            )
            text = Tex(label, font_size=50).next_to(arrow, RIGHT)
            outline_arrows.append(arrow)
            outline_texts.append(text)

        self.play(
            Transform(subitems_outline[0], outline_texts[0]),
            FadeIn(outline_title),
            FadeIn(outline_arrows[0]),
            *[FadeIn(arrow) for arrow in outline_arrows[1:]],
            *[FadeIn(text) for text in outline_texts[1:]],
            run_time=1.2,
        )
        self.next_slide()
        
        self.play(FadeOut(outline_title), 
                    *[FadeOut(titulo) for index, titulo in enumerate(outline_texts) if index not in (0, 1)], 
                    *[FadeOut(arrow) for index, arrow in enumerate(outline_arrows) if index != 1],
                    FadeOut(subitems_outline[0]),
                    run_time=1)
        
        title_slide = Title("What methods does it use?", font_size=55).to_edge(UP)
        self.play(ReplacementTransform(outline_texts[1], title_slide), FadeOut(outline_arrows[1]), run_time=0.5)
        self.wait()
            
        self.next_slide()
        non_dem_based_label = Tex("Non-DEM-based", " methods", font_size = 55)
        non_dem_based_label[0].set_color("#C6A64B")
        self.play(Write(non_dem_based_label), run_time= 0.5)
        
        self.next_slide()
        
        constructive_label = Tex("Constructive", " methods", font_size = 55)
        constructive_label[0].set_color("#C6A64B")
        self.play(ReplacementTransform(non_dem_based_label, constructive_label), run_time= 0.5)
        
        self.next_slide()
        self.play(constructive_label.animate.shift(2*UP))
        
        constructive_side = 3.4
        cubic_square = Square(side_length=constructive_side, color=WHITE)
        cubic_rows = VGroup()
        cubic_particles_per_side = 9
        cubic_radius = constructive_side / (2 * cubic_particles_per_side)
        cubic_lower_left = cubic_square.get_corner(DL)
        for row in range(cubic_particles_per_side):
            cubic_row = VGroup()
            for column in range(cubic_particles_per_side):
                cubic_row.add(
                    Circle(
                        radius=cubic_radius,
                        stroke_color=BLACK,
                        stroke_width=0.6,
                        fill_color="#C6A64B",
                        fill_opacity=0.92,
                    ).move_to(
                        cubic_lower_left
                        + RIGHT * ((2 * column + 1) * cubic_radius)
                        + UP * ((2 * row + 1) * cubic_radius)
                    )
                )
            cubic_rows.add(cubic_row)

        hpc_square = Square(side_length=constructive_side, color=WHITE)
        hpc_particle_rows = VGroup()
        hpc_row_count = 10
        hpc_radius = constructive_side / 18
        hpc_lower_left = hpc_square.get_corner(DL)
        hpc_height = 2 * hpc_radius + (hpc_row_count - 1) * (3 ** 0.5) * hpc_radius
        hpc_vertical_margin = (constructive_side - hpc_height) / 2
        for row in range(hpc_row_count):
            hpc_columns = 9 if row % 2 == 0 else 8
            horizontal_offset = 0 if row % 2 == 0 else hpc_radius
            hpc_row = VGroup()
            for column in range(hpc_columns):
                hpc_row.add(
                    Circle(
                        radius=hpc_radius,
                        stroke_color=BLACK,
                        stroke_width=0.6,
                        fill_color="#C6A64B",
                        fill_opacity=0.92,
                    ).move_to(
                        hpc_lower_left
                        + RIGHT * (hpc_radius + horizontal_offset + 2 * column * hpc_radius)
                        + UP * (hpc_vertical_margin + hpc_radius + row * (3 ** 0.5) * hpc_radius)
                    )
                )
            hpc_particle_rows.add(hpc_row)
            
        hpc_particle_rows.set_z_index(0)
        cubic_rows.set_z_index(0)
        hpc_square.set_z_index(1)
        cubic_square.set_z_index(1)

        cubic_packing = VGroup(cubic_square, cubic_rows).move_to(LEFT * 3 + DOWN * 0.4)
        hpc_packing = VGroup(hpc_square, hpc_particle_rows).move_to(RIGHT * 3 + DOWN * 0.4)
        cubic_label = Tex("Cubic", font_size=40).next_to(cubic_packing, DOWN, buff=0.25)
        hpc_label = Tex("HPC", font_size=40).next_to(hpc_packing, DOWN, buff=0.25)
        
        
        
        self.play(Create(cubic_square), Create(hpc_square))
        row_animations = []
        for row_index in range(max(cubic_particles_per_side, hpc_row_count)):
            animations = []
            if row_index < cubic_particles_per_side:
                animations.append(DrawBorderThenFill(cubic_rows[row_index]))
            if row_index < hpc_row_count:
                animations.append(DrawBorderThenFill(hpc_particle_rows[row_index]))
            row_animations.append(AnimationGroup(*animations))
        self.play(
            LaggedStart(*row_animations, lag_ratio=0.18),
            run_time=3.0,
        )
        self.play(
            Write(cubic_label),
            Write(hpc_label),
            run_time=1,
        )
        
        self.next_slide()
        
        objects_to_remove = [
            mobject
            for mobject in self.mobjects
            if mobject is not title_slide
        ]
        dem_based_label = Tex("DEM-based", " methods", font_size = 55).shift(LEFT * 15 + UP * 2)
        dem_based_label[0].set_color("#C6A64B")
        dynamic_label = Tex("Dynamic", " methods", font_size = 55).shift(UP * 2)
        dynamic_label[0].set_color("#C6A64B")
        self.play(
            *[mobject.animate.shift(RIGHT * 15) for mobject in objects_to_remove],
            dem_based_label.animate.shift(RIGHT * 15),
            run_time=1.2,
        )
        self.remove(*objects_to_remove)
        
        self.next_slide()
        self.play(ReplacementTransform(dem_based_label, dynamic_label), run_time=0.5)
        
        self.next_slide()
        self.play(Unwrite(dynamic_label), run_time=0.5)
        
        gravitational_label = Tex("Gravitational deposition", font_size = 40)
        isotropic_label = Tex("Isotropic compression", font_size = 40)
        radius_expansion_label = Tex("Radius expansion", font_size = 40)
        radius_expansion_servo_label = Tex("Radius expansion with servo control", font_size = 40)
        improved_radius_expansion_label = Tex("Improved radius expansion with servo control", font_size = 40)
        
        arrows = VGroup(
            Arrow(start=LEFT, end=0.5*RIGHT, color="#C6A64B"),
            Arrow(start=LEFT, end=0.5*RIGHT, color="#C6A64B"),
            Arrow(start=LEFT, end=0.5*RIGHT, color="#C6A64B"),
            Arrow(start=LEFT, end=0.5*RIGHT, color="#C6A64B"),
            Arrow(start=LEFT, end=0.5*RIGHT, color="#C6A64B")
        )
        arrows.arrange(DOWN, buff=0.7).to_edge(LEFT, buff=1)
        arrows.shift(DOWN * 0.5)
        labels = VGroup(gravitational_label, isotropic_label, 
                        radius_expansion_label, radius_expansion_servo_label, 
                        improved_radius_expansion_label)
        labels.arrange(DOWN, buff=0.7)
        for label,arrow in zip(labels, arrows):
            label.next_to(arrow, RIGHT, buff=0.5)
        
        self.play(Write(arrows), Write(labels), run_time=2)
        self.next_slide()
        
        self.play(ApplyWave(arrows[0:3],amplitude=0.1),ApplyWave(labels[0:3],amplitude=0.1),FadeOut(arrows[3:5]),FadeOut(labels[3:5]), run_time=1.2)
        
        self.next_slide()
        
        initial_state = VGroup(arrows[0:3], labels[0:3]).save_state()
        self.play(FadeOut(arrows[0:3]), FadeOut(labels[1:3]), run_time=0.5)
        self.play(labels[0].animate.to_edge(DOWN, buff=0.5).set_x(0), run_time=1)
        
        # Gravitational deposition, slide 1: the receiving box and its inlet.
        self.next_slide()

        container_width = 3
        container_height = 3
        container_bottom = DOWN * 2.1
        container_bottom_left = container_bottom + LEFT * container_width / 2
        container_bottom_right = container_bottom + RIGHT * container_width / 2
        container_top_left = container_bottom + LEFT * container_width / 2 + UP * container_height
        container_top_right = container_bottom + RIGHT * container_width / 2 + UP * container_height
        container = VGroup(
            Line(container_bottom_left, container_bottom_right, color=WHITE, stroke_width=4),
            Line(container_bottom_left, container_top_left, color=WHITE, stroke_width=4),
            Line(container_bottom_right, container_top_right, color=WHITE, stroke_width=4),
        )

        inlet = VGroup(
            Line(LEFT * 1.05 + UP * 3.35, LEFT * 0.30 + UP * 2.35, color=BLUE_C, stroke_width=5),
            Line(RIGHT * 1.05 + UP * 3.35, RIGHT * 0.30 + UP * 2.35, color=BLUE_C, stroke_width=5),
            Line(LEFT * 1.05 + UP * 3.35, RIGHT * 1.05 + UP * 3.35, color=BLUE_C, stroke_width=5),
            Line(LEFT * 0.30 + UP * 2.35, RIGHT * 0.30 + UP * 2.35, color=BLUE_C, stroke_width=5),
        )
        inlet_label = Tex("Particle inlet", font_size=30, color=BLUE_B).next_to(inlet, RIGHT, buff=0.25)
        
        inlet.shift(DOWN)
        inlet_label.shift(DOWN)
        inlet_particles = VGroup(
            *[
                Circle(
                    radius=0.12,
                    stroke_color=BLACK,
                    stroke_width=0.5,
                    fill_color="#C6A64B",
                    fill_opacity=0.95,
                ).move_to(position)
                for position in (
                    LEFT * 0.48 + UP * 3.08,
                    UP * 3.08,
                    RIGHT * 0.48 + UP * 3.08,
                    LEFT * 0.24 + UP * 2.72,
                    RIGHT * 0.24 + UP * 2.72,
                )
            ]
        )
        inlet_particles.shift(DOWN)

        self.play(Create(container), Create(inlet), Write(inlet_label), run_time=1.3)
        self.play(
            LaggedStart(*[FadeIn(particle, scale=0.7) for particle in inlet_particles], lag_ratio=0.12),
            run_time=0.9,
        )

        # Slide 2: the text file contains frame-by-frame positions from a small
        # 2D DEM-like simulation (gravity, inelastic collisions and damping).
        self.next_slide()

        trajectory_path = Path(__file__).with_name("gravitational_deposition_trajectory.txt")
        frames = {}
        with trajectory_path.open(newline="", encoding="utf-8") as trajectory_file:
            for row in csv.DictReader(trajectory_file):
                frame_number = int(row["frame"])
                frames.setdefault(frame_number, {})[int(row["particle_id"])] = {
                    "x": float(row["x"]),
                    "y": float(row["y"]),
                    "radius": float(row["radius"]),
                    "active": row["active"] == "1",
                }

        frame_numbers = sorted(frames)
        last_frame = frame_numbers[-1]
        particle_ids = sorted(frames[frame_numbers[0]])
        frame_tracker = ValueTracker(0)
        density_by_frame = {
            frame_number: sum(
                PI * particle_data["radius"] ** 2
                for particle_data in frame_data.values()
                if particle_data["active"]
            )
            / 0.8
            for frame_number, frame_data in frames.items()
        }

        def to_scene_point(particle_data):
            return (
                container_bottom_left
                + RIGHT * (particle_data["x"] * container_width)
                + UP * (particle_data["y"] / 0.8 * container_height)
            )

        def update_particle(circle, particle_id):
            frame_value = frame_tracker.get_value()
            lower_frame = min(int(frame_value), last_frame)
            upper_frame = min(lower_frame + 1, last_frame)
            interpolation = frame_value - lower_frame
            lower_data = frames[lower_frame][particle_id]
            upper_data = frames[upper_frame][particle_id]
            circle.move_to(
                interpolate(
                    to_scene_point(lower_data),
                    to_scene_point(upper_data),
                    interpolation,
                )
            )
            circle.set_opacity(1 if lower_data["active"] else 0)

        def update_density(decimal_number):
            frame_value = frame_tracker.get_value()
            lower_frame = min(int(frame_value), last_frame)
            upper_frame = min(lower_frame + 1, last_frame)
            decimal_number.set_value(
                interpolate(
                    density_by_frame[lower_frame],
                    density_by_frame[upper_frame],
                    frame_value - lower_frame,
                )
            )
            decimal_number.next_to(density_label, RIGHT, buff=0.12)

        animated_particles = VGroup()
        for particle_id in particle_ids:
            initial_data = frames[frame_numbers[0]][particle_id]
            particle = Circle(
                radius=initial_data["radius"] * container_width,
                stroke_color=BLACK,
                stroke_width=0.6,
                fill_color="#C6A64B",
                fill_opacity=0.95,
            ).move_to(to_scene_point(initial_data))
            particle.add_updater(
                lambda circle, particle_id=particle_id: update_particle(circle, particle_id)
            )
            animated_particles.add(particle)

        behaviour_label = Tex("Gravity + contact collisions", font_size=30, color="#C6A64B")
        behaviour_label.next_to(container, LEFT, buff=0.55).shift(UP * 0.5)
        density_label = Tex("Packing density $\\phi$ =", font_size=30)
        density_label.next_to(container, RIGHT, buff=0.45).shift(UP * 0.85)
        density_number = DecimalNumber(0, num_decimal_places=2, font_size=30, color="#C6A64B")
        density_number.next_to(density_label, RIGHT, buff=0.12)
        density_number.add_updater(update_density)
        self.play(FadeOut(inlet_particles), FadeOut(inlet_label), run_time=0.35)
        self.add(animated_particles, density_number)
        self.play(Write(behaviour_label), Write(density_label), FadeIn(density_number), run_time=0.5)
        self.play(frame_tracker.animate.set_value(last_frame), run_time=12, rate_func=linear)
        self.wait(0.4)
        for particle in animated_particles:
            particle.clear_updaters()
        density_number.clear_updaters()

        self.next_slide()

        container_lid = Line(
            container_top_left,
            container_top_right,
            color=WHITE,
            stroke_width=4,
        )
        self.play(Create(container_lid), FadeOut(inlet), run_time=0.8)
        
        self.next_slide()
        isotropic_title = Tex("Isotropic compression", font_size=40).move_to(labels[0].get_center())
        self.play(
            FadeOut(container),
            FadeOut(container_lid),
            FadeOut(animated_particles),
            FadeOut(behaviour_label),
            FadeOut(density_label),
            FadeOut(density_number),
            ReplacementTransform(labels[0], isotropic_title),
            run_time=0.5,
        )

        # Isotropic compression, slide 1: a loose, pre-generated packing.
        initial_width = 4.8
        initial_height = 4.8
        compression_bottom = DOWN * 2.25
        initial_bottom_left = compression_bottom + LEFT * initial_width / 2
        isotropic_trajectory_path = Path(__file__).with_name("isotropic_compression_trajectory.txt")
        isotropic_frames = {}
        with isotropic_trajectory_path.open(newline="", encoding="utf-8") as trajectory_file:
            for row in csv.DictReader(trajectory_file):
                frame_number = int(row["frame"])
                isotropic_frames.setdefault(frame_number, {})[int(row["particle_id"])] = {
                    key: float(row[key])
                    for key in ("x", "y", "radius", "left", "right", "bottom", "top")
                }

        isotropic_frame_numbers = sorted(isotropic_frames)
        initial_compression_frame = isotropic_frame_numbers[0]
        compression_start_frame = next(
            frame_number
            for frame_number in isotropic_frame_numbers
            if isotropic_frames[frame_number][0]["left"] > 0
        )
        final_compression_frame = isotropic_frame_numbers[-1]
        isotropic_particle_ids = sorted(isotropic_frames[initial_compression_frame])
        compression_frame_tracker = ValueTracker(compression_start_frame)

        def isotropic_scene_point(particle_data):
            return (
                initial_bottom_left
                + RIGHT * (particle_data["x"] * initial_width)
                + UP * (particle_data["y"] * initial_height)
            )

        def container_from_frame(frame_number):
            box = isotropic_frames[frame_number][0]
            bottom_left = (
                initial_bottom_left
                + RIGHT * (box["left"] * initial_width)
                + UP * (box["bottom"] * initial_height)
            )
            bottom_right = bottom_left + RIGHT * ((box["right"] - box["left"]) * initial_width)
            top_left = bottom_left + UP * ((box["top"] - box["bottom"]) * initial_height)
            top_right = bottom_right + UP * ((box["top"] - box["bottom"]) * initial_height)
            return VGroup(
                Line(bottom_left, bottom_right, color=WHITE, stroke_width=4),
                Line(bottom_left, top_left, color=WHITE, stroke_width=4),
                Line(bottom_right, top_right, color=WHITE, stroke_width=4),
                Line(top_left, top_right, color=WHITE, stroke_width=4),
            )

        compression_container = container_from_frame(initial_compression_frame)
        initial_bottom_right = initial_bottom_left + RIGHT * initial_width
        compression_particles = VGroup()
        for particle_id in isotropic_particle_ids:
            initial_data = isotropic_frames[initial_compression_frame][particle_id]
            compression_particles.add(
                Circle(
                    radius=initial_data["radius"] * initial_width,
                    stroke_color=BLACK,
                    stroke_width=0.5,
                    fill_color="#C6A64B",
                    fill_opacity=0.95,
                ).move_to(isotropic_scene_point(initial_data))
            )

        initialization_label = Tex("Loose initial packing", font_size=30, color="#C6A64B")
        initialization_label.next_to(compression_container, DOWN, buff=0.25)
        self.play(Create(compression_container), run_time=1.2)
        self.play(
            LaggedStart(*[FadeIn(particle, scale=0.7) for particle in compression_particles], lag_ratio=0.025),
            Write(initialization_label),
            run_time=2,
        )

        # Slide 2: random external forces keep the particles rearranging.
        self.next_slide()

        random_forces_label = Tex("Repeated random forces", font_size=30, color=YELLOW)
        random_forces_label.next_to(compression_container, RIGHT, buff=0.45).shift(UP * 0.8)
        self.play(FadeOut(initialization_label), Write(random_forces_label), run_time=0.5)
        
        self.next_slide(loop=True)
        
        force_cycles = [
            [(2, RIGHT + UP), (15, LEFT), (31, DOWN + RIGHT), (48, UP), (59, LEFT + DOWN)],
            [(7, LEFT + UP), (22, RIGHT), (37, LEFT + DOWN), (45, RIGHT + UP), (61, DOWN)],
            [(4, DOWN), (18, RIGHT + UP), (28, LEFT), (52, UP), (56, RIGHT + DOWN)],
        ]
        for force_cycle in force_cycles:
            force_arrows = VGroup()
            flashes = []
            for particle_index, direction in force_cycle:
                direction = normalize(direction)
                center = compression_particles[particle_index].get_center()
                force_arrows.add(
                    Arrow(
                        center + direction * 0.15,
                        center + direction * 0.52,
                        buff=0,
                        color=RED,
                        stroke_width=3,
                        max_tip_length_to_length_ratio=0.28,
                    )
                )
                flashes.append(Flash(center, color=RED, flash_radius=0.28, line_length=0.1))
            self.play(*[GrowArrow(arrow) for arrow in force_arrows], *flashes, run_time=0.55)
            self.play(FadeOut(force_arrows), run_time=0.25)

        # Slide 3: all four boundaries move inwards at the same rate.
        self.next_slide()

        compression_label = Tex("All boundaries move inward", font_size=30, color="#C6A64B")
        compression_label.next_to(compression_container, RIGHT, buff=0.45).shift(UP * 0.8)
        container_side_by_frame = {
            frame_number: frame_data[0]["right"] - frame_data[0]["left"]
            for frame_number, frame_data in isotropic_frames.items()
        }
        container_size_label = Tex("Container side $L$ =", font_size=30)
        container_size_label.next_to(compression_container, RIGHT, buff=0.45).shift(DOWN * 0.15)
        container_size_number = DecimalNumber(
            container_side_by_frame[compression_start_frame],
            num_decimal_places=2,
            font_size=30,
            color="#C6A64B",
        )
        container_size_number.next_to(container_size_label, RIGHT, buff=0.12)

        def update_container_size(decimal_number):
            frame_value = compression_frame_tracker.get_value()
            lower_frame = min(int(frame_value), final_compression_frame)
            upper_frame = min(lower_frame + 1, final_compression_frame)
            decimal_number.set_value(
                interpolate(
                    container_side_by_frame[lower_frame],
                    container_side_by_frame[upper_frame],
                    frame_value - lower_frame,
                )
            )
            decimal_number.next_to(container_size_label, RIGHT, buff=0.12)

        container_size_number.add_updater(update_container_size)
        compressed_container = container_from_frame(final_compression_frame)
        initial_bottom_center = (initial_bottom_left + initial_bottom_right) / 2
        initial_top_center = initial_bottom_center + UP * initial_height
        initial_left_center = initial_bottom_left + UP * initial_height / 2
        initial_right_center = initial_bottom_right + UP * initial_height / 2
        inward_arrows = VGroup(
            Arrow(initial_left_center + LEFT * 0.7, initial_left_center + RIGHT * 0.15, color=BLUE_C, buff=0),
            Arrow(initial_right_center + RIGHT * 0.7, initial_right_center + LEFT * 0.15, color=BLUE_C, buff=0),
            Arrow(initial_bottom_center + DOWN * 0.7, initial_bottom_center + UP * 0.15, color=BLUE_C, buff=0),
            Arrow(initial_top_center + UP * 0.7, initial_top_center + DOWN * 0.15, color=BLUE_C, buff=0),
        )
        final_box = isotropic_frames[final_compression_frame][0]
        final_bottom_left = (
            initial_bottom_left
            + RIGHT * (final_box["left"] * initial_width)
            + UP * (final_box["bottom"] * initial_height)
        )
        final_bottom_right = final_bottom_left + RIGHT * ((final_box["right"] - final_box["left"]) * initial_width)
        final_bottom_center = (final_bottom_left + final_bottom_right) / 2
        final_top_center = final_bottom_center + UP * ((final_box["top"] - final_box["bottom"]) * initial_height)
        final_left_center = final_bottom_left + UP * ((final_box["top"] - final_box["bottom"]) * initial_height / 2)
        final_right_center = final_bottom_right + UP * ((final_box["top"] - final_box["bottom"]) * initial_height / 2)
        final_inward_arrows = VGroup(
            Arrow(final_left_center + LEFT * 0.7, final_left_center + RIGHT * 0.15, color=BLUE_C, buff=0),
            Arrow(final_right_center + RIGHT * 0.7, final_right_center + LEFT * 0.15, color=BLUE_C, buff=0),
            Arrow(final_bottom_center + DOWN * 0.7, final_bottom_center + UP * 0.15, color=BLUE_C, buff=0),
            Arrow(final_top_center + UP * 0.7, final_top_center + DOWN * 0.15, color=BLUE_C, buff=0),
        )
        self.add(container_size_number)
        self.play(
            ReplacementTransform(random_forces_label, compression_label),
            Create(inward_arrows),
            Write(container_size_label),
            FadeIn(container_size_number),
            *[
                particle.animate.move_to(
                    isotropic_scene_point(isotropic_frames[compression_start_frame][particle_id])
                )
                for particle, particle_id in zip(compression_particles, isotropic_particle_ids)
            ],
            run_time=0.7,
        )

        def update_compression_particle(circle, particle_id):
            frame_value = compression_frame_tracker.get_value()
            lower_frame = min(int(frame_value), final_compression_frame)
            upper_frame = min(lower_frame + 1, final_compression_frame)
            circle.move_to(
                interpolate(
                    isotropic_scene_point(isotropic_frames[lower_frame][particle_id]),
                    isotropic_scene_point(isotropic_frames[upper_frame][particle_id]),
                    frame_value - lower_frame,
                )
            )

        for particle, particle_id in zip(compression_particles, isotropic_particle_ids):
            particle.add_updater(
                lambda circle, particle_id=particle_id: update_compression_particle(circle, particle_id)
            )
        self.play(
            Transform(compression_container, compressed_container),
            Transform(inward_arrows, final_inward_arrows),
            compression_frame_tracker.animate.set_value(final_compression_frame),
            run_time=6,
            rate_func=smooth,
        )
        for particle in compression_particles:
            particle.clear_updaters()
        container_size_number.clear_updaters()

        self.next_slide()
        radius_title = Tex("Radius expansion", font_size=40).move_to(isotropic_title.get_center())
        self.play(
            ReplacementTransform(isotropic_title, radius_title),
            FadeOut(compression_container),
            FadeOut(compression_particles),
            FadeOut(compression_label),
            FadeOut(container_size_label),
            FadeOut(container_size_number),
            FadeOut(inward_arrows),
            run_time=0.5,
        )

        # Radius expansion, slide 1: a fixed box with initially small particles.
        
        radius_container_side = 4.8
        radius_container = Square(side_length=radius_container_side, color=WHITE, stroke_width=4)
        radius_container.move_to(UP * 0.15)
        radius_bottom_left = radius_container.get_corner(DL)

        radius_trajectory_path = Path(__file__).with_name("radius_expansion_trajectory.txt")
        radius_frames = {}
        with radius_trajectory_path.open(newline="", encoding="utf-8") as trajectory_file:
            for row in csv.DictReader(trajectory_file):
                frame_number = int(row["frame"])
                radius_frames.setdefault(frame_number, {})[int(row["particle_id"])] = {
                    key: float(row[key]) for key in ("x", "y", "radius")
                }

        radius_frame_numbers = sorted(radius_frames)
        radius_initial_frame = radius_frame_numbers[0]
        radius_final_frame = radius_frame_numbers[-1]
        radius_particle_ids = sorted(radius_frames[radius_initial_frame])
        radius_tracker = ValueTracker(radius_initial_frame)

        def radius_scene_point(particle_data):
            return (
                radius_bottom_left
                + RIGHT * (particle_data["x"] * radius_container_side)
                + UP * (particle_data["y"] * radius_container_side)
            )

        radius_particles = VGroup()
        for particle_id in radius_particle_ids:
            initial_data = radius_frames[radius_initial_frame][particle_id]
            radius_particles.add(
                Circle(
                    radius=initial_data["radius"] * radius_container_side,
                    stroke_color=BLACK,
                    stroke_width=0.5,
                    fill_color="#C6A64B",
                    fill_opacity=0.95,
                ).move_to(radius_scene_point(initial_data))
            )

        fixed_container_label = Tex("Fixed container", font_size=30, color="#C6A64B")
        fixed_container_label.next_to(radius_container, DOWN, buff=0.25)
        self.play(Create(radius_container), run_time=1.2)
        self.play(
            LaggedStart(*[FadeIn(particle, scale=0.7) for particle in radius_particles], lag_ratio=0.02),
            Write(fixed_container_label),
            run_time=2,
        )

        # Slide 2: read the simulated positions and radii while all particles grow.
        self.next_slide()

        initial_radius = radius_frames[radius_initial_frame][radius_particle_ids[0]]["radius"]
        radius_multiplier_by_frame = {
            frame_number: frame_data[radius_particle_ids[0]]["radius"] / initial_radius
            for frame_number, frame_data in radius_frames.items()
        }
        radius_multiplier_label = Tex("Radius multiplier $r/r_0$ =", font_size=30)
        radius_multiplier_label.next_to(radius_container, RIGHT, buff=0.45).shift(UP * 0.7)
        radius_multiplier_number = DecimalNumber(1, num_decimal_places=2, font_size=30, color="#C6A64B")
        radius_multiplier_number.next_to(radius_multiplier_label, RIGHT, buff=0.12)

        def update_radius_multiplier(decimal_number):
            frame_value = radius_tracker.get_value()
            lower_frame = min(int(frame_value), radius_final_frame)
            upper_frame = min(lower_frame + 1, radius_final_frame)
            decimal_number.set_value(
                interpolate(
                    radius_multiplier_by_frame[lower_frame],
                    radius_multiplier_by_frame[upper_frame],
                    frame_value - lower_frame,
                )
            )
            decimal_number.next_to(radius_multiplier_label, RIGHT, buff=0.12)

        def update_radius_particle(circle, particle_id):
            frame_value = radius_tracker.get_value()
            lower_frame = min(int(frame_value), radius_final_frame)
            upper_frame = min(lower_frame + 1, radius_final_frame)
            interpolation = frame_value - lower_frame
            lower_data = radius_frames[lower_frame][particle_id]
            upper_data = radius_frames[upper_frame][particle_id]
            circle.move_to(
                interpolate(
                    radius_scene_point(lower_data),
                    radius_scene_point(upper_data),
                    interpolation,
                )
            )
            diameter = 2 * interpolate(lower_data["radius"], upper_data["radius"], interpolation) * radius_container_side
            circle.scale_to_fit_width(diameter)
            circle.scale_to_fit_height(diameter)

        radius_multiplier_number.add_updater(update_radius_multiplier)
        for particle, particle_id in zip(radius_particles, radius_particle_ids):
            particle.add_updater(
                lambda circle, particle_id=particle_id: update_radius_particle(circle, particle_id)
            )

        self.add(radius_multiplier_number)
        self.play(
            FadeOut(fixed_container_label),
            Write(radius_multiplier_label),
            FadeIn(radius_multiplier_number),
            run_time=0.5,
        )
        self.play(radius_tracker.animate.set_value(radius_final_frame), run_time=8, rate_func=linear)
        for particle in radius_particles:
            particle.clear_updaters()
        radius_multiplier_number.clear_updaters()

        self.next_slide()
        self.play(
            FadeOut(radius_title),
            FadeOut(radius_container),
            FadeOut(radius_particles),
            FadeOut(radius_multiplier_label),
            FadeOut(radius_multiplier_number),
            run_time=0.5,
        )

        
        table = Table(
            [
                ["Geometric rules", "Random"],
                ["Low", "High"],
                ["Low", "High"],
                ["Limited","High"],
                [
                    r"\shortstack{Validation or\\test cases}",
                    r"\shortstack{Realistic materials and\\mechanical studies}",
                ]
            ],
            row_labels=[
                Tex("Initialize"),
                Tex("Cost"),
                Tex("Randomness"),
                Tex("Reality"),
                Tex("Use")
            ],
            col_labels=[
                Tex("Constructive",color="#C6A64B", font_size = 55),
                Tex("Dynamics",color="#C6A64B", font_size = 55),
            ],
            top_left_entry=Tex(""),
            element_to_mobject=Tex,
        )

        table.scale(0.75).shift(0.5*DOWN)

        self.play(FadeIn(table), run_time = 2)
        self.wait()
        self.next_slide()
        
        self.play(Indicate(table.get_row_labels()[0], color="#C6A64B"), run_time=1.2)
        
        self.next_slide()
        
        self.play(Indicate(table.get_row_labels()[1], color="#C6A64B"), run_time=1.2)
                
        self.next_slide()

        self.play(Indicate(table.get_row_labels()[2], color="#C6A64B"), run_time=1.2)
                
        self.next_slide()

        self.play(Indicate(table.get_row_labels()[3], color="#C6A64B"), run_time=1.2)
                
        self.next_slide()

        self.play(Indicate(table.get_row_labels()[4], color="#C6A64B"), run_time=1.2)
        
        self.next_slide()
        self.play(FadeOut(table), run_time = 1.2)
        
        outline_title = Tex("DEMGen", ": Outline", font_size=65).to_edge(UP + LEFT)
        outline_title[0].set_color("#C6A64B")
        outline_labels = (
            "What is DEMGen?",
            "What methods does it use?",
            "Deep dive: IRESR",
            "New method: Tapping",
            "Conclusions",
        )
        outline_arrows = []
        outline_texts = []
        for index, label in enumerate(outline_labels):
            arrow = Arrow(
                start=outline_title.get_left() + DOWN * (index + 2) + RIGHT * 0.5,
                end=outline_title.get_left() + DOWN * (index + 2) + RIGHT,
                color="#C6A64B",
                buff=0,
            )
            text = Tex(label, font_size=50).next_to(arrow, RIGHT)
            outline_arrows.append(arrow)
            outline_texts.append(text)

        self.play(
            ReplacementTransform(title_slide, outline_texts[1]),
            FadeIn(outline_title),
            *[FadeIn(arrow) for arrow in outline_arrows[0:]],
            *[FadeIn(text) for text in outline_texts[0:] if text is not outline_texts[1]],
            run_time=1.2,
        )
        
        self.next_slide()
        
        self.play(FadeOut(outline_title), 
            *[FadeOut(titulo) for index, titulo in enumerate(outline_texts) if index != 2], 
            *[FadeOut(arrow) for index, arrow in enumerate(outline_arrows) if index != 2],
            run_time=1)
        
        title_slide = Title("Deep dive: IRESR", font_size=55).to_edge(UP)
        self.play(ReplacementTransform(outline_texts[2], title_slide), FadeOut(outline_arrows[2]), run_time=0.5)
        self.wait()

        # Improved radius expansion with servo control: normal radii, scaling,
        # expansion, and final stress control are replayed from a 2D simulation.
        self.next_slide()

        servo_method_label = Tex("Radius expansion with servo control", font_size=32, color="#C6A64B")
        servo_method_label.next_to(title_slide, DOWN, buff=0.25)
        servo_container_side = 4.4
        servo_container = Square(side_length=servo_container_side, color=WHITE, stroke_width=4)
        servo_container.move_to(DOWN * 0.25)
        servo_bottom_left = servo_container.get_corner(DL)

        servo_trajectory_path = Path(__file__).with_name("radius_expansion_servo_trajectory.txt")
        servo_frames = {}
        servo_phase_frames = {}
        with servo_trajectory_path.open(newline="", encoding="utf-8") as trajectory_file:
            for row in csv.DictReader(trajectory_file):
                frame_number = int(row["frame"])
                servo_phase_frames.setdefault(row["phase"], set()).add(frame_number)
                servo_frames.setdefault(frame_number, {})[int(row["particle_id"])] = {
                    key: float(row[key])
                    for key in ("x", "y", "radius", "left", "right", "bottom", "top", "stress_kpa")
                }

        nominal_frame = min(servo_phase_frames["nominal"])
        reduction_final_frame = max(servo_phase_frames["reduction"])
        expansion_final_frame = max(servo_phase_frames["expansion"])
        servo_final_frame = max(servo_phase_frames["servo"])
        servo_particle_ids = sorted(servo_frames[nominal_frame])
        servo_frame_tracker = ValueTracker(nominal_frame)

        def servo_scene_point(particle_data):
            return (
                servo_bottom_left
                + RIGHT * (particle_data["x"] * servo_container_side)
                + UP * (particle_data["y"] * servo_container_side)
            )

        def servo_container_from_frame(frame_number):
            box = servo_frames[frame_number][0]
            bottom_left = (
                servo_bottom_left
                + RIGHT * (box["left"] * servo_container_side)
                + UP * (box["bottom"] * servo_container_side)
            )
            side_x = (box["right"] - box["left"]) * servo_container_side
            side_y = (box["top"] - box["bottom"]) * servo_container_side
            bottom_right = bottom_left + RIGHT * side_x
            top_left = bottom_left + UP * side_y
            top_right = bottom_right + UP * side_y
            return VGroup(
                Line(bottom_left, bottom_right, color=WHITE, stroke_width=4),
                Line(bottom_left, top_left, color=WHITE, stroke_width=4),
                Line(bottom_right, top_right, color=WHITE, stroke_width=4),
                Line(top_left, top_right, color=WHITE, stroke_width=4),
            )

        servo_container = servo_container_from_frame(nominal_frame)
        servo_particles = VGroup()
        for particle_id in servo_particle_ids:
            nominal_data = servo_frames[nominal_frame][particle_id]
            servo_particles.add(
                Circle(
                    radius=nominal_data["radius"] * servo_container_side,
                    stroke_color=BLACK,
                    stroke_width=0.5,
                    fill_color="#C6A64B",
                    fill_opacity=0.95,
                ).move_to(servo_scene_point(nominal_data))
            )

        nominal_label = Tex("Particles generated at nominal radius", font_size=30)
        nominal_label.next_to(servo_container, DOWN, buff=0.23)
        friction_nominal_label = Tex(
            "Friction: $\\mu_s = \\mu_d = 0.60$",
            font_size=26,
            color=GREEN,
        )
        friction_nominal_label.next_to(servo_container, RIGHT, buff=0.45).shift(DOWN * 0.40)
        self.play(Write(servo_method_label), Create(servo_container), run_time=1.1)
        self.play(
            LaggedStart(*[FadeIn(particle, scale=0.7) for particle in servo_particles], lag_ratio=0.02),
            Write(nominal_label),
            Write(friction_nominal_label),
            run_time=2,
        )

        # The scaled initialization from CreateParticlesInsideOfADomain.
        self.next_slide()

        nominal_radius = servo_frames[nominal_frame][0]["radius"]
        radius_label = Tex("Particle radius $r$ =", font_size=30)
        radius_label.next_to(servo_container, RIGHT, buff=0.45).shift(UP * 0.55)
        radius_number = DecimalNumber(nominal_radius, num_decimal_places=3, font_size=30, color="#C6A64B")
        radius_number.next_to(radius_label, RIGHT, buff=0.12)
        zero_friction_label = Tex(
            "Friction: $\\mu_s = \\mu_d = 0.00$",
            font_size=26,
            color=RED,
        )
        zero_friction_label.move_to(friction_nominal_label)

        def update_servo_particles(circle, particle_id):
            frame_value = servo_frame_tracker.get_value()
            lower_frame = min(int(frame_value), servo_final_frame)
            upper_frame = min(lower_frame + 1, servo_final_frame)
            interpolation = frame_value - lower_frame
            lower_data = servo_frames[lower_frame][particle_id]
            upper_data = servo_frames[upper_frame][particle_id]
            circle.move_to(
                interpolate(
                    servo_scene_point(lower_data),
                    servo_scene_point(upper_data),
                    interpolation,
                )
            )
            diameter = 2 * interpolate(lower_data["radius"], upper_data["radius"], interpolation) * servo_container_side
            circle.scale_to_fit_width(diameter)
            circle.scale_to_fit_height(diameter)

        def update_radius_number(decimal_number):
            frame_value = servo_frame_tracker.get_value()
            lower_frame = min(int(frame_value), expansion_final_frame)
            upper_frame = min(lower_frame + 1, expansion_final_frame)
            decimal_number.set_value(
                interpolate(
                    servo_frames[lower_frame][0]["radius"],
                    servo_frames[upper_frame][0]["radius"],
                    frame_value - lower_frame,
                )
            )
            decimal_number.next_to(radius_label, RIGHT, buff=0.12)

        for particle, particle_id in zip(servo_particles, servo_particle_ids):
            particle.add_updater(
                lambda circle, particle_id=particle_id: update_servo_particles(circle, particle_id)
            )
        radius_number.add_updater(update_radius_number)
        self.add(radius_number)
        self.play(
            FadeOut(nominal_label),
            Write(radius_label),
            FadeIn(radius_number),
            ReplacementTransform(friction_nominal_label, zero_friction_label),
            run_time=0.5,
        )
        self.play(servo_frame_tracker.animate.set_value(reduction_final_frame), run_time=2.5, rate_func=linear)

        # Radius expansion reconstructs the target particle radii gradually.
        self.next_slide()
        expansion_label = Tex("Gradual radius expansion", font_size=30, color="#C6A64B")
        expansion_label.next_to(servo_container, DOWN, buff=0.23)
        self.play(Write(expansion_label), run_time=0.4)
        self.play(servo_frame_tracker.animate.set_value(expansion_final_frame), run_time=8, rate_func=linear)
        radius_number.clear_updaters()

        # Servo phase: replace the radius readout with measured stress.
        self.next_slide()
        measured_stress_label = Tex("Measured stress $\\sigma$ =", font_size=30)
        measured_stress_label.next_to(servo_container, RIGHT, buff=0.45).shift(UP * 0.55)
        measured_stress_number = DecimalNumber(
            servo_frames[expansion_final_frame][0]["stress_kpa"],
            num_decimal_places=2,
            font_size=30,
            color="#C6A64B",
        )
        measured_stress_number.next_to(measured_stress_label, RIGHT, buff=0.12)
        stress_unit = Tex("kPa", font_size=30).next_to(measured_stress_number, RIGHT, buff=0.12)
        target_stress_label = Tex("Target stress $\\sigma^*$ = 5.00 kPa", font_size=30, color=YELLOW)
        target_stress_label.next_to(measured_stress_label, DOWN, aligned_edge=LEFT, buff=0.28)
        servo_active_label = Tex("Servo control active", font_size=30, color=RED)
        servo_active_label.next_to(servo_container, DOWN, buff=0.23)
        restored_friction_label = Tex(
            "Friction: $\\mu_s = \\mu_d = 0.60$",
            font_size=26,
            color=GREEN,
        )
        restored_friction_label.move_to(zero_friction_label)

        def update_stress_number(decimal_number):
            frame_value = servo_frame_tracker.get_value()
            lower_frame = min(int(frame_value), servo_final_frame)
            upper_frame = min(lower_frame + 1, servo_final_frame)
            decimal_number.set_value(
                interpolate(
                    servo_frames[lower_frame][0]["stress_kpa"],
                    servo_frames[upper_frame][0]["stress_kpa"],
                    frame_value - lower_frame,
                )
            )
            decimal_number.next_to(measured_stress_label, RIGHT, buff=0.12)
            stress_unit.next_to(decimal_number, RIGHT, buff=0.12)

        measured_stress_number.add_updater(update_stress_number)
        servo_container_final = servo_container_from_frame(servo_final_frame)
        self.add(measured_stress_number)
        self.play(
            FadeOut(radius_label),
            FadeOut(radius_number),
            FadeOut(expansion_label),
            Write(measured_stress_label),
            FadeIn(measured_stress_number),
            Write(stress_unit),
            Write(target_stress_label),
            Write(servo_active_label),
            ReplacementTransform(zero_friction_label, restored_friction_label),
            run_time=0.7,
        )
        self.play(
            Transform(servo_container, servo_container_final),
            servo_frame_tracker.animate.set_value(servo_final_frame),
            run_time=6,
            rate_func=smooth,
        )
        for particle in servo_particles:
            particle.clear_updaters()
        measured_stress_number.clear_updaters()
        self.wait(0.5)
        self.next_slide()

        # IRESR keeps the same packing result while adding more robust controls.
        iresr_label = Tex("IRESR", font_size=38, color="#C6A64B").move_to(servo_method_label)
        differences_title = Tex("Differences vs. the previous method", font_size=40, color="#C6A64B")
        differences_title.to_edge(LEFT, buff=0.45).shift(UP * 0.95)
        iresr_differences = VGroup(
            Tex(r"$\bullet$ Random particle shifting", font_size=40),
            Tex(r"$\bullet$ Rolling-friction control", font_size=40),
            Tex(r"$\bullet$ Force-balance criterion", font_size=40),
            Tex(r"$\bullet$ Repeated zero-friction settling", font_size=40),
        ).shift(DOWN)
        iresr_differences.arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        iresr_differences.next_to(differences_title, DOWN, aligned_edge=LEFT, buff=0.3)
        self.play(
            Transform(servo_method_label, iresr_label),
            servo_container.animate.shift(RIGHT * 3.35),
            servo_particles.animate.shift(RIGHT * 3.35),
            servo_active_label.animate.shift(RIGHT * 3.35),
            FadeOut(measured_stress_label, shift=RIGHT * 0.15),
            FadeOut(measured_stress_number, shift=RIGHT * 0.15),
            FadeOut(stress_unit, shift=RIGHT * 0.15),
            FadeOut(target_stress_label, shift=RIGHT * 0.15),
            FadeOut(restored_friction_label, shift=RIGHT * 0.15),
            FadeIn(differences_title, shift=RIGHT * 0.2),
            LaggedStart(*[FadeIn(item, shift=RIGHT * 0.15) for item in iresr_differences], lag_ratio=0.18),
            run_time=1.5,
        )
        self.wait(0.5)

        self.next_slide()

        boundary_axes = Axes(
            x_range=[0, 2.5, 1],
            y_range=[59, 67, 1],
            x_length=4.4,
            y_length=3.55,
            axis_config={"color": GREY_B, "stroke_width": 2},
            tips=False,
        )
        boundary_axes.to_edge(LEFT, buff=0.65).shift(DOWN * 0.32 + RIGHT * 0.35)
        x_tick_labels = VGroup(
            MathTex("10^0", font_size=23).next_to(boundary_axes.c2p(0, 59), DOWN, buff=0.13),
            MathTex("10^1", font_size=23).next_to(boundary_axes.c2p(1, 59), DOWN, buff=0.13),
            MathTex("10^2", font_size=23).next_to(boundary_axes.c2p(2, 59), DOWN, buff=0.13),
        )
        y_tick_labels = VGroup(
            *[
                MathTex(str(value), font_size=20).next_to(boundary_axes.c2p(0, value), LEFT, buff=0.13)
                for value in range(59, 68)
            ]
        )
        pressure_axis_label = Tex("$p$ [kPa]", font_size=25).next_to(boundary_axes, DOWN, buff=0.45)
        alpha_axis_label = Tex(r"$\alpha$ [\%]", font_size=25).rotate(PI / 2)
        alpha_axis_label.next_to(boundary_axes, LEFT, buff=0.85)

        def lower_boundary(value):
            return boundary_axes.c2p(value, 59.3 - 0.10 * value + 0.36 * value**2)

        def lower_boundary_scene(value):
            return lower_boundary(value)

        def upper_boundary(value):
            return boundary_axes.c2p(value, 64.9 - 0.10 * value + 0.36 * value**2)

        lower_curve = ParametricFunction(lower_boundary, t_range=[0, 2.38], color=YELLOW, stroke_width=5)
        upper_curve = ParametricFunction(upper_boundary, t_range=[0, 2.38], color=YELLOW, stroke_width=5)
        upper_label = Tex("Upper boundary", font_size=24, color=YELLOW).next_to(upper_curve.get_end(), RIGHT, buff=0.18)
        lower_label = Tex("Lower boundary", font_size=24, color=YELLOW).next_to(lower_curve.get_end(), RIGHT, buff=0.18)
        boundary_graph = VGroup(
            boundary_axes,
            x_tick_labels,
            y_tick_labels,
            pressure_axis_label,
            alpha_axis_label,
            upper_curve,
            lower_curve,
            upper_label,
            lower_label,
        ).shift(RIGHT * 0.25)
        self.play(
            FadeOut(differences_title, shift=LEFT * 0.15),
            FadeOut(iresr_differences, shift=LEFT * 0.15),
            FadeOut(servo_active_label, shift=DOWN * 0.1),
            FadeIn(boundary_graph, shift=LEFT * 0.2),
            run_time=1.1,
        )
        self.wait(0.5)

        self.next_slide()

        single_point_label = Tex("Single point", font_size=30, color="#C6A64B")
        single_point_label.next_to(servo_container, DOWN, buff=0.38)
        single_point_marker = Dot(
            boundary_axes.c2p(np.log10(5), 62.5),
            radius=0.095,
            color=BLUE,
        )
        self.play(
            FadeIn(single_point_label, shift=UP * 0.12),
            FadeIn(single_point_marker, scale=0.4),
            run_time=0.8,
        )
        self.wait(0.5)

        # A pressure sweep traces the lower-density boundary while the packing
        # undergoes the corresponding small isotropic compression.
        self.next_slide()

        sweep_start = np.log10(5)
        sweep_end = np.log10(200)
        sweep_tracker = ValueTracker(sweep_start)
        horizontal_sweep_label = Tex("Horizontal sweep", font_size=30, color="#C6A64B")
        horizontal_sweep_label.move_to(single_point_label)
        sweep_stress_label = Tex("Stress =", font_size=27)
        sweep_stress_number = DecimalNumber(5.0, num_decimal_places=1, font_size=27, color=BLUE)
        sweep_stress_unit = Tex("kPa", font_size=27)
        sweep_stress_group = VGroup(
            sweep_stress_label,
            sweep_stress_number,
            sweep_stress_unit,
        ).arrange(RIGHT, buff=0.12)
        sweep_stress_group.next_to(servo_container, UP, buff=0.27)

        self.play(
            Transform(single_point_label, horizontal_sweep_label),
            single_point_marker.animate.move_to(lower_boundary_scene(sweep_start)),
            FadeIn(sweep_stress_label),
            FadeIn(sweep_stress_number),
            FadeIn(sweep_stress_unit),
            run_time=0.8,
        )

        lower_boundary_trace = always_redraw(
            lambda: ParametricFunction(
                lower_boundary_scene,
                t_range=[sweep_start, max(sweep_start + 1e-3, sweep_tracker.get_value())],
                color=RED,
                stroke_width=5,
            )
        )

        def update_sweep_marker(marker):
            marker.move_to(lower_boundary_scene(sweep_tracker.get_value()))

        def update_sweep_stress(number):
            number.set_value(10 ** sweep_tracker.get_value())
            number.next_to(sweep_stress_label, RIGHT, buff=0.12)
            sweep_stress_unit.next_to(number, RIGHT, buff=0.12)

        single_point_marker.add_updater(update_sweep_marker)
        sweep_stress_number.add_updater(update_sweep_stress)
        self.add(lower_boundary_trace)
        self.bring_to_front(single_point_marker)
        compression_ratio = 0.982
        packing_center = servo_container.get_center()
        compressed_container = servo_container.copy().scale(compression_ratio, about_point=packing_center)
        compressed_particles = VGroup(
            *[
                particle.copy().move_to(
                    packing_center + compression_ratio * (particle.get_center() - packing_center)
                )
                for particle in servo_particles
            ]
        )
        self.play(
            sweep_tracker.animate.set_value(sweep_end),
            Transform(servo_container, compressed_container),
            Transform(servo_particles, compressed_particles),
            run_time=10,
            rate_func=linear,
        )
        single_point_marker.clear_updaters()
        sweep_stress_number.clear_updaters()
        self.play(lower_label.animate.set_color(RED), run_time=0.35)
        self.wait(0.5)

        # A second sweep starts from an interior density, illustrating that the
        # accessible region can be explored from any initial density.
        self.next_slide()

        middle_sweep_start = np.log10(5)
        middle_sweep_end = np.log10(200)
        middle_sweep_tracker = ValueTracker(middle_sweep_start)

        def middle_boundary(value):
            return boundary_axes.c2p(value, 62.1 - 0.10 * value + 0.36 * value**2)

        any_density_label = Tex("Any initial density", font_size=30, color="#C6A64B")
        any_density_label.move_to(single_point_label)
        sweep_stress_number.set_value(5.0)
        sweep_stress_number.next_to(sweep_stress_label, RIGHT, buff=0.12)
        sweep_stress_unit.next_to(sweep_stress_number, RIGHT, buff=0.12)
        self.play(
            Transform(single_point_label, any_density_label),
            single_point_marker.animate.move_to(middle_boundary(middle_sweep_start)),
            run_time=0.8,
        )

        middle_sweep_trace = always_redraw(
            lambda: ParametricFunction(
                middle_boundary,
                t_range=[middle_sweep_start, max(middle_sweep_start + 1e-3, middle_sweep_tracker.get_value())],
                color=BLUE,
                stroke_width=5,
            )
        )

        def update_middle_sweep_marker(marker):
            marker.move_to(middle_boundary(middle_sweep_tracker.get_value()))

        def update_middle_sweep_stress(number):
            number.set_value(10 ** middle_sweep_tracker.get_value())
            number.next_to(sweep_stress_label, RIGHT, buff=0.12)
            sweep_stress_unit.next_to(number, RIGHT, buff=0.12)

        single_point_marker.add_updater(update_middle_sweep_marker)
        sweep_stress_number.add_updater(update_middle_sweep_stress)
        self.add(middle_sweep_trace)
        self.bring_to_front(single_point_marker)
        middle_compression_ratio = 0.991
        middle_packing_center = servo_container.get_center()
        middle_compressed_container = servo_container.copy().scale(
            middle_compression_ratio,
            about_point=middle_packing_center,
        )
        middle_compressed_particles = VGroup(
            *[
                particle.copy().move_to(
                    middle_packing_center
                    + middle_compression_ratio * (particle.get_center() - middle_packing_center)
                )
                for particle in servo_particles
            ]
        )
        self.play(
            middle_sweep_tracker.animate.set_value(middle_sweep_end),
            Transform(servo_container, middle_compressed_container),
            Transform(servo_particles, middle_compressed_particles),
            run_time=8,
            rate_func=linear,
        )
        single_point_marker.clear_updaters()
        sweep_stress_number.clear_updaters()

        # Sweep back from high to low pressure along the upper boundary.
        self.next_slide()

        descending_sweep_start = np.log10(200)
        descending_sweep_end = np.log10(5)
        descending_sweep_tracker = ValueTracker(descending_sweep_start)
        descending_sweep_label = Tex("Descending sweep", font_size=30, color="#C6A64B")
        descending_sweep_label.move_to(single_point_label)
        self.play(
            FadeOut(lower_boundary_trace),
            FadeOut(middle_sweep_trace),
            lower_label.animate.set_color(YELLOW),
            Transform(single_point_label, descending_sweep_label),
            single_point_marker.animate.move_to(upper_boundary(descending_sweep_start)),
            run_time=0.9,
        )
        self.remove(lower_boundary_trace, middle_sweep_trace)

        descending_sweep_trace = always_redraw(
            lambda: ParametricFunction(
                upper_boundary,
                t_range=[
                    min(descending_sweep_start - 1e-3, descending_sweep_tracker.get_value()),
                    descending_sweep_start,
                ],
                color=RED,
                stroke_width=5,
            )
        )

        def update_descending_sweep_marker(marker):
            marker.move_to(upper_boundary(descending_sweep_tracker.get_value()))

        def update_descending_sweep_stress(number):
            number.set_value(10 ** descending_sweep_tracker.get_value())
            number.next_to(sweep_stress_label, RIGHT, buff=0.12)
            sweep_stress_unit.next_to(number, RIGHT, buff=0.12)

        single_point_marker.add_updater(update_descending_sweep_marker)
        sweep_stress_number.add_updater(update_descending_sweep_stress)
        self.add(descending_sweep_trace)
        self.bring_to_front(single_point_marker)
        descending_expansion_ratio = 1.009
        descending_packing_center = servo_container.get_center()
        descending_container = servo_container.copy().scale(
            descending_expansion_ratio,
            about_point=descending_packing_center,
        )
        descending_particles = VGroup(
            *[
                particle.copy().move_to(
                    descending_packing_center
                    + descending_expansion_ratio * (particle.get_center() - descending_packing_center)
                )
                for particle in servo_particles
            ]
        )
        self.play(
            descending_sweep_tracker.animate.set_value(descending_sweep_end),
            Transform(servo_container, descending_container),
            Transform(servo_particles, descending_particles),
            run_time=8,
            rate_func=linear,
        )
        single_point_marker.clear_updaters()
        sweep_stress_number.clear_updaters()
        self.wait(0.5)

        # At fixed pressure, a density sweep moves between the two accessible
        # boundaries rather than following either one.
        self.next_slide()

        density_sweep_pressure = np.log10(20)
        density_sweep_lower = 59.3 - 0.10 * density_sweep_pressure + 0.36 * density_sweep_pressure**2
        density_sweep_upper = 64.9 - 0.10 * density_sweep_pressure + 0.36 * density_sweep_pressure**2
        density_sweep_tracker = ValueTracker(density_sweep_lower)
        density_sweep_label = Tex("Density sweep", font_size=30, color="#C6A64B")
        density_sweep_label.move_to(single_point_label)
        sweep_stress_number.set_value(20.0)
        sweep_stress_number.next_to(sweep_stress_label, RIGHT, buff=0.12)
        sweep_stress_unit.next_to(sweep_stress_number, RIGHT, buff=0.12)
        self.play(
            FadeOut(descending_sweep_trace),
            Transform(single_point_label, density_sweep_label),
            single_point_marker.animate.move_to(
                boundary_axes.c2p(density_sweep_pressure, density_sweep_lower)
            ),
            run_time=0.9,
        )
        self.remove(descending_sweep_trace)

        density_sweep_trace = always_redraw(
            lambda: Line(
                boundary_axes.c2p(density_sweep_pressure, density_sweep_lower),
                boundary_axes.c2p(density_sweep_pressure, density_sweep_tracker.get_value()),
                color=PINK,
                stroke_width=5,
            )
        )

        def update_density_sweep_marker(marker):
            marker.move_to(
                boundary_axes.c2p(density_sweep_pressure, density_sweep_tracker.get_value())
            )

        single_point_marker.add_updater(update_density_sweep_marker)
        self.add(density_sweep_trace)
        self.bring_to_front(single_point_marker)
        density_compression_ratio = 0.985
        density_packing_center = servo_container.get_center()
        density_compressed_container = servo_container.copy().scale(
            density_compression_ratio,
            about_point=density_packing_center,
        )
        density_compressed_particles = VGroup(
            *[
                particle.copy().move_to(
                    density_packing_center
                    + density_compression_ratio * (particle.get_center() - density_packing_center)
                )
                for particle in servo_particles
            ]
        )
        self.play(
            density_sweep_tracker.animate.set_value(density_sweep_upper),
            Transform(servo_container, density_compressed_container),
            Transform(servo_particles, density_compressed_particles),
            run_time=6,
            rate_func=linear,
        )
        single_point_marker.clear_updaters()
        self.wait(0.5)

        # Zigzag point: alternating fractional stress and density corrections
        # converge to one requested packing state.
        self.next_slide()

        zigzag_initial = boundary_axes.c2p(np.log10(20), 60.4)
        zigzag_target = boundary_axes.c2p(np.log10(100), 64.0)
        zigzag_label = Tex("Zigzag point", font_size=30, color="#C6A64B")
        zigzag_label.move_to(single_point_label)
        target_marker = Dot(zigzag_target, radius=0.09, color=GREEN)
        target_label = Tex("Target", font_size=22, color=GREEN).next_to(target_marker, UP, buff=0.14)
        self.play(
            FadeOut(density_sweep_trace),
            Transform(single_point_label, zigzag_label),
            single_point_marker.animate.move_to(zigzag_initial),
            FadeIn(target_marker, scale=0.5),
            FadeIn(target_label, shift=UP * 0.08),
            run_time=0.9,
        )
        self.remove(density_sweep_trace)

        zigzag_stress_tracker = ValueTracker(20.0)

        def update_zigzag_stress(number):
            number.set_value(zigzag_stress_tracker.get_value())
            number.next_to(sweep_stress_label, RIGHT, buff=0.12)
            sweep_stress_unit.next_to(number, RIGHT, buff=0.12)

        def zigzag_stress_leg(start, end):
            return Line(start, end, color=RED, stroke_width=4)

        zigzag_points = [
            zigzag_initial,
            boundary_axes.c2p(np.log10(45), 60.4),
            boundary_axes.c2p(np.log10(45), 62.25),
            boundary_axes.c2p(np.log10(67), 62.25),
            boundary_axes.c2p(np.log10(67), 63.2),
            boundary_axes.c2p(np.log10(82), 63.2),
            boundary_axes.c2p(np.log10(82), 64.0),
            zigzag_target,
        ]
        zigzag_paths = [
            zigzag_stress_leg(zigzag_points[0], zigzag_points[1]),
            Line(zigzag_points[1], zigzag_points[2], color=RED, stroke_width=4),
            zigzag_stress_leg(zigzag_points[2], zigzag_points[3]),
            Line(zigzag_points[3], zigzag_points[4], color=RED, stroke_width=4),
            zigzag_stress_leg(zigzag_points[4], zigzag_points[5]),
            Line(zigzag_points[5], zigzag_points[6], color=RED, stroke_width=4),
            zigzag_stress_leg(zigzag_points[6], zigzag_points[7]),
        ]
        zigzag_stress_targets = (45.0, 45.0, 67.0, 67.0, 82.0, 82.0, 100.0)
        zigzag_trace = TracedPath(
            single_point_marker.get_center,
            stroke_color=RED,
            stroke_width=4,
        )
        sweep_stress_number.add_updater(update_zigzag_stress)
        self.add(zigzag_trace)
        self.bring_to_front(single_point_marker)

        def compacted_zigzag_packing(ratio):
            packing_center = servo_container.get_center()
            container_target = servo_container.copy().scale(ratio, about_point=packing_center)
            particles_target = VGroup(
                *[
                    particle.copy().move_to(
                        packing_center + ratio * (particle.get_center() - packing_center)
                    )
                    for particle in servo_particles
                ]
            )
            return container_target, particles_target

        for path, stress_target, compression_ratio in zip(
            zigzag_paths,
            zigzag_stress_targets,
            (0.997, 0.995, 0.997, 0.995, 0.997, 0.995, 0.997),
        ):
            zigzag_container_target, zigzag_particles_target = compacted_zigzag_packing(
                compression_ratio
            )
            self.play(
                MoveAlongPath(single_point_marker, path),
                zigzag_stress_tracker.animate.set_value(stress_target),
                Transform(servo_container, zigzag_container_target),
                Transform(servo_particles, zigzag_particles_target),
                run_time=1.25,
                rate_func=smooth,
            )
        sweep_stress_number.clear_updaters()
        self.play(Indicate(target_marker, color=GREEN), run_time=0.5)
        self.wait(0.5)

        # Cyclic stress repeatedly compresses and decompresses the packing
        # between two stable stress targets.
        self.next_slide()

        cyclic_minimum_stress = 20.0
        cyclic_maximum_stress = 100.0
        cyclic_start = boundary_axes.c2p(np.log10(cyclic_minimum_stress), 62.0)
        cyclic_label = Tex("Cyclic stress", font_size=30, color="#C6A64B")
        cyclic_label.move_to(single_point_label)
        sweep_stress_number.set_value(cyclic_minimum_stress)
        sweep_stress_number.next_to(sweep_stress_label, RIGHT, buff=0.12)
        sweep_stress_unit.next_to(sweep_stress_number, RIGHT, buff=0.12)
        self.play(
            FadeOut(zigzag_trace),
            FadeOut(target_marker),
            FadeOut(target_label),
            Transform(single_point_label, cyclic_label),
            single_point_marker.animate.move_to(cyclic_start),
            run_time=0.9,
        )
        self.remove(zigzag_trace)

        cyclic_stress_tracker = ValueTracker(cyclic_minimum_stress)

        def update_cyclic_stress(number):
            number.set_value(cyclic_stress_tracker.get_value())
            number.next_to(sweep_stress_label, RIGHT, buff=0.12)
            sweep_stress_unit.next_to(number, RIGHT, buff=0.12)

        def cyclic_path(start, end, color, vertical_offset):
            return ParametricFunction(
                lambda t: interpolate(start, end, t) + UP * vertical_offset * np.sin(PI * t),
                t_range=[0, 1],
                color=color,
                stroke_width=4,
            )

        cyclic_peak = boundary_axes.c2p(np.log10(cyclic_maximum_stress), 64.4)
        compression_path = cyclic_path(cyclic_start, cyclic_peak, RED, 0.16)
        decompression_path = cyclic_path(cyclic_peak, cyclic_start, BLUE, -0.16)
        cyclic_paths = (
            compression_path,
            decompression_path,
            compression_path,
            decompression_path,
            compression_path,
            decompression_path,
        )
        cyclic_stress_targets = (
            cyclic_maximum_stress,
            cyclic_minimum_stress,
            cyclic_maximum_stress,
            cyclic_minimum_stress,
            cyclic_maximum_stress,
            cyclic_minimum_stress,
        )
        cyclic_compression_ratios = (0.993, 1.006, 0.993, 1.006, 0.993, 1.006)
        sweep_stress_number.add_updater(update_cyclic_stress)

        def transformed_cyclic_packing(ratio):
            packing_center = servo_container.get_center()
            container_target = servo_container.copy().scale(ratio, about_point=packing_center)
            particles_target = VGroup(
                *[
                    particle.copy().move_to(
                        packing_center + ratio * (particle.get_center() - packing_center)
                    )
                    for particle in servo_particles
                ]
            )
            return container_target, particles_target

        for path, stress_target, packing_ratio in zip(
            cyclic_paths,
            cyclic_stress_targets,
            cyclic_compression_ratios,
        ):
            segment_trace = TracedPath(
                single_point_marker.get_center,
                stroke_color=path.get_color(),
                stroke_width=4,
            )
            self.add(segment_trace)
            cyclic_container_target, cyclic_particles_target = transformed_cyclic_packing(
                packing_ratio
            )
            self.play(
                MoveAlongPath(single_point_marker, path),
                cyclic_stress_tracker.animate.set_value(stress_target),
                Transform(servo_container, cyclic_container_target),
                Transform(servo_particles, cyclic_particles_target),
                run_time=1.35,
                rate_func=smooth,
            )
            self.remove(segment_trace)
            completed_segment = segment_trace.copy()
            completed_segment.clear_updaters()
            self.add(completed_segment)
            self.bring_to_front(single_point_marker)
        sweep_stress_number.clear_updaters()
        self.wait(0.5)
        
