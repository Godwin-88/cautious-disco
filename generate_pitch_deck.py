"""
AMD EA Strategy Optimizer — Hackathon Pitch Deck Generator
Produces: amd_ea_pitch_deck.pdf  (16:9, 12 slides)
Run: python generate_pitch_deck.py
"""

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
import math

# ── Canvas size: 16:9 ────────────────────────────────────────────────────────
W, H = 960, 540

# ── Palette ──────────────────────────────────────────────────────────────────
AMD_RED      = HexColor("#ED1C24")
AMD_DARK_RED = HexColor("#A50F15")
DARK_BG      = HexColor("#0D0D0D")
CARD_BG      = HexColor("#1A1A1A")
CARD_BG2     = HexColor("#141414")
ACCENT_BLUE  = HexColor("#00BFFF")
ACCENT_GREEN = HexColor("#27AE60")
ACCENT_AMBER = HexColor("#F39C12")
WHITE        = HexColor("#FFFFFF")
LIGHT_GREY   = HexColor("#B0B0B0")
MID_GREY     = HexColor("#555555")
DIM_GREY     = HexColor("#333333")
PANEL_BORDER = HexColor("#2A2A2A")

OUT = "amd_ea_pitch_deck.pdf"


# ── Helpers ───────────────────────────────────────────────────────────────────

def new_slide(c: canvas.Canvas):
    c.showPage()
    c.setFillColor(DARK_BG)
    c.rect(0, 0, W, H, fill=1, stroke=0)


def bg(c, col=DARK_BG):
    c.setFillColor(col)
    c.rect(0, 0, W, H, fill=1, stroke=0)


def red_bar(c, y=H - 56, height=56):
    """Top header bar in AMD red."""
    c.setFillColor(AMD_RED)
    c.rect(0, y, W, height, fill=1, stroke=0)


def accent_line(c, y, col=AMD_RED, x0=40, x1=None, width=3):
    x1 = x1 or W - 40
    c.setStrokeColor(col)
    c.setLineWidth(width)
    c.line(x0, y, x1, y)


def card(c, x, y, w, h, col=CARD_BG, radius=6, border=PANEL_BORDER):
    c.setFillColor(col)
    c.setStrokeColor(border)
    c.setLineWidth(0.5)
    c.roundRect(x, y, w, h, radius, fill=1, stroke=1)


def txt(c, text, x, y, size=12, col=WHITE, bold=False, align="left"):
    c.setFillColor(col)
    face = "Helvetica-Bold" if bold else "Helvetica"
    c.setFont(face, size)
    if align == "center":
        c.drawCentredString(x, y, text)
    elif align == "right":
        c.drawRightString(x, y, text)
    else:
        c.drawString(x, y, text)


def wrapped(c, text, x, y, max_w, size=11, col=WHITE, leading=16, bold=False):
    """Simple word-wrap."""
    face = "Helvetica-Bold" if bold else "Helvetica"
    c.setFont(face, size)
    c.setFillColor(col)
    words = text.split()
    line = ""
    cy = y
    for w in words:
        test = (line + " " + w).strip()
        if c.stringWidth(test, face, size) <= max_w:
            line = test
        else:
            c.drawString(x, cy, line)
            cy -= leading
            line = w
    if line:
        c.drawString(x, cy, line)
    return cy - leading


def pill(c, x, y, label, bg_col=AMD_RED, text_col=WHITE, size=9, pad_x=8, pad_y=4):
    w = c.stringWidth(label, "Helvetica-Bold", size) + pad_x * 2
    h = size + pad_y * 2
    c.setFillColor(bg_col)
    c.roundRect(x, y - pad_y, w, h, 3, fill=1, stroke=0)
    c.setFillColor(text_col)
    c.setFont("Helvetica-Bold", size)
    c.drawString(x + pad_x, y + 1, label)
    return w


def dot(c, x, y, r=4, col=AMD_RED):
    c.setFillColor(col)
    c.circle(x, y, r, fill=1, stroke=0)


def arrow_right(c, x, y, col=LIGHT_GREY):
    c.setStrokeColor(col)
    c.setFillColor(col)
    c.setLineWidth(1.5)
    c.line(x, y, x + 18, y)
    # arrowhead
    p = c.beginPath()
    p.moveTo(x + 18, y + 4)
    p.lineTo(x + 26, y)
    p.lineTo(x + 18, y - 4)
    p.close()
    c.drawPath(p, fill=1, stroke=0)


def progress_bar(c, x, y, w, h, pct, fg=AMD_RED, bg=DIM_GREY, radius=3):
    c.setFillColor(bg)
    c.roundRect(x, y, w, h, radius, fill=1, stroke=0)
    c.setFillColor(fg)
    c.roundRect(x, y, w * pct, h, radius, fill=1, stroke=0)


# ── Slide 1 — Cover ───────────────────────────────────────────────────────────

