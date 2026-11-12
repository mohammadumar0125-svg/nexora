#!/usr/bin/env python3
"""
NEXORA Order Agent - Startup Pitch Presentation Video Generator
Generates a broadcast-quality Full HD 1080p motion graphics animation video
at 30 FPS with clear studio English voiceover (en-US-ChristopherNeural).
"""

import math
import os
import subprocess
import sys
from PIL import Image, ImageDraw, ImageFont

# Paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BUILD_DIR = "/tmp/nexora_pitch_build"
AUDIO_DIR = "/tmp/nexora_7scenes_audio"
OUTPUT_MP4 = os.path.join(BASE_DIR, "nexora_pitch_presentation.mp4")
FRONTEND_DIST_MP4 = os.path.join(BASE_DIR, "frontend", "dist", "demo-video.mp4")
ROOT_DEMO_MP4 = os.path.join(BASE_DIR, "nexora_demo_walkthrough.mp4")
FFMPEG = "/opt/homebrew/bin/ffmpeg"
FFPROBE = "/opt/homebrew/bin/ffprobe"

os.makedirs(BUILD_DIR, exist_ok=True)
os.makedirs(os.path.dirname(FRONTEND_DIST_MP4), exist_ok=True)

# Typography Fonts
FONT_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
FONT_REG = "/System/Library/Fonts/Supplemental/Arial.ttf"

font_title = ImageFont.truetype(FONT_BOLD, 36)
font_subtitle = ImageFont.truetype(FONT_REG, 20)
font_card_header = ImageFont.truetype(FONT_BOLD, 22)
font_body = ImageFont.truetype(FONT_REG, 18)
font_body_bold = ImageFont.truetype(FONT_BOLD, 18)
font_small = ImageFont.truetype(FONT_REG, 15)
font_small_bold = ImageFont.truetype(FONT_BOLD, 15)
font_stat_big = ImageFont.truetype(FONT_BOLD, 52)
font_stat_med = ImageFont.truetype(FONT_BOLD, 36)

# Colors
BG_DARK = (11, 15, 25)
TOPBAR_BG = (15, 23, 42)
CARD_BG = (19, 29, 49)
CARD_BORDER = (37, 52, 77)
TEXT_WHITE = (248, 250, 252)
TEXT_MUTED = (148, 163, 184)
TEXT_BODY = (203, 213, 225)
CYAN = (56, 189, 248)
EMERALD = (16, 185, 129)
ROSE = (244, 63, 94)
AMBER = (245, 158, 11)
INDIGO = (99, 102, 241)

SCENE_TABS = [
    "1. The Dilemma",
    "2. Meet NEXORA",
    "3. Multimodal AI",
    "4. Rule R1: Never Guess",
    "5. Shorthand Memory",
    "6. Rule R2: Approval",
    "7. Enterprise Core"
]

def ease_out_cubic(t):
    t = min(max(t, 0.0), 1.0)
    return 1 - (1 - t) ** 3

def ease_in_out(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)

def lerp(a, b, t):
    return a + (b - a) * t

def draw_topbar(draw, active_scene_id, t):
    # Top header
    draw.rectangle([(0, 0), (1920, 75)], fill=TOPBAR_BG)
    draw.line([(0, 75), (1920, 75)], fill=CARD_BORDER, width=2)
    
    # Logo
    draw.rectangle([(60, 18), (100, 58)], fill=CYAN)
    draw.text((70, 22), "N", font=font_card_header, fill=BG_DARK)
    draw.text((115, 21), "NEXORA", font=font_title, fill=TEXT_WHITE)
    draw.text((285, 30), "ORDER AGENT", font=font_body_bold, fill=CYAN)
    
    # Subhead
    draw.line([(450, 22), (450, 54)], fill=CARD_BORDER, width=2)
    draw.text((470, 28), "Enterprise FMCG Wholesale Automation", font=font_body, fill=TEXT_MUTED)
    
    # Status Dot & Badge
    glow = 0.5 + 0.5 * math.sin(t * 4.0)
    dot_color = (int(16 + 20 * glow), int(185 + 40 * glow), int(129 + 30 * glow))
    draw.rectangle([(1600, 20), (1860, 54)], fill=(15, 35, 25), outline=EMERALD, width=1)
    draw.ellipse([(1615, 31), (1627, 43)], fill=dot_color)
    draw.text((1638, 26), "LIVE • R1–R6 ACTIVE", font=font_small_bold, fill=TEXT_WHITE)

    # Breadcrumb Tab bar
    draw.rectangle([(0, 75), (1920, 120)], fill=(12, 19, 34))
    draw.line([(0, 120), (1920, 120)], fill=CARD_BORDER, width=1)
    
    tab_w = 1920 // len(SCENE_TABS)
    for i, tab_title in enumerate(SCENE_TABS):
        tx = i * tab_w
        is_active = (i + 1 == active_scene_id)
        if is_active:
            draw.rectangle([(tx + 4, 77), (tx + tab_w - 4, 118)], fill=CARD_BG)
            draw.line([(tx + 4, 117), (tx + tab_w - 4, 117)], fill=CYAN, width=3)
            draw.text((tx + 20, 89), tab_title, font=font_small_bold, fill=CYAN)
        else:
            draw.text((tx + 20, 89), tab_title, font=font_small, fill=TEXT_MUTED)

def draw_footer(draw):
    draw.rectangle([(0, 1025), (1920, 1080)], fill=TOPBAR_BG)
    draw.line([(0, 1025), (1920, 1025)], fill=CARD_BORDER, width=2)
    draw.text((60, 1042), "NEXORA Startup Presentation • 1080p 30fps Motion Graphics • Zero Guesswork", font=font_small, fill=TEXT_MUTED)
    draw.text((1650, 1042), "Singhania & Sons Wholesale", font=font_small_bold, fill=TEXT_BODY)

def draw_cursor(draw, x, y, clicking=False):
    size = 20 if not clicking else 16
    pts = [
        (int(x), int(y)),
        (int(x), int(y + size)),
        (int(x + size * 0.35), int(y + size * 0.75)),
        (int(x + size * 0.75), int(y + size * 0.75))
    ]
    draw.polygon(pts, fill=(255, 255, 255), outline=(0, 0, 0))

def draw_audio_wave(draw, x, y, w, max_h, t, num_bars=24, color=CYAN):
    bar_w = int(w / num_bars) - 4
    for i in range(num_bars):
        freq = 3.0 + (i % 5) * 1.5
        phase = i * 0.4
        h = int(12 + (max_h - 12) * abs(math.sin(t * freq + phase)))
        bx = x + i * (bar_w + 4)
        by = y + (max_h - h) // 2
        draw.rounded_rectangle([(bx, by), (bx + bar_w, by + h)], radius=2, fill=color)

