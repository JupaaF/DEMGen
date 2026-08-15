"""
DEMGen Conference Presentation in Manim Slides
==============================================
Based on sketches from Presentacion.pdf

Visual Style:
- Background: Black (#000000)
- Primary Text: Crisp White (#FFFFFF)
- Secondary / Subtitle Text: Slate Silver (#94A3B8)
- Highlight Accent: Academic Gold (#FBBF24 / #F59E0B)
- Annotations: Academic Coral / Crimson (#F87171)
- Typography: Latin Modern Sans / AMS-LaTeX (Professional Academic Standard)
"""

import numpy as np
from manim import *
from manim_slides import Slide

# ==========================================
# Color Palette Tokens
# ==========================================
BG_COLOR = BLACK             # Black background
TEXT_WHITE = "#FFFFFF"       # Crisp primary text
TEXT_MUTED = "#94A3B8"       # Secondary text (Slate 400)
ACCENT_GOLD = "#FBBF24"      # Academic gold accent (Amber 400)
ACCENT_CORAL = "#F87171"     # Annotation coral/red (Red 400)
PARTICLE_FILL = "#F59E0B"    # Particle core color (Amber 500)
PARTICLE_STROKE = "#D97706"  # Particle border (Amber 600)
PARTICLE_GLINT = "#FEF9C3"   # Specular reflection (Yellow 100)
BOX_LINE_PRI = "#CBD5E1"     # Box primary wireframe (Slate 300)
BOX_LINE_SEC = "#475569"     # Box secondary/back wireframe (Slate 600)

# ==========================================
# LaTeX Academic Typography Template
# ==========================================
ACADEMIC_TEX_TEMPLATE = TexTemplate()
ACADEMIC_TEX_TEMPLATE.add_to_preamble(r"""
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{lmodern}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{xcolor}
\renewcommand*\familydefault{\sfdefault}
\definecolor{gold}{HTML}{FBBF24}
\definecolor{amber}{HTML}{F59E0B}
\definecolor{coral}{HTML}{F87171}
\definecolor{muted}{HTML}{94A3B8}
""")


def get_academic_tex(tex_string, font_size=36, color=WHITE, **kwargs):
    """Helper to generate consistent academic Tex mobjects."""
    return Tex(
        tex_string,
        tex_template=ACADEMIC_TEX_TEMPLATE,
        font_size=font_size,
        color=color,
        **kwargs
    )


def get_academic_mathtex(tex_string, font_size=36, color=WHITE, **kwargs):
    """Helper to generate consistent academic MathTex mobjects."""
    return MathTex(
        tex_string,
        tex_template=ACADEMIC_TEX_TEMPLATE,
        font_size=font_size,
        color=color,
        **kwargs
    )


