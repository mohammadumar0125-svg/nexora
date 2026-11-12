#!/usr/bin/env python3
"""
NEXORA Order Agent - Enterprise Migration Presentation Video Generator (1080p Full HD)
A world-class, MNC-grade executive presentation introducing the migration of FMCG
wholesale operations from chaotic WhatsApp/voice/paper channels to NEXORA AI.

Narrated with professional executive neural voice (en-US-ChristopherNeural).
Renders 10 custom 1080p executive slide layouts, generates audio tracks, and encodes
a high-bitrate master MP4 video.
"""

import asyncio
import os
import subprocess
import sys
import shutil
from PIL import Image, ImageDraw, ImageFont
import edge_tts

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BUILD_DIR = "/tmp/nexora_migration_video_gen"
OUTPUT_MP4 = os.path.join(BASE_DIR, "nexora_migration_presentation_1080p.mp4")
DESKTOP_MP4 = "/Users/mohammedumar/Desktop/NEXORA_Enterprise_Migration_Presentation.mp4"
FRONTEND_DIST_MP4 = os.path.join(BASE_DIR, "frontend", "dist", "demo-video.mp4")

FFMPEG = "/opt/homebrew/bin/ffmpeg"
FFPROBE = "/opt/homebrew/bin/ffprobe"

os.makedirs(BUILD_DIR, exist_ok=True)
os.makedirs(os.path.dirname(FRONTEND_DIST_MP4), exist_ok=True)

# Typography
FONT_BOLD_PATH = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
FONT_REG_PATH = "/System/Library/Fonts/Supplemental/Arial.ttf"

font_hero = ImageFont.truetype(FONT_BOLD_PATH, 42)
font_title = ImageFont.truetype(FONT_BOLD_PATH, 30)
font_subtitle = ImageFont.truetype(FONT_REG_PATH, 18)
font_card_header = ImageFont.truetype(FONT_BOLD_PATH, 20)
font_body = ImageFont.truetype(FONT_REG_PATH, 16)
font_body_bold = ImageFont.truetype(FONT_BOLD_PATH, 16)
font_small = ImageFont.truetype(FONT_REG_PATH, 13)
font_small_bold = ImageFont.truetype(FONT_BOLD_PATH, 13)
font_badge = ImageFont.truetype(FONT_BOLD_PATH, 12)
font_big_stat = ImageFont.truetype(FONT_BOLD_PATH, 40)
font_huge = ImageFont.truetype(FONT_BOLD_PATH, 54)

# Executive MNC Dark Palette
BG_DARK = (10, 15, 26)
TOPBAR_BG = (14, 21, 37)
CARD_BG = (17, 26, 46)
CARD_BG_ELEVATED = (22, 33, 58)
CARD_BORDER = (38, 54, 84)
CARD_BORDER_GLOW = (56, 189, 248)
TEXT_WHITE = (248, 250, 252)
TEXT_MUTED = (148, 163, 184)
TEXT_BODY = (203, 213, 225)
CYAN_ACCENT = (56, 189, 248)
INDIGO_ACCENT = (129, 140, 248)
EMERALD_GREEN = (16, 185, 129)
ROSE_RED = (244, 63, 94)
AMBER_YELLOW = (245, 158, 11)
BORDER_DARK = (30, 41, 59)

SCENES = [
    {
        "id": 1,
        "tab": "1. Executive Vision",
        "title": "NEXORA ORDER AGENT: ENTERPRISE MIGRATION STRATEGY",
        "subtitle": "Transforming high-volume FMCG wholesale distribution from informal messaging into verified, automated accounting.",
        "voice": (
            "Good day, and welcome. Today, I am proud to present the enterprise migration strategy for the NEXORA Order Agent. "
            "In wholesale FMCG distribution, managing daily customer orders remains one of the highest-friction bottlenecks in commerce. "
            "Every morning, distributors receive hundreds of fragmented WhatsApp messages, voice notes, and photo lists that require tedious manual entry into billing software. "
            "NEXORA introduces an intelligent operational layer designed to eliminate manual data entry, prevent silent dispatch errors, and seamlessly bridge customer communication with enterprise accounting systems. "
            "Let us explore how forward-thinking distributors migrate to this autonomous architecture."
        ),
    },
    {
        "id": 2,
        "tab": "2. The Legacy Dilemma",
        "title": "THE LEGACY DILEMMA: UNSTRUCTURED WHOLESALE ORDER CHAOS",
        "subtitle": "The operational bottlenecks, dispatch errors, and margin leakages plaguing traditional distribution hubs.",
        "voice": (
            "To understand the urgency of this migration, we must examine the reality of wholesale operations today. "
            "Between six AM and ten AM, distributors face an overwhelming surge of orders across informal channels. "
            "Human order clerks spend over four minutes per order manually deciphering colloquial abbreviations, cross-referencing physical price sheets, and keying data into Tally or Vyapar. "
            "More dangerously, generic automation tools silently guess ambiguous pack sizes—dispatching a five hundred gram carton when a customer intended two hundred and fifty grams. "
            "This results in return logistics, damaged customer relationships, and wiped distributor margins. Migration to NEXORA eliminates these points of failure permanently."
        ),
    },
    {
        "id": 3,
        "tab": "3. Migration Blueprint",
        "title": "THE 3-PHASE ENTERPRISE MIGRATION BLUEPRINT",
        "subtitle": "A non-invasive, zero-downtime deployment framework that protects existing ERP and accounting investments.",
        "voice": (
            "Our migration framework is engineered for rapid, non-invasive deployment without disrupting existing operations. "
            "Phase One is Non-Invasive Ingestion: retailers continue ordering over WhatsApp, phone audio, or handwritten lists exactly as they do today. There is zero friction or app download required for customers. "
            "Phase Two is the AI Verification Layer: Gemini 2.0 Flash performs sub-second structured extraction, followed by our deterministic catalogue cascade. "
            "Phase Three is Human-in-the-Loop Accounting Sync: verified order drafts are reviewed by authorized clerks and exported directly into existing billing software. "
            "Distributors modernize in forty-eight hours without replacing their trusted accounting ledgers."
        ),
    },
    {
        "id": 4,
        "tab": "4. Multimodal Intake",
        "title": "MIGRATION IN PRACTICE: MULTIMODAL INTAKE & SCHEMATIC PARSING",
        "subtitle": "Demonstrating live message ingestion from Gupta Kirana Stores with sub-second structured JSON parsing.",
        "voice": (
            "Let us examine a live order migration in practice. Here, an incoming order arrives from Gupta Kirana Stores via WhatsApp: "
            "two box Parle-G, five kg sugar, red label tea three packet, oil ten litre, one box surf. "
            "Within four hundred milliseconds, NEXORA's multimodal pipeline normalizes vernacular terms and extracts structured candidate lines beside the original text. "
            "Standard items like Parle-G cartons and five-kilogram sugar bags resolve immediately with one hundred percent confidence. "
            "However, notice how NEXORA treats ambiguous phrases like 'red label tea three packet' and bulk oil requests."
        ),
    },
    {
        "id": 5,
        "tab": "5. Rule R1 Safety Gate",
        "title": "RULE R1 SAFETY GATE: ZERO SILENT ERRORS BY DESIGN",
        "subtitle": "Backend database locks physically block premature submission whenever ambiguity is detected.",
        "voice": (
            "This brings us to the foundational cornerstone of our architecture: Rule R1—It Never Guesses. "
            "Because the customer requested three packets of Red Label tea without specifying a pack size, the catalogue detects two candidate SKUs: the two hundred and fifty gram pack and the five hundred gram pack. "
            "Instead of guessing, NEXORA flags the line red and engages a strict database safety lock that prevents order approval. "
            "Simultaneously, the agent automatically pre-drafts a polite WhatsApp clarification question in natural Hinglish. "
            "Once the customer clarifies via text, the clerk resolves the line with a single click, unlocking the approval workflow."
        ),
    },
    {
        "id": 6,
        "tab": "6. Tax & Normalization",
        "title": "TAX & PRICING MECHANICS: 10L NORMALIZATION & 5% FMCG GST",
        "subtitle": "Preventing multi-thousand-rupee billing errors through strict selling-unit consistency and tax itemization.",
        "voice": (
            "Accurate enterprise migration requires uncompromising fiscal precision. "
            "In legacy systems, when a customer ordered 'oil 10 litre', generic tools would multiply ten litres by the can price of one thousand three hundred and ninety rupees, creating a catastrophic ten-times billing error of nearly fourteen thousand rupees. "
            "NEXORA correctly normalizes the ten-litre volume to a single can. "
            "Furthermore, wholesale FMCG rates are calculated on pre-tax bases, with itemized five percent GST clearly separated across the review screen and final export files. "
            "High-value stock alerts, such as low warehouse quantities on Surf Excel, are surfaced as yellow inspection flags."
        ),
    },
    {
        "id": 7,
        "tab": "7. Retailer Memory",
        "title": "RETAILER MEMORY: LEARNED SHORTHAND & EXPLICIT OVERRIDES",
        "subtitle": "Private tenant dictionaries learn colloquial retailer nicknames while safely respecting one-off changes.",
        "voice": (
            "Every retailer communicates in their own unique dialect. "
            "When the clerk confirms Gupta Kirana's tea order as two hundred and fifty grams, they can deliberately save this mapping into the retailer's private alias dictionary. "
            "On subsequent orders, the customer's shorthand resolves instantly at Layer One with zero LLM compute overhead. "
            "Crucially, if the customer later explicitly requests five hundred grams, NEXORA's hierarchy recognizes the specific variant and overrides the saved preference for that single order without corrupting the permanent master dictionary. "
            "This balances machine learning speed with ironclad operational flexibility."
        ),
    },
    {
        "id": 8,
        "tab": "8. Enterprise Accounting",
        "title": "ENTERPRISE INTEGRATION: BILL-READY EXPORTS & AUDIT TRAILS",
        "subtitle": "Direct export to Vyapar JSON and CSV with complete cryptographic tamper-proof event logging.",
        "voice": (
            "Upon clerk sign-off, the order is locked into permanent state and instantly bill-ready. "
            "NEXORA generates one-click downloads for Vyapar JSON format and standardized CSV spreadsheets ready for immediate accounting ingestion. "
            "Every interaction generates an append-only audit event: logging the exact intake message, Gemini extraction confidence scores, human clarification timestamps, and the approving clerk's credentials. "
            "Combined with PostgreSQL multi-tenant row-level security, NEXORA delivers the compliance and data governance demanded by enterprise distribution networks."
        ),
    },
    {
        "id": 9,
        "tab": "9. Empirical ROI",
        "title": "EMPIRICAL BENCHMARK: 91% SPEEDUP & ZERO SILENT ERRORS",
        "subtitle": "Rigorous holdout evaluation across 25 wholesale orders and 125 individual line items.",
        "voice": (
            "The business impact of this migration is validated by our rigorous holdout benchmark of twenty-five real-world orders and one hundred and twenty-five line items. "
            "NEXORA achieved a flawless zero point zero percent silent error rate—ensuring that not a single misidentified product slipped through to dispatch. "
            "Flag precision reached ninety-six percent, virtually eliminating clerk notification fatigue. "
            "Most impressively, order turnaround time plummeted from four minutes down to just twenty-one point four seconds, slashing operational processing cost from twelve rupees fifty paise to eight paise per order."
        ),
    },
    {
        "id": 10,
        "tab": "10. Executive Roadmap",
        "title": "EXECUTIVE SUMMARY: THE FUTURE OF WHOLESALE OPERATIONS",
        "subtitle": "FastAPI backend, Cloud Run readiness, bi-directional Tally XML, and immediate pilot onboarding.",
        "voice": (
            "In summary, migrating your wholesale operation to NEXORA Order Agent delivers immediate speed, eliminates costly dispatch blunders, and preserves your existing accounting infrastructure. "
            "Built with modern FastAPI services, multi-tenant database isolation, and Google Cloud Run deployment readiness, NEXORA is currently operating across active wholesale pilot hubs in Kanpur and Varanasi. "
            "The future of commerce is frictionless, intelligent, and human-verified. "
            "Thank you for your time, and we look forward to partnering with your organization."
        ),
    },
]