def draw_particles(draw, x1, y1, x2, y2, t, count=6, color=CYAN):
    for i in range(count):
        prog = ((t * 0.8) + (i / count)) % 1.0
        px = int(lerp(x1, x2, prog))
        py = int(lerp(y1, y2, prog))
        radius = int(3 + 2 * math.sin(prog * math.pi))
        draw.ellipse([(px - radius, py - radius), (px + radius, py + radius)], fill=color)

# ==================== SCENE ANIMATION RENDERERS ====================

def render_frame_scene_1(draw, t, dur):
    # Scene 1: The Wholesale Dilemma
    draw_topbar(draw, 1, t)
    draw.text((60, 145), "The Daily Wholesale Dilemma: WhatsApp Order Chaos", font=font_title, fill=TEXT_WHITE)
    draw.text((60, 195), "Why manual order entry bleeds 4+ minutes per order, causing errors and stalled trucks.", font=font_subtitle, fill=TEXT_MUTED)

    # Left Container: Traditional Chaos
    draw.rounded_rectangle([(60, 245), (930, 995)], radius=12, fill=CARD_BG, outline=ROSE, width=2)
    draw.rectangle([(60, 245), (930, 305)], fill=(50, 15, 25))
    draw.text((90, 262), "❌ CURRENT MANUAL BOTTLENECK", font=font_card_header, fill=ROSE)

    # 3 Animated Incoming Chat Bubbles
    bubbles = [
        (0.6, "💬 06:14 AM • Gupta Kirana", "“Bhaiya 10 bori Fortune atta, 5 peti Maggi aur woh meetha biscuit jaldi bhejo”"),
        (2.2, "🎙️ 06:28 AM • Sharma Stores (Voice Note 0:18)", "“Arre Sharma ji, Tata Tea ka 10 packet bhija dena truck aane se pehle...”"),
        (3.8, "💬 06:45 AM • Verma Traders", "“Surfed excel 5 cartoon aur lifebuoy laal sabun 2 peti bhejo rate purana lagana”")
    ]
    by = 330
    for trigger_t, sender, text in bubbles:
        if t >= trigger_t:
            prog = ease_out_cubic((t - trigger_t) / 0.6)
            bx_off = int((1.0 - prog) * -80)
            bx = 90 + bx_off
            draw.rounded_rectangle([(bx, by), (bx + 780, by + 85)], radius=8, fill=(24, 38, 66), outline=CARD_BORDER)
            draw.text((bx + 20, by + 12), sender, font=font_small_bold, fill=CYAN)
            draw.text((bx + 20, by + 42), text, font=font_small, fill=TEXT_WHITE)
        by += 105

    # Animated Voice Waveform on Audio note
    if t >= 2.2:
        draw_audio_wave(draw, 520, 445, 320, 26, t, num_bars=18, color=EMERALD)

    # Red Alert Box (Appears at t=5.0s with pulse)
    if t >= 5.0:
        pulse = 0.5 + 0.5 * math.sin((t - 5.0) * 5.0)
        border_c = (int(244 * pulse + 100 * (1 - pulse)), 63, 94)
        draw.rounded_rectangle([(90, 680), (900, 810)], radius=8, fill=(45, 15, 25), outline=border_c, width=2)
        draw.text((115, 700), "⚠️ SILENT PACKAGING & SKU ERROR HAZARD", font=font_body_bold, fill=ROSE)
        draw.text((115, 735), "Missing pack size (250g vs 500g) dispatched incorrectly.", font=font_small, fill=TEXT_BODY)
        draw.text((115, 765), "Retailer rejects delivery at shop ➔ Entire crate returned at distributor's loss.", font=font_small, fill=TEXT_MUTED)

    # Delivery Truck Delay Animation
    draw.rounded_rectangle([(90, 840), (900, 965)], radius=8, fill=(15, 23, 42), outline=CARD_BORDER)
    draw.text((115, 860), "🚚 WAREHOUSE LOADING DOCK STATUS", font=font_small_bold, fill=TEXT_MUTED)
    truck_prog = min(t / dur, 1.0)
    truck_x = int(120 + truck_prog * 400)
    draw.line([(120, 920), (870, 920)], fill=CARD_BORDER, width=2)
    draw.rectangle([(truck_x, 900), (truck_x + 60, 925)], fill=ROSE)
    draw.text((truck_x + 10, 905), "TRUCK", font=font_small_bold, fill=TEXT_WHITE)
    draw.text((600, 860), "STATUS: STALLED FOR INVOICES", font=font_small_bold, fill=ROSE)

    # Right Container: Quantified Business Cost
    draw.rounded_rectangle([(990, 245), (1860, 995)], radius=12, fill=CARD_BG, outline=CARD_BORDER, width=2)
    draw.rectangle([(990, 245), (1860, 305)], fill=(20, 35, 60))
    draw.text((1020, 262), "📊 QUANTIFIED COST TO WHOLESALERS", font=font_card_header, fill=CYAN)

    # Stopwatch Counter Ticking Up (0.0 to 4.2 min)
    draw.rounded_rectangle([(1020, 335), (1830, 480)], radius=8, fill=(15, 23, 42), outline=CARD_BORDER)
    curr_min = min(t * (4.2 / 8.0), 4.2)
    draw.text((1050, 365), f"{curr_min:.1f} min", font=font_stat_big, fill=AMBER)
    draw.text((1290, 365), "Average Retyping Time Per Order", font=font_body_bold, fill=TEXT_WHITE)
    draw.text((1290, 405), "Clerk listens repeatedly, checks paper price sheets, and types into Tally.", font=font_small, fill=TEXT_MUTED)

    # Error Rate Meter
    draw.rounded_rectangle([(1020, 505), (1830, 650)], radius=8, fill=(15, 23, 42), outline=CARD_BORDER)
    err_rate = min(t * (12.0 / 10.0), 12.0)
    draw.text((1050, 535), f"{err_rate:.0f}%", font=font_stat_big, fill=ROSE)
    draw.text((1290, 535), "Dispatch Error Rate During Rush Hours", font=font_body_bold, fill=TEXT_WHITE)
    draw.text((1290, 575), "Wrong items or quantities loaded during chaotic morning dispatch.", font=font_small, fill=TEXT_MUTED)

    # Monthly Loss Card
    draw.rounded_rectangle([(1020, 675), (1830, 820)], radius=8, fill=(15, 23, 42), outline=CARD_BORDER)
    draw.text((1050, 705), "₹48,000", font=font_stat_big, fill=CYAN)
    draw.text((1290, 705), "Monthly Cost in Returns & Re-billing", font=font_body_bold, fill=TEXT_WHITE)
    draw.text((1290, 745), "Wasted freight, repackaging damaged goods, and strained customer relationships.", font=font_small, fill=TEXT_MUTED)

    # Bottom Core Objective
    draw.rounded_rectangle([(1020, 845), (1830, 965)], radius=8, fill=(24, 38, 66), outline=CYAN)
    draw.text((1050, 870), "⚡ THE NEXORA SOLUTION", font=font_body_bold, fill=CYAN)
    draw.text((1050, 905), "Automate extraction and catalogue mapping with sub-second AI,", font=font_body, fill=TEXT_WHITE)
    draw.text((1050, 935), "keeping the clerk in 1-click control. Zero guesswork.", font=font_body, fill=TEXT_BODY)

    draw_footer(draw)

