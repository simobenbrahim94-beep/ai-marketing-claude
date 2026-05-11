#!/usr/bin/env python3
"""
Routines.fr — Video Campaign Generator
Generates 5 branded promotional videos as MP4 files.

Output: campaigns/routines-video-campaign/videos/
Usage:  python3 scripts/generate_videos.py
"""

import os
import textwrap
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import ImageClip, concatenate_videoclips, AudioFileClip, CompositeVideoClip

# ── Brand constants ────────────────────────────────────────────────────────────
W, H = 1920, 1080          # 16:9 Full HD
FPS  = 24

# Brand palette
CREAM     = (248, 246, 242)
DARK      = (26,  26,  26)
GOLD      = (212, 175, 122)
SLATE     = (90,  122, 138)
WHITE     = (255, 255, 255)
BLACK     = (0,   0,   0)
DIM_DARK  = (18,  18,  18)

# Fonts
FONT_DIR  = "/usr/share/fonts/truetype"
F_SERIF_B = f"{FONT_DIR}/dejavu/DejaVuSerif-Bold.ttf"
F_SANS    = f"{FONT_DIR}/liberation/LiberationSans-Regular.ttf"
F_SANS_B  = f"{FONT_DIR}/liberation/LiberationSans-Bold.ttf"

OUTPUT_DIR = Path("campaigns/routines-video-campaign/videos")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ── Drawing helpers ────────────────────────────────────────────────────────────