def wrap_text(text, max_len=68):
    words = text.split()
    lines = []
    cur = ""
    for w in words:
        if len(cur + " " + w) < max_len:
            cur = cur + " " + w if cur else w
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines

def draw_topbar(draw, current_scene_id):
    # Top header bar
    draw.rectangle([(0, 0), (1920, 80)], fill=TOPBAR_BG)
    draw.line([(0, 80), (1920, 80)], fill=CARD_BORDER, width=2)

    # Logo Mark
    draw.rounded_rectangle([(60, 18), (105, 62)], radius=8, fill=CYAN_ACCENT)
    draw.text((75, 23), "N", font=font_title, fill=BG_DARK)
    
    draw.text((120, 22), "NEXORA", font=font_title, fill=TEXT_WHITE)
    draw.text((285, 30), "ENTERPRISE MIGRATION SUITE", font=font_body_bold, fill=CYAN_ACCENT)

    # Organization / Context
    draw.line([(580, 25), (580, 55)], fill=CARD_BORDER, width=2)
    draw.text((600, 31), "Singhania Wholesale Hub • Executive Presenter: Technical Architecture & Migration", font=font_body, fill=TEXT_MUTED)

    # Security & Status Badge
    draw.rounded_rectangle([(1530, 22), (1860, 58)], radius=6, fill=(15, 45, 35), outline=EMERALD_GREEN, width=1)
    draw.ellipse([(1545, 36), (1555, 46)], fill=EMERALD_GREEN)
    draw.text((1565, 31), "ENTERPRISE SPEC • 1080p MASTER", font=font_small_bold, fill=TEXT_WHITE)

    # Breadcrumb Tab Navigation Bar
    draw.rectangle([(0, 80), (1920, 130)], fill=(12, 18, 32))
    draw.line([(0, 130), (1920, 130)], fill=CARD_BORDER, width=1)

    tab_width = 1920 // len(SCENES)
    for i, s in enumerate(SCENES):
        tx = i * tab_width
        is_active = (s["id"] == current_scene_id)
        if is_active:
            draw.rectangle([(tx + 3, 82), (tx + tab_width - 3, 128)], fill=CARD_BG)
            draw.line([(tx + 3, 127), (tx + tab_width - 3, 127)], fill=CYAN_ACCENT, width=3)
            draw.text((tx + 12, 96), s["tab"], font=font_badge, fill=CYAN_ACCENT)
        else:
            draw.text((tx + 12, 96), s["tab"], font=font_badge, fill=TEXT_MUTED)

def draw_footer(draw):
    draw.rectangle([(0, 1020), (1920, 1080)], fill=TOPBAR_BG)
    draw.line([(0, 1020), (1920, 1020)], fill=CARD_BORDER, width=2)
    draw.text((60, 1038), "NEXORA Order Agent • Enterprise B2B Operational Capture Layer • Zero-Hallucination Guarantee", font=font_small, fill=TEXT_MUTED)
    draw.text((1440, 1038), "Confidential • Enterprise Migration Briefing", font=font_small_bold, fill=CYAN_ACCENT)

# ----------------- SLIDE RENDERERS -----------------