def create_packed_dem_box(center, seed=42, angle_deg=28, n_particles=90, box_size=1.9, box_height=2.1):
    """
    Creates an isometric 3D DEM granular packing container with spherical particles.
    """
    np.random.seed(seed)
    box_group = VGroup()
    
    rad = np.radians(angle_deg)
    cos_a, sin_a = np.cos(rad), np.sin(rad)
    u_x = np.array([cos_a, -sin_a, 0])
    u_y = np.array([-cos_a, -sin_a, 0])
    u_z = np.array([0, 1, 0])
    
    L = box_size
    H = box_height
    
    v_bot = center + DOWN * 0.85
    v_bl = v_bot + L * u_y
    v_br = v_bot + L * u_x
    v_bb = v_bot + L * u_x + L * u_y
    
    v_top = v_bot + H * u_z
    v_tl = v_bl + H * u_z
    v_tr = v_br + H * u_z
    v_tb = v_bb + H * u_z
    
    # Subtle floor shading
    floor = Polygon(
        v_bot, v_br, v_bb, v_bl,
        fill_opacity=0.06,
        fill_color=WHITE,
        stroke_opacity=0
    )
    
    # Back wireframe (hidden/dashed)
    back_lines = VGroup(
        DashedLine(v_bl, v_bb, color=BOX_LINE_SEC, stroke_width=1.5, dash_length=0.08),
        DashedLine(v_br, v_bb, color=BOX_LINE_SEC, stroke_width=1.5, dash_length=0.08),
        DashedLine(v_bb, v_tb, color=BOX_LINE_SEC, stroke_width=1.5, dash_length=0.08),
    )
    
    # Front wireframe (visible pillars and base edges)
    front_lines = VGroup(
        Line(v_bot, v_bl, color=BOX_LINE_PRI, stroke_width=2.5),
        Line(v_bot, v_br, color=BOX_LINE_PRI, stroke_width=2.5),
        Line(v_bot, v_top, color=TEXT_WHITE, stroke_width=2.5),
        Line(v_bl, v_tl, color=BOX_LINE_PRI, stroke_width=2.5),
        Line(v_br, v_tr, color=BOX_LINE_PRI, stroke_width=2.5),
    )
    
    # Particles inside container
    particles = VGroup()
    raw_particles = []
    
    for _ in range(n_particles):
        px = np.random.uniform(0.08, 0.92)
        py = np.random.uniform(0.08, 0.92)
        pz = np.random.uniform(0.06, 0.94)
        pos = v_bot + px * L * u_x + py * L * u_y + pz * H * u_z
        depth = -(px + py) + pz * 0.1
        r = np.random.uniform(0.085, 0.125)
        raw_particles.append((depth, pos, r))
    
    # Sort back-to-front for proper 3D rendering
    raw_particles.sort(key=lambda item: item[0])
    
    for _, pos, r in raw_particles:
        p_circle = Circle(
            radius=r,
            color=PARTICLE_STROKE,
            fill_color=PARTICLE_FILL,
            fill_opacity=0.92,
            stroke_width=1.2
        ).move_to(pos)
        
        glint = Circle(
            radius=r * 0.28,
            color=PARTICLE_GLINT,
            fill_color=PARTICLE_GLINT,
            fill_opacity=0.85,
            stroke_width=0
        ).move_to(pos + np.array([-r * 0.35, r * 0.35, 0]))
        
        particles.add(VGroup(p_circle, glint))
    
    box_group.add(floor, back_lines, particles, front_lines)
    return box_group, v_bot, v_top, center