def load_font(path: str, size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default(size=size)


def draw_centered(draw, text: str, y: int, font, color, img_w: int = W, wrap: int = 0):
    """Draw horizontally-centered text, optionally word-wrapped."""
    if wrap:
        lines = textwrap.wrap(text, width=wrap)
    else:
        lines = [text]

    line_h = font.size + 8
    total_h = line_h * len(lines)
    cur_y = y - total_h // 2

    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        x = (img_w - tw) // 2
        draw.text((x, cur_y), line, font=font, fill=color)
        cur_y += line_h


def horizontal_rule(draw, y: int, color, width: int = 120, thickness: int = 2):
    """Draw a centered horizontal rule."""
    x0 = (W - width) // 2
    draw.rectangle([x0, y, x0 + width, y + thickness], fill=color)


def corner_accent(draw, color=GOLD):
    """Thin gold border around the frame."""
    bw = 4
    draw.rectangle([0, 0, W - 1, bw - 1], fill=color)
    draw.rectangle([0, H - bw, W - 1, H - 1], fill=color)
    draw.rectangle([0, 0, bw - 1, H - 1], fill=color)
    draw.rectangle([W - bw, 0, W - 1, H - 1], fill=color)


def logo_text(draw, font_s, font_l):
    """Draw 'ROUTINES.FR' in the bottom-right corner."""
    text = "ROUTINES.FR"
    bbox = draw.textbbox((0, 0), text, font=font_s)
    tw = bbox[2] - bbox[0]
    draw.text((W - tw - 40, H - 52), text, font=font_s, fill=GOLD)


def make_scene(
    bg_color,
    title: str = "",
    subtitle: str = "",
    eyebrow: str = "",
    cta: str = "",
    dark_bg: bool = False,
    accent_bar: bool = True,
    label: str = "",
) -> np.ndarray:
    """Render one video frame and return as numpy RGB array."""
    img = Image.new("RGB", (W, H), bg_color)
    draw = ImageDraw.Draw(img)

    # Subtle gradient overlay via bands (simulated)
    for i in range(H):
        alpha = int(12 * (i / H))
        r = max(0, bg_color[0] - alpha)
        g = max(0, bg_color[1] - alpha)
        b = max(0, bg_color[2] - alpha)
        draw.line([(0, i), (W, i)], fill=(r, g, b))

    # Fonts
    f_eyebrow = load_font(F_SANS,    28)
    f_title   = load_font(F_SERIF_B, 96)
    f_sub     = load_font(F_SANS,    42)
    f_cta     = load_font(F_SANS_B,  38)
    f_logo    = load_font(F_SANS_B,  22)

    text_color = WHITE if dark_bg else DARK
    sub_color  = (200, 200, 200) if dark_bg else (80, 80, 80)

    # Eyebrow
    if eyebrow:
        draw_centered(draw, eyebrow.upper(), H // 2 - 160, f_eyebrow, GOLD)

    # Horizontal rule
    if accent_bar and eyebrow:
        horizontal_rule(draw, H // 2 - 135, GOLD, width=80)

    # Title
    if title:
        draw_centered(draw, title, H // 2 - 10, f_title, text_color, wrap=30)

    # Subtitle
    if subtitle:
        draw_centered(draw, subtitle, H // 2 + 120, f_sub, sub_color, wrap=52)

    # CTA
    if cta:
        # Pill button
        bbox = draw.textbbox((0, 0), cta, font=f_cta)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        pad_x, pad_y = 40, 18
        bx = (W - tw - 2 * pad_x) // 2
        by = H // 2 + 220
        draw.rounded_rectangle(
            [bx, by, bx + tw + 2 * pad_x, by + th + 2 * pad_y],
            radius=8, fill=GOLD
        )
        draw.text((bx + pad_x, by + pad_y), cta, font=f_cta, fill=DARK)

    # Corner border
    corner_accent(draw, GOLD)

    # Phase label (top-left badge)
    if label:
        f_lbl = load_font(F_SANS_B, 20)
        draw.rounded_rectangle([32, 32, 32 + len(label) * 12 + 24, 72], radius=6, fill=SLATE)
        draw.text((44, 40), label, font=f_lbl, fill=WHITE)

    # Logo watermark
    logo_text(draw, f_logo, f_logo)

    return np.array(img)


def frames_to_clip(frame: np.ndarray, duration: float) -> ImageClip:
    return ImageClip(frame, duration=duration)


def fade_transition(clip_a: ImageClip, clip_b: ImageClip, t: float = 0.5):
    """Cross-dissolve between two clips."""
    clip_a_fade = clip_a.with_effects(
        [__import__("moviepy.video.fx", fromlist=["CrossFadeOut"]).CrossFadeOut(t)]
    )
    clip_b_fade = clip_b.with_effects(
        [__import__("moviepy.video.fx", fromlist=["CrossFadeIn"]).CrossFadeIn(t)]
    )
    return clip_a_fade, clip_b_fade


def build_video(scenes: list[tuple], output_path: str, fps: int = FPS):
    """
    scenes: list of (frame_array, duration_seconds)
    Assembles clips with cross-dissolve transitions and exports to MP4.
    """
    print(f"  Building {len(scenes)} scenes...")
    clips = []
    for i, (frame, dur) in enumerate(scenes):
        clip = ImageClip(frame, duration=dur)
        clips.append(clip)

    # Apply cross-fade transitions between consecutive clips
    final_clips = [clips[0]]
    for i in range(1, len(clips)):
        prev = final_clips[-1]
        curr = clips[i]
        fade_dur = min(0.5, prev.duration / 2, curr.duration / 2)
        prev_faded = prev.with_effects(
            [__import__("moviepy.video.fx", fromlist=["CrossFadeOut"]).CrossFadeOut(fade_dur)]
        )
        curr_faded = curr.with_effects(
            [__import__("moviepy.video.fx", fromlist=["CrossFadeIn"]).CrossFadeIn(fade_dur)]
        )
        final_clips[-1] = prev_faded
        final_clips.append(curr_faded)

    video = concatenate_videoclips(final_clips, method="compose")
    video.write_videofile(
        output_path,
        fps=fps,
        codec="libx264",
        audio=False,
        logger=None,
        preset="fast",
    )
    print(f"  Saved → {output_path}  ({video.duration:.1f}s)")
    return output_path


# ══════════════════════════════════════════════════════════════════════════════
# VIDEO 1 — Brand Film Hero (60s)
# ══════════════════════════════════════════════════════════════════════════════

def video_hero_brand_film():
    print("\n[1/5] Brand Film Hero — 60s")
    scenes = [
        # [00:00] Opening — dark, dramatic
        (make_scene(DIM_DARK,
                    title="Chaque jour,\nvotre peau vieillit.",
                    dark_bg=True, accent_bar=False,
                    label="BRAND FILM · 60S"), 4.0),

        # [00:04] Contrast
        (make_scene(DIM_DARK,
                    title="Ou elle ne vieillit pas.",
                    subtitle="La différence, c'est ce que vous faites chaque jour.",
                    dark_bg=True, accent_bar=False), 5.0),

        # [00:09] Problem
        (make_scene(CREAM,
                    eyebrow="Le problème",
                    title="L'industrie vous vend\ndes miracles.",
                    subtitle="Des promesses. Des effets. Des tendances.",
                    accent_bar=True), 5.0),

        # [00:14] Pivot
        (make_scene(DARK,
                    title="Routines ne vend\npas de miracles.",
                    dark_bg=True, accent_bar=False), 4.0),

        # [00:18] Longevity Complex intro
        (make_scene(CREAM,
                    eyebrow="Notre technologie",
                    title="Le Longevity Complex™",
                    subtitle="La première formule ciblant simultanément\nles 3 mécanismes du vieillissement cutané.",
                    accent_bar=True), 7.0),

        # [00:25] 3 mechanisms
        (make_scene(SLATE,
                    eyebrow="3 mécanismes. 1 formule.",
                    title="Régénération\nBarrière\nCommunication",
                    dark_bg=True, accent_bar=True), 6.0),

        # [00:31] Protocol
        (make_scene(CREAM,
                    eyebrow="Le protocole",
                    title="4 étapes.\nSynergiques.",
                    subtitle="Préparer · Traiter · Booster · Restaurer",
                    accent_bar=True), 6.0),

        # [00:37] Made in France
        (make_scene((240, 238, 234),
                    eyebrow="Qualité",
                    title="Fabriqué en France.\nStandards pharmaceutiques.",
                    subtitle="Dermatologiquement testé · Tous types de peau",
                    accent_bar=True), 5.0),

        # [00:42] Proof
        (make_scene(DARK,
                    eyebrow="Résultats cliniques · 28 jours",
                    title="+94% de peau revitalisée",
                    subtitle="Étude indépendante · 52 volontaires",
                    dark_bg=True, accent_bar=True), 5.0),

        # [00:47] Community
        (make_scene(CREAM,
                    eyebrow="La communauté",
                    title="50 000+\nLongevity Activists",
                    subtitle="Ceux qui prennent soin de leur peau\navec constance, conscience et conviction.",
                    accent_bar=True), 6.0),

        # [00:53] Tagline
        (make_scene(DIM_DARK,
                    title="Corriger aujourd'hui.\nPréserver demain.",
                    dark_bg=True, accent_bar=False), 4.0),

        # [00:57] CTA
        (make_scene(CREAM,
                    eyebrow="Routines.fr",
                    title="La longévité\ncommence par la peau.",
                    cta="Découvrez votre protocole →",
                    accent_bar=True), 3.0),
    ]
    return build_video(scenes, str(OUTPUT_DIR / "01_brand_film_hero_60s.mp4"))


# ══════════════════════════════════════════════════════════════════════════════
# VIDEO 2 — Collagen Boost Serum (30s)
# ══════════════════════════════════════════════════════════════════════════════

def video_collagen_boost_serum():
    print("\n[2/5] Collagen Boost Serum — 30s")
    scenes = [
        # Hook
        (make_scene(DIM_DARK,
                    title="Votre collagène diminue\nde 1% par an.",
                    subtitle="À 40 ans — c'est 20% de perdu.",
                    dark_bg=True, accent_bar=False,
                    label="PRODUIT · 30S"), 5.0),

        # Product intro
        (make_scene(CREAM,
                    eyebrow="Étape 2 — Traiter",
                    title="Collagen Boost Serum",
                    subtitle="Longevity Complex™ · Fabriqué en France",
                    accent_bar=True), 5.0),

        # Formula
        (make_scene(SLATE,
                    eyebrow="Formule clinique",
                    title="Stimule votre production\nde collagène.",
                    subtitle="Actifs cliniquement évalués · Texture légère · Pénétration immédiate",
                    dark_bg=True, accent_bar=True), 6.0),

        # Clinical proof
        (make_scene(DARK,
                    eyebrow="Étude clinique · 28 jours · 47 volontaires",
                    title="+87% de fermeté\n+92% de peau repulpée",
                    subtitle="*Résultats d'une étude clinique, conditions contrôlées",
                    dark_bg=True, accent_bar=True), 7.0),

        # CTA
        (make_scene(CREAM,
                    eyebrow="Routines.fr",
                    title="Collagen Boost Serum",
                    subtitle="Protocole Longévité · Étape 2",
                    cta="Découvrir le sérum →",
                    accent_bar=True), 7.0),
    ]
    return build_video(scenes, str(OUTPUT_DIR / "02_collagen_boost_serum_30s.mp4"))


# ══════════════════════════════════════════════════════════════════════════════
# VIDEO 3 — Collagen Skin Beauty (30s)
# ══════════════════════════════════════════════════════════════════════════════

def video_collagen_skin_beauty():
    print("\n[3/5] Collagen Skin Beauty — 30s")
    scenes = [
        # Hook — sensory
        (make_scene(CREAM,
                    title="Le dernier geste.\nLe plus important.",
                    subtitle="Étape 4 — Restaurer",
                    accent_bar=False,
                    label="PRODUIT · 30S"), 5.0),

        # Product
        (make_scene((242, 240, 236),
                    eyebrow="Étape 4 — Restaurer",
                    title="Collagen Skin Beauty",
                    subtitle="Crème restauratrice · Longevity Complex™\nFabriquée en France · Peau sensible OK",
                    accent_bar=True), 6.0),

        # Benefits
        (make_scene(SLATE,
                    eyebrow="Triple action",
                    title="Densité.\nFermeté.\nVitalité.",
                    subtitle="Renforce la barrière cutanée · Stimule la fermeté · Révèle la vitalité",
                    dark_bg=True, accent_bar=True), 6.0),

        # Proof
        (make_scene(DARK,
                    eyebrow="Résultats cliniques · 52 volontaires · 28 jours",
                    title="+94% satisfaction\n+89% vitalité perçue",
                    subtitle="*Étude clinique indépendante, conditions contrôlées",
                    dark_bg=True, accent_bar=True), 6.0),

        # CTA
        (make_scene(CREAM,
                    eyebrow="Routines.fr",
                    title="Collagen Skin Beauty",
                    subtitle="Protocole complet disponible",
                    cta="Étape 4 — Restaurer →",
                    accent_bar=True), 7.0),
    ]
    return build_video(scenes, str(OUTPUT_DIR / "03_collagen_skin_beauty_30s.mp4"))


# ══════════════════════════════════════════════════════════════════════════════
# VIDEO 4 — Science : Le Longevity Complex (45s)
# ══════════════════════════════════════════════════════════════════════════════

def video_science_longevity():
    print("\n[4/5] Science — Longevity Complex — 45s")
    scenes = [
        # Question
        (make_scene(CREAM,
                    title="Pourquoi la peau\nvieillit-elle ?",
                    subtitle="La plupart des soins n'en adressent qu'une cause.",
                    accent_bar=False,
                    label="SCIENCE · 45S"), 5.0),

        # Mechanism 1
        (make_scene(DIM_DARK,
                    eyebrow="Mécanisme #1",
                    title="Régénération\ncellulaire ralentie",
                    subtitle="Vos cellules se renouvellent moins vite avec le temps.",
                    dark_bg=True, accent_bar=True), 5.0),

        # Mechanism 2
        (make_scene(DIM_DARK,
                    eyebrow="Mécanisme #2",
                    title="Barrière cutanée\naffaiblie",
                    subtitle="Votre peau retient moins bien l'hydratation.",
                    dark_bg=True, accent_bar=True), 5.0),

        # Mechanism 3
        (make_scene(DIM_DARK,
                    eyebrow="Mécanisme #3",
                    title="Communication\nintercellulaire réduite",
                    subtitle="Vos cellules coordonnent moins efficacement leur réponse.",
                    dark_bg=True, accent_bar=True), 5.0),

        # The solution
        (make_scene(CREAM,
                    eyebrow="La réponse de Routines",
                    title="Le Longevity Complex™",
                    subtitle="La première formule à cibler les 3 mécanismes\nsimultanément et en synergie.",
                    accent_bar=True), 7.0),

        # Proof
        (make_scene(SLATE,
                    eyebrow="Étude clinique indépendante · 52 volontaires · 28 jours",
                    title="+91% régénération\n+87% fermeté  ·  +94% vitalité",
                    subtitle="Standards pharmaceutiques · Fabriqué en France",
                    dark_bg=True, accent_bar=True), 8.0),

        # CTA
        (make_scene(CREAM,
                    eyebrow="Routines.fr",
                    title="La science au service\nde votre longévité.",
                    cta="Découvrez le protocole →",
                    accent_bar=True), 5.0),
    ]
    return build_video(scenes, str(OUTPUT_DIR / "04_science_longevity_complex_45s.mp4"))


# ══════════════════════════════════════════════════════════════════════════════
# VIDEO 5 — Tutoriel Protocole 4 Étapes (45s)
# ══════════════════════════════════════════════════════════════════════════════

def video_tutoriel_protocole():
    print("\n[5/5] Tutoriel — Protocole 4 Étapes — 45s")
    scenes = [
        # Hook
        (make_scene(CREAM,
                    title="Mon protocole peau\ndu matin.",
                    subtitle="4 étapes · 5 minutes · Résultats en 28 jours",
                    accent_bar=False,
                    label="TUTORIEL · 45S"), 4.0),

        # Step 1
        (make_scene((235, 243, 248),
                    eyebrow="Étape 1 / 4",
                    title="PRÉPARER",
                    subtitle="Nettoyant Routines\nPeau propre, sans tiraillement.",
                    accent_bar=True), 7.0),

        # Step 2
        (make_scene(CREAM,
                    eyebrow="Étape 2 / 4",
                    title="TRAITER",
                    subtitle="Collagen Boost Serum\n3–4 gouttes · Longevity Complex™ en action.",
                    accent_bar=True), 8.0),

        # Step 3
        (make_scene((235, 243, 248),
                    eyebrow="Étape 3 / 4",
                    title="BOOSTER",
                    subtitle="Booster concentré Routines\nApplication ciblée sur les zones prioritaires.",
                    accent_bar=True), 7.0),

        # Step 4
        (make_scene(CREAM,
                    eyebrow="Étape 4 / 4",
                    title="RESTAURER",
                    subtitle="Collagen Skin Beauty\nLe geste final qui scelle le protocole.",
                    accent_bar=True), 8.0),

        # Results
        (make_scene(DARK,
                    eyebrow="4 semaines · Résultats prouvés",
                    title="Ce n'est pas de la magie.\nC'est de la science.",
                    subtitle="Fabriqué en France · Standards pharmaceutiques · +94% en 28 jours",
                    dark_bg=True, accent_bar=True), 5.0),

        # CTA
        (make_scene(CREAM,
                    eyebrow="Rejoignez les",
                    title="Longevity Activists",
                    subtitle="Protocole complet disponible sur routines.fr",
                    cta="Démarrez votre routine →",
                    accent_bar=True), 6.0),
    ]
    return build_video(scenes, str(OUTPUT_DIR / "05_tutoriel_protocole_4etapes_45s.mp4"))


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import time
    start = time.time()

    print("=" * 60)
    print("  ROUTINES.FR — Video Campaign Generator")
    print("  'Corriger aujourd'hui. Préserver demain.'")
    print("=" * 60)

    outputs = []
    outputs.append(video_hero_brand_film())
    outputs.append(video_collagen_boost_serum())
    outputs.append(video_collagen_skin_beauty())
    outputs.append(video_science_longevity())
    outputs.append(video_tutoriel_protocole())

    elapsed = time.time() - start
    print("\n" + "=" * 60)
    print(f"  ✓ {len(outputs)} vidéos générées en {elapsed:.0f}s")
    print(f"  Dossier : {OUTPUT_DIR.resolve()}")
    print("=" * 60)
    for p in outputs:
        size_kb = Path(p).stat().st_size // 1024
        print(f"  • {Path(p).name}  ({size_kb} KB)")
    print()