def render_frame_scene_2(draw, t, dur):
    # Scene 2: Meet NEXORA
    draw_topbar(draw, 2, t)
    draw.text((60, 145), "Meet NEXORA: The Autonomous Wholesale Order Agent", font=font_title, fill=TEXT_WHITE)
    draw.text((60, 195), "Bridges the gap between chaotic customer messaging and rigid enterprise ERP accounting.", font=font_subtitle, fill=TEXT_MUTED)

    # 3 Columns Architecture: Input (Left) -> NEXORA Core (Center) -> ERP Output (Right)
    # Left: Chaotic Input Card
    draw.rounded_rectangle([(60, 250), (600, 980)], radius=12, fill=CARD_BG, outline=CARD_BORDER, width=2)
    draw.rectangle([(60, 250), (600, 310)], fill=(30, 20, 40))
    draw.text((85, 270), "📱 UNSTRUCTURED INPUT", font=font_card_header, fill=TEXT_WHITE)

    draw.rounded_rectangle([(85, 340), (575, 470)], radius=8, fill=(15, 23, 42), outline=CARD_BORDER)
    draw.text((105, 358), "WhatsApp Voice Notes", font=font_body_bold, fill=CYAN)
    draw.text((105, 390), "Hinglish, regional vernacular,", font=font_small, fill=TEXT_MUTED)
    draw.text((105, 415), "colloquial units (bori, peti)", font=font_small, fill=TEXT_MUTED)
    draw_audio_wave(draw, 105, 440, 250, 20, t, num_bars=14, color=CYAN)

    draw.rounded_rectangle([(85, 500), (575, 630)], radius=8, fill=(15, 23, 42), outline=CARD_BORDER)
    draw.text((105, 520), "Informal Chat & SMS", font=font_body_bold, fill=TEXT_WHITE)
    draw.text((105, 555), "Fragmented text, typos, slang,", font=font_small, fill=TEXT_MUTED)
    draw.text((105, 580), "customer nicknames for goods.", font=font_small, fill=TEXT_MUTED)

    draw.rounded_rectangle([(85, 660), (575, 790)], radius=8, fill=(15, 23, 42), outline=CARD_BORDER)
    draw.text((105, 680), "Paper Slips & Photos", font=font_body_bold, fill=TEXT_WHITE)
    draw.text((105, 715), "Handwritten retailer order slips", font=font_small, fill=TEXT_MUTED)
    draw.text((105, 740), "captured with mobile camera.", font=font_small, fill=TEXT_MUTED)

    # Center: NEXORA Autonomous Core Engine
    draw.rounded_rectangle([(660, 250), (1260, 980)], radius=12, fill=CARD_BG, outline=CYAN, width=2)
    draw.rectangle([(660, 250), (1260, 310)], fill=(18, 45, 75))
    draw.text((790, 270), "⚡ NEXORA AGENT CORE", font=font_card_header, fill=CYAN)

    # Rotating / Pulsing Central Shield Emblem
    center_x, center_y = 960, 460
    pulse = 0.5 + 0.5 * math.sin(t * 3.0)
    r1 = int(75 + 10 * pulse)
    r2 = int(105 + 15 * pulse)
    draw.ellipse([(center_x - r2, center_y - r2), (center_x + r2, center_y + r2)], outline=(30, 80, 130), width=2)
    draw.ellipse([(center_x - r1, center_y - r1), (center_x + r1, center_y + r1)], outline=CYAN, width=3)
    draw.rectangle([(center_x - 30, center_y - 30), (center_x + 30, center_y + 30)], fill=CYAN)
    draw.text((center_x - 12, center_y - 18), "N", font=font_card_header, fill=BG_DARK)

    # Core Capabilities Box
    draw.rounded_rectangle([(690, 610), (1230, 940)], radius=8, fill=(15, 23, 42), outline=CARD_BORDER)
    draw.text((720, 630), "INTELLIGENT PIPELINE:", font=font_body_bold, fill=CYAN)
    pipeline_items = [
        "1. Multimodal Audio Extraction (Gemini 2.0)",
        "2. Layer 1 Learned Shorthand Memory Cache",
        "3. Layer 2 pgvector Semantic Catalogue Search",
        "4. Rule R1: Never Guess (Ambiguity Gate)",
        "5. Rule R2: 1-Click Human Approval Verification"
    ]
    py = 670
    for pi in pipeline_items:
        draw.text((720, py), pi, font=font_small, fill=TEXT_WHITE)
        py += 35

    # Right: Verified ERP Accounting Output
    draw.rounded_rectangle([(1320, 250), (1860, 980)], radius=12, fill=CARD_BG, outline=EMERALD, width=2)
    draw.rectangle([(1320, 250), (1860, 310)], fill=(15, 45, 30))
    draw.text((1380, 270), "🚀 ACCOUNTING & ERP SYNC", font=font_card_header, fill=EMERALD)

    erp_boxes = [
        ("Tally Prime XML", "Standardized Sales Voucher format.", "Auto-import without typing."),
        ("Vyapar / Busy JSON", "REST ledger & invoice sync.", "Instant customer balance update."),
        ("Warehouse Pick-List", "Optimized bin-location order.", "Ready for loading dock."),
        ("Immutable Audit Log", "Who approved, timestamps, diffs.", "100% financial compliance.")
    ]
    ey = 340
    for title, desc1, desc2 in erp_boxes:
        draw.rounded_rectangle([(1350, ey), (1830, ey + 115)], radius=8, fill=(15, 23, 42), outline=CARD_BORDER)
        draw.text((1375, ey + 15), title, font=font_body_bold, fill=EMERALD)
        draw.text((1375, ey + 45), desc1, font=font_small, fill=TEXT_BODY)
        draw.text((1375, ey + 70), desc2, font=font_small, fill=TEXT_MUTED)
        ey += 135

    # Streaming Particles from Left to Center, Center to Right
    draw_particles(draw, 600, 460, 850, 460, t, count=5, color=CYAN)
    draw_particles(draw, 1070, 460, 1320, 460, t + 0.5, count=5, color=EMERALD)

    draw_footer(draw)