class Presentation(Slide):
    """
    Complete DEMGen Conference Presentation with Manim Slides.
    Includes all 7 slides from Presentacion.pdf:
    - Slide 1: Title Slide
    - Slides 2-6: Outline progressive reveal (5 items)
    - Slide 7: Section 1 - What is DemGen: the problem (Isometric DEM Packings)
    """

    def construct(self):
        self.camera.background_color = BLACK
        
        # ==========================================
        # SLIDE 1: Title Slide
        # ==========================================
        self.play_title_slide()
        self.next_slide()
        
        # ==========================================
        # SLIDES 2-6: Outline (Progressive Reveal)
        # ==========================================
        self.play_outline_slides()
        
        # ==========================================
        # SLIDE 7: Section 1 - The Problem
        # ==========================================
        self.play_problem_slide()
        self.next_slide()

    def play_title_slide(self):
        """Slide 1: Mobility to Utrecht - How does DemGen work?"""
        # Header / Context
        header = get_academic_tex(
            r"\textbf{Mobility to Utrecht:}",
            font_size=44,
            color=TEXT_WHITE
        ).move_to(UP * 1.6 + LEFT * 0.5)
        
        # Main Question Title
        title = get_academic_tex(
            r"\textbf{How does }{\color{gold}\textbf{DemGen}}\textbf{ work?}",
            font_size=52,
            color=TEXT_WHITE
        ).next_to(header, DOWN, buff=0.45, aligned_edge=LEFT)
        
        # Elegant subtle divider line
        divider = Line(
            start=LEFT * 5.8,
            end=RIGHT * 5.8,
            color="#334155",
            stroke_width=1.5
        ).move_to(DOWN * 0.8)
        
        # Author & Date details
        author = get_academic_tex(
            r"\textbf{Fernandez, Juan Pablo}",
            font_size=32,
            color=TEXT_WHITE
        ).move_to(LEFT * 3.8 + DOWN * 1.8)
        
        dates = get_academic_tex(
            r"01/08/26 -- 31/08/26",
            font_size=28,
            color=TEXT_MUTED
        ).next_to(author, DOWN, buff=0.25, aligned_edge=LEFT)
        
        # Conference badge / metadata tag
        conf_tag = get_academic_tex(
            r"{\color{gold}\textbf{DEMGen}} $\cdot$ Particle Packing Generator for DEM",
            font_size=24,
            color=TEXT_MUTED
        ).move_to(RIGHT * 2.8 + DOWN * 2.0)
        
        # Animations
        self.play(
            FadeIn(header, shift=UP * 0.3),
            run_time=0.8
        )
        self.play(
            Write(title),
            run_time=1.2
        )
        self.play(
            Create(divider),
            FadeIn(author, shift=RIGHT * 0.3),
            FadeIn(dates, shift=RIGHT * 0.3),
            FadeIn(conf_tag, shift=LEFT * 0.3),
            run_time=1.0
        )
        self.wait(0.5)

    def play_outline_slides(self):
        """Slides 2-6: Outline with progressive reveal of items 1 to 5."""
        self.clear()
        
        # Outline Header
        outline_title = get_academic_tex(
            r"\textbf{Outline:}",
            font_size=46,
            color=TEXT_WHITE
        ).move_to(UP * 2.7 + LEFT * 4.2)
        
        # Gold double underline matching sketch
        underline_1 = Line(
            start=outline_title.get_left() + DOWN * 0.1,
            end=outline_title.get_right() + DOWN * 0.1,
            color=ACCENT_GOLD,
            stroke_width=3.0
        )
        underline_2 = Line(
            start=outline_title.get_left() + DOWN * 0.18,
            end=outline_title.get_right() + DOWN * 0.18,
            color=ACCENT_GOLD,
            stroke_width=1.5
        )
        
        self.play(
            FadeIn(outline_title, shift=DOWN * 0.2),
            Create(underline_1),
            Create(underline_2),
            run_time=0.8
        )
        
        # Define the 5 Outline items exactly matching sketch
        items_tex = [
            r"{\color{gold}\textbf{\textcircled{\small 1}}}\quad \textbf{What is }{\color{gold}\textbf{DemGen}}\textbf{?}",
            r"{\color{gold}\textbf{\textcircled{\small 2}}}\quad \textbf{What }{\color{gold}\textbf{methods}}\textbf{ does }{\color{gold}\textbf{DemGen}}\textbf{ use?}",
            r"{\color{gold}\textbf{\textcircled{\small 3}}}\quad \textbf{Deep dive: }{\color{gold}\textbf{IRESC}}",
            r"{\color{gold}\textbf{\textcircled{\small 4}}}\quad \textbf{New method: }{\color{gold}\textbf{tapping}}",
            r"{\color{gold}\textbf{\textcircled{\small 5}}}\quad \textbf{Conclusions and future }{\color{gold}\textbf{improvements}}"
        ]
        
        item_mobjects = []
        start_y = 1.3
        spacing = 0.88
        
        for i, it_tex in enumerate(items_tex):
            mob = get_academic_tex(
                it_tex,
                font_size=36,
                color=TEXT_WHITE
            ).move_to(LEFT * 1.5 + UP * (start_y - i * spacing))
            mob.align_to(LEFT * 5.0, LEFT)
            item_mobjects.append(mob)
        
        # Item 1 (Page 2 in PDF)
        self.play(
            FadeIn(item_mobjects[0], shift=RIGHT * 0.4),
            run_time=0.8
        )
        self.wait(0.4)
        self.next_slide()
        
        # Item 2 (Page 3 in PDF)
        self.play(
            FadeIn(item_mobjects[1], shift=RIGHT * 0.4),
            run_time=0.8
        )
        self.wait(0.4)
        self.next_slide()
        
        # Item 3 (Page 4 in PDF)
        self.play(
            FadeIn(item_mobjects[2], shift=RIGHT * 0.4),
            run_time=0.8
        )
        self.wait(0.4)
        self.next_slide()
        
        # Item 4 (Page 5 in PDF)
        self.play(
            FadeIn(item_mobjects[3], shift=RIGHT * 0.4),
            run_time=0.8
        )
        self.wait(0.4)
        self.next_slide()
        
        # Item 5 (Page 6 in PDF)
        self.play(
            FadeIn(item_mobjects[4], shift=RIGHT * 0.4),
            run_time=0.8
        )
        self.wait(0.5)
        self.next_slide()

    def play_problem_slide(self):
        """Slide 7: Section 1 - What is DemGen: the problem"""
        self.clear()
        
        # Section 1 Title
        title = get_academic_tex(
            r"{\color{gold}\textbf{\textcircled{\small 1}}}\quad \textbf{What is }{\color{gold}\textbf{DemGen}}\textbf{: the problem}",
            font_size=40,
            color=TEXT_WHITE
        ).to_edge(UP, buff=0.45)
        
        self.play(
            FadeIn(title, shift=DOWN * 0.2),
            run_time=0.7
        )
        
        # Containers: Left Packing & Right Packing
        box_left, bot_l, top_l, c_l = create_packed_dem_box(LEFT * 3.3 + DOWN * 0.1, seed=42)
        box_right, bot_r, top_r, c_r = create_packed_dem_box(RIGHT * 3.3 + DOWN * 0.1, seed=137)
        
        self.play(
            FadeIn(box_left, shift=UP * 0.3),
            FadeIn(box_right, shift=UP * 0.3),
            run_time=1.0
        )
        
        # Left Box Annotations (Coral / Red)
        lbl_mcn_l = get_academic_mathtex(r"\mathrm{MCN} = 5", font_size=32, color=ACCENT_CORAL).move_to(LEFT * 5.75 + UP * 1.8)
        arr_mcn_l = CurvedArrow(lbl_mcn_l.get_right() + RIGHT * 0.1, c_l + LEFT * 0.4 + UP * 1.0, color=ACCENT_CORAL, radius=-2.5, tip_length=0.18)
        
        lbl_alpha_l = get_academic_mathtex(r"\alpha = 0.62", font_size=32, color=ACCENT_CORAL).move_to(LEFT * 5.75 + UP * 0.55)
        arr_alpha_l = CurvedArrow(lbl_alpha_l.get_right() + RIGHT * 0.1, c_l + LEFT * 1.0 + UP * 0.1, color=ACCENT_CORAL, radius=-3.5, tip_length=0.18)
        
        lbl_sigma_l = get_academic_mathtex(r"\sigma = 60\,\mathrm{kPa}", font_size=32, color=ACCENT_CORAL).move_to(LEFT * 5.75 + DOWN * 0.65)
        arr_sigma_l = CurvedArrow(lbl_sigma_l.get_right() + RIGHT * 0.1, c_l + LEFT * 0.75 + DOWN * 0.65, color=ACCENT_CORAL, radius=-3.0, tip_length=0.18)
        
        lbl_k_l = get_academic_mathtex(r"k = \,?\,\frac{\mathrm{W}}{\mathrm{m}\cdot\mathrm{K}}", font_size=34, color=ACCENT_CORAL).move_to(LEFT * 5.75 + DOWN * 1.95)
        arr_k_l = CurvedArrow(lbl_k_l.get_right() + RIGHT * 0.1, c_l + LEFT * 0.35 + DOWN * 1.45, color=ACCENT_CORAL, radius=-2.8, tip_length=0.18)
        
        # Right Box Annotations (Coral / Red)
        lbl_mcn_r = get_academic_mathtex(r"\mathrm{MCN} = 5", font_size=32, color=ACCENT_CORAL).move_to(RIGHT * 5.75 + UP * 1.8)
        arr_mcn_r = CurvedArrow(lbl_mcn_r.get_left() + LEFT * 0.1, c_r + RIGHT * 0.4 + UP * 1.0, color=ACCENT_CORAL, radius=2.5, tip_length=0.18)
        
        lbl_alpha_r = get_academic_mathtex(r"\alpha = 0.62", font_size=32, color=ACCENT_CORAL).move_to(RIGHT * 5.75 + UP * 0.55)
        arr_alpha_r = CurvedArrow(lbl_alpha_r.get_left() + LEFT * 0.1, c_r + RIGHT * 1.0 + UP * 0.1, color=ACCENT_CORAL, radius=3.5, tip_length=0.18)
        
        lbl_sigma_r = get_academic_mathtex(r"\sigma = 50\,\mathrm{kPa}", font_size=32, color=ACCENT_CORAL).move_to(RIGHT * 5.75 + DOWN * 0.65)
        arr_sigma_r = CurvedArrow(lbl_sigma_r.get_left() + LEFT * 0.1, c_r + RIGHT * 0.75 + DOWN * 0.65, color=ACCENT_CORAL, radius=3.0, tip_length=0.18)
        
        lbl_k_r = get_academic_mathtex(r"k = \,?\,\frac{\mathrm{W}}{\mathrm{m}\cdot\mathrm{K}}", font_size=34, color=ACCENT_CORAL).move_to(RIGHT * 5.75 + DOWN * 1.95)
        arr_k_r = CurvedArrow(lbl_k_r.get_left() + LEFT * 0.1, c_r + RIGHT * 0.35 + DOWN * 1.45, color=ACCENT_CORAL, radius=2.8, tip_length=0.18)
        
        self.play(
            LaggedStart(
                AnimationGroup(FadeIn(lbl_mcn_l), Create(arr_mcn_l)),
                AnimationGroup(FadeIn(lbl_alpha_l), Create(arr_alpha_l)),
                AnimationGroup(FadeIn(lbl_sigma_l), Create(arr_sigma_l)),
                AnimationGroup(FadeIn(lbl_k_l), Create(arr_k_l)),
                AnimationGroup(FadeIn(lbl_mcn_r), Create(arr_mcn_r)),
                AnimationGroup(FadeIn(lbl_alpha_r), Create(arr_alpha_r)),
                AnimationGroup(FadeIn(lbl_sigma_r), Create(arr_sigma_r)),
                AnimationGroup(FadeIn(lbl_k_r), Create(arr_k_r)),
                lag_ratio=0.12
            ),
            run_time=1.6
        )
        
        # Bottom Takeaway Statement
        statement = get_academic_tex(
            r"\textbf{Two }{\color{gold}\textbf{packings}}\textbf{ with similar}\\[0.22em]"
            r"{\color{gold}\textbf{microstructure}}\textbf{ variables can}\\[0.22em]"
            r"\textbf{behave }{\color{gold}\textbf{differently}}",
            font_size=32,
            color=TEXT_WHITE
        ).move_to(DOWN * 2.85)
        
        # Subtle framing background card behind the takeaway
        statement_card = RoundedRectangle(
            corner_radius=0.15,
            width=statement.width + 0.6,
            height=statement.height + 0.35,
            fill_color="#0F172A",
            fill_opacity=0.85,
            stroke_color="#334155",
            stroke_width=1.0
        ).move_to(statement.get_center())
        
        self.play(
            FadeIn(statement_card, shift=UP * 0.2),
            Write(statement),
            run_time=1.2
        )
        self.wait(0.8)


# ===================================================
# Modular Standalone Scenes (for rehearsal or testing)
# ===================================================
class TitleSlideScene(Slide):
    """Standalone Slide 1 Scene."""
    def construct(self):
        self.camera.background_color = BLACK
        Presentation.play_title_slide(self)
        self.next_slide()


class OutlineSlideScene(Slide):
    """Standalone Outline Scene (Slides 2 to 6)."""
    def construct(self):
        self.camera.background_color = BLACK
        Presentation.play_outline_slides(self)


class ProblemSlideScene(Slide):
    """Standalone Problem Scene (Slide 7)."""
    def construct(self):
        self.camera.background_color = BLACK
        Presentation.play_problem_slide(self)
        self.next_slide()