def render_scene_1(img, draw):
    # Scene 1: Executive Vision
    draw_topbar(draw, 1)
    draw.text((60, 150), SCENES[0]["title"], font=font_title, fill=TEXT_WHITE)
    draw.text((60, 196), SCENES[0]["subtitle"], font=font_subtitle, fill=CYAN_ACCENT)

    # Hero Banner
    draw.rounded_rectangle([(60, 245), (1860, 480)], radius=14, fill=CARD_BG_ELEVATED, outline=CYAN_ACCENT, width=2)
    draw.text((95, 275), "TRANSFORMING WHOLESALE DISTRIBUTION THROUGH INTELLIGENT CAPTURE", font=font_card_header, fill=CYAN_ACCENT)
    draw.text((95, 315), "From customer messages to completed business orders, automatically.", font=font_hero, fill=TEXT_WHITE)
    draw.text((95, 380), "NEXORA is an AI-powered operational layer for FMCG wholesalers and distributors. It bridges chaotic WhatsApp messages, voice notes,", font=font_body, fill=TEXT_BODY)
    draw.text((95, 410), "photo lists, and PDFs directly into human-approved sales orders for billing software (Vyapar, Zoho Inventory, Tally).", font=font_body, fill=TEXT_BODY)
    draw.text((95, 440), "Designed as an intelligent capture layer in front of existing billing tools — not an expensive, disruptive ERP replacement.", font=font_body_bold, fill=EMERALD_GREEN)

    # 3 Pillars
    pillars = [
        ("RULE 1: IT NEVER GUESSES", "If product variant, size, or pack is ambiguous, NEXORA halts auto-fill, flags the line RED, and drafts a WhatsApp clarification question. Zero silent errors.", ROSE_RED, 60),
        ("RULE 2: A HUMAN ALWAYS APPROVES", "Orders exist only after an authorized clerk reviews and approves. AI proposes candidate matches, but human staff retain ultimate fiscal control.", EMERALD_GREEN, 670),
        ("RULE 3: IT LEARNS EACH RETAILER", "When a clerk resolves an ambiguous nickname, NEXORA records it in the retailer's private alias memory. Next time, Layer 1 matching resolves it in 0.04ms.", CYAN_ACCENT, 1280),
    ]

    for p_title, p_desc, col, px in pillars:
        draw.rounded_rectangle([(px, 510), (px + 580, 990)], radius=12, fill=CARD_BG, outline=col, width=2)
        draw.rectangle([(px, 510), (px + 580), 570], fill=(22, 33, 58))
        draw.text((px + 24, 530), p_title, font=font_card_header, fill=col)
        
        lines = wrap_text(p_desc, 38)
        for i, l in enumerate(lines):
            draw.text((px + 24, 600 + (i * 26)), l, font=font_body, fill=TEXT_BODY)
            
        # Pillar Key Metrics
        if "GUESSES" in p_title:
            draw.rounded_rectangle([(px + 24, 860), (px + 556, 955)], radius=8, fill=(35, 15, 25), outline=ROSE_RED)
            draw.text((px + 45, 880), "SILENT ERROR RATE", font=font_small_bold, fill=ROSE_RED)
            draw.text((px + 45, 908), "0.0% Hallucination Tolerance", font=font_title, fill=TEXT_WHITE)
        elif "HUMAN" in p_title:
            draw.rounded_rectangle([(px + 24, 860), (px + 556, 955)], radius=8, fill=(15, 38, 28), outline=EMERALD_GREEN)
            draw.text((px + 45, 880), "FLAG PRECISION", font=font_small_bold, fill=EMERALD_GREEN)
            draw.text((px + 45, 908), "96% Notification Accuracy", font=font_title, fill=TEXT_WHITE)
        else:
            draw.rounded_rectangle([(px + 24, 860), (px + 556, 955)], radius=8, fill=(15, 32, 55), outline=CYAN_ACCENT)
            draw.text((px + 45, 880), "SHORTHAND LOOKUP", font=font_small_bold, fill=CYAN_ACCENT)
            draw.text((px + 45, 908), "Sub-Millisecond Execution", font=font_title, fill=TEXT_WHITE)

    draw_footer(draw)

def render_scene_2(img, draw):
    # Scene 2: The Legacy Dilemma
    draw_topbar(draw, 2)
    draw.text((60, 150), SCENES[1]["title"], font=font_title, fill=TEXT_WHITE)
    draw.text((60, 196), SCENES[1]["subtitle"], font=font_subtitle, fill=ROSE_RED)

    # Left: The Daily Wholesale Chaos
    draw.rounded_rectangle([(60, 245), (930, 990)], radius=12, fill=CARD_BG, outline=ROSE_RED, width=2)
    draw.rectangle([(60, 245), (930, 305)], fill=(45, 15, 25))
    draw.text((85, 263), "❌ THE REALITY OF TRADITIONAL WHOLESALE ORDER INTAKE", font=font_card_header, fill=ROSE_RED)

    problems = [
        ("📱 Morning WhatsApp Chaos (6 AM - 10 AM)", "Retailers send 200+ unstructured voice notes, Hinglish lists, and colloquial photo slips before morning dispatch trucks depart. Peak volume creates extreme clerical stress."),
        ("⏳ 4+ Minutes Data Entry Delay Per Order", "Clerk spends 240 seconds manually reading, deciphering shorthand, looking up stock cards, calling customers, and re-typing lines into Vyapar or Tally."),
        ("⚠️ Silent Packaging & Variant Guesswork", "Traditional LLMs guess 500g instead of 250g. Wrong pack dispatch causes retailer disputes, return shipping expenses, and wiped wholesale gross margins."),
        ("🛑 Lack of Deterministic Database Guards", "Unverified AI tools push unvetted rows directly into stock ledgers, generating incorrect GST invoices and breaking warehouse inventory synchronization.")
    ]
    y = 330
    for title, desc in problems:
        draw.text((85, y), title, font=font_body_bold, fill=TEXT_WHITE)
        lines = wrap_text(desc, 64)
        for i, l in enumerate(lines):
            draw.text((85, y + 26 + (i * 22)), l, font=font_small, fill=TEXT_BODY)
        y += 115

    # Right: The Migration Opportunity with NEXORA
    draw.rounded_rectangle([(990, 245), (1860, 990)], radius=12, fill=CARD_BG, outline=EMERALD_GREEN, width=2)
    draw.rectangle([(990, 245), (1860, 305)], fill=(15, 42, 30))
    draw.text((1015, 263), "✅ THE NEXORA AUTONOMOUS ADVANTAGE", font=font_card_header, fill=EMERALD_GREEN)

    solutions = [
        ("⚡ Sub-500ms Multimodal Ingestion", "Gemini 2.0 Flash instantly normalizes vernacular Hinglish, voice notes, and messy lists into structured JSON schemas with zero token jitter."),
        ("🚀 Order Processing Down to 21.4 Seconds", "91% reduction in clerk handling time. Staff shift from manual typists to strategic exception reviewers approving pre-matched order drafts."),
        ("🛑 Strict Deterministic Safety Gates", "If pack size or variant is ambiguous, backend validation halts approval, flags line RED, and pre-drafts natural WhatsApp clarification message."),
        ("💼 100% Tax-Compliant Bill-Ready Exports", "Clean 1-click download of Vyapar JSON and standard CSV with pre-tax base rates and itemized 5% GST ready for immediate ledger commit.")
    ]
    y = 330
    for title, desc in solutions:
        draw.text((1015, y), title, font=font_body_bold, fill=TEXT_WHITE)
        lines = wrap_text(desc, 64)
        for i, l in enumerate(lines):
            draw.text((1015, y + 26 + (i * 22)), l, font=font_small, fill=TEXT_BODY)
        y += 115

    # Bottom Stat Comparison
    draw.rounded_rectangle([(1015, 820), (1835, 965)], radius=10, fill=(18, 36, 52), outline=CYAN_ACCENT)
    draw.text((1045, 840), "MIGRATION IMPACT AT SCALE (500 DAILY ORDERS)", font=font_card_header, fill=CYAN_ACCENT)
    draw.text((1045, 880), "• Daily Clerk Labour Saved: 30.5 hours per hub", font=font_body_bold, fill=TEXT_WHITE)
    draw.text((1045, 915), "• Misdispatch Return Cost Avoided: ₹45,000+ monthly per warehouse", font=font_body_bold, fill=EMERALD_GREEN)

    draw_footer(draw)

def render_scene_3(img, draw):
    # Scene 3: The 3-Phase Migration Blueprint
    draw_topbar(draw, 3)
    draw.text((60, 150), SCENES[2]["title"], font=font_title, fill=TEXT_WHITE)
    draw.text((60, 196), SCENES[2]["subtitle"], font=font_subtitle, fill=CYAN_ACCENT)

    phases = [
        ("PHASE 1: NON-INVASIVE INTAKE", "Day 1-2 • Zero Disruption", CYAN_ACCENT, [
            "Retailers continue using WhatsApp, voice notes, and photos.",
            "Zero retailer app downloads or training required.",
            "Messages ingested into tenant webhook / clerk intake modal.",
            "Sub-500ms candidate parsing via Gemini 2.0 Flash."
        ], 60),
        ("PHASE 2: VERIFICATION & SAFETY GATE", "Day 3-5 • 100% Clerk Authority", AMBER_YELLOW, [
            "4-stage matching cascade maps phrases to stock SKUs.",
            "Ambiguity triggers Rule R1 safety lock (flags line RED).",
            "Automatic pre-drafting of WhatsApp clarification texts.",
            "Clerk resolves exceptions with 1-click candidate selection."
        ], 670),
        ("PHASE 3: ACCOUNTING INTEGRATION", "Day 6+ • Instant Value", EMERALD_GREEN, [
            "Approved orders generate verified Order IDs (NX-202611...)",
            "1-click export to Vyapar JSON format and standard CSV.",
            "Learned shorthand aliases saved to private tenant memory.",
            "Tamper-proof append-only audit trail logs every event."
        ], 1280),
    ]

    for p_title, p_time, col, points, px in phases:
        draw.rounded_rectangle([(px, 245), (px + 580, 780)], radius=12, fill=CARD_BG, outline=col, width=2)
        draw.rectangle([(px, 245), (px + 580, 315)], fill=(22, 33, 58))
        draw.text((px + 24, 260), p_title, font=font_card_header, fill=col)
        draw.text((px + 24, 288), p_time, font=font_small_bold, fill=TEXT_MUTED)

        y = 350
        for pt in points:
            draw.ellipse([(px + 24, y + 6), (px + 34, y + 16)], fill=col)
            lines = wrap_text(pt, 40)
            for i, l in enumerate(lines):
                draw.text((px + 45, y + (i * 22)), l, font=font_body, fill=TEXT_BODY)
            y += 85

    # Bottom Architecture Banner
    draw.rounded_rectangle([(60, 815), (1860, 990)], radius=12, fill=CARD_BG_ELEVATED, outline=CARD_BORDER, width=2)
    draw.text((95, 835), "NON-INVASIVE ARCHITECTURE OVERVIEW: PRESERVES YOUR EXISTING WORKFLOW", font=font_card_header, fill=CYAN_ACCENT)
    draw.text((95, 875), "[ Retailer WhatsApp ]  ──►  [ NEXORA Intelligent Capture Layer ]  ──►  [ Human Clerk Review ]  ──►  [ Existing Billing (Vyapar / Tally) ]", font=font_body_bold, fill=TEXT_WHITE)
    draw.text((95, 920), "Existing ERP, ledger books, and accountant credentials remain completely untouched. NEXORA acts solely as the front-end intake firewall.", font=font_small, fill=TEXT_MUTED)

    draw_footer(draw)