def render_frame_scene_3(draw, t, dur):
    # Scene 3: Multimodal AI Ingestion
    draw_topbar(draw, 3, t)
    draw.text((60, 145), "Multimodal Ingestion: Instant Voice & Hinglish Extraction", font=font_title, fill=TEXT_WHITE)
    draw.text((60, 195), "Gemini 2.0 Flash parses unstructured voice notes and colloquial units in under 500 milliseconds.", font=font_subtitle, fill=TEXT_MUTED)

    # Left: Audio Input Card with Laser Scan Line
    draw.rounded_rectangle([(60, 245), (930, 995)], radius=12, fill=CARD_BG, outline=CARD_BORDER, width=2)
    draw.rectangle([(60, 245), (930, 305)], fill=(20, 45, 35))
    draw.text((90, 262), "💬 RAW INCOMING WHATSAPP MESSAGE", font=font_card_header, fill=EMERALD)

    # Retailer Info
    draw.rectangle([(90, 330), (900, 400)], fill=(15, 23, 42), outline=CARD_BORDER)
    draw.text((115, 345), "Gupta Kirana Stores • Varanasi (+91 98765 43210)", font=font_body_bold, fill=TEXT_WHITE)
    draw.text((115, 372), "Audio Format: OGG Opus (WhatsApp Voice Note 0:14) • 06:42 AM", font=font_small, fill=TEXT_MUTED)

    # Animated Audio Player Box
    draw.rounded_rectangle([(90, 420), (900, 560)], radius=8, fill=(24, 38, 66), outline=CYAN)
    draw.text((115, 438), "🎙️ Live Audio Stream (Multimodal Direct Feed)", font=font_body_bold, fill=CYAN)
    draw_audio_wave(draw, 115, 475, 750, 40, t, num_bars=32, color=CYAN)

    # Laser Scan Beam sweeping over audio card
    scan_y = int(330 + ((t * 120) % 230))
    draw.line([(90, scan_y), (900, scan_y)], fill=(56, 189, 248), width=2)

    # Typewriter Transcript Effect
    full_transcript = "“10 bori Fortune Chakki Atta, 5 peti Maggi 70g, aur 2 peti woh meetha biscuit jaldi bhija dena...”"
    chars_to_show = int(min(t * 22, len(full_transcript)))
    partial_text = full_transcript[:chars_to_show]
    cursor = "|" if int(t * 3) % 2 == 0 else ""
    draw.rounded_rectangle([(90, 580), (900, 710)], radius=8, fill=(15, 23, 42), outline=CARD_BORDER)
    draw.text((115, 600), "LIVE MULTIMODAL TRANSCRIPT:", font=font_small_bold, fill=CYAN)
    draw.text((115, 635), partial_text + cursor, font=font_body, fill=TEXT_WHITE)

    # Regional Units Normalization Card
    draw.rounded_rectangle([(90, 730), (900, 965)], radius=8, fill=(15, 23, 42), outline=CARD_BORDER)
    draw.text((115, 755), "REGIONAL PACKAGING NORMALIZATION:", font=font_body_bold, fill=CYAN)
    units = [
        ("“bori” (Sacks)", "➔ Normalized to 10kg Master Bag", "Packaging: Sacks"),
        ("“peti” (Cartons)", "➔ Normalized to Master Carton (24 Packs)", "Packaging: Carton"),
        ("“meetha biscuit”", "➔ Colloquial Slang ➔ Routing to Layer 1 Memory", "Private Vernacular")
    ]
    uy = 795
    for slang, norm, note in units:
        draw.text((115, uy), slang, font=font_small_bold, fill=AMBER)
        draw.text((310, uy), norm, font=font_small, fill=TEXT_WHITE)
        uy += 45

    # Right: Extracted Structured Order Lines
    draw.rounded_rectangle([(990, 245), (1860, 995)], radius=12, fill=CARD_BG, outline=CYAN, width=2)
    draw.rectangle([(990, 245), (1860, 305)], fill=(18, 38, 65))
    draw.text((1020, 262), "⚡ GEMINI 2.0 FLASH EXTRACTION CORE", font=font_card_header, fill=CYAN)

    # Latency Counter (Clocks down from 500ms to 418ms)
    draw.rounded_rectangle([(1020, 330), (1830, 420)], radius=8, fill=(15, 23, 42), outline=CARD_BORDER)
    curr_lat = max(500 - int(t * 35), 418)
    draw.text((1050, 345), f"{curr_lat} ms", font=font_stat_big, fill=EMERALD)
    draw.text((1280, 350), "End-to-End Extraction Latency", font=font_body_bold, fill=TEXT_WHITE)
    draw.text((1280, 380), "Multimodal audio parsed directly without lossy intermediate speech-to-text.", font=font_small, fill=TEXT_MUTED)

    # 3 Extracted Rows (Staggered Animation)
    rows = [
        (1.5, "Fortune Chakki Atta 10kg", "10 Bags (100kg)", "Adani Wilmar", "99.8%", EMERALD),
        (3.0, "Maggi 2-Minute Noodles 70g", "5 Cartons (120 Pcs)", "Nestle India", "99.2%", EMERALD),
        (4.5, "“meetha biscuit” (Unresolved)", "2 Cartons (48 Pcs)", "Routing to Layer 1", "MEMORY", AMBER)
    ]
    ry = 450
    for trigger_t, product, qty, brand, match_score, badge_c in rows:
        if t >= trigger_t:
            prog = ease_out_cubic((t - trigger_t) / 0.5)
            rx_off = int((1.0 - prog) * 100)
            rx = 1020 + rx_off
            draw.rounded_rectangle([(rx, ry), (rx + 810, ry + 85)], radius=8, fill=(15, 25, 45), outline=CARD_BORDER)
            draw.text((rx + 25, ry + 15), product, font=font_body_bold, fill=TEXT_WHITE)
            draw.text((rx + 25, ry + 48), f"Brand: {brand} • Qty: {qty}", font=font_small, fill=TEXT_MUTED)
            draw.rectangle([(rx + 680, ry + 25), (rx + 785, ry + 60)], fill=badge_c)
            draw.text((rx + 700, ry + 33), match_score, font=font_small_bold, fill=TEXT_WHITE)
        ry += 105

    # Bottom Callout Box
    draw.rounded_rectangle([(1020, 785), (1830, 965)], radius=8, fill=(24, 38, 66), outline=CYAN)
    draw.text((1050, 810), "⚡ DUAL PIPELINE SAFETY:", font=font_body_bold, fill=CYAN)
    draw.text((1050, 845), "• High-confidence items (>85%) map directly to catalogue SKUs.", font=font_body, fill=TEXT_WHITE)
    draw.text((1050, 880), "• Slang and nicknames route instantly to Layer 1 Learned Shorthand.", font=font_body, fill=TEXT_WHITE)
    draw.text((1050, 915), "• Ambiguous items with missing pack sizes trigger Rule R1 Red Gate.", font=font_body_bold, fill=ROSE)

    draw_footer(draw)