def slide_cover(c):
    bg(c)

    # gradient-like left band
    c.setFillColor(HexColor("#1A0000"))
    c.rect(0, 0, 320, H, fill=1, stroke=0)

    # AMD red vertical stripe
    c.setFillColor(AMD_RED)
    c.rect(316, 0, 8, H, fill=1, stroke=0)

    # top-right badge
    c.setFillColor(HexColor("#1A0000"))
    c.rect(W - 200, H - 50, 200, 50, fill=1, stroke=0)
    txt(c, "AMD Developer Hackathon 2026", W - 100, H - 32, size=9,
        col=LIGHT_GREY, align="center")
    txt(c, "Lablab.ai  ·  Track 1 — AI Agents", W - 100, H - 44, size=8,
        col=MID_GREY, align="center")

    # main title block
    c.setFillColor(AMD_RED)
    c.setFont("Helvetica-Bold", 36)
    c.drawString(350, 360, "AMD EA Strategy")
    c.drawString(350, 315, "Optimizer")

    accent_line(c, 300, col=AMD_RED, x0=350, x1=900, width=2)

    txt(c, "Agentic Enterprise Architecture Intelligence", 350, 278,
        size=14, col=LIGHT_GREY)
    txt(c, "From a 10-minute questionnaire to a governance-grounded,",
        350, 250, size=11, col=HexColor("#888888"))
    txt(c, "Jira-ready strategic roadmap — powered by AMD MI300X.",
        350, 234, size=11, col=HexColor("#888888"))

    # stats row
    stats = [("44", "Domains"), ("1,416", "Capabilities"), ("Qwen-72B", "on MI300X"), ("ROCm", "Powered")]
    sx = 350
    for val, label in stats:
        txt(c, val, sx, 175, size=16, col=WHITE, bold=True)
        txt(c, label, sx, 158, size=8, col=LIGHT_GREY)
        sx += 148

    # left panel title
    c.setFillColor(AMD_RED)
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(158, 430, "EA")
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(158, 380, "Strategy")
    c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(158, 354, "Optimizer")
    accent_line(c, 340, col=HexColor("#444444"), x0=60, x1=256, width=1)
    txt(c, "AMD  ·  Neo4j  ·  LangGraph", 158, 318, size=9,
        col=LIGHT_GREY, align="center")
    txt(c, "Streamlit  ·  FastAPI  ·  vLLM", 158, 302, size=9,
        col=MID_GREY, align="center")

    # bottom bar
    c.setFillColor(HexColor("#111111"))
    c.rect(0, 0, W, 32, fill=1, stroke=0)
    txt(c, "huggingface.co/spaces/TheQuantEd/EA_strat_optimizer  ·  linkedin.com/in/godwin-edgar-opuka",
        W // 2, 11, size=9, col=HexColor("#666666"), align="center")


# ── Slide 2 — Problem ─────────────────────────────────────────────────────────

def slide_problem(c):
    new_slide(c)
    red_bar(c)
    txt(c, "THE PROBLEM", 40, H - 34, size=14, col=WHITE, bold=True)
    txt(c, "Enterprise Architecture is broken — expensive, slow, and inaccessible",
        40, H - 85, size=13, col=LIGHT_GREY)
    accent_line(c, H - 95, x0=40, x1=920)

    problems = [
        ("$500K – $2M", "per consulting engagement", "Average cost of a professional EA strategy project",
         AMD_RED),
        ("6 – 18 months", "delivery timeline", "Time from brief to actionable roadmap in traditional consulting",
         ACCENT_AMBER),
        ("Expertise gap", "for emerging markets", "Kenya and Africa lack enough certified EA consultants to serve demand",
         ACCENT_BLUE),
    ]

    cx = 60
    for val, label, desc, col in problems:
        card(c, cx, 160, 270, 220, col=CARD_BG)
        c.setFillColor(col)
        c.rect(cx, 360, 270, 20, fill=1, stroke=0)  # top colour band
        txt(c, val, cx + 135, 333, size=22, col=col, bold=True, align="center")
        txt(c, label, cx + 135, 308, size=11, col=WHITE, bold=True, align="center")
        accent_line(c, 302, col=DIM_GREY, x0=cx + 20, x1=cx + 250, width=1)
        wrapped(c, desc, cx + 20, 285, 230, size=9, col=LIGHT_GREY, leading=14)
        cx += 300

    # insight box
    card(c, 40, 80, W - 80, 65, col=HexColor("#1A0000"))
    c.setStrokeColor(AMD_RED)
    c.setLineWidth(1)
    c.roundRect(40, 80, W - 80, 65, 6, fill=0, stroke=1)
    txt(c, "💡  The opportunity:", 60, 127, size=10, col=AMD_RED, bold=True)
    txt(c, "Compress months of expert consulting into a 10-minute AI-guided conversation,",
        60, 110, size=10, col=WHITE)
    txt(c, "grounded in real governance standards and sector-specific knowledge graphs.",
        60, 94, size=10, col=LIGHT_GREY)


# ── Slide 3 — Solution ────────────────────────────────────────────────────────

def slide_solution(c):
    new_slide(c)
    red_bar(c)
    txt(c, "OUR SOLUTION", 40, H - 34, size=14, col=WHITE, bold=True)
    txt(c, "One platform. End-to-end EA intelligence.", 40, H - 85, size=13, col=LIGHT_GREY)
    accent_line(c, H - 95, x0=40, x1=920)

    # input → output flow
    card(c, 40, 310, 200, 170, col=HexColor("#0A1A0A"))
    c.setStrokeColor(ACCENT_GREEN)
    c.setLineWidth(1)
    c.roundRect(40, 310, 200, 170, 6, fill=0, stroke=1)
    txt(c, "INPUT", 140, 463, size=9, col=ACCENT_GREEN, bold=True, align="center")
    items_in = ["Organisation type", "Strategic goals", "Target sectors", "Budget / timeline"]
    iy = 443
    for it in items_in:
        dot(c, 62, iy + 3, r=3, col=ACCENT_GREEN)
        txt(c, it, 74, iy, size=9, col=LIGHT_GREY)
        iy -= 18

    # pipeline arrow
    arrow_right(c, 248, 395, col=AMD_RED)

    # pipeline box
    card(c, 280, 310, 380, 170, col=CARD_BG)
    txt(c, "AGENTIC PIPELINE", 470, 463, size=9, col=AMD_RED, bold=True, align="center")
    stages = ["① Graph RAG Retrieval", "② DRL Prioritisation (AMD MI300X)",
              "③ Qwen-72B Generation (ROCm)", "④ Compliance Verification"]
    sy = 443
    for st in stages:
        dot(c, 298, sy + 3, r=3, col=AMD_RED)
        txt(c, st, 310, sy, size=9, col=WHITE)
        sy -= 18

    # output arrow
    arrow_right(c, 668, 395, col=ACCENT_BLUE)

    # output box
    card(c, 700, 310, 220, 170, col=HexColor("#000A1A"))
    c.setStrokeColor(ACCENT_BLUE)
    c.setLineWidth(1)
    c.roundRect(700, 310, 220, 170, 6, fill=0, stroke=1)
    txt(c, "OUTPUT", 810, 463, size=9, col=ACCENT_BLUE, bold=True, align="center")
    items_out = ["Phased roadmap", "Epics + User Stories", "Compliance score", "Live Jira export"]
    oy = 443
    for it in items_out:
        dot(c, 718, oy + 3, r=3, col=ACCENT_BLUE)
        txt(c, it, 730, oy, size=9, col=LIGHT_GREY)
        oy -= 18

    # features row
    features = [
        ("🧠", "AI Advisor", "Streaming chat grounded\nin 1,416 capabilities"),
        ("📊", "Graph Explorer", "Visual Neo4j knowledge\ngraph browser"),
        ("🗺️", "Strategic Roadmap", "Multi-phase roadmap\nwith Jira export"),
        ("🤖", "AI Learning Engine", "DRL that improves\nwith every session"),
    ]
    fx = 40
    for icon, title, desc in features:
        card(c, fx, 130, 210, 160, col=CARD_BG2)
        txt(c, icon, fx + 105, 262, size=18, align="center")
        txt(c, title, fx + 105, 240, size=10, col=WHITE, bold=True, align="center")
        accent_line(c, 232, col=DIM_GREY, x0=fx + 20, x1=fx + 190, width=1)
        lines = desc.split("\n")
        ly = 218
        for line in lines:
            txt(c, line, fx + 105, ly, size=9, col=LIGHT_GREY, align="center")
            ly -= 14
        fx += 228


# ── Slide 4 — Architecture ────────────────────────────────────────────────────

def slide_architecture(c):
    new_slide(c)
    red_bar(c)
    txt(c, "SYSTEM ARCHITECTURE", 40, H - 34, size=14, col=WHITE, bold=True)
    txt(c, "LangGraph agentic pipeline — retrieve → optimise → generate → verify",
        40, H - 85, size=13, col=LIGHT_GREY)
    accent_line(c, H - 95, x0=40, x1=920)

    # LangGraph pipeline diagram
    stages = [
        ("Retrieve", "Graph RAG\n44 domains\n1,416 caps", ACCENT_BLUE),
        ("Optimise", "DRL Policy\nREINFORCE\nAMD MI300X", ACCENT_AMBER),
        ("Generate", "Qwen-72B\nvLLM / ROCm\nStreaming", AMD_RED),
        ("Verify", "Compliance\nScore ≥70\nAuto-retry", ACCENT_GREEN),
    ]
    bw, bh, gap = 170, 140, 30
    total = len(stages) * bw + (len(stages) - 1) * gap
    sx = (W - total) // 2

    for i, (name, desc, col) in enumerate(stages):
        bx = sx + i * (bw + gap)
        by = 260

        # connector arrow
        if i > 0:
            ax = bx - gap
            c.setStrokeColor(col)
            c.setLineWidth(1.5)
            c.line(ax + 2, by + bh // 2, bx - 2, by + bh // 2)
            p = c.beginPath()
            p.moveTo(bx - 8, by + bh // 2 - 4)
            p.lineTo(bx - 2, by + bh // 2)
            p.lineTo(bx - 8, by + bh // 2 + 4)
            p.close()
            c.setFillColor(col)
            c.drawPath(p, fill=1, stroke=0)

        card(c, bx, by, bw, bh, col=CARD_BG)
        c.setFillColor(col)
        c.rect(bx, by + bh - 24, bw, 24, fill=1, stroke=0)
        txt(c, name, bx + bw // 2, by + bh - 10, size=11, col=WHITE,
            bold=True, align="center")
        lines = desc.split("\n")
        ly = by + bh - 46
        for line in lines:
            txt(c, line, bx + bw // 2, ly, size=9, col=LIGHT_GREY, align="center")
            ly -= 16

        # step number
        c.setFillColor(col)
        c.circle(bx + bw // 2, by - 16, 12, fill=1, stroke=0)
        txt(c, str(i + 1), bx + bw // 2, by - 20, size=10, col=WHITE,
            bold=True, align="center")

    # retry loop indicator
    c.setStrokeColor(ACCENT_AMBER)
    c.setDash(4, 3)
    c.setLineWidth(1)
    ry = 230
    lx = sx + 2 * (bw + gap)
    rx = sx + 3 * (bw + gap) + bw
    c.line(lx, ry, rx, ry)
    c.line(lx, ry, lx, 260)
    c.line(rx, ry, rx, 260)
    c.setDash()
    txt(c, "↺  Auto-retry if compliance score < 70", W // 2, ry - 12, size=8,
        col=ACCENT_AMBER, align="center")

    # state keys
    card(c, 40, 80, W - 80, 120, col=CARD_BG2)
    txt(c, "AgentState Keys:", 60, 180, size=9, col=AMD_RED, bold=True)
    keys = ["request", "enriched_capabilities", "graph_context", "priority_result",
            "roadmap_draft", "compliance_summary", "final_roadmap", "iteration", "timing"]
    kx = 60
    ky = 162
    for k in keys:
        pill(c, kx, ky, k, bg_col=DIM_GREY, text_col=LIGHT_GREY, size=8)
        kx += c.stringWidth(k, "Helvetica-Bold", 8) + 28
        if kx > W - 150:
            kx = 60
            ky -= 22

    txt(c, "Cache layer: MD5(capability_ids + org_type) → Neo4j GeneratedOutput node  (<100ms hit)",
        60, 96, size=8, col=MID_GREY)


# ── Slide 5 — Knowledge Graph ─────────────────────────────────────────────────

def slide_knowledge_graph(c):
    new_slide(c)
    red_bar(c)
    txt(c, "KNOWLEDGE GRAPH", 40, H - 34, size=14, col=WHITE, bold=True)
    txt(c, "Neo4j — the intelligence layer behind every recommendation",
        40, H - 85, size=13, col=LIGHT_GREY)
    accent_line(c, H - 95, x0=40, x1=920)

    # left: node type breakdown
    node_types = [
        ("Domain", "44", AMD_RED, 0.08),
        ("SubDomain", "~220", ACCENT_AMBER, 0.40),
        ("Capability", "1,416", ACCENT_BLUE, 1.00),
        ("Standard", "44+", ACCENT_GREEN, 0.08),
        ("Trend", "44+", HexColor("#9B59B6"), 0.08),
        ("TrainingRun", "132+", HexColor("#E74C3C"), 0.24),
    ]
    ty = 410
    for ntype, count, col, pct in node_types:
        card(c, 40, ty - 28, 320, 32, col=CARD_BG)
        dot(c, 60, ty - 12, r=5, col=col)
        txt(c, ntype, 76, ty - 8, size=10, col=WHITE)
        txt(c, count, 200, ty - 8, size=10, col=col, bold=True)
        progress_bar(c, 240, ty - 20, 108, 8, pct, fg=col)
        ty -= 40

    # centre: relationship types
    rels = [
        ("PARENT_OF", "Domain → SubDomain → Capability hierarchy"),
        ("GOVERNED_BY", "Domain links to ISO / TOGAF / COBIT Standards"),
        ("INFLUENCED_BY", "Domain links to Technology Trends"),
        ("ENABLES", "Cross-domain capability dependencies"),
        ("HAS_SECTOR", "Generic Core to sector-specific domains"),
        ("HAS_MESSAGE", "Chat session persistence"),
    ]
    card(c, 385, 155, 310, 275, col=CARD_BG2)
    txt(c, "Relationship Types", 540, 410, size=10, col=AMD_RED, bold=True, align="center")
    ry2 = 388
    for rel, desc in rels:
        pill(c, 400, ry2, rel, bg_col=DIM_GREY, text_col=ACCENT_BLUE, size=7, pad_x=5)
        txt(c, desc, 530, ry2, size=7.5, col=LIGHT_GREY)
        ry2 -= 34

    # right: schema snippet
    card(c, 710, 155, 210, 275, col=HexColor("#050510"))
    c.setStrokeColor(ACCENT_BLUE)
    c.setLineWidth(0.5)
    c.roundRect(710, 155, 210, 275, 6, fill=0, stroke=1)
    txt(c, "Schema", 815, 410, size=9, col=ACCENT_BLUE, bold=True, align="center")
    schema_lines = [
        "(:Domain {",
        "  id, name, sector,",
        "  drl_trained,",
        "  drl_final_reward",
        "})",
        "",
        "(:Capability {",
        "  id, name, description,",
        "  business_outcomes,",
        "  risk_factors, kpis,",
        "  duration_weeks,",
        "  complexity",
        "})",
    ]
    sly = 394
    for line in schema_lines:
        col = ACCENT_BLUE if line.startswith("(:") else (LIGHT_GREY if line.strip() else WHITE)
        txt(c, line, 722, sly, size=7.5, col=col)
        sly -= 16

    # bottom stats
    stats = [("6,500+", "Nodes seeded", ACCENT_BLUE),
             ("44", "Governance Standards", ACCENT_GREEN),
             ("44", "Innovation Trends", ACCENT_AMBER),
             ("384-dim", "Vector Embeddings", AMD_RED)]
    sx2 = 40
    for val, label, col in stats:
        card(c, sx2, 80, 215, 60, col=CARD_BG)
        txt(c, val, sx2 + 108, 122, size=16, col=col, bold=True, align="center")
        txt(c, label, sx2 + 108, 104, size=8, col=LIGHT_GREY, align="center")
        sx2 += 233


# ── Slide 6 — AMD MI300X + ROCm ──────────────────────────────────────────────

def slide_amd(c):
    new_slide(c)
    red_bar(c)
    txt(c, "AMD MI300X + ROCm", 40, H - 34, size=14, col=WHITE, bold=True)
    txt(c, "The hardware advantage — production-scale AI on AMD Instinct",
        40, H - 85, size=13, col=LIGHT_GREY)
    accent_line(c, H - 95, x0=40, x1=920)

    # left: MI300X specs card
    card(c, 40, 130, 280, 330, col=CARD_BG)
    c.setFillColor(AMD_RED)
    c.rect(40, 430, 280, 30, fill=1, stroke=0)
    txt(c, "AMD Instinct MI300X", 180, 442, size=11, col=WHITE, bold=True, align="center")

    specs = [
        ("Architecture", "CDNA 3"),
        ("HBM3 Memory", "192 GB"),
        ("Memory B/W", "5.3 TB/s"),
        ("FP8 FLOPS", "2,610 TFLOPS"),
        ("Compute Units", "228"),
        ("TDP", "750W"),
        ("Software", "ROCm 6.x"),
    ]
    sy2 = 410
    for key, val in specs:
        txt(c, key, 60, sy2, size=9, col=LIGHT_GREY)
        txt(c, val, 300, sy2, size=9, col=AMD_RED, bold=True, align="right")
        accent_line(c, sy2 - 8, col=DIM_GREY, x0=60, x1=300, width=0.5)
        sy2 -= 28

    # centre: how we use it
    card(c, 340, 130, 290, 330, col=CARD_BG2)
    txt(c, "How We Use AMD", 485, 442, size=10, col=ACCENT_AMBER, bold=True, align="center")
    uses = [
        ("vLLM Inference", "Qwen-72B served via OpenAI-compatible\nendpoint on MI300X — zero code changes"),
        ("DRL Training", "REINFORCE policy network trains on\nROCm via PyTorch — detects via\ntorch.version.hip"),
        ("Embeddings", "sentence-transformers/all-MiniLM-L6-v2\n(384-dim) pre-downloaded into image"),
    ]
    uy = 420
    for title, desc in uses:
        txt(c, title, 358, uy, size=9, col=WHITE, bold=True)
        uy -= 16
        for line in desc.split("\n"):
            txt(c, line, 358, uy, size=8, col=LIGHT_GREY)
            uy -= 14
        uy -= 10

    # right: ROCm integration
    card(c, 650, 130, 270, 330, col=HexColor("#050510"))
    c.setStrokeColor(AMD_RED)
    c.setLineWidth(0.8)
    c.roundRect(650, 130, 270, 330, 6, fill=0, stroke=1)
    txt(c, "ROCm Integration", 785, 442, size=10, col=AMD_RED, bold=True, align="center")
    code_lines = [
        "import torch",
        "",
        "if torch.cuda.is_available():",
        "  device = 'cuda'",
        "  # AMD MI300X detected",
        "  if torch.version.hip:",
        "    log('ROCm: '",
        "        + torch.version.hip)",
        "else:",
        "  device = 'cpu'",
        "",
        "model = model.to(device)",
        "# Trains on MI300X",
        "# or CPU fallback",
    ]
    cly = 424
    for line in code_lines:
        col = ACCENT_BLUE if line.startswith("if") or line.startswith("else") else \
              ACCENT_GREEN if "#" in line else \
              ACCENT_AMBER if "device" in line and "=" in line else WHITE
        txt(c, line, 664, cly, size=7.5, col=col)
        cly -= 16

    # bottom: performance note
    card(c, 40, 80, W - 80, 36, col=HexColor("#1A0000"))
    txt(c, "⚡  MI300X inference throughput noticeably lower latency vs A100 benchmarks  ·  "
        "192 GB HBM3 fits Qwen-72B weights with headroom for batching",
        W // 2, 100, size=9, col=LIGHT_GREY, align="center")


# ── Slide 7 — DRL Engine ──────────────────────────────────────────────────────

def slide_drl(c):
    new_slide(c)
    red_bar(c)
    txt(c, "DEEP REINFORCEMENT LEARNING ENGINE", 40, H - 34, size=14, col=WHITE, bold=True)
    txt(c, "EAPolicyNetwork — learns optimal capability prioritisation per domain",
        40, H - 85, size=13, col=LIGHT_GREY)
    accent_line(c, H - 95, x0=40, x1=920)

    # network diagram
    layers = [
        ("State\nInput", "20-dim\nOrg features", ACCENT_BLUE, 40),
        ("Hidden 1", "Linear 20→128\nReLU + Dropout", ACCENT_AMBER, 210),
        ("Hidden 2", "Linear 128→64\nReLU + Dropout", ACCENT_AMBER, 380),
        ("Action\nOutput", "LogSoftmax\n10-dim ranking", ACCENT_GREEN, 550),
    ]
    for name, desc, col, lx in layers:
        card(c, lx, 270, 150, 160, col=CARD_BG)
        c.setFillColor(col)
        c.rect(lx, 406, 150, 24, fill=1, stroke=0)
        for i, ln in enumerate(name.split("\n")):
            txt(c, ln, lx + 75, 396 - i * 14, size=9, col=WHITE, bold=True, align="center")
        for i, ln in enumerate(desc.split("\n")):
            txt(c, ln, lx + 75, 360 - i * 16, size=8.5, col=LIGHT_GREY, align="center")
        if lx < 550:
            arrow_right(c, lx + 155, 350, col=col)

    # reward function
    card(c, 720, 270, 200, 160, col=CARD_BG2)
    txt(c, "Reward Function", 820, 413, size=9, col=AMD_RED, bold=True, align="center")
    r_items = [
        ("Complexity align.", ACCENT_AMBER),
        ("Budget feasibility", ACCENT_BLUE),
        ("Domain coverage", ACCENT_GREEN),
        ("Range: −1.0 → +1.0", LIGHT_GREY),
    ]
    ry3 = 392
    for label, col in r_items:
        dot(c, 738, ry3 + 3, r=3, col=col)
        txt(c, label, 750, ry3, size=8.5, col=col)
        ry3 -= 22

    # training details row
    details = [
        ("REINFORCE", "Policy gradient\nalgorithm — Williams 1992"),
        ("Gumbel-top-k", "Sample without\nreplacement — no repeats"),
        ("200 episodes", "Pre-trained per domain\nvia seed_graph_cache.py"),
        ("132+ runs", "TrainingRun nodes\nstored in Neo4j"),
    ]
    dx = 40
    for title, desc in details:
        card(c, dx, 130, 210, 120, col=CARD_BG)
        txt(c, title, dx + 105, 228, size=10, col=WHITE, bold=True, align="center")
        accent_line(c, 220, col=DIM_GREY, x0=dx + 15, x1=dx + 195, width=1)
        for i, line in enumerate(desc.split("\n")):
            txt(c, line, dx + 105, 204 - i * 16, size=8.5, col=LIGHT_GREY, align="center")
        dx += 228

    # auto-enrichment note
    card(c, 40, 80, W - 80, 36, col=HexColor("#001A0A"))
    txt(c, "🔄  Chat-triggered enrichment: each EA Advisor session auto-trains any untrained domain "
        "(50 episodes, fire-and-forget) — the graph continuously improves itself",
        W // 2, 100, size=9, col=LIGHT_GREY, align="center")


# ── Slide 8 — Platform Features ──────────────────────────────────────────────

def slide_features(c):
    new_slide(c)
    red_bar(c)
    txt(c, "PLATFORM FEATURES", 40, H - 34, size=14, col=WHITE, bold=True)
    txt(c, "7-tab Streamlit application — fully deployed on Hugging Face Docker SDK",
        40, H - 85, size=13, col=LIGHT_GREY)
    accent_line(c, H - 95, x0=40, x1=920)

    tabs = [
        ("EA Advisor", "🧠",
         ["Streaming chat with SSE", "Knowledge Graph RAG grounding",
          "Session persistence (Neo4j)", "Auto DRL enrichment trigger"],
         AMD_RED),
        ("Graph Explorer", "🌐",
         ["Force-directed domain network", "Full enriched domain breakdown",
          "Standards + Trends per domain", "Capability deep-dives"],
         ACCENT_BLUE),
        ("Strategic Roadmap", "🗺️",
         ["Phased roadmap generation", "Compliance score verification",
          "Export to PDF / JSON", "Jira Epic creation"],
         ACCENT_GREEN),
        ("AI Learning Engine", "🤖",
         ["Training heatmap coverage", "Reward progression charts",
          "Sector-level benchmarks", "Manual training trigger"],
         ACCENT_AMBER),
    ]

    tx = 40
    for name, icon, features, col in tabs:
        card(c, tx, 140, 210, 290, col=CARD_BG)
        c.setFillColor(col)
        c.rect(tx, 400, 210, 30, fill=1, stroke=0)
        txt(c, f"{icon}  {name}", tx + 105, 412, size=10, col=WHITE, bold=True, align="center")
        fy = 378
        for feat in features:
            dot(c, tx + 20, fy + 3, r=3, col=col)
            txt(c, feat, tx + 32, fy, size=8.5, col=LIGHT_GREY)
            fy -= 22
        tx += 228

    # additional features footer
    extras = ["Integrations tab (Jira live · ServiceNow · Azure DevOps)",
              "Export & Handover (full package download)",
              "ArchiMate layer classification (Business / Application / Technology)",
              "ERP/CRM CSV ingest → Neo4j ExternalSystem nodes"]
    card(c, 40, 80, W - 80, 46, col=CARD_BG2)
    ex = 60
    ey = 114
    for i, extra in enumerate(extras):
        dot(c, ex, ey + 3, r=3, col=LIGHT_GREY)
        txt(c, extra, ex + 14, ey, size=8, col=LIGHT_GREY)
        ey -= 16
        if i == 1:
            ex = 500
            ey = 114


# ── Slide 9 — Demo Flow ───────────────────────────────────────────────────────

def slide_demo(c):
    new_slide(c)
    red_bar(c)
    txt(c, "LIVE DEMO FLOW", 40, H - 34, size=14, col=WHITE, bold=True)
    txt(c, "5 steps from zero to Jira-ready roadmap", 40, H - 85, size=13, col=LIGHT_GREY)
    accent_line(c, H - 95, x0=40, x1=920)

    steps = [
        ("1", "Questionnaire", AMD_RED,
         "Select organisation type,\nstrategic goals, sectors,\nbudget & timeline",
         "Input Form tab"),
        ("2", "Graph RAG", ACCENT_BLUE,
         "Retriever expands queries via\nLLM, runs vector similarity\nsearch + Cypher traversal",
         "~2-3 seconds"),
        ("3", "DRL Optimise", ACCENT_AMBER,
         "Policy network scores and\nranks top-40 capabilities\nby value and feasibility",
         "AMD MI300X"),
        ("4", "Qwen Generates", AMD_RED,
         "72B model produces phased\nroadmap with governance\ncitations and KPIs",
         "Streaming SSE"),
        ("5", "Verify + Export", ACCENT_GREEN,
         "Compliance verifier scores\nthe output; Jira Epics\ncreated via REST API v3",
         "Live Jira export"),
    ]

    sw = 158
    sx3 = 30
    for step in steps:
        num, name, col, desc, note = step
        card(c, sx3, 180, sw, 260, col=CARD_BG)
        # number circle
        c.setFillColor(col)
        c.circle(sx3 + sw // 2, 420, 22, fill=1, stroke=0)
        txt(c, num, sx3 + sw // 2, 413, size=16, col=WHITE, bold=True, align="center")
        # name bar
        c.setFillColor(HexColor("#1A1A1A"))
        c.rect(sx3, 380, sw, 24, fill=1, stroke=0)
        txt(c, name, sx3 + sw // 2, 388, size=10, col=col, bold=True, align="center")
        # description
        dy = 368
        for line in desc.split("\n"):
            txt(c, line, sx3 + sw // 2, dy, size=8, col=LIGHT_GREY, align="center")
            dy -= 15
        # note pill
        pill(c, sx3 + (sw - c.stringWidth(note, "Helvetica-Bold", 7) - 10) // 2,
             192, note, bg_col=DIM_GREY, text_col=LIGHT_GREY, size=7)

        if sx3 + sw + 30 < W - 30:
            arrow_right(c, sx3 + sw + 2, 310, col=col)

        sx3 += sw + 32

    # timing note
    card(c, 40, 110, W - 80, 52, col=HexColor("#001A1A"))
    txt(c, "⏱  Typical end-to-end time", 60, 150, size=9, col=ACCENT_BLUE, bold=True)
    timings = [("RAG retrieval", "2-3s"), ("DRL optimise", "<1s"),
               ("LLM generation", "15-45s"), ("Compliance verify", "5-10s"),
               ("Jira export", "3-5s"), ("Cached hit", "<100ms")]
    tx2 = 280
    for label, time in timings:
        txt(c, label, tx2, 148, size=8, col=LIGHT_GREY)
        pill(c, tx2, 127, time, bg_col=AMD_RED, size=8)
        tx2 += 112


# ── Slide 10 — Business Value ─────────────────────────────────────────────────

def slide_business(c):
    new_slide(c)
    red_bar(c)
    txt(c, "BUSINESS VALUE", 40, H - 34, size=14, col=WHITE, bold=True)
    txt(c, "Democratising enterprise architecture for emerging markets",
        40, H - 85, size=13, col=LIGHT_GREY)
    accent_line(c, H - 95, x0=40, x1=920)

    # impact metrics
    metrics = [
        ("$1.5M", "avg consulting cost\nreplaced", AMD_RED),
        ("10 min", "vs 6-18 months\ntraditional", ACCENT_AMBER),
        ("44", "industry sectors\ncovered", ACCENT_BLUE),
        ("100%", "governance-grounded\noutput", ACCENT_GREEN),
    ]
    mx = 40
    for val, label, col in metrics:
        card(c, mx, 350, 210, 110, col=CARD_BG)
        txt(c, val, mx + 105, 430, size=22, col=col, bold=True, align="center")
        for i, ln in enumerate(label.split("\n")):
            txt(c, ln, mx + 105, 405 - i * 16, size=9, col=LIGHT_GREY, align="center")
        mx += 228

    # target markets
    card(c, 40, 195, 420, 140, col=CARD_BG2)
    txt(c, "Target Markets", 60, 315, size=10, col=AMD_RED, bold=True)
    markets = [
        "🏦  Banks & FinTechs — regulatory compliance roadmaps",
        "🏥  Hospitals & Health Systems — HL7 FHIR & interoperability",
        "✈️  Aviation & Logistics — operational capability mapping",
        "🌾  Agribusiness — food supply chain digitalisation",
        "🔒  Government & Defense — cybersecurity architecture",
    ]
    my = 297
    for m in markets:
        txt(c, m, 60, my, size=8.5, col=LIGHT_GREY)
        my -= 20

    # value props
    card(c, 480, 195, 440, 140, col=CARD_BG2)
    txt(c, "Unique Value Propositions", 500, 315, size=10, col=ACCENT_GREEN, bold=True)
    props = [
        "✓  Africa / Kenya-first: local regulatory context",
        "✓  DRL improves with every session — self-learning",
        "✓  Graph output — not flat text, structured knowledge",
        "✓  Jira integration bridges strategy to delivery",
        "✓  Open platform — extensible to any domain",
    ]
    py = 297
    for p in props:
        txt(c, p, 500, py, size=8.5, col=LIGHT_GREY)
        py -= 20

    # bottom: market size
    card(c, 40, 110, W - 80, 68, col=CARD_BG)
    txt(c, "Market Opportunity", 60, 162, size=9, col=AMD_RED, bold=True)
    txt(c, "Global EA tools & consulting market: $47B (2024) → $89B (2030)  ·  "
        "Africa digital transformation spend: $22B (2025)  ·  "
        "SME EA tools segment: fastest-growing sub-market at 24% CAGR",
        60, 140, size=8.5, col=LIGHT_GREY)
    txt(c, "Our target beachhead: 50,000 mid-size enterprises in Kenya, Nigeria, South Africa "
        "currently underserved by enterprise-grade EA tooling",
        60, 122, size=8.5, col=MID_GREY)


# ── Slide 11 — Tech Stack ─────────────────────────────────────────────────────

def slide_stack(c):
    new_slide(c)
    red_bar(c)
    txt(c, "TECHNOLOGY STACK", 40, H - 34, size=14, col=WHITE, bold=True)
    txt(c, "Production-grade, cloud-native, AMD-first", 40, H - 85, size=13, col=LIGHT_GREY)
    accent_line(c, H - 95, x0=40, x1=920)

    layers_data = [
        ("LLM Inference", AMD_RED, [
            "Qwen/Qwen2.5-72B-Instruct", "AMD MI300X via vLLM",
            "ROCm GPU compute", "OpenAI-compatible SSE streaming",
            "Together.ai fallback",
        ]),
        ("Agentic Orchestration", ACCENT_AMBER, [
            "LangGraph StateGraph", "4-node pipeline",
            "Compliance auto-retry loop", "AgentState typed dict",
            "Async / await throughout",
        ]),
        ("Knowledge Graph", ACCENT_BLUE, [
            "Neo4j Community 5.x", "Cypher + vector index",
            "384-dim embeddings (MiniLM)", "6,500+ nodes seeded",
            "Output caching layer",
        ]),
        ("Backend / Frontend", ACCENT_GREEN, [
            "FastAPI + async routes", "Streamlit 7-tab UI",
            "SSE streaming responses", "Plotly + NetworkX graphs",
            "Docker + supervisord (HF)",
        ]),
    ]

    lx = 40
    for layer_name, col, items in layers_data:
        card(c, lx, 130, 215, 310, col=CARD_BG)
        c.setFillColor(col)
        c.rect(lx, 410, 215, 30, fill=1, stroke=0)
        txt(c, layer_name, lx + 108, 422, size=9, col=WHITE, bold=True, align="center")
        iy = 396
        for item in items:
            dot(c, lx + 18, iy + 3, r=3, col=col)
            txt(c, item, lx + 30, iy, size=8.5, col=LIGHT_GREY)
            iy -= 22
        lx += 233

    # bottom badges
    card(c, 40, 80, W - 80, 36, col=CARD_BG2)
    badges = ["Python 3.12", "PyTorch ROCm", "sentence-transformers",
              "Pydantic-settings", "Jira REST v3", "LFS-free HF deploy",
              "LangGraph 0.2", "neo4j-python-driver", "Plotly"]
    bx3 = 60
    by3 = 100
    for badge in badges:
        w = c.stringWidth(badge, "Helvetica-Bold", 8) + 16
        pill(c, bx3, by3, badge, bg_col=DIM_GREY, text_col=LIGHT_GREY, size=8)
        bx3 += w + 8
        if bx3 > W - 120:
            bx3 = 60
            by3 -= 20


# ── Slide 12 — Thank You ──────────────────────────────────────────────────────

def slide_closing(c):
    new_slide(c)
    bg(c)

    # red left band
    c.setFillColor(AMD_RED)
    c.rect(0, 0, 8, H, fill=1, stroke=0)

    # top bar
    c.setFillColor(HexColor("#1A0000"))
    c.rect(0, H - 56, W, 56, fill=1, stroke=0)
    txt(c, "AMD Developer Hackathon 2026", W // 2, H - 22, size=11,
        col=LIGHT_GREY, align="center")
    txt(c, "Track 1: AI Agents & Agentic Workflows  ·  Hugging Face Special Prize",
        W // 2, H - 38, size=9, col=MID_GREY, align="center")

    txt(c, "Thank You", W // 2, 400, size=40, col=WHITE, bold=True, align="center")
    accent_line(c, 378, col=AMD_RED, x0=300, x1=660, width=2)
    txt(c, "AMD EA Strategy Optimizer", W // 2, 350, size=18, col=AMD_RED,
        bold=True, align="center")
    txt(c, "Agentic Enterprise Architecture Intelligence — powered by AMD MI300X",
        W // 2, 325, size=11, col=LIGHT_GREY, align="center")

    # CTA cards
    ctas = [
        ("🚀  Live Demo", "huggingface.co/spaces/\nTheQuantEd/EA_strat_optimizer", ACCENT_BLUE),
        ("⭐  Like on HF", "A ❤️ supports us for the\nHugging Face Special Prize", ACCENT_AMBER),
        ("💼  LinkedIn", "linkedin.com/in/\ngodwin-edgar-opuka", AMD_RED),
    ]
    cx2 = 120
    for label, detail, col in ctas:
        card(c, cx2, 190, 230, 110, col=CARD_BG)
        c.setFillColor(col)
        c.rect(cx2, 276, 230, 24, fill=1, stroke=0)
        txt(c, label, cx2 + 115, 284, size=10, col=WHITE, bold=True, align="center")
        dy2 = 262
        for line in detail.split("\n"):
            txt(c, line, cx2 + 115, dy2, size=8.5, col=LIGHT_GREY, align="center")
            dy2 -= 16
        cx2 += 260

    # stack tags
    tags = ["Qwen-72B", "AMD MI300X", "ROCm", "LangGraph", "Neo4j",
            "DRL/REINFORCE", "Graph RAG", "FastAPI", "Streamlit"]
    tx3 = (W - sum(c.stringWidth(t, "Helvetica-Bold", 9) + 24 for t in tags)) // 2
    for tag in tags:
        w = pill(c, tx3, 155, tag, bg_col=DIM_GREY, text_col=LIGHT_GREY, size=9)
        tx3 += w + 8

    # footer
    c.setFillColor(HexColor("#111111"))
    c.rect(0, 0, W, 40, fill=1, stroke=0)
    txt(c, "🔗 huggingface.co/spaces/TheQuantEd/EA_strat_optimizer     💼 linkedin.com/in/godwin-edgar-opuka",
        W // 2, 15, size=8, col=MID_GREY, align="center")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    c = canvas.Canvas(OUT, pagesize=(W, H))
    c.setTitle("AMD EA Strategy Optimizer — Pitch Deck")
    c.setAuthor("Godwin Edgar Opuka")
    c.setSubject("AMD Developer Hackathon 2026")

    # Slide 1 — first page, no showPage() needed
    bg(c)
    slide_cover(c)

    slide_problem(c)
    slide_solution(c)
    slide_architecture(c)
    slide_knowledge_graph(c)
    slide_amd(c)
    slide_drl(c)
    slide_features(c)
    slide_demo(c)
    slide_business(c)
    slide_stack(c)
    slide_closing(c)

    c.save()
    print(f"✓  Saved {OUT}  (12 slides)")


if __name__ == "__main__":
    main()