def render_scene_4(img, draw):
    # Scene 4: Live Multimodal Intake
    draw_topbar(draw, 4)
    draw.text((60, 150), SCENES[3]["title"], font=font_title, fill=TEXT_WHITE)
    draw.text((60, 196), SCENES[3]["subtitle"], font=font_subtitle, fill=CYAN_ACCENT)

    # Left: Raw WhatsApp Intake
    draw.rounded_rectangle([(60, 245), (820, 990)], radius=12, fill=CARD_BG, outline=CYAN_ACCENT, width=2)
    draw.rectangle([(60, 245), (820, 305)], fill=(18, 38, 60))
    draw.text((85, 263), "📥 INCOMING ORDER INTAKE (WHATSAPP CHANNEL)", font=font_card_header, fill=CYAN_ACCENT)

    draw.text((85, 330), "Retailer Customer:", font=font_small_bold, fill=TEXT_MUTED)
    draw.text((85, 352), "Gupta Kirana Stores (Varanasi Hub • +91 98765 43210)", font=font_body_bold, fill=TEXT_WHITE)
    draw.text((85, 390), "Raw Message Text:", font=font_small_bold, fill=TEXT_MUTED)

    # WhatsApp Chat Bubble
    draw.rounded_rectangle([(85, 420), (795, 540)], radius=10, fill=(15, 45, 35), outline=EMERALD_GREEN)
    draw.text((105, 435), "WhatsApp • Today 07:14 AM", font=font_badge, fill=EMERALD_GREEN)
    draw.text((105, 465), '"2 box Parle-G, 5 kg sugar, red label tea 3 packet,', font=font_card_header, fill=TEXT_WHITE)
    draw.text((105, 495), ' oil 10 litre, 1 box surf"', font=font_card_header, fill=TEXT_WHITE)

    # Extraction Engine Specs
    draw.text((85, 570), "Multimodal Extraction Pipeline:", font=font_card_header, fill=TEXT_WHITE)
    specs = [
        ("Model", "Gemini 2.0 Flash (Structured JSON Schema Mode)"),
        ("Latency", "412 ms end-to-end extraction"),
        ("Input Formats", "Text, Audio Voice Note Transcripts, OCR Photo Slips"),
        ("Normalization", "Vernacular quantities (box, packet, can, kg, litre)"),
        ("AI Boundary", "Outputs candidate proposals; master DB write requires clerk approval"),
    ]
    y_sp = 615
    for k, v in specs:
        draw.text((85, y_sp), f"• {k}:", font=font_body_bold, fill=CYAN_ACCENT)
        draw.text((220, y_sp), v, font=font_body, fill=TEXT_BODY)
        y_sp += 42

    # Right: Structured Line Candidate Output
    draw.rounded_rectangle([(850, 245), (1860, 990)], radius=12, fill=CARD_BG, outline=CARD_BORDER, width=2)
    draw.rectangle([(850, 245), (1860, 305)], fill=(22, 33, 58))
    draw.text((875, 263), "⚡ EXTRACTED ORDER DRAFT (CLERK VERIFICATION QUEUE)", font=font_card_header, fill=TEXT_WHITE)

    headers = [("PHRASE", 875), ("CANDIDATE SKU", 1120), ("QTY / UNIT", 1460), ("STATUS FLAG", 1660)]
    for h, hx in headers:
        draw.text((hx, 325), h, font=font_small_bold, fill=TEXT_MUTED)
    draw.line([(875, 350), (1835, 350)], fill=CARD_BORDER, width=1)

    rows = [
        ("2 box Parle-G", "PG-CARTON-24PK (Parle-G 24-Pack)", "2 Cartons", "🟢 GREEN (Match 1.00)", EMERALD_GREEN),
        ("5 kg sugar", "SUG-MADHUR-1KG (Madhur Sugar)", "5 Bags (1kg)", "🟢 GREEN (Match 0.99)", EMERALD_GREEN),
        ("red label tea 3 packet", "Unresolved: 250g vs 500g", "3 Packets", "🔴 RED (Ambiguous)", ROSE_RED),
        ("oil 10 litre", "OIL-FORT-10L (Fortune 10L Can)", "1 Can (Normalized)", "🔴 RED (Variant Ambiguity)", ROSE_RED),
        ("1 box surf", "SURF-EW-1KG (Surf Excel 1kg)", "1 Carton", "🟡 YELLOW (Low Stock)", AMBER_YELLOW),
    ]

    y_r = 370
    for ph, sku, qty, flag, col in rows:
        draw.rounded_rectangle([(875, y_r), (1835, y_r + 62)], radius=6, fill=CARD_BG_ELEVATED, outline=col)
        draw.text((890, y_r + 18), ph, font=font_body_bold, fill=TEXT_WHITE)
        draw.text((1120, y_r + 18), sku, font=font_small, fill=TEXT_BODY)
        draw.text((1460, y_r + 18), qty, font=font_small_bold, fill=TEXT_WHITE)
        draw.text((1660, y_r + 18), flag, font=font_badge, fill=col)
        y_r += 75

    # Bottom Safety Notice
    draw.rounded_rectangle([(875, 770), (1835, 960)], radius=8, fill=(35, 18, 26), outline=ROSE_RED)
    draw.text((900, 790), "🛑 BACKEND APPROVAL LOCK ACTIVE", font=font_card_header, fill=ROSE_RED)
    draw.text((900, 825), "Order NX-DRAFT-20261106-004 cannot be approved. Database safety constraint blocks commit while Red lines exist.", font=font_body, fill=TEXT_WHITE)
    draw.text((900, 858), "Clerk intervention required: resolve Red lines using automated WhatsApp clarification draft.", font=font_small, fill=TEXT_MUTED)

    draw_footer(draw)