def render_frame_scene_4(draw, t, dur):
    # Scene 4: Rule R1 - Never Guess
    draw_topbar(draw, 4, t)
    draw.text((60, 145), "Rule R1: Never Guess — The Ambiguity Safety Gate", font=font_title, fill=TEXT_WHITE)
    draw.text((60, 195), "Generic AI hallucinates when details are missing. NEXORA halts, flags in red, and prevents bad dispatches.", font=font_subtitle, fill=TEXT_MUTED)

    # Left: The Ambiguity Red Gate Card
    pulse = 0.5 + 0.5 * math.sin(t * 4.0)
    red_glow = (int(244 * pulse + 120 * (1 - pulse)), 40, 70)
    draw.rounded_rectangle([(60, 245), (930, 995)], radius=12, fill=CARD_BG, outline=red_glow, width=2)
    draw.rectangle([(60, 245), (930, 305)], fill=(55, 15, 25))
    draw.text((90, 262), "🛑 RULE R1: ZERO GUESSWORK ENFORCED", font=font_card_header, fill=ROSE)

    # Problem Item Box with Pulsing Red Hazard Border
    draw.rounded_rectangle([(90, 335), (900, 485)], radius=8, fill=(35, 15, 20), outline=ROSE, width=2)
    draw.text((115, 355), "LINE ITEM 04: AMBIGUOUS PACK SIZE DETECTED", font=font_small_bold, fill=ROSE)
    draw.text((115, 388), "Raw Spoken: “10 packet Tata Tea Gold bhej do”", font=font_body_bold, fill=TEXT_WHITE)
    draw.text((115, 420), "Product: Tata Tea Gold  |  Quantity: 10  |  Pack Size: NULL", font=font_small, fill=TEXT_MUTED)
    draw.text((115, 448), "Available Packs in Warehouse: 250g (₹140) • 500g (₹270) • 1kg (₹520)", font=font_small_bold, fill=AMBER)

    # Padlock Animation: Closes at t=1.0s
    draw.rounded_rectangle([(90, 510), (900, 640)], radius=8, fill=(20, 10, 15), outline=CARD_BORDER)
    draw.text((180, 535), "🔒 POSTGRESQL DATABASE TRIGGER ACTIVE", font=font_body_bold, fill=ROSE)
    draw.text((180, 570), "Trigger: trg_prevent_unresolved_approval", font=font_small_bold, fill=TEXT_WHITE)
    draw.text((180, 598), "Unconditionally blocks INSERT into orders table while red lines exist.", font=font_small, fill=TEXT_MUTED)
    # Big Lock Icon
    draw.rectangle([(120, 545), (155, 595)], fill=ROSE)
    draw.ellipse([(127, 525), (148, 555)], outline=ROSE, width=3)

    # Generic AI vs NEXORA
    draw.rounded_rectangle([(90, 665), (900, 965)], radius=8, fill=(15, 23, 42), outline=CARD_BORDER)
    draw.text((115, 690), "WHY GENERIC AI FAILS IN WHOLESALE:", font=font_body_bold, fill=TEXT_WHITE)
    comparisons = [
        ("❌ Generic Bots Guess:", "Silently picks 500g. Distributor dispatches ₹2,700 of wrong stock. Retailer rejects delivery at dock."),
        ("✅ NEXORA Halts:", "Rule R1 locks the gate. Zero guesses. Confidence is strictly verified server-side on every PATCH."),
        ("🛡️ Immutable Audit:", "Records ambiguity event and prevents unauthorized overrides until clerk confirms.")
    ]
    cy = 730
    for title, desc in comparisons:
        draw.text((115, cy), title, font=font_small_bold, fill=ROSE if "❌" in title else EMERALD)
        draw.text((115, cy + 24), desc[:85], font=font_small, fill=TEXT_BODY)
        draw.text((115, cy + 46), desc[85:], font=font_small, fill=TEXT_BODY)
        cy += 75

    # Right: WhatsApp Clarification Assistant
    draw.rounded_rectangle([(990, 245), (1860, 995)], radius=12, fill=CARD_BG, outline=CARD_BORDER, width=2)
    draw.rectangle([(990, 245), (1860, 305)], fill=(20, 35, 60))
    draw.text((1020, 262), "📲 1-CLICK WHATSAPP CLARIFICATION ASSISTANT", font=font_card_header, fill=CYAN)

    draw.text((1020, 335), "Auto-Drafted Clarification (Hinglish):", font=font_body_bold, fill=TEXT_WHITE)

    # Chat Bubble
    draw.rounded_rectangle([(1020, 375), (1830, 540)], radius=10, fill=(18, 52, 40), outline=EMERALD)
    draw.text((1050, 395), "To: Gupta Kirana Stores (+91 98765 43210)", font=font_small_bold, fill=CYAN)
    draw.text((1050, 430), "“Namaste Gupta ji! 🙏", font=font_body, fill=TEXT_WHITE)
    draw.text((1050, 460), " Tata Tea Gold mein kaun sa pack bhejna hai - 250g ya 500g?", font=font_body, fill=TEXT_WHITE)
    draw.text((1050, 490), " Dono ka fresh stock warehouse mein ready hai.”", font=font_body, fill=TEXT_WHITE)

    # Button States & Animated Mouse Cursor Click
    # Cursor starts at (1500, 800) and moves to button at (1220, 605)
    click_t = 6.0
    btn_clicked = (t >= click_t)
    btn_bg = (16, 185, 129) if not btn_clicked else (22, 101, 52)
    btn_label = "✓ Send WhatsApp (1-Click)" if not btn_clicked else "✓ Dispatched via WhatsApp API"

    draw.rounded_rectangle([(1020, 570), (1420, 635)], radius=8, fill=btn_bg, outline=EMERALD)
    draw.text((1050, 592), btn_label, font=font_body_bold, fill=TEXT_WHITE)

    draw.rounded_rectangle([(1450, 570), (1830, 635)], radius=8, fill=(30, 41, 59), outline=CARD_BORDER)
    draw.text((1480, 592), "✏️ Edit Pack Manually", font=font_body_bold, fill=TEXT_BODY)

    # Shockwave ripple when clicked
    if btn_clicked and t < click_t + 1.2:
        ripple_r = int((t - click_t) * 90)
        draw.ellipse([(1220 - ripple_r, 602 - ripple_r), (1220 + ripple_r, 602 + ripple_r)], outline=EMERALD, width=2)

    # Cursor Path
    if t < 10.0:
        c_prog = ease_in_out(min(t / click_t, 1.0))
        cur_x = lerp(1600, 1220, c_prog)
        cur_y = lerp(750, 605, c_prog)
        draw_cursor(draw, cur_x, cur_y, clicking=(click_t <= t < click_t + 0.4))

    # Resolution Steps
    draw.rounded_rectangle([(1020, 670), (1830, 965)], radius=8, fill=(15, 23, 42), outline=CARD_BORDER)
    draw.text((1050, 695), "CLERK RESOLUTION WORKFLOW:", font=font_body_bold, fill=CYAN)
    steps = [
        "1. Retailer replies on WhatsApp: '500g wala bhejo'.",
        "2. Line immediately flips from 🔴 RED to 🟢 GREEN.",
        "3. Price & GST recomputed: 10 packs × ₹270 = ₹2,700.",
        "4. Live stock check: 10 packs ≤ 48 packs in warehouse stock.",
        "5. Database approval lock releases automatically."
    ]
    sy = 735
    for s in steps:
        draw.text((1050, sy), s, font=font_body, fill=TEXT_WHITE if "🟢" in s else TEXT_BODY)
        sy += 42

    draw_footer(draw)

