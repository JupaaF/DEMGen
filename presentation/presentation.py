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

        self.play(Create(table), run_time = 2)
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
        