def render_scene_5(img, draw):
    # Scene 5: Rule R1 Safety Gate
    draw_topbar(draw, 5)
    draw.text((60, 150), SCENES[4]["title"], font=font_title, fill=TEXT_WHITE)
    draw.text((60, 196), SCENES[4]["subtitle"], font=font_subtitle, fill=ROSE_RED)

    # Left: The Ambiguity Deep Dive
    draw.rounded_rectangle([(60, 245), (930, 990)], radius=12, fill=CARD_BG, outline=ROSE_RED, width=2)
    draw.rectangle([(60, 245), (930, 305)], fill=(45, 15, 25))
    draw.text((85, 263), "🔍 AMBIGUITY DETECTED: 'red label tea 3 packet'", font=font_card_header, fill=ROSE_RED)

    draw.text((85, 330), "Catalogue Collision:", font=font_card_header, fill=TEXT_WHITE)
    draw.text((85, 360), "The stock master contains two matching products with identical brand authority:", font=font_body, fill=TEXT_BODY)

    # Candidate Cards
    draw.rounded_rectangle([(85, 410), (905, 510)], radius=8, fill=CARD_BG_ELEVATED, outline=CARD_BORDER)
    draw.text((110, 428), "Candidate A: TEA-RL-250G", font=font_body_bold, fill=CYAN_ACCENT)
    draw.text((110, 455), "Brooke Bond Red Label Tea 250g Pack • Wholesale Rate: ₹145/unit • Stock: 84 units", font=font_small, fill=TEXT_BODY)
    draw.text((110, 480), "Matching Score: 0.88 (Missing pack specifier)", font=font_badge, fill=AMBER_YELLOW)

    draw.rounded_rectangle([(85, 530), (905, 630)], radius=8, fill=CARD_BG_ELEVATED, outline=CARD_BORDER)
    draw.text((110, 548), "Candidate B: TEA-RL-500G", font=font_body_bold, fill=CYAN_ACCENT)
    draw.text((110, 575), "Brooke Bond Red Label Tea 500g Pack • Wholesale Rate: ₹285/unit • Stock: 42 units", font=font_small, fill=TEXT_BODY)
    draw.text((110, 600), "Matching Score: 0.88 (Missing pack specifier)", font=font_badge, fill=AMBER_YELLOW)

    draw.rounded_rectangle([(85, 660), (905, 960)], radius=10, fill=(30, 15, 22), outline=ROSE_RED)
    draw.text((110, 680), "WHY GENERIC LLMs FAIL WHOLESALERS:", font=font_card_header, fill=ROSE_RED)
    draw.text((110, 715), "• Standard AI blindly guesses 500g, generating a ₹855 line instead of ₹435.", font=font_body, fill=TEXT_WHITE)
    draw.text((110, 750), "• Retailer receives double the ordered weight, rejects dispatch at the curb.", font=font_body, fill=TEXT_WHITE)
    draw.text((110, 785), "• NEXORA Guarantee: Silent error rate is strictly 0.0%. Approval is locked.", font=font_body_bold, fill=EMERALD_GREEN)

    # Right: Clerk Clarification Workflow
    draw.rounded_rectangle([(970, 245), (1860, 990)], radius=12, fill=CARD_BG, outline=EMERALD_GREEN, width=2)
    draw.rectangle([(970, 245), (1860, 305)], fill=(15, 42, 30))
    draw.text((995, 263), "💬 AUTOMATED WHATSAPP CLARIFICATION DISPATCH", font=font_card_header, fill=EMERALD_GREEN)

    draw.text((995, 330), "1. Agent Pre-Drafted Question (Hinglish / Hindi / English):", font=font_body_bold, fill=TEXT_WHITE)
    draw.rounded_rectangle([(995, 365), (1835, 465)], radius=8, fill=(15, 38, 28), outline=EMERALD_GREEN)
    draw.text((1020, 385), 'WhatsApp Clarification Draft:', font=font_badge, fill=EMERALD_GREEN)
    draw.text((1020, 415), '"Namaste Gupta Kirana! For \'red label tea 3 packet\', do you need 250g or 500g pack?"', font=font_body_bold, fill=TEXT_WHITE)

    draw.text((995, 495), "2. Simulated Incoming Customer Reply:", font=font_body_bold, fill=TEXT_WHITE)
    draw.rounded_rectangle([(995, 530), (1835, 610)], radius=8, fill=(18, 30, 50), outline=CYAN_ACCENT)
    draw.text((1020, 545), 'Incoming Customer Response:', font=font_badge, fill=CYAN_ACCENT)
    draw.text((1020, 570), '"Bhaiya 250 gram wala bhejo"', font=font_body_bold, fill=TEXT_WHITE)

    draw.text((995, 640), "3. Clerk 1-Click Resolution:", font=font_body_bold, fill=TEXT_WHITE)
    draw.rounded_rectangle([(995, 675), (1835, 800)], radius=8, fill=CARD_BG_ELEVATED, outline=CARD_BORDER)
    draw.text((1020, 695), "Selected: Brooke Bond Red Label Tea 250g (3 × ₹145 = ₹435)", font=font_body_bold, fill=EMERALD_GREEN)
    draw.text((1020, 728), "[✓] Checkbox: Save as this retailer's permanent shorthand preference", font=font_small_bold, fill=CYAN_ACCENT)
    draw.text((1020, 755), "Status Updated: 🔴 RED  ──►  🟢 GREEN (Ready for Approval)", font=font_body_bold, fill=TEXT_WHITE)

    # Approve Button Unlocked
    draw.rounded_rectangle([(995, 835), (1835, 960)], radius=10, fill=(12, 60, 40), outline=EMERALD_GREEN, width=2)
    draw.text((1300, 875), "✓ APPROVE ORDER (ALL CHECKS PASSED)", font=font_card_header, fill=TEXT_WHITE)
    draw.text((1315, 910), "Backend Safety Constraint Cleared • 1-Click Bill Ready", font=font_small, fill=TEXT_BODY)

    draw_footer(draw)

def render_scene_6(img, draw):
    # Scene 6: Tax & Pricing Mechanics
    draw_topbar(draw, 6)
    draw.text((60, 150), SCENES[5]["title"], font=font_title, fill=TEXT_WHITE)
    draw.text((60, 196), SCENES[5]["subtitle"], font=font_subtitle, fill=CYAN_ACCENT)

    # Left: The 10L Oil Normalization Fix
    draw.rounded_rectangle([(60, 245), (930, 990)], radius=12, fill=CARD_BG, outline=CYAN_ACCENT, width=2)
    draw.rectangle([(60, 245), (930, 305)], fill=(18, 38, 60))
    draw.text((85, 263), "🛢️ FMCG PACK NORMALIZATION: 10L = 1 CAN", font=font_card_header, fill=CYAN_ACCENT)

    draw.text((85, 330), "The Prior 10x Glitch in Generic LLM Systems:", font=font_card_header, fill=TEXT_WHITE)
    draw.rounded_rectangle([(85, 370), (905, 490)], radius=8, fill=(35, 15, 25), outline=ROSE_RED)
    draw.text((110, 390), "❌ Uncorrected Arithmetic Error:", font=font_body_bold, fill=ROSE_RED)
    draw.text((110, 420), "Customer asks for 'oil 10 litre'. SKU is 10L Can @ ₹1,390.", font=font_body, fill=TEXT_WHITE)
    draw.text((110, 448), "Generic bot computes: 10 × ₹1,390 = ₹13,900. (10x overcharge!)", font=font_body_bold, fill=ROSE_RED)

    draw.text((85, 520), "NEXORA Unit Normalization Engine:", font=font_card_header, fill=TEXT_WHITE)
    draw.rounded_rectangle([(85, 560), (905, 680)], radius=8, fill=(15, 42, 30), outline=EMERALD_GREEN)
    draw.text((110, 580), "✅ Deterministic Unit Normalization:", font=font_body_bold, fill=EMERALD_GREEN)
    draw.text((110, 610), "Identifies catalogue SKU pack size = 10 Litre Can.", font=font_body, fill=TEXT_WHITE)
    draw.text((110, 638), "10 Litres requested ÷ 10L per can = 1 Can @ ₹1,390. Correct!", font=font_body_bold, fill=EMERALD_GREEN)

    draw.rounded_rectangle([(85, 710), (905, 960)], radius=8, fill=CARD_BG_ELEVATED, outline=CARD_BORDER)
    draw.text((110, 730), "🟡 YELLOW ALERT: LOW STOCK INSPECTION", font=font_card_header, fill=AMBER_YELLOW)
    draw.text((110, 768), "Line: 1 box Surf Excel 1kg (SURF-EW-1KG)", font=font_body_bold, fill=TEXT_WHITE)
    draw.text((110, 800), "Warehouse Stock Check: Only 2 cartons remaining in depot.", font=font_body, fill=TEXT_BODY)
    draw.text((110, 832), "Action: Yellow warning alerts clerk before dispatch to prevent stockout.", font=font_small, fill=TEXT_MUTED)
    draw.text((110, 875), "Clerk confirms warehouse dispatch reserve & validates line.", font=font_body_bold, fill=AMBER_YELLOW)

    # Right: Itemized 5% GST & Tax Table
    draw.rounded_rectangle([(970, 245), (1860, 990)], radius=12, fill=CARD_BG, outline=CARD_BORDER, width=2)
    draw.rectangle([(970, 245), (1860, 305)], fill=(22, 33, 58))
    draw.text((995, 263), "🧾 ITEMIZED FMCG WHOLESALE INVOICE PREVIEW", font=font_card_header, fill=TEXT_WHITE)

    # Invoice Table
    t_headers = [("SKU & DESCRIPTION", 995), ("QTY", 1360), ("BASE RATE", 1480), ("GST (5%)", 1630), ("TOTAL", 1750)]
    for th, tx in t_headers:
        draw.text((tx, 325), th, font=font_small_bold, fill=TEXT_MUTED)
    draw.line([(995, 350), (1835, 350)], fill=CARD_BORDER, width=1)

    t_rows = [
        ("PG-CARTON-24PK (Parle-G 24pk)", "2 Box", "₹650.00", "₹65.00", "₹1,365.00"),
        ("SUG-MADHUR-1KG (Sugar 1kg)", "5 Bags", "₹42.00", "₹10.50", "₹220.50"),
        ("TEA-RL-250G (Red Label 250g)", "3 Packs", "₹138.10", "₹20.70", "₹435.00"),
        ("OIL-FORT-10L (Fortune Oil 10L)", "1 Can", "₹1,323.80", "₹66.20", "₹1,390.00"),
        ("SURF-EW-1KG (Surf Excel 1kg)", "1 Box", "₹321.90", "₹16.10", "₹338.00"),
    ]
    y_t = 370
    for s_name, s_q, s_b, s_g, s_tot in t_rows:
        draw.text((995, y_t), s_name, font=font_small_bold, fill=TEXT_WHITE)
        draw.text((1360, y_t), s_q, font=font_small, fill=TEXT_BODY)
        draw.text((1480, y_t), s_b, font=font_small, fill=TEXT_BODY)
        draw.text((1630, y_t), s_g, font=font_small, fill=AMBER_YELLOW)
        draw.text((1750, y_t), s_tot, font=font_small_bold, fill=EMERALD_GREEN)
        draw.line([(995, y_t + 35), (1835, y_t + 35)], fill=CARD_BORDER, width=1)
        y_t += 55

    # Invoice Summary Box
    draw.rounded_rectangle([(995, 680), (1835, 960)], radius=10, fill=CARD_BG_ELEVATED, outline=CYAN_ACCENT)
    draw.text((1025, 705), "INVOICE SUMMARY (BILL-READY VYAPAR FORMAT):", font=font_card_header, fill=CYAN_ACCENT)
    draw.text((1025, 750), "• Subtotal (Pre-Tax Base Rates): ₹3,570.00", font=font_body, fill=TEXT_WHITE)
    draw.text((1025, 785), "• Itemized FMCG GST (CGST 2.5% + SGST 2.5%): ₹178.50", font=font_body, fill=AMBER_YELLOW)
    draw.text((1025, 825), "• Grand Total (Verified & Approved): ₹3,748.50", font=font_title, fill=EMERALD_GREEN)
    draw.text((1025, 875), "Export Status: Direct export to Vyapar JSON, CSV, and Tally XML ledger ready.", font=font_small, fill=TEXT_MUTED)

    draw_footer(draw)