def render_frame_scene_5(draw, t, dur):
    # Scene 5: Learned Shorthand Memory Engine
    draw_topbar(draw, 5, t)
    draw.text((60, 145), "Layer 1: Learned Shorthand (Retailer Vernacular Memory)", font=font_title, fill=TEXT_WHITE)
    draw.text((60, 195), "Retailers have nicknames. NEXORA remembers them forever with strict tenant and retailer isolation.", font=font_subtitle, fill=TEXT_MUTED)

    # Left: Shorthand Memory Table
    draw.rounded_rectangle([(60, 245), (1050, 995)], radius=12, fill=CARD_BG, outline=CYAN, width=2)
    draw.rectangle([(60, 245), (1050, 305)], fill=(18, 38, 65))
    draw.text((90, 262), "🧠 RETAILER-SPECIFIC LEARNED MEMORY MAP", font=font_card_header, fill=CYAN)

    draw.text((90, 330), "Retailer: Gupta Kirana Stores • Tenant: Singhania & Sons", font=font_body_bold, fill=TEXT_WHITE)

    # Synaptic Mapping Animation: Left node -> Wire -> Right node
    draw.rounded_rectangle([(90, 375), (420, 465)], radius=8, fill=(35, 30, 20), outline=AMBER)
    draw.text((115, 395), "SLANG PHRASE:", font=font_small_bold, fill=AMBER)
    draw.text((115, 425), "“meetha biscuit”", font=font_body_bold, fill=TEXT_WHITE)

    # Animated Energy Wire
    draw.line([(420, 420), (680, 420)], fill=CYAN, width=3)
    draw_particles(draw, 420, 420, 680, 420, t, count=4, color=CYAN)

    draw.rounded_rectangle([(680, 375), (1020, 465)], radius=8, fill=(15, 35, 25), outline=EMERALD)
    draw.text((705, 395), "CANONICAL CATALOGUE SKU:", font=font_small_bold, fill=EMERALD)
    draw.text((705, 425), "Britannia Good Day 75g", font=font_body_bold, fill=TEXT_WHITE)

    # Memory Table Rows
    draw.rectangle([(90, 495), (1020, 535)], fill=(15, 23, 42))
    draw.text((110, 508), "COLLOQUIAL NICKNAME", font=font_small_bold, fill=TEXT_MUTED)
    draw.text((450, 508), "MAPPED CATALOGUE SKU", font=font_small_bold, fill=TEXT_MUTED)
    draw.text((850, 508), "CONFIDENCE", font=font_small_bold, fill=TEXT_MUTED)

    memory_rows = [
        ("“laal sabun”", "Lifebuoy Total Red 125g (Peti)", "100% (Confirmed)"),
        ("“chhoti maggi”", "Maggi 2-Min 70g Single Pack", "100% (Confirmed)"),
        ("“kala tel”", "Navratna Ayurvedic 100ml", "100% (Confirmed)"),
        ("“5 no. chawal”", "India Gate Basmati Dubar 25kg", "100% (Confirmed)")
    ]
    my = 545
    for phrase, sku, conf in memory_rows:
        draw.rectangle([(90, my), (1020, my + 55)], fill=(15, 25, 45), outline=CARD_BORDER)
        draw.text((110, my + 16), phrase, font=font_body_bold, fill=AMBER)
        draw.text((450, my + 16), sku, font=font_body, fill=TEXT_WHITE)
        draw.text((850, my + 16), "100%", font=font_small_bold, fill=EMERALD)
        my += 65

    # Memory Architecture explanation
    draw.rounded_rectangle([(90, 825), (1020, 965)], radius=8, fill=(15, 23, 42), outline=CARD_BORDER)
    draw.text((115, 845), "SELF-LEARNING REINFORCEMENT:", font=font_body_bold, fill=CYAN)
    draw.text((115, 880), "• First time: Clerk resolves 'meetha biscuit' to Britannia Good Day.", font=font_small, fill=TEXT_WHITE)
    draw.text((115, 908), "• Committed to retailer_aliases with composite tenant foreign keys.", font=font_small, fill=TEXT_BODY)
    draw.text((115, 936), "• Future orders match with 100% confidence. Zero clerk edits needed.", font=font_small_bold, fill=EMERALD)

    # Right: The Self-Learning Advantage
    draw.rounded_rectangle([(1110, 245), (1860, 995)], radius=12, fill=CARD_BG, outline=CARD_BORDER, width=2)
    draw.rectangle([(1110, 245), (1860, 305)], fill=(20, 35, 60))
    draw.text((1140, 262), "⚡ THE SELF-LEARNING ADVANTAGE", font=font_card_header, fill=CYAN)

    # Circular Confidence Meter Animating: 50% -> 85% -> 100%
    draw.rounded_rectangle([(1140, 335), (1830, 485)], radius=8, fill=(15, 23, 42), outline=CARD_BORDER)
    conf_val = min(50 + int(t * 10), 100)
    draw.text((1170, 370), f"{conf_val}%", font=font_stat_big, fill=EMERALD)
    draw.text((1350, 370), "Memory Confidence Score", font=font_body_bold, fill=TEXT_WHITE)
    draw.text((1350, 408), "Layer 1 memory match bypasses LLM latency, cost, and hallucination.", font=font_small, fill=TEXT_MUTED)

    # Tenant Isolation Shield
    draw.rounded_rectangle([(1140, 510), (1830, 750)], radius=8, fill=(15, 23, 42), outline=CARD_BORDER)
    draw.text((1170, 535), "🔒 STRICT MULTI-TENANT PRIVACY", font=font_body_bold, fill=CYAN)
    privacy_points = [
        "• Aliases are strictly scoped to one retailer and one tenant distributor.",
        "• Competing wholesalers on NEXORA never see your retailer's nicknames.",
        "• Clerks can manually add, edit, or test shorthand phrases from the UI.",
        "• Owners can delete or reset learned aliases at any time."
    ]
    py2 = 575
    for pp in privacy_points:
        draw.text((1170, py2), pp, font=font_small, fill=TEXT_BODY)
        py2 += 40

    # Sub-millisecond B-Tree Lookup
    draw.rounded_rectangle([(1140, 775), (1830, 965)], radius=8, fill=(24, 38, 66), outline=CYAN)
    draw.text((1170, 805), "0.04 ms", font=font_stat_big, fill=CYAN)
    draw.text((1400, 810), "Layer 1 Lookup Latency", font=font_body_bold, fill=TEXT_WHITE)
    draw.text((1400, 845), "Indexed directly in PostgreSQL B-Tree cache.", font=font_small, fill=TEXT_MUTED)
    draw.text((1170, 910), "Every repeat order gets processed faster than the last.", font=font_body_bold, fill=EMERALD)

    draw_footer(draw)