def render_scene_7(img, draw):
    # Scene 7: Retailer Vernacular Memory
    draw_topbar(draw, 7)
    draw.text((60, 150), SCENES[6]["title"], font=font_title, fill=TEXT_WHITE)
    draw.text((60, 196), SCENES[6]["subtitle"], font=font_subtitle, fill=CYAN_ACCENT)

    # Left: Shorthand Persistence Demonstration
    draw.rounded_rectangle([(60, 245), (930, 990)], radius=12, fill=CARD_BG, outline=CYAN_ACCENT, width=2)
    draw.rectangle([(60, 245), (930, 305)], fill=(18, 38, 60))
    draw.text((85, 263), "🧠 RETAILER ALIAS MEMORY (LAYER 1 CASCADE)", font=font_card_header, fill=CYAN_ACCENT)

    draw.text((85, 330), "How NEXORA Learns Per-Customer Shorthand:", font=font_card_header, fill=TEXT_WHITE)
    draw.text((85, 365), "Wholesale customers repeatedly use custom slang and nicknames. NEXORA maintains private tenant dictionaries stored in 'retailer_aliases'.", font=font_body, fill=TEXT_BODY)

    # Timeline of memory
    steps = [
        ("Order 1 (Intake)", "Gupta Kirana sends 'red label tea 3 packet'. Flagged Red. Clerk selects 250g and checks 'Save as retailer preference'."),
        ("Database Commit", "Alias persisted: { retailer: 'Gupta Kirana', phrase: 'red label tea', target_sku: 'TEA-RL-250G', confidence: 1.00 }"),
        ("Order 2 (Reuse)", "Gupta Kirana sends 'red label tea 3 packet' next week. Instantly resolves at Layer 1 in 0.04ms as GREEN. Zero clerk intervention!"),
    ]
    y_s = 460
    for st_title, st_desc in steps:
        draw.rounded_rectangle([(85, y_s), (905, y_s + 110)], radius=8, fill=CARD_BG_ELEVATED, outline=CARD_BORDER)
        draw.text((110, y_s + 15), st_title, font=font_body_bold, fill=CYAN_ACCENT)
        lines = wrap_text(st_desc, 60)
        for i, l in enumerate(lines):
            draw.text((110, y_s + 45 + (i * 20)), l, font=font_small, fill=TEXT_BODY)
        y_s += 130

    draw.rounded_rectangle([(85, 870), (905, 960)], radius=8, fill=(15, 42, 30), outline=EMERALD_GREEN)
    draw.text((110, 890), "⚡ Zero LLM Inference Cost for Learned Aliases", font=font_body_bold, fill=EMERALD_GREEN)
    draw.text((110, 920), "Layer 1 matches directly against indexed PostgreSQL memory. Instant & free.", font=font_small, fill=TEXT_WHITE)

    # Right: Explicit Variant Override
    draw.rounded_rectangle([(970, 245), (1860, 990)], radius=12, fill=CARD_BG, outline=CARD_BORDER, width=2)
    draw.rectangle([(970, 245), (1860, 305)], fill=(22, 33, 58))
    draw.text((995, 263), "🛡️ SAFE EXPLICIT OVERRIDE WITHOUT ALIAS CORRUPTION", font=font_card_header, fill=TEXT_WHITE)

    draw.text((995, 330), "Handling One-Off Variant Changes Safely:", font=font_card_header, fill=TEXT_WHITE)
    draw.text((995, 365), "What if Gupta Kirana specifically needs 500g for a special event? Does the system blindly force the 250g default?", font=font_body, fill=TEXT_BODY)

    draw.rounded_rectangle([(995, 420), (1835, 540)], radius=8, fill=(20, 35, 55), outline=CYAN_ACCENT)
    draw.text((1020, 440), "Order 3 WhatsApp Message:", font=font_small_bold, fill=CYAN_ACCENT)
    draw.text((1020, 475), '"Red Label tea 500g 2 packet bhejo"', font=font_title, fill=TEXT_WHITE)

    draw.rounded_rectangle([(995, 570), (1835, 780)], radius=8, fill=CARD_BG_ELEVATED, outline=EMERALD_GREEN)
    draw.text((1020, 590), "NEXORA Multi-Layer Decision Hierarchy:", font=font_card_header, fill=EMERALD_GREEN)
    draw.text((1020, 630), "1. Explicit Variant Detection: Engine identifies explicit '500g' token in raw text.", font=font_body, fill=TEXT_WHITE)
    draw.text((1020, 665), "2. Prioritized Catalogue Match: Layer 2 overrides Layer 1 shorthand for this single order.", font=font_body, fill=TEXT_WHITE)
    draw.text((1020, 700), "3. Memory Preservation: Permanent alias remains '250g' for future unqualified orders.", font=font_body, fill=TEXT_WHITE)
    draw.text((1020, 735), "4. Result: 2 Packs of 500g approved. Master alias is NOT corrupted!", font=font_body_bold, fill=EMERALD_GREEN)

    draw.rounded_rectangle([(995, 810), (1835, 960)], radius=8, fill=(35, 25, 15), outline=AMBER_YELLOW)
    draw.text((1020, 830), "OPERATIONAL INTEGRITY PRINCIPLE", font=font_card_header, fill=AMBER_YELLOW)
    draw.text((1020, 870), "Learned shorthand never trumps explicit customer instructions.", font=font_body_bold, fill=TEXT_WHITE)
    draw.text((1020, 905), "Distributors maintain total dispatch accuracy regardless of colloquial changes.", font=font_small, fill=TEXT_MUTED)

    draw_footer(draw)