def render_frame_scene_6(draw, t, dur):
    # Scene 6: Rule R2 - Human Approval & ERP Sync
    draw_topbar(draw, 6, t)
    draw.text((60, 145), "Rule R2: 1-Click Human Approval & Instant ERP Sync", font=font_title, fill=TEXT_WHITE)
    draw.text((60, 195), "Orders exist in accounting only after a clerk approves. 1-click sync to Tally, Vyapar, and warehouse pick lists.", font=font_subtitle, fill=TEXT_MUTED)

    # Left: Active Draft Review Screen (All Green)
    draw.rounded_rectangle([(60, 245), (1150, 995)], radius=12, fill=CARD_BG, outline=EMERALD, width=2)
    draw.rectangle([(60, 245), (1150, 305)], fill=(15, 45, 30))
    draw.text((90, 262), "📋 ORDER DRAFT #ORD-2026-0842 • 100% VERIFIED", font=font_card_header, fill=EMERALD)

    # Metadata bar
    draw.rectangle([(90, 330), (1120, 380)], fill=(15, 23, 42))
    draw.text((110, 345), "Customer: Gupta Kirana Stores • Reviewer: Rahul Verma", font=font_small_bold, fill=TEXT_WHITE)
    draw.text((850, 345), "STATUS: ALL LINES GREEN", font=font_small_bold, fill=EMERALD)

    # Verified Rows
    v_lines = [
        ("Fortune Chakki Atta 10kg", "10 Bags", "₹420.00", "₹4,200.00", "Stock: 140 Bags"),
        ("Maggi 2-Min Noodles 70g", "5 Cartons (120)", "₹720.00", "₹3,600.00", "Stock: 85 Cartons"),
        ("Britannia Good Day 75g", "2 Cartons (48)", "₹960.00", "₹1,920.00", "Stock: 40 Cartons")
    ]
    vy = 400
    for item, qty, price, total, stock in v_lines:
        draw.rectangle([(90, vy), (1120, vy + 60)], fill=(15, 25, 45), outline=CARD_BORDER)
        draw.ellipse([(110, vy + 24), (122, vy + 36)], fill=EMERALD)
        draw.text((135, vy + 18), item, font=font_body_bold, fill=TEXT_WHITE)
        draw.text((540, vy + 20), qty, font=font_small, fill=CYAN)
        draw.text((680, vy + 20), stock, font=font_small, fill=TEXT_MUTED)
        draw.text((840, vy + 20), price, font=font_small, fill=TEXT_BODY)
        draw.text((980, vy + 18), total, font=font_body_bold, fill=TEXT_WHITE)
        vy += 75

    # Financial Total rolling up: 0 -> 10,206
    draw.rounded_rectangle([(90, 645), (1120, 770)], radius=8, fill=(15, 23, 42), outline=CARD_BORDER)
    draw.text((115, 665), "Subtotal: ₹9,720.00  |  GST (5%): ₹486.00", font=font_body, fill=TEXT_MUTED)
    total_val = min(int(t * 1500), 10206)
    draw.text((115, 700), f"Invoice Grand Total: ₹{total_val:,}.00", font=font_title, fill=EMERALD)
    draw.text((820, 710), "Terms: 7-Day Credit OK", font=font_small_bold, fill=CYAN)

    # Big 1-Click Approve Button
    approve_t = 6.0
    approved = (t >= approve_t)
    btn_bg2 = (22, 101, 52) if not approved else (16, 185, 129)
    btn_txt = "✅ APPROVE & COMMIT ORDER (RULE R2)" if not approved else "✅ ORDER APPROVED & COMMITTED"

    draw.rounded_rectangle([(90, 800), (1120, 890)], radius=10, fill=btn_bg2, outline=EMERALD, width=2)
    draw.text((340, 825), btn_txt, font=font_card_header, fill=TEXT_WHITE)
    draw.text((430, 860), "1-Click Human Approval • Database Record Locked", font=font_small, fill=CYAN)

    # Animated Cursor clicking Approve button
    if t < 9.0:
        c_prog = ease_in_out(min(t / approve_t, 1.0))
        cx = lerp(800, 600, c_prog)
        cy = lerp(950, 840, c_prog)
        draw_cursor(draw, cx, cy, clicking=(approve_t <= t < approve_t + 0.4))

    # Right: Instant ERP Export Streams
    draw.rounded_rectangle([(1200, 245), (1860, 995)], radius=12, fill=CARD_BG, outline=CARD_BORDER, width=2)
    draw.rectangle([(1200, 245), (1860, 305)], fill=(20, 35, 60))
    draw.text((1230, 262), "🚀 INSTANT ERP INTEGRATIONS", font=font_card_header, fill=CYAN)

    # 3 Export Cards shooting out after approval
    exports = [
        ("📄 Tally Prime XML Voucher", "Standardized Sales Voucher format.", "1-click direct voucher import."),
        ("📊 Vyapar / Busy JSON API", "REST ledger & invoice webhook.", "Automatic customer balance update."),
        ("📑 Warehouse Pick-List CSV", "Optimized bin-location order.", "Ready for loading dock pickers."),
        ("📜 Immutable Audit Log", "Clerk ID, timestamp, before/after.", "100% audit log compliance.")
    ]
    ey2 = 335
    for exp_title, exp_d1, exp_d2 in exports:
        draw.rounded_rectangle([(1230, ey2), (1830, ey2 + 95)], radius=8, fill=(15, 23, 42), outline=CARD_BORDER)
        draw.text((1255, ey2 + 15), exp_title, font=font_body_bold, fill=TEXT_WHITE)
        draw.text((1255, ey2 + 45), exp_d1, font=font_small, fill=TEXT_BODY)
        draw.text((1255, ey2 + 68), exp_d2, font=font_small, fill=TEXT_MUTED)
        ey2 += 115

    # 12 Seconds Comparison Stat
    draw.rounded_rectangle([(1230, 830), (1830, 965)], radius=8, fill=(24, 38, 66), outline=EMERALD)
    draw.text((1255, 855), "12 SECONDS", font=font_stat_big, fill=EMERALD)
    draw.text((1580, 860), "Total Clerk Review Time", font=font_body_bold, fill=TEXT_WHITE)
    draw.text((1580, 895), "Down from 4.2 minutes manual retyping (95% time reduction).", font=font_small, fill=TEXT_MUTED)

    draw_footer(draw)

def render_frame_scene_7(draw, t, dur):
    # Scene 7: Enterprise Foundation & Vision
    draw_topbar(draw, 7, t)
    draw.text((60, 145), "Enterprise Foundation: Built for High-Volume Wholesale", font=font_title, fill=TEXT_WHITE)
    draw.text((60, 195), "Strict PostgreSQL Row Level Security, Argon2id authentication, RBAC, and immutable audit logs.", font=font_subtitle, fill=TEXT_MUTED)

    # 4 Enterprise Security Pillar Cards (2x2 Grid)
    pillars = [
        ("🔒 MULTI-TENANT ISOLATION (RLS)", [
            "• PostgreSQL Row Level Security enforced on all 11 core tables.",
            "• Session tenant parameter enforced in every connection context.",
            "• Complete cross-tenant data isolation guaranteed at engine level.",
            "• Distributorship data strictly isolated from competing distributors."
        ], (20, 35, 60), CYAN),

        ("🛡️ ENTERPRISE AUTHENTICATION", [
            "• Argon2id password hashing with modern memory & salt parameters.",
            "• SameSite=Strict HttpOnly session cookies.",
            "• Double-submit CSRF token validation on all state-changing routes.",
            "• Automatic brute-force login rate limiting & temporary lockouts."
        ], (15, 45, 30), EMERALD),

        ("👥 ROLE-BASED ACCESS CONTROL (RBAC)", [
            "• Strict Clerk vs Owner permission enforcement on all API routes.",
            "• Clerks receive, review, fix, and approve incoming order drafts.",
            "• Owners manage users, reset passwords, and edit catalogue/pricing.",
            "• Clerk blocked with HTTP 403 on any administrative route."
        ], (45, 35, 15), AMBER),

        ("📜 IMMUTABLE AUDIT TRAIL", [
            "• Append-only audit_events log: zero UPDATE or DELETE allowed.",
            "• Records every voice ingestion, manual edit, approval, and export.",
            "• Stores actor ID, client IP, action type, and before/after JSON diffs.",
            "• Meets strict regulatory and financial wholesale compliance requirements."
        ], (40, 20, 50), INDIGO),
    ]

    coords = [
        (60, 250, 930, 595),
        (990, 250, 1860, 595),
        (60, 625, 930, 920),
        (990, 625, 1860, 920),
    ]

    for (p_title, p_lines, p_bg, p_accent), (x1, y1, x2, y2) in zip(pillars, coords):
        draw.rounded_rectangle([(x1, y1), (x2, y2)], radius=12, fill=CARD_BG, outline=p_accent, width=2)
        draw.rectangle([(x1, y1), (x2, y1 + 55)], fill=p_bg)
        draw.text((x1 + 25, y1 + 16), p_title, font=font_card_header, fill=p_accent)
        
        py = y1 + 75
        for l in p_lines:
            draw.text((x1 + 25, py), l, font=font_body, fill=TEXT_BODY)
            py += 36

    # Test Suite Status Bar Sweeping across bottom
    draw.rounded_rectangle([(60, 940), (1860, 1005)], radius=8, fill=(15, 23, 42), outline=CARD_BORDER)
    test_prog = min(t / (dur * 0.5), 1.0)
    bar_w = int(1780 * test_prog)
    draw.rounded_rectangle([(70, 950), (70 + bar_w, 995)], radius=6, fill=(22, 101, 52))
    draw.text((95, 960), "✓ 25/25 AUTOMATED TESTS PASSING • MULTI-TENANT ISOLATION • ROLE CHECKS • AUDIT VERIFIED", font=font_body_bold, fill=TEXT_WHITE)

    draw_footer(draw)

SCENE_FRAME_RENDERERS = {
    1: render_frame_scene_1,
    2: render_frame_scene_2,
    3: render_frame_scene_3,
    4: render_frame_scene_4,
    5: render_frame_scene_5,
    6: render_frame_scene_6,
    7: render_frame_scene_7,
}

def get_audio_duration(audio_file):
    res = subprocess.check_output([
        FFPROBE, "-i", audio_file,
        "-show_entries", "format=duration", "-v", "quiet", "-of", "csv=p=0"
    ]).decode().strip()
    return float(res)

def generate_scene_clip(scene_id, audio_file, output_clip):
    dur = get_audio_duration(audio_file)
    fps = 30
    total_frames = int(dur * fps)
    print(f"Scene {scene_id}: duration {dur:.2f}s ({total_frames} frames at {fps} fps)...", flush=True)
    
    # FFmpeg Pipe process without -shortest to avoid early pipe closure
    cmd = [
        FFMPEG, "-y",
        "-f", "rawvideo",
        "-pix_fmt", "rgb24",
        "-s", "1920x1080",
        "-r", str(fps),
        "-i", "-",
        "-i", audio_file,
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-t", f"{dur:.2f}",
        output_clip
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    renderer = SCENE_FRAME_RENDERERS[scene_id]
    base_frame = Image.new("RGB", (1920, 1080), BG_DARK)
    
    try:
        for f in range(total_frames):
            t = f / fps
            img = base_frame.copy()
            draw = ImageDraw.Draw(img)
            renderer(draw, t, dur)
            proc.stdin.write(img.tobytes())
    except (BrokenPipeError, IOError):
        pass
    finally:
        try:
            proc.stdin.close()
        except (BrokenPipeError, IOError):
            pass
        proc.wait()

    print(f"Generated clip {scene_id}: {output_clip} ({os.path.getsize(output_clip):,} bytes)", flush=True)

def main():
    print("=== NEXORA STARTUP PITCH ANIMATION VIDEO GENERATION ===")
    
    clip_files = []
    for sid in range(1, 8):
        audio_file = os.path.join(AUDIO_DIR, f"scene_{sid}.mp3")
        clip_file = os.path.join(BUILD_DIR, f"scene_{sid}_animated.mp4")
        if os.path.exists(clip_file) and os.path.getsize(clip_file) > 200000:
            print(f"Scene {sid} clip already exists ({os.path.getsize(clip_file):,} bytes), skipping render.", flush=True)
        else:
            generate_scene_clip(sid, audio_file, clip_file)
        clip_files.append(clip_file)
        
    # Concatenate all 7 clips
    print("\n--- Concatenating 7 Scenes into Master Presentation Video ---")
    concat_list = os.path.join(BUILD_DIR, "concat_list.txt")
    with open(concat_list, "w") as f:
        for c in clip_files:
            f.write(f"file '{c}'\n")
            
    concat_cmd = [
        FFMPEG, "-y",
        "-f", "concat", "-safe", "0",
        "-i", concat_list,
        "-c", "copy",
        OUTPUT_MP4
    ]
    subprocess.check_call(concat_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"Generated master MP4: {OUTPUT_MP4} ({os.path.getsize(OUTPUT_MP4):,} bytes)")

    # Copy to frontend/dist/demo-video.mp4 and root nexora_demo_walkthrough.mp4
    import shutil
    shutil.copyfile(OUTPUT_MP4, FRONTEND_DIST_MP4)
    shutil.copyfile(OUTPUT_MP4, ROOT_DEMO_MP4)
    print(f"Copied to frontend: {FRONTEND_DIST_MP4}")
    print(f"Copied to root: {ROOT_DEMO_MP4}")

    total_dur = get_audio_duration(OUTPUT_MP4)
    print(f"\nSUCCESS! Startup Presentation Video rendered successfully.")
    print(f"Total Runtime: {int(total_dur // 60)}m {int(total_dur % 60)}s ({total_dur:.2f}s)")
    print(f"Framerate: 30 FPS Full HD (1920x1080)")
    print(f"Voice: Microsoft Edge Neural TTS (en-US-ChristopherNeural)")

if __name__ == "__main__":
    main()