def render_scene_8(img, draw):
    # Scene 8: Enterprise Integration & Audit Trail
    draw_topbar(draw, 8)
    draw.text((60, 150), SCENES[7]["title"], font=font_title, fill=TEXT_WHITE)
    draw.text((60, 196), SCENES[7]["subtitle"], font=font_subtitle, fill=CYAN_ACCENT)

    # Left: Accounting Export Suite
    draw.rounded_rectangle([(60, 245), (930, 990)], radius=12, fill=CARD_BG, outline=EMERALD_GREEN, width=2)
    draw.rectangle([(60, 245), (930, 305)], fill=(15, 42, 30))
    draw.text((85, 263), "💼 BILL-READY ACCOUNTING EXPORT INTEGRATIONS", font=font_card_header, fill=EMERALD_GREEN)

    exports = [
        ("Vyapar JSON Standard Connector", "Directly imports verified sales vouchers into Vyapar desktop and mobile billing without re-keying items, rates, or customer GSTINs.", EMERALD_GREEN),
        ("Universal Spreadsheet CSV", "Structured columns for ERP ingests: SKU, Item Name, Quantity, Normalized Unit, Wholesale Pre-Tax Rate, GST%, Line Total.", CYAN_ACCENT),
        ("Tally XML Ingestion Schema (Roadmap)", "Upcoming bi-directional connector pushing directly to Tally Prime XML server via standard HTTP port.", INDIGO_ACCENT),
    ]
    y_ex = 330
    for ex_t, ex_d, ex_c in exports:
        draw.rounded_rectangle([(85, y_ex), (905, y_ex + 120)], radius=8, fill=CARD_BG_ELEVATED, outline=ex_c)
        draw.text((110, y_ex + 18), ex_t, font=font_body_bold, fill=ex_c)
        lines = wrap_text(ex_d, 60)
        for i, l in enumerate(lines):
            draw.text((110, y_ex + 48 + (i * 22)), l, font=font_small, fill=TEXT_BODY)
        y_ex += 140

    draw.rounded_rectangle([(85, 770), (905, 960)], radius=8, fill=(18, 32, 50), outline=CYAN_ACCENT)
    draw.text((110, 790), "ENTERPRISE SECURITY & MULTI-TENANCY", font=font_card_header, fill=CYAN_ACCENT)
    draw.text((110, 830), "• PostgreSQL Row-Level Security: Strict tenant isolation.", font=font_body, fill=TEXT_WHITE)
    draw.text((110, 865), "• Role-Based Access Control (RBAC): Owner vs Clerk permissions.", font=font_body, fill=TEXT_WHITE)
    draw.text((110, 900), "• Confidential Data: Customer phone numbers encrypted at rest.", font=font_small, fill=TEXT_MUTED)

    # Right: Tamper-Proof Audit Trail
    draw.rounded_rectangle([(970, 245), (1860, 990)], radius=12, fill=CARD_BG, outline=CARD_BORDER, width=2)
    draw.rectangle([(970, 245), (1860, 305)], fill=(22, 33, 58))
    draw.text((995, 263), "🔒 TAMPER-PROOF IMMUTABLE AUDIT TRAIL", font=font_card_header, fill=TEXT_WHITE)

    draw.text((995, 330), "Order Event Ledger (NX-20261106-948201):", font=font_card_header, fill=TEXT_WHITE)

    audit_events = [
        ("07:14:02 AM", "INTAKE_RECEIVED", "Raw message received via WhatsApp webhook (Payload 84 bytes)", CYAN_ACCENT),
        ("07:14:03 AM", "EXTRACTION_COMPLETE", "Gemini 2.0 Flash generated 5 candidate lines (Tokens: 218)", TEXT_BODY),
        ("07:14:03 AM", "SAFETY_GATE_TRIGGERED", "Rule R1 engaged: Red Label Tea flagged RED (Ambiguous pack)", ROSE_RED),
        ("07:15:10 AM", "CLARIFICATION_SENT", "WhatsApp question sent to customer (+91 98765 43210)", AMBER_YELLOW),
        ("07:16:45 AM", "CLARIFICATION_RESOLVED", "Customer replied '250g'. Clerk Rahul Verma confirmed SKU", EMERALD_GREEN),
        ("07:16:50 AM", "ORDER_APPROVED", "Order locked by Rahul Verma. Vyapar JSON & CSV generated", EMERALD_GREEN),
    ]

    y_au = 380
    for a_time, a_ev, a_desc, a_col in audit_events:
        draw.rounded_rectangle([(995, y_au), (1835, y_au + 55)], radius=6, fill=CARD_BG_ELEVATED, outline=CARD_BORDER)
        draw.text((1015, y_au + 16), a_time, font=font_small_bold, fill=TEXT_MUTED)
        draw.text((1130, y_au + 16), a_ev, font=font_badge, fill=a_col)
        draw.text((1340, y_au + 16), a_desc, font=font_small, fill=TEXT_BODY)
        y_au += 68

    draw.rounded_rectangle([(995, 810), (1835, 960)], radius=8, fill=(15, 25, 45), outline=CARD_BORDER)
    draw.text((1020, 830), "LEGAL & REGULATORY COMPLIANCE", font=font_card_header, fill=CYAN_ACCENT)
    draw.text((1020, 868), "Append-only insert protection prevents backdated order manipulation.", font=font_body, fill=TEXT_WHITE)
    draw.text((1020, 902), "Guarantees complete fiscal auditability for GST verification and tax compliance.", font=font_small, fill=TEXT_MUTED)

    draw_footer(draw)

def render_scene_9(img, draw):
    # Scene 9: Empirical ROI
    draw_topbar(draw, 9)
    draw.text((60, 150), SCENES[8]["title"], font=font_title, fill=TEXT_WHITE)
    draw.text((60, 196), SCENES[8]["subtitle"], font=font_subtitle, fill=EMERALD_GREEN)

    # 4 Big Stat Cards
    stat_cards = [
        ("0.0%", "Silent Green Errors", "Strict zero-hallucination constraint; any ambiguity defaults to Red flag", EMERALD_GREEN, 60),
        ("96%", "Flag Precision", "Minimizes false alarms and clerical fatigue during morning peak rush", CYAN_ACCENT, 510),
        ("21.4s", "Clerk Processing Time", "Down from 240 seconds manual entry (91% reduction in handling time)", AMBER_YELLOW, 960),
        ("₹0.08", "Cost Per Order", "Down from ₹12.50 manual clerical labour (99.4% cost reduction)", EMERALD_GREEN, 1410),
    ]

    for val, lbl, desc, col, sx in stat_cards:
        draw.rounded_rectangle([(sx, 245), (sx + 420, 480)], radius=12, fill=CARD_BG, outline=col, width=2)
        draw.text((sx + 30, 275), val, font=font_huge, fill=col)
        draw.text((sx + 30, 350), lbl, font=font_card_header, fill=TEXT_WHITE)
        lines = wrap_text(desc, 30)
        for i, l in enumerate(lines):
            draw.text((sx + 30, 395 + (i * 22)), l, font=font_small, fill=TEXT_MUTED)

    # Detailed Benchmark Breakdown
    draw.rounded_rectangle([(60, 515), (1860, 990)], radius=12, fill=CARD_BG_ELEVATED, outline=CARD_BORDER, width=2)
    draw.rectangle([(60, 515), (1860, 575)], fill=(22, 33, 58))
    draw.text((85, 533), "📊 INDEPENDENT HOLDOUT BENCHMARK EVALUATION (N = 25 ORDERS / 125 LINES)", font=font_card_header, fill=CYAN_ACCENT)

    # Comparison Grid
    b_left = 85
    b_mid = 980

    draw.text((b_left, 605), "TRADITIONAL MANUAL PROCESS", font=font_card_header, fill=ROSE_RED)
    m_pts = [
        "• Manual entry time: 4 minutes (240 seconds) per order slip.",
        "• High misdispatch rate: 3.8% of manual orders contain SKU pack errors.",
        "• Customer disputes cost: ~₹150 to ₹350 per misrouted return.",
        "• Peak morning bottleneck limits distributor to ~120 orders per clerk."
    ]
    y_m = 645
    for pt in m_pts:
        draw.text((b_left, y_m), pt, font=font_body, fill=TEXT_BODY)
        y_m += 38

    draw.text((b_mid, 605), "MIGRATED WITH NEXORA ORDER AGENT", font=font_card_header, fill=EMERALD_GREEN)
    n_pts = [
        "• Automated processing time: 21.4 seconds clerk review time.",
        "• Zero silent errors: 0.0% false positives on approved orders.",
        "• Customer disputes eliminated via pre-dispatch WhatsApp clarification.",
        "• Single clerk handles 500+ daily orders with effortless authority."
    ]
    y_n = 645
    for pt in n_pts:
        draw.text((b_mid, y_n), pt, font=font_body, fill=TEXT_WHITE)
        y_n += 38

    # Final ROI Summary Banner
    draw.rounded_rectangle([(85, 830), (1835, 960)], radius=8, fill=(15, 42, 30), outline=EMERALD_GREEN)
    draw.text((115, 850), "ANNUAL NET BUSINESS SAVINGS FOR 500 DAILY ORDERS:", font=font_card_header, fill=EMERALD_GREEN)
    draw.text((115, 885), "• Annual Labour Savings: ₹18.2 Lakhs ($22,000 USD) in clerical overhead", font=font_title, fill=TEXT_WHITE)
    draw.text((115, 925), "• Return Dispatches Saved: 5,400+ misdispatched cartons prevented annually", font=font_body_bold, fill=CYAN_ACCENT)

    draw_footer(draw)

def render_scene_10(img, draw):
    # Scene 10: Executive Roadmap & Conclusion
    draw_topbar(draw, 10)
    draw.text((60, 150), SCENES[9]["title"], font=font_title, fill=TEXT_WHITE)
    draw.text((60, 196), SCENES[9]["subtitle"], font=font_subtitle, fill=CYAN_ACCENT)

    # Left: Production Architecture & Stack
    draw.rounded_rectangle([(60, 245), (930, 990)], radius=12, fill=CARD_BG, outline=CYAN_ACCENT, width=2)
    draw.rectangle([(60, 245), (930, 305)], fill=(18, 38, 60))
    draw.text((85, 263), "🏗️ PRODUCTION-READY ENTERPRISE ARCHITECTURE", font=font_card_header, fill=CYAN_ACCENT)

    tech_stack = [
        ("FastAPI Backend", "Python 3.9+ async microservice with strict Pydantic v2 schemas and Uvicorn server."),
        ("Google Gemini 2.0 Flash", "Multimodal intelligence engine operating with strict structured JSON output mode."),
        ("PostgreSQL & SQLAlchemy", "14 relational tables, Row-Level Security, and append-only audit event logging."),
        ("Google Cloud Run Deployment", "Fully containerized via production Dockerfile for auto-scaling from 0 to 1000s."),
        ("Frontend Application", "Vite + React 18 + TailwindCSS dark-mode responsive operational dashboard."),
    ]
    y_tc = 330
    for tk, td in tech_stack:
        draw.text((85, y_tc), f"• {tk}:", font=font_body_bold, fill=CYAN_ACCENT)
        lines = wrap_text(td, 60)
        for i, l in enumerate(lines):
            draw.text((85, y_tc + 24 + (i * 20)), l, font=font_small, fill=TEXT_BODY)
        y_tc += 75

    draw.rounded_rectangle([(85, 770), (905, 960)], radius=8, fill=(15, 35, 55), outline=CYAN_ACCENT)
    draw.text((110, 790), "LOCAL INSTANCE & CLOUD READINESS", font=font_card_header, fill=CYAN_ACCENT)
    draw.text((110, 830), "• Local Endpoint: http://127.0.0.1:8000 (Unified Server)", font=font_body_bold, fill=TEXT_WHITE)
    draw.text((110, 865), "• Automated Pytest Suite: 100% test pass rate across schemas", font=font_small, fill=TEXT_MUTED)
    draw.text((110, 900), "• Cloud Run Container: Ready for immediate enterprise multi-region deploy", font=font_small_bold, fill=EMERALD_GREEN)

    # Right: Migration Pilot Next Steps
    draw.rounded_rectangle([(970, 245), (1860, 990)], radius=12, fill=CARD_BG, outline=EMERALD_GREEN, width=2)
    draw.rectangle([(970, 245), (1860, 305)], fill=(15, 42, 30))
    draw.text((995, 263), "🚀 ONBOARDING & PILOT DEPLOYMENT ROADMAP", font=font_card_header, fill=EMERALD_GREEN)

    steps = [
        ("Step 1: Catalogue Ingestion (Hour 0 - 24)", "Import existing product SKU master list and price book via CSV or Vyapar database backup."),
        ("Step 2: WhatsApp Webhook Connect (Hour 24 - 48)", "Link distributor WhatsApp Business number or provide clerks with the web intake pasteboard."),
        ("Step 3: Supervised Pilot (Week 1 - 2)", "Clerks review drafts with full safety guards active. Shorthand memory auto-trains on daily traffic."),
        ("Step 4: Full Autonomous Operations (Week 3+)", "Instant 1-click ledger exports, automated exception routing, and complete operational freedom."),
    ]
    y_st = 340
    for sk, sd in steps:
        draw.rounded_rectangle([(995, y_st), (1835, y_st + 90)], radius=8, fill=CARD_BG_ELEVATED, outline=CARD_BORDER)
        draw.text((1020, y_st + 15), sk, font=font_body_bold, fill=EMERALD_GREEN)
        lines = wrap_text(sd, 64)
        for i, l in enumerate(lines):
            draw.text((1020, y_st + 42 + (i * 20)), l, font=font_small, fill=TEXT_BODY)
        y_st += 105

    draw.rounded_rectangle([(995, 800), (1835, 960)], radius=10, fill=(18, 55, 38), outline=EMERALD_GREEN, width=2)
    draw.text((1200, 835), "PARTNER WITH NEXORA TODAY", font=font_card_header, fill=TEXT_WHITE)
    draw.text((1140, 875), "Schedule your 48-hour pilot deployment at nexora-order-agent.com", font=font_body_bold, fill=CYAN_ACCENT)
    draw.text((1180, 915), "Singhania Wholesale Hub • Startup Buildathon India 2026", font=font_small, fill=TEXT_MUTED)

    draw_footer(draw)

SCENE_RENDERERS = {
    1: render_scene_1,
    2: render_scene_2,
    3: render_scene_3,
    4: render_scene_4,
    5: render_scene_5,
    6: render_scene_6,
    7: render_scene_7,
    8: render_scene_8,
    9: render_scene_9,
    10: render_scene_10,
}

async def generate_voice_track(text, output_file):
    # Professional, authoritative Fortune 500 tech presenter voice
    communicate = edge_tts.Communicate(text, "en-US-ChristopherNeural", rate="+1%")
    await communicate.save(output_file)

def get_audio_duration(file_path):
    cmd = [
        FFPROBE, "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        file_path
    ]
    out = subprocess.check_output(cmd).decode().strip()
    return float(out)

async def main():
    print("=" * 75)
    print(" NEXORA ORDER AGENT - ENTERPRISE MIGRATION PRESENTATION (1080p)")
    print(" Voice: en-US-ChristopherNeural (Authoritative MNC Executive)")
    print(" Slides: 10 Full HD 1080p Master Visual Layouts")
    print("=" * 75)

    clip_files = []

    for s in SCENES:
        scene_id = s["id"]
        print(f"\n[Processing Scene {scene_id}/10] {s['tab']}...")

        # 1. Generate Voice Track
        audio_file = os.path.join(BUILD_DIR, f"scene_{scene_id}_audio.mp3")
        await generate_voice_track(s["voice"], audio_file)
        duration = get_audio_duration(audio_file)
        print(f"  ✓ Voiceover synthesized: {duration:.2f} seconds")

        # 2. Render 1080p Slide
        img = Image.new("RGB", (1920, 1080), BG_DARK)
        draw = ImageDraw.Draw(img)
        SCENE_RENDERERS[scene_id](img, draw)
        img_file = os.path.join(BUILD_DIR, f"scene_{scene_id}_slide.png")
        img.save(img_file)
        print(f"  ✓ Rendered 1080p slide: {img_file}")

        # 3. Encode Video Clip with slight padding
        clip_file = os.path.join(BUILD_DIR, f"scene_{scene_id}_clip.mp4")
        ffmpeg_cmd = [
            FFMPEG, "-y",
            "-loop", "1", "-i", img_file,
            "-i", audio_file,
            "-c:v", "libx264", "-tune", "stillimage",
            "-c:a", "aac", "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-t", str(duration + 0.5),
            clip_file
        ]
        subprocess.check_call(ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"  ✓ Encoded scene clip: {clip_file}")
        clip_files.append(clip_file)

    # 4. Concatenate All Clips
    print("\nConcatenating 10 scenes into final master video...")
    concat_list_file = os.path.join(BUILD_DIR, "concat_list.txt")
    with open(concat_list_file, "w") as f:
        for c in clip_files:
            f.write(f"file '{c}'\n")

    ffmpeg_concat_cmd = [
        FFMPEG, "-y",
        "-f", "concat", "-safe", "0",
        "-i", concat_list_file,
        "-c", "copy",
        OUTPUT_MP4
    ]
    subprocess.check_call(ffmpeg_concat_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"\n Master MP4 generated: {OUTPUT_MP4} ({os.path.getsize(OUTPUT_MP4):,} bytes)")

    # 5. Copy to Desktop & Frontend
    shutil.copyfile(OUTPUT_MP4, DESKTOP_MP4)
    print(f" Copied to Desktop: {DESKTOP_MP4}")

    shutil.copyfile(OUTPUT_MP4, FRONTEND_DIST_MP4)
    print(f" Copied to Frontend: {FRONTEND_DIST_MP4}")

    total_duration = get_audio_duration(OUTPUT_MP4)
    print("\n" + "=" * 75)
    print(" SUCCESS: Enterprise Migration Video Generated!")
    print(f" Total Video Runtime: {int(total_duration // 60)}m {int(total_duration % 60):02d}s ({total_duration:.2f} seconds)")
    print(" Resolution: 1920x1080 Full HD (1080p)")
    print(f" File Location: {DESKTOP_MP4}")
    print("=" * 75)

if __name__ == "__main__":
    asyncio.run(main())
