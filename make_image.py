#!/usr/bin/env python3
"""news-image-20261120 v21 - fresh build from prompt-v74.md.
'One Day in the World' front page, Friday 20 November 2026.
Python + Pillow only. Deterministic. 1024x1024, under 1 MiB.
Fonts: DejaVu Serif / DejaVu Sans only.
Layout per prompt-v74: kicker, centred date, double rule, two strips,
region bar, 3 leads, 10 mediums, real map, compact list, DATE CHECK, footer.
6 regions (Middle East counts as Asia - no separate Middle East)."""

import json
import os
from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
M = 14                      # margin
CW = 996                    # content width (x 14..1010)
PAPER = (250, 246, 235)
INK = (18, 18, 18)
DARK = (25, 25, 25)
GREY = (90, 90, 90)
RED = (178, 30, 45)
FRAME = (176, 166, 148)
DIV = (168, 158, 142)
MAPFILL = (243, 238, 224)
PINK = (255, 215, 215)
NAVY = (23, 42, 74)

REGCOL = {
    "EU": (70, 120, 200), "AS": (198, 55, 65), "AF": (60, 140, 70),
    "AM": (138, 92, 182), "OC": (40, 140, 150), "WO": (120, 120, 120),
}
BARCOL = dict(REGCOL)
BARCOL["AF"] = (78, 158, 88)
BARCOL["OC"] = (58, 168, 178)
BARCOL["WO"] = (148, 148, 148)
REGNAME = {"EU": "EUROPE", "AS": "ASIA", "AF": "AFRICA",
           "AM": "AMERICAS", "OC": "OCEANIA", "WO": "WORLD"}
REGCOUNT = [("EU", 8), ("AS", 8), ("AF", 4), ("AM", 10), ("OC", 2), ("WO", 3)]

FD = "/usr/share/fonts/truetype/dejavu/"
FONTS = {
    ("serif", False): FD + "DejaVuSerif.ttf",
    ("serif", True): FD + "DejaVuSerif-Bold.ttf",
    ("sans", False): FD + "DejaVuSans.ttf",
    ("sans", True): FD + "DejaVuSans-Bold.ttf",
}
_cache = {}


def F(family, size, bold=False):
    key = (family, round(float(size), 1), bold)
    if key not in _cache:
        _cache[key] = ImageFont.truetype(FONTS[(family, bold)], float(size))
    return _cache[key]


def tw(text, font):
    return font.getlength(text)


def wrap(draw, text, font, max_w):
    """Greedy word wrap; returns list of lines (each fits max_w)."""
    words = text.split()
    lines, cur = [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if tw(t, font) <= max_w or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def wrap_segments(draw, segs, font_fn, max_w):
    """Wrap a list of (text, font) segments into lines; each line is a list
    of (text, font) pieces. Keeps segment boundaries; never splits a word."""
    # flatten to words with their font
    words = []
    for text, font in segs:
        for w in text.split(" "):
            words.append((w, font))
    lines, cur, cur_w = [], [], 0.0
    space_w = {}
    for w, font in words:
        sw = font.getlength(" ")
        ww = font.getlength(w)
        add = ww if not cur else sw + ww
        if cur and cur_w + add > max_w:
            lines.append(cur)
            cur, cur_w = [(w, font)], ww
        else:
            cur.append((w, font))
            cur_w += add
    if cur:
        lines.append(cur)
    return lines


def draw_segs_line(draw, x, y, line, gap=0):
    """Draw one wrapped segment line; returns width used."""
    cx = x
    for i, (t, font) in enumerate(line):
        draw.text((cx, y), t, font=font, fill=font._fill if hasattr(font, "_fill") else INK)
        cx += font.getlength(t)
        if i < len(line) - 1:
            cx += font.getlength(" ")
    return cx - x


def fit_size(text, family, start, max_w, bold=False, minimum=6):
    size = float(start)
    while size > minimum and F(family, size, bold).getlength(text) > max_w:
        size -= 0.5
    return size


# ---------------------------------------------------------------- data
# region key: 1 EU 2 AS 3 AS 4 EU 5 EU 6 EU 7 AS 8 EU 9 AS 10 AF 11 AM 12 AS
# 13 OC 14 AS 15 AM 16 AS 17 EU 18 WO 19 EU 20 AF 21 AF 22 AF 23 WO 24 AM
# 25 AM 26 AM 27 AM 28 AS 29 OC 30 WO 31 EU 32 AM 33 AM 34 AM 35 AM
LEADS = [
    dict(n=1, reg="EU", banner="KYIV", badge="REPORTED · JUST SECURITY",
         desc="3 bridges hit", kicker="1. KYIV, UKRAINE · WAR",
         head="Russian missiles hit three Kyiv bridges",
         summ="Missiles and drones hit bridges overnight; 8 killed, 28 hurt in nine regions, power cut in Kyiv. (Just Security)",
         summ_trim="Missiles and drones hit bridges overnight; 8 killed, 28 hurt, power cut in Kyiv. (Just Security)"),
    dict(n=2, reg="AS", banner="CYCLONE AKVAN", badge="OFFICIAL · IMD",
         desc="Comes ashore in India", kicker="2. GOPALPUR, INDIA · WEATHER",
         head="Cyclone Akvan comes ashore in India",
         summ="Akvan came ashore near Gopalpur; 300,000+ moved to shelters, no deaths. (IMD, The Hindu)"),
    dict(n=3, reg="AS", banner="AI SELL-OFF", badge="REPORTED · REUTERS",
         desc="Asia's markets sink", kicker="3. ASIA · MARKETS",
         head="AI sell-off sinks Asia's stock markets",
         summ="Nasdaq fell 5.3% in its worst week since 2020; Taiwan's Taiex fell 6.2% on Friday. (Reuters)"),
]
MEDIUMS = [
    dict(n=4, reg="EU", banner="UK-EU", src="BBC", kicker="4. UK & EU · DEAL",
         head="UK and EU seal a 'reset' deal",
         summ="100,000-a-year youth mobility agreed. (BBC)"),
    dict(n=5, reg="EU", banner="COP31", src="Japan Times", kicker="5. TÜRKİYE · CLIMATE",
         head="COP31 ends with no deal",
         summ="Draft text leaves out fossil fuels. (Japan Times)"),
    dict(n=6, reg="EU", banner="POLAND", src="Just Security", kicker="6. POLAND · WAR",
         head="Russia breaches Polish airspace",
         summ="3 objects crossed the border overnight. (Just Security)"),
    dict(n=7, reg="AS", banner="IRAQ", src="Euronews", kicker="7. IRAQ · SECURITY",
         head="Iraqi army enters militia stronghold",
         summ="Troops deploy to Jurf al-Sakhar. (Euronews)"),
    dict(n=8, reg="EU", banner="ITALY", src="France 24", kicker="8. ITALY · LABOUR",
         head="Strike over Italy's budget",
         summ="Workers and students march. (France 24)"),
    dict(n=9, reg="AS", banner="SEOUL", src="Japan Times", kicker="9. SEOUL · COURTS",
         head="Seoul voids ex-PM Han verdict",
         summ="Court orders a retrial. (Japan Times)"),
    dict(n=10, reg="AF", banner="SUDAN", src="AllAfrica", kicker="10. SUDAN · WAR",
         head="Drone strike kills 10 at mine",
         summ="At least 10 dead at Bajoun mine. (AllAfrica)"),
    dict(n=11, reg="AM", banner="COLOMBIA", src="Al Jazeera", kicker="11. COLOMBIA · PROTEST",
         head="Colombia tax protests swell",
         summ="Unions & students march in Bogota. (Al Jazeera)"),
    dict(n=12, reg="AS", banner="GAZA", src="BBC", kicker="12. GAZA · WAR",
         head="Israeli troops cross Gaza line",
         summ="First breach since ceasefire. (BBC)"),
    dict(n=13, reg="OC", banner="PHILLIPS", src="Cricbuzz", kicker="13. WELLINGTON · CRICKET",
         head="Phillips hits 118 against India",
         summ="NZ reach 368; India 159/1. (Cricbuzz)"),
]
COMPACT = [
    (14, "AS", "RIYADH", "Houthi missile hits tower (Sky News)"),
    (15, "AM", "SAN FRANCISCO", "Anthropic -9% day two (Reuters)"),
    (16, "AS", "TANKER", "Burns after a mine strike (Japan Times)"),
    (17, "EU", "ESTONIA", "Border with Russia to shut (Just Security)"),
    (18, "WO", "WORLDWIDE", "25-nation youth strike (Straits Times)"),
    (19, "EU", "LONDON", "London-born told not British (Guardian)"),
    (20, "AF", "SOUTH AFRICA", "Lindela review (France 24)"),
    (21, "AF", "SUDAN", "Halts imports from Kenya (BBC)"),
    (22, "AF", "SOMALIA", "Expels UAE envoy (Africanews)"),
    (23, "WO", "TENNIS", "Medvedev bt Tiafoe 6-3, 6-4 (TNT Sports)"),
    (24, "AM", "WASHINGTON", "WH fires cyber chief (France 24)"),
    (25, "AM", "WASHINGTON", "Trump pardons Pete Rose (BBC)"),
    (26, "AM", "CALIFORNIA", "Mailchimp $3.68B sale (Investopedia)"),
    (27, "AM", "NEW YORK", "GTA 6 sales pass $2.3bn (BBC)"),
    (28, "AS", "TOKYO", "SBC Medical breach hits 2m (SecurityWeek)"),
    (29, "OC", "KENYA", "Jepchirchir banned for 3 years (ABC News)"),
    (30, "WO", "INDIA", "Under-17s qualify for Asian Cup (IANS)"),
    (31, "EU", "BRAZIL", "Lula backs Sanchez in Spain (Euronews)"),
    (32, "AM", "BRAZIL", "Raoni land recognised (Al Jazeera)"),
    (33, "AM", "BRAZIL", "Sells $1bn of reserves (MercoPress)"),
    (34, "AM", "ARGENTINA", "Tesla opens for business (Reuters)"),
    (35, "AM", "LAS VEGAS", "F1 practice cancelled (Kendanafrica)"),
]

STRIP1 = [
    ("OVERNIGHT", "Kyiv bridges hit"),
    ("EARLY", "Akvan makes landfall"),
    ("MORNING", "Taiwan ends \u22126.2%"),
    ("MID-MORNING", "Poland airspace breached"),
    ("MIDDAY", "COP31 closes, no deal"),
    ("EVENING", "Medvedev beats Tiafoe"),
    ("CLOSE", "Nasdaq ends \u22125.3%"),
]
STRIP2 = [
    ("3", "bridges damaged over the Dnipro in Kyiv"),
    ("300,000+", "people moved to shelters before Akvan"),
    ("\u22126.2%", "Taiwan's Taiex at Friday's close"),
    ("100,000", "youth visas a year under the UK-EU deal"),
    ("\u22125.3%", "Nasdaq's fall, worst week since 2020"),
    ("118", "runs by Glenn Phillips against India"),
]
DATECHECK = ("DATE CHECK \u2014 Left out as other days' news: the Shenzhen summit "
             "itself \u00b7 ICJ Myanmar Rohingya verdict \u00b7 GTA VI midnight launch "
             "\u00b7 BepiColombo's Mercury orbit entry. Not yet happened: any final "
             "COP31 text \u00b7 the ATP Finals final.")
FOOTER = ("Every story here happened, or was first reported, on Friday 20 November "
          "2026. Sources named beside each story.")

# --- map coastline data (lon/lat polygons, from v19 lineage; shared material)
# order: NA, Greenland, SA, Europe, UK, Africa, Madagascar, Asia, Japan,
# Taiwan, Sri Lanka, Australia, NZ north, NZ south
CONTINENTS_LL = [
    [(-168, 66), (-163, 60), (-156, 58), (-149, 61), (-140, 60), (-135, 57),
     (-129, 52), (-125, 49), (-124, 43), (-121, 37), (-117, 33), (-113, 29),
     (-109, 25), (-106, 22), (-100, 18), (-95, 16), (-90, 14), (-86, 12),
     (-83, 9), (-79, 8), (-77, 8), (-80, 10), (-82, 14), (-85, 15),
     (-88, 17), (-90, 21), (-91, 19), (-95, 19), (-97, 23), (-97, 26),
     (-94, 29), (-90, 29), (-85, 30), (-81, 26), (-80, 31), (-76, 34),
     (-74, 39), (-70, 42), (-67, 44), (-64, 44), (-60, 46), (-55, 47),
     (-58, 50), (-63, 53), (-65, 58), (-68, 58), (-72, 62), (-77, 62),
     (-80, 58), (-84, 56), (-88, 56), (-92, 57), (-90, 61), (-87, 64),
     (-89, 66), (-95, 69), (-105, 68), (-115, 69), (-125, 70), (-135, 69),
     (-145, 70), (-155, 71), (-162, 70), (-166, 68)],
    [(-58, 64), (-53, 60), (-45, 60), (-40, 63), (-33, 68), (-25, 70),
     (-20, 72), (-28, 73), (-40, 73), (-50, 71), (-57, 69), (-60, 66)],
    [(-77, 8), (-75, 10), (-72, 12), (-68, 11), (-64, 10), (-60, 8),
     (-55, 6), (-52, 5), (-50, 0), (-45, -3), (-39, -5), (-35, -8),
     (-37, -13), (-39, -18), (-41, -23), (-48, -27), (-52, -33), (-57, -38),
     (-62, -41), (-66, -45), (-68, -50), (-69, -54), (-72, -54), (-74, -50),
     (-73, -44), (-73, -37), (-72, -30), (-70, -23), (-70, -18), (-75, -15),
     (-79, -8), (-81, -4), (-80, 1), (-78, 5)],
    [(-9, 43), (-9, 37), (-6, 36), (-2, 37), (0, 39), (3, 42), (7, 44),
     (10, 44), (12, 42), (14, 40), (16, 38), (16, 40), (18, 40), (15, 44),
     (13, 45), (19, 45), (21, 42), (23, 40), (26, 38), (23, 36), (27, 37),
     (30, 36), (30, 40), (28, 45), (30, 46), (32, 47), (30, 50), (28, 54),
     (25, 57), (22, 59), (21, 60), (18, 59), (18, 63), (13, 65), (11, 63),
     (7, 61), (5, 60), (5, 58), (8, 57), (10, 55), (8, 54), (8, 52),
     (5, 53), (3, 53), (3, 51), (1, 51), (-2, 50), (-4, 48), (-2, 47),
     (-1, 44), (-2, 43)],
    [(-5, 50), (-3, 53), (-5, 55), (-4, 57), (-2, 58), (-1, 57), (0, 54),
     (1, 51), (-1, 50), (-3, 50)],
    [(-6, 35), (-10, 31), (-14, 28), (-16, 22), (-17, 15), (-16, 12),
     (-13, 8), (-8, 5), (-4, 5), (2, 6), (6, 4), (9, 4), (12, 0),
     (12, -5), (13, -10), (12, -17), (14, -22), (16, -28), (19, -34),
     (26, -34), (31, -29), (32, -26), (35, -22), (39, -17), (40, -11),
     (41, -6), (43, -2), (47, 0), (51, 2), (51, 11), (48, 11), (44, 11),
     (43, 12), (40, 15), (38, 18), (37, 22), (35, 28), (34, 29), (34, 31),
     (32, 31), (30, 32), (25, 32), (20, 32), (15, 32), (10, 34), (5, 37),
     (0, 36), (-6, 35)],
    [(44, -16), (47, -15), (50, -16), (49, -20), (46, -25), (43, -23),
     (43, -19)],
    [(27, 37), (30, 36), (33, 36), (36, 36), (36, 33), (35, 31), (35, 29),
     (39, 31), (42, 29), (44, 29), (47, 30), (48, 29), (50, 26), (52, 25),
     (54, 24), (57, 25), (59, 22), (61, 25), (63, 25), (66, 25), (68, 23),
     (70, 20), (72, 20), (73, 16), (75, 13), (77, 8), (80, 8), (80, 13),
     (82, 17), (85, 19), (88, 22), (91, 22), (93, 17), (95, 16), (97, 15),
     (99, 11), (101, 8), (103, 7), (105, 9), (107, 11), (109, 13),
     (106, 20), (108, 18), (110, 20), (114, 22), (117, 23), (120, 25),
     (122, 28), (120, 32), (122, 35), (122, 38), (124, 37), (126, 35),
     (129, 35), (129, 37), (127, 40), (130, 42), (132, 43), (135, 44),
     (138, 46), (141, 50), (142, 54), (140, 59), (142, 60), (156, 60),
     (162, 60), (162, 65), (170, 66), (178, 65), (180, 66), (178, 68),
     (170, 70), (160, 70), (150, 72), (140, 72), (130, 72), (120, 73),
     (110, 73), (100, 75), (90, 75), (80, 73), (70, 72), (68, 70),
     (60, 69), (55, 68), (50, 68), (45, 68), (40, 67), (35, 66), (32, 65),
     (30, 62), (28, 60), (30, 58), (28, 56), (30, 55), (28, 52), (30, 50),
     (32, 48), (30, 46), (28, 44), (27, 41)],
    [(130, 31), (132, 33), (134, 34), (137, 35), (139, 36), (141, 38),
     (141, 41), (140, 43), (142, 44), (144, 43), (141, 40), (139, 37),
     (136, 35), (133, 34), (130, 33)],
    [(120, 22), (121, 23), (122, 25), (121, 25), (120, 23)],
    [(80, 6), (81, 7), (81, 9), (80, 8)],
    [(114, -22), (114, -30), (115, -34), (118, -35), (124, -33), (129, -32),
     (132, -32), (135, -35), (138, -35), (140, -38), (145, -38), (150, -37),
     (153, -32), (153, -27), (150, -23), (146, -19), (142, -15), (142, -11),
     (141, -13), (137, -12), (136, -15), (135, -12), (132, -11), (130, -13),
     (127, -14), (124, -17), (122, -17), (119, -20), (114, -22)],
    [(173, -35), (176, -37), (178, -38), (176, -40), (174, -41), (173, -39),
     (172, -37)],
    [(167, -45), (169, -43), (171, -42), (173, -41), (172, -43), (170, -46),
     (167, -46)],
]
POLY_REG = ["AM", "AM", "AM", "EU", "EU", "AF", "AF",
            "AS", "AS", "AS", "AS", "OC", "OC", "OC"]
# pin (n, map-x, map-y) in the 380x84 map, nudged so none overlap (14px dia)
MAP_PINS = [(1, 226, 12), (2, 280, 40), (3, 312, 38), (4, 188, 14),
            (5, 214, 32), (6, 208, 12), (7, 244, 27), (8, 196, 26),
            (9, 326, 30), (10, 218, 48), (11, 112, 49), (12, 230, 36),
            (13, 371, 76)]


# ---------------------------------------------------------------- scenes
# Each scene draws on its own transparent layer exactly the size of its art
# box, at 3x, then downscales with LANCZOS. Scene content stays below the
# banner zone (top 34px leads / 30px mediums) and, for leads, below the
# 13px descriptor strip. `top` = first 3x y where scene content may start.
S3 = 3


def scene_layer(w, h):
    img = Image.new("RGBA", (w * S3, h * S3), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)


def paste_scene(page, layer, x, y, w, h):
    small = layer.resize((w, h), Image.LANCZOS)
    page.paste(small, (x, y), small)


def chip(d, x, y, text, font, fg, bg):
    """Small label chip; returns its width."""
    tw_ = font.getlength(text)
    pad = 4 * S3
    hgt = int(font.size * 1.7)
    d.rounded_rectangle([x, y, x + tw_ + pad * 2, y + hgt], radius=3 * S3, fill=bg)
    d.text((x + pad, y + (hgt - font.size) / 2 - 1 * S3), text, font=font, fill=fg)
    return tw_ + pad * 2


def star(d, cx, cy, r, color):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)


import math
import random


# --- v22 realism helpers ---------------------------------------------------
def _win_grid(d, x0, y0, x1, y1, cols, rows, lit, dark, seed=0, lit_p=0.55):
    """Grid of small windows, some lit warm, some dark."""
    rnd = random.Random(seed)
    cw = (x1 - x0) / cols
    ch = (y1 - y0) / rows
    for r in range(rows):
        for c in range(cols):
            wx = x0 + c * cw + cw * 0.22
            wy = y0 + r * ch + ch * 0.22
            col = lit if rnd.random() < lit_p else dark
            d.rectangle([wx, wy, wx + cw * 0.56, wy + ch * 0.56], fill=col)


def _puff(d, cx, cy, r, tones):
    """Smoke/dust cloud: overlapping circles in several grey tones."""
    for (dx, dy, rr, col) in tones:
        d.ellipse([cx + dx - rr, cy + dy - rr, cx + dx + rr, cy + dy + rr], fill=col)


def _person(d, px, py, hgt, shirt, skin=(238, 198, 158), hair=(45, 32, 24),
            arm_up=True, trousers=(45, 45, 55)):
    """Small standing figure, feet at (px, py), total height hgt (3x px)."""
    s = S3
    hr = hgt * 0.13
    # legs
    lw = max(1, int(hgt * 0.05))
    d.line([px - hgt * 0.06, py - hgt * 0.52, px - hgt * 0.09, py], fill=trousers, width=lw)
    d.line([px + hgt * 0.06, py - hgt * 0.52, px + hgt * 0.09, py], fill=trousers, width=lw)
    # torso
    d.rectangle([px - hgt * 0.17, py - hgt * 0.80, px + hgt * 0.17, py - hgt * 0.52], fill=shirt)
    # arms
    aw = max(1, int(hgt * 0.05))
    if arm_up:
        d.line([px + hgt * 0.15, py - hgt * 0.76, px + hgt * 0.32, py - hgt * 1.02],
               fill=shirt, width=aw)
        d.line([px - hgt * 0.15, py - hgt * 0.76, px - hgt * 0.28, py - hgt * 0.58],
               fill=shirt, width=aw)
    else:
        d.line([px + hgt * 0.15, py - hgt * 0.76, px + hgt * 0.26, py - hgt * 0.55],
               fill=shirt, width=aw)
        d.line([px - hgt * 0.15, py - hgt * 0.76, px - hgt * 0.26, py - hgt * 0.55],
               fill=shirt, width=aw)
    # head + hair cap
    d.ellipse([px - hr, py - hgt, px + hr, py - hgt + 2 * hr], fill=skin)
    d.pieslice([px - hr, py - hgt, px + hr, py - hgt + 2 * hr], 180, 360, fill=hair)


def _palm(d, px, py, hgt, lean=0.15):
    """Bent palm tree, base at (px, py), fronds drooping in the wind."""
    s = S3
    top_x = px + hgt * lean
    top_y = py - hgt
    d.line([px, py, top_x, top_y], fill=(95, 72, 42), width=2 * s)
    for ang in (-150, -110, -70, -30, 10, 50):
        ex = top_x + hgt * 0.42 * math.cos(math.radians(ang))
        ey = top_y + hgt * 0.30 * math.sin(math.radians(ang)) + hgt * 0.12
        d.arc([min(top_x, ex) - hgt * 0.18, min(top_y, ey) - hgt * 0.10,
               max(top_x, ex) + hgt * 0.18, max(top_y, ey) + hgt * 0.10],
              200 if ang < 0 else 340, 340 if ang < 0 else 160,
              fill=(35, 110, 55), width=1 * s)
    d.ellipse([top_x - 2 * s, top_y - 2 * s, top_x + 2 * s, top_y + 2 * s], fill=(120, 80, 40))


def _tree(d, px, py, r):
    s = S3
    d.line([px, py, px, py - r * 1.2], fill=(95, 72, 42), width=2 * s)
    for (dx, dy, rr, col) in [(-r * 0.5, -r * 1.3, r * 0.7, (45, 120, 55)),
                              (r * 0.5, -r * 1.4, r * 0.65, (60, 140, 65)),
                              (0, -r * 1.8, r * 0.75, (55, 130, 60))]:
        d.ellipse([px + dx - rr, py + dy - rr, px + dx + rr, py + dy + rr], fill=col)


def scene_kyiv(d, W, H, top):
    s = S3
    # night sky: darker zenith, lighter toward the horizon
    d.rectangle([0, top, W, top + (H - top) * 0.45], fill=(12, 19, 40))
    d.rectangle([0, top + (H - top) * 0.45, W, H], fill=(20, 30, 58))
    d.rectangle([0, H - 26 * s, W, H], fill=(24, 48, 92))
    # stars, varied sizes
    rnd = random.Random(7)
    for _ in range(26):
        fx = rnd.random()
        fy = rnd.random() * 0.45
        r = 1 * s if rnd.random() < 0.7 else 2 * s
        star(d, W * fx, top + (H - top) * fy, r, (255, 255, 255))
    # crescent moon with a shaded limb
    mx, my, mr = W * 0.90, top + 13 * s, 9 * s
    d.ellipse([mx - mr, my - mr, mx + mr, my + mr], fill=(242, 232, 196))
    d.ellipse([mx - mr + 5 * s, my - mr - 2 * s, mx + mr + 4 * s, my + mr - 1 * s],
              fill=(20, 30, 58))
    d.ellipse([mx - 3 * s, my - 2 * s, mx - 1 * s, my], fill=(225, 212, 170))
    # skyline: varied towers, clearly lighter than the sky, lit windows
    base = H - 26 * s
    sky = (118, 133, 172)
    sky2 = (96, 110, 150)
    for i, (fx, fw, fh, col) in enumerate([
            (0.03, 0.12, 0.34, sky), (0.17, 0.09, 0.48, sky2), (0.28, 0.13, 0.30, sky),
            (0.55, 0.10, 0.42, sky2), (0.68, 0.12, 0.36, sky), (0.83, 0.11, 0.50, sky2)]):
        bx0 = W * fx
        by0 = base - (H - top) * fh
        d.rectangle([bx0, by0, W * (fx + fw), base], fill=col)
        # roofline detail: antenna or parapet
        if i % 2 == 0:
            d.line([bx0 + W * fw / 2, by0, bx0 + W * fw / 2, by0 - 5 * s], fill=col, width=1 * s)
        _win_grid(d, bx0 + 2 * s, by0 + 3 * s, W * (fx + fw) - 2 * s, base - 2 * s,
                  3, max(2, int(fh * 6)), (255, 214, 130), (70, 82, 118), seed=i + 1)
    # golden onion dome with cross, on its own drum
    dx, dy = W * 0.47, base - (H - top) * 0.55
    d.rectangle([dx - 7 * s, dy + 2 * s, dx + 7 * s, base], fill=(148, 118, 58))
    d.ellipse([dx - 8 * s, dy - 9 * s, dx + 8 * s, dy + 2 * s], fill=(214, 162, 42))
    d.ellipse([dx - 4 * s, dy - 8 * s, dx + 1 * s, dy - 2 * s], fill=(235, 190, 80))
    d.line([dx, dy - 9 * s, dx, dy - 15 * s], fill=(214, 162, 42), width=1 * s)
    d.line([dx - 2 * s, dy - 12 * s, dx + 2 * s, dy - 12 * s], fill=(214, 162, 42), width=1 * s)
    _win_grid(d, dx - 5 * s, dy + 5 * s, dx + 5 * s, base - 2 * s, 1, 3,
              (255, 214, 130), (110, 88, 44), seed=9)
    # two suspension bridges: pylons, main cables, suspenders, car lights
    for by, col, deck in [(base - 10 * s, (52, 52, 58), (70, 70, 76)),
                          (base - 4 * s, (36, 36, 42), (52, 52, 58))]:
        d.rectangle([0, by, W, by + 3 * s], fill=deck)
        for fx in (0.15, 0.45, 0.75):
            px = W * fx
            d.rectangle([px - 1 * s, by - 13 * s, px + 1 * s, by], fill=col)
            # main cable: two curved segments meeting at the pylon top
            for k in range(12):
                t0 = k / 12.0
                t1 = (k + 1) / 12.0
                x0 = px - 24 * s + 24 * s * t0
                x1 = px - 24 * s + 24 * s * t1
                y0 = by - 13 * s + 9 * s * (1 - t0) * (1 - t0)
                y1 = by - 13 * s + 9 * s * (1 - t1) * (1 - t1)
                d.line([x0, y0, x1, y1], fill=col, width=1 * s)
                x0 = px + 24 * s * t0
                x1 = px + 24 * s * t1
                d.line([x0, y0, x1, y1], fill=col, width=1 * s)
            # vertical suspenders
            for ox in (-18, -9, 9, 18):
                sx = px + ox * s
                sy = by - 13 * s + 9 * s * (1 - abs(ox) / 24.0) ** 2
                d.line([sx, sy, sx, by], fill=col, width=1 * s)
        for fx, col2 in [(0.08, (255, 220, 120)), (0.25, (255, 240, 200)),
                         (0.55, (255, 220, 120)), (0.88, (255, 120, 90))]:
            d.ellipse([W * fx - 1 * s, by - 2 * s, W * fx + 1 * s, by], fill=col2)
    # missile burst + drifting smoke plume on the upper bridge
    bx, by = W * 0.62, base - 15 * s
    for ang in range(0, 360, 30):
        r = 10 * s
        d.line([bx, by, bx + r * math.cos(math.radians(ang)),
                by + r * math.sin(math.radians(ang))], fill=(255, 170, 40), width=2 * s)
    d.ellipse([bx - 5 * s, by - 5 * s, bx + 5 * s, by + 5 * s], fill=(255, 222, 96))
    d.ellipse([bx - 2 * s, by - 2 * s, bx + 2 * s, by + 2 * s], fill=(255, 245, 200))
    _puff(d, W * 0.60, top + (H - top) * 0.28, 0, [
        (0, 0, 6 * s, (150, 150, 160)), (7 * s, -4 * s, 5 * s, (165, 165, 175)),
        (-6 * s, -5 * s, 4 * s, (140, 140, 150)), (12 * s, -9 * s, 4 * s, (175, 175, 185)),
        (3 * s, -9 * s, 3 * s, (185, 185, 195))])
    # river reflections: broken light streaks under each bridge
    for fx, ln in [(0.12, 20), (0.35, 26), (0.60, 18), (0.82, 22)]:
        d.line([W * fx, H - 12 * s, W * fx + ln * s, H - 12 * s], fill=(150, 180, 230), width=1 * s)
        d.line([W * fx + 4 * s, H - 6 * s, W * fx + ln * s - 6 * s, H - 6 * s],
               fill=(120, 150, 210), width=1 * s)
    chip(d, 6 * s, top + 3 * s, "THE DNIPRO BRIDGES", F("sans", 8 * s, True),
         (18, 18, 18), (255, 210, 60))


def scene_akvan(d, W, H, top):
    s = S3
    # storm sky: layered grey-blue bands
    d.rectangle([0, top, W, top + (H - top) * 0.40], fill=(120, 165, 200))
    d.rectangle([0, top + (H - top) * 0.40, W, H], fill=(150, 200, 225))
    # cloud banks: overlapping soft ellipses
    for (fx, fy, fw, fh, col) in [(0.08, 0.06, 0.30, 0.10, (200, 215, 230)),
                                  (0.45, 0.02, 0.34, 0.09, (185, 205, 222)),
                                  (0.70, 0.10, 0.26, 0.08, (205, 220, 232))]:
        d.ellipse([W * fx, top + (H - top) * fy, W * (fx + fw), top + (H - top) * (fy + fh)], fill=col)
        d.ellipse([W * (fx + 0.06), top + (H - top) * (fy - 0.03),
                   W * (fx + fw - 0.04), top + (H - top) * (fy + fh - 0.03)], fill=col)
    # sea: two tones with whitecaps
    d.rectangle([0, top + (H - top) * 0.52, W, H], fill=(70, 130, 170))
    d.rectangle([0, top + (H - top) * 0.52, W, top + (H - top) * 0.60], fill=(95, 155, 190))
    # curved coast: sand, wet-sand band, land
    d.polygon([(W * 0.55, H), (W * 0.62, H * 0.62), (W * 0.80, H * 0.55),
               (W, H * 0.60), (W, H)], fill=(216, 192, 142))
    d.polygon([(W * 0.57, H), (W * 0.635, H * 0.63), (W * 0.80, H * 0.56),
               (W, H * 0.605), (W, H * 0.66), (W * 0.80, H * 0.62),
               (W * 0.64, H * 0.68), (W * 0.58, H)], fill=(190, 160, 110))
    d.polygon([(W * 0.66, H * 0.72), (W * 0.72, H * 0.60), (W * 0.88, H * 0.57),
               (W, H * 0.62), (W, H * 0.78), (W * 0.82, H * 0.74)], fill=(170, 150, 95))
    # spiral storm bands over the sea, with a bright eye
    cx, cy = W * 0.38, top + (H - top) * 0.42
    for r, wd in [(36 * s, 4 * s), (28 * s, 3 * s), (20 * s, 3 * s), (12 * s, 3 * s)]:
        d.arc([cx - r, cy - r, cx + r, cy + r], 15, 310, fill=(255, 255, 255), width=wd)
        d.arc([cx - r, cy - r, cx + r, cy + r], 200, 260, fill=(225, 235, 245), width=wd)
    d.ellipse([cx - 6 * s, cy - 6 * s, cx + 6 * s, cy + 6 * s], fill=(255, 255, 255))
    d.ellipse([cx - 3 * s, cy - 3 * s, cx + 3 * s, cy + 3 * s], fill=(200, 225, 245))
    # rain streaks, denser and slanted
    rnd = random.Random(3)
    for _ in range(14):
        fx = rnd.random() * 0.6
        fy = 0.05 + rnd.random() * 0.30
        x0 = W * fx
        y0 = top + (H - top) * fy
        d.line([x0, y0, x0 - 5 * s, y0 + 12 * s], fill=(220, 235, 245), width=1 * s)
    # houses on the coast: walls, roofs, doors, windows
    for fx, roof in [(0.66, (120, 60, 40)), (0.74, (140, 70, 45)), (0.85, (110, 55, 38))]:
        hx0 = W * fx
        hy0 = H - 15 * s
        d.rectangle([hx0, hy0, hx0 + 11 * s, H - 6 * s], fill=(200, 170, 130))
        d.polygon([(hx0 - 1 * s, hy0), (hx0 + 5 * s, hy0 - 5 * s),
                   (hx0 + 12 * s, hy0)], fill=roof)
        d.rectangle([hx0 + 4 * s, H - 11 * s, hx0 + 7 * s, H - 6 * s], fill=(90, 60, 40))
        d.rectangle([hx0 + 1 * s, hy0 + 2 * s, hx0 + 3 * s, hy0 + 4 * s], fill=(255, 220, 130))
    # bent palms, fronds streaming sideways
    _palm(d, W * 0.60, H - 8 * s, 13 * s, lean=0.35)
    _palm(d, W * 0.92, H - 8 * s, 11 * s, lean=-0.3)
    # small fishing boat heeling in the waves
    bx0, by0 = W * 0.30, H - 16 * s
    d.polygon([(bx0, by0), (bx0 + 16 * s, by0 - 3 * s), (bx0 + 13 * s, by0 + 4 * s),
               (bx0 + 3 * s, by0 + 4 * s)], fill=(120, 70, 40))
    d.line([bx0 + 8 * s, by0, bx0 + 8 * s, by0 - 8 * s], fill=(80, 55, 30), width=1 * s)
    d.polygon([(bx0 + 8 * s, by0 - 8 * s), (bx0 + 8 * s, by0 - 1 * s),
               (bx0 + 14 * s, by0 - 1 * s)], fill=(240, 230, 200))
    # waves with white crests
    for fx in (0.05, 0.22, 0.42):
        d.arc([W * fx, H - 13 * s, W * fx + 30 * s, H - 3 * s], 180, 360,
              fill=(255, 255, 255), width=2 * s)
        d.arc([W * fx + 4 * s, H - 10 * s, W * fx + 26 * s, H - 4 * s], 200, 340,
              fill=(200, 225, 240), width=1 * s)
    # dotted track to Gopalpur dot
    gx, gy = W * 0.63, H * 0.60
    d.ellipse([gx - 3 * s, gy - 3 * s, gx + 3 * s, gy + 3 * s], fill=(178, 30, 45))
    d.ellipse([gx - 1 * s, gy - 1 * s, gx + 1 * s, gy + 1 * s], fill=(255, 255, 255))
    d.text((gx + 5 * s, gy - 4 * s), "GOPALPUR", font=F("sans", 7 * s, True), fill=(18, 18, 18))
    chip(d, 6 * s, top + 3 * s, "GOPALPUR COAST", F("sans", 8 * s, True),
         (18, 18, 18), (255, 255, 255))
    chip(d, 6 * s, H - 13 * s, "300,000+ TO SHELTERS", F("sans", 8 * s, True),
         (255, 255, 255), (178, 30, 45))


def scene_markets(d, W, H, top):
    s = S3
    d.rectangle([0, top, W, H], fill=(8, 22, 17))
    # faint grid
    for i in range(1, 5):
        yy = top + (H - top) * i / 5
        d.line([0, yy, W, yy], fill=(25, 45, 35), width=1 * s)
    # candlestick chart falling left to right, with wicks and varied bodies
    chart_x0, chart_x1 = 8 * s, W * 0.62
    chart_y0, chart_y1 = top + 10 * s, H - 18 * s
    candles = [(0.05, 0.28, 0.52), (0.17, 0.33, 0.60), (0.29, 0.43, 0.66),
               (0.41, 0.48, 0.72), (0.53, 0.58, 0.80), (0.65, 0.66, 0.88),
               (0.77, 0.72, 0.93), (0.89, 0.80, 1.00)]
    cw = (chart_x1 - chart_x0) / 9
    for i, (lo, hi, cl) in enumerate(candles):
        x0 = chart_x0 + i * cw + cw * 0.22
        x1 = chart_x0 + (i + 1) * cw - cw * 0.22
        yhi = chart_y0 + (chart_y1 - chart_y0) * hi
        ylo = chart_y0 + (chart_y1 - chart_y0) * lo
        ycl = chart_y0 + (chart_y1 - chart_y0) * cl
        yop = chart_y0 + (chart_y1 - chart_y0) * (lo - 0.06)
        # upper + lower wicks
        d.line([(x0 + x1) / 2, yop, (x0 + x1) / 2, ylo], fill=(255, 110, 95), width=1 * s)
        d.rectangle([x0, yhi, x1, ycl], fill=(222, 52, 46))
        d.rectangle([x0, yhi, x1, yhi + 2 * s], fill=(255, 120, 105))
    # last candle: small green bounce
    gx0 = chart_x0 + 8 * cw + cw * 0.22
    gx1 = chart_x0 + 9 * cw - cw * 0.22
    gy1 = chart_y0 + (chart_y1 - chart_y0) * 0.97
    gy0 = chart_y0 + (chart_y1 - chart_y0) * 0.90
    d.line([(gx0 + gx1) / 2, gy0 - 3 * s, (gx0 + gx1) / 2, gy1 + 3 * s],
           fill=(90, 220, 130), width=1 * s)
    d.rectangle([gx0, gy0, gx1, gy1], fill=(45, 180, 90))
    # volume bars, growing as the sell-off deepens
    for i in range(9):
        vx0 = chart_x0 + i * cw + cw * 0.25
        vh = (4 + i * 1.6) * s
        col = (110, 150, 115) if i < 8 else (90, 200, 120)
        d.rectangle([vx0, chart_y1 + 2 * s, vx0 + cw * 0.5, chart_y1 + 2 * s + vh], fill=col)
    # dashed average line sloping down
    for x in range(int(chart_x0), int(chart_x1), 10 * s):
        yy = chart_y0 + 12 * s + (x - chart_x0) * 0.10
        d.line([x, yy, x + 5 * s, yy + 0.5 * s], fill=(255, 220, 120), width=1 * s)
    # data table right side, with divider rules
    tx = W * 0.66
    fnt = F("sans", 9 * s, True)
    fnt2 = F("sans", 9 * s, False)
    rows = [("Taipei", "\u22126.2%"), ("Seoul", "\u22125.2%"), ("Tokyo", "\u22125.1%")]
    for i, (city, val) in enumerate(rows):
        yy = top + 12 * s + i * 15 * s
        d.text((tx, yy), city, font=fnt2, fill=(230, 230, 230))
        d.text((W - 4 * s - fnt.getlength(val), yy), val, font=fnt, fill=(255, 90, 80))
        if i < 2:
            d.line([tx, yy + 12 * s, W - 4 * s, yy + 12 * s], fill=(45, 70, 55), width=1 * s)


def scene_ukeu(d, W, H, top):
    s = S3
    d.rectangle([0, top, W, H], fill=(138, 178, 220))
    # soft clouds
    for (fx, fy, fw) in [(0.55, 0.06, 0.22), (0.80, 0.14, 0.16)]:
        d.ellipse([W * fx, top + (H - top) * fy, W * (fx + fw), top + (H - top) * (fy + 0.10)],
                  fill=(245, 248, 252))
    # river band at the bottom
    d.rectangle([0, H - 8 * s, W, H], fill=(110, 160, 200))
    d.line([0, H - 8 * s, W, H - 8 * s], fill=(90, 140, 185), width=1 * s)
    # Big Ben: brick tower with pale stone trim, clock face, spire
    bx, bw = W * 0.05, 15 * s
    d.rectangle([bx, top + 10 * s, bx + bw, H - 8 * s], fill=(96, 74, 52))
    d.rectangle([bx, top + 10 * s, bx + bw, top + 14 * s], fill=(200, 185, 160))
    d.rectangle([bx, top + 26 * s, bx + bw, top + 30 * s], fill=(200, 185, 160))
    for wy in range(int(top + 32 * s), int(H - 12 * s), 8 * s):
        d.rectangle([bx + 3 * s, wy, bx + 6 * s, wy + 4 * s], fill=(60, 45, 32))
        d.rectangle([bx + bw - 6 * s, wy, bx + bw - 3 * s, wy + 4 * s], fill=(60, 45, 32))
    d.polygon([(bx - 2 * s, top + 10 * s), (bx + bw / 2, top - 1 * s),
               (bx + bw + 2 * s, top + 10 * s)], fill=(58, 48, 38))
    d.ellipse([bx + 2 * s, top + 14 * s, bx + bw - 2 * s, top + 26 * s], fill=(250, 245, 220))
    d.ellipse([bx + 3 * s, top + 15 * s, bx + bw - 3 * s, top + 25 * s], outline=(60, 50, 40), width=1 * s)
    d.line([bx + bw / 2, top + 20 * s, bx + bw / 2, top + 16 * s], fill=INK, width=1 * s)
    d.line([bx + bw / 2, top + 20 * s, bx + bw / 2 + 3 * s, top + 22 * s], fill=INK, width=1 * s)
    d.ellipse([bx + bw / 2 - 1 * s, top + 19 * s, bx + bw / 2 + 1 * s, top + 21 * s], fill=INK)
    # London Eye: rim, spokes, capsules, support legs
    ex, ey, er = W * 0.38, top + (H - top) * 0.55, 15 * s
    d.ellipse([ex - er, ey - er, ex + er, ey + er], outline=(255, 255, 255), width=2 * s)
    for ang in range(0, 360, 30):
        d.line([ex, ey, ex + er * math.cos(math.radians(ang)),
                ey + er * math.sin(math.radians(ang))], fill=(255, 255, 255), width=1 * s)
    for ang in range(0, 360, 30):
        cxp = ex + (er + 1 * s) * math.cos(math.radians(ang))
        cyp = ey + (er + 1 * s) * math.sin(math.radians(ang))
        d.ellipse([cxp - 1 * s, cyp - 1 * s, cxp + 1 * s, cyp + 1 * s], fill=(220, 230, 245))
    d.line([ex - 6 * s, ey + er, ex - 2 * s, H - 8 * s], fill=(200, 200, 210), width=1 * s)
    d.line([ex + 6 * s, ey + er, ex + 2 * s, H - 8 * s], fill=(200, 200, 210), width=1 * s)
    # gold arc of 12 EU stars across a seam
    for i in range(12):
        fx = 0.56 + i * 0.035
        fy = 0.22 + 0.10 * abs(i - 5.5) / 5.5
        star(d, W * fx, top + (H - top) * fy, 1 * s + (1 * s if i % 3 == 0 else 0),
             (255, 210, 60))
    d.line([W * 0.56, top + (H - top) * 0.42, W * 0.97, top + (H - top) * 0.42],
           fill=(255, 210, 60), width=1 * s)
    # Atomium: nine spheres on tubes
    ax, ay = W * 0.86, top + (H - top) * 0.45
    pts = [(0, -12), (-9, -6), (9, -6), (-9, 6), (9, 6), (0, 10), (-14, 0), (14, 0), (0, 0)]
    for (dx, dy) in pts:
        d.line([ax, ay, ax + dx * s, ay + dy * s], fill=(110, 120, 140), width=1 * s)
    for (dx, dy) in pts:
        d.ellipse([ax + dx * s - 3 * s, ay + dy * s - 3 * s,
                   ax + dx * s + 3 * s, ay + dy * s + 3 * s], fill=(130, 140, 160))
        d.ellipse([ax + dx * s - 2 * s, ay + dy * s - 2 * s,
                   ax + dx * s, ay + dy * s], fill=(170, 180, 200))
    chip(d, 6 * s, H - 13 * s, "LONDON \u00b7 BRUSSELS", F("sans", 7 * s, True),
         (255, 255, 255), (30, 40, 60))


def scene_cop31(d, W, H, top):
    s = S3
    d.rectangle([0, top, W, H], fill=(168, 203, 233))
    # sun disc with pale halo rings, top-right
    sx, sy = W * 0.90, top + (H - top) * 0.18
    for r, col in [(14 * s, (255, 235, 170)), (11 * s, (255, 215, 110)), (8 * s, (255, 200, 60))]:
        d.ellipse([sx - r, sy - r, sx + r, sy + r], fill=col)
    for ang in (15, 55, 95, 135, 175):
        x1 = sx + 16 * s * math.cos(math.radians(ang))
        y1 = sy - 16 * s * math.sin(math.radians(ang))
        d.line([sx + 11 * s * math.cos(math.radians(ang)), sy - 11 * s * math.sin(math.radians(ang)),
                x1, y1], fill=(255, 205, 90), width=2 * s)
    # globe: real continents clipped into a disc, sea with cloud swirls
    gx, gy, gr = W * 0.24, top + (H - top) * 0.52, 17 * s
    globe = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(globe)
    for poly, reg in zip(CONTINENTS_LL, POLY_REG):
        pts = []
        for lon, lat in poly:
            px = gx - gr + (lon + 180) / 360.0 * 2 * gr
            py = gy - gr + (80 - lat) / 130.0 * 2 * gr
            pts.append((px, py))
        gd.polygon(pts, fill=(58, 138, 68))
    mask = Image.new("L", (W, H), 0)
    md = ImageDraw.Draw(mask)
    md.ellipse([gx - gr, gy - gr, gx + gr, gy + gr], fill=255)
    sea = Image.new("RGBA", (W, H), (68, 118, 198, 255))
    sea.putalpha(mask)
    globe.putalpha(mask)
    d._image.paste(sea, (0, 0), sea)
    d._image.paste(globe, (0, 0), globe)
    # cloud swirls on the globe
    for (fx, fy, r) in [(0.20, 0.42, 4), (0.28, 0.60, 3), (0.16, 0.58, 3)]:
        d.arc([W * fx - r * s, top + (H - top) * fy - r * s,
               W * fx + r * s, top + (H - top) * fy + r * s], 20, 300,
              fill=(255, 255, 255), width=1 * s)
    d.ellipse([gx - gr, gy - gr, gx + gr, gy + gr], outline=(30, 60, 120), width=1 * s)
    # deadline clock with tick marks, hands, red-X badge
    cx, cy, cr = W * 0.56, top + (H - top) * 0.42, 11 * s
    d.ellipse([cx - cr, cy - cr, cx + cr, cy + cr], fill=(255, 255, 255), outline=INK, width=1 * s)
    for ang in range(0, 360, 30):
        x0 = cx + (cr - 2 * s) * math.cos(math.radians(ang))
        y0 = cy + (cr - 2 * s) * math.sin(math.radians(ang))
        x1 = cx + (cr - 1 * s) * math.cos(math.radians(ang))
        y1 = cy + (cr - 1 * s) * math.sin(math.radians(ang))
        d.line([x0, y0, x1, y1], fill=INK, width=1 * s)
    d.line([cx, cy, cx, cy - 6 * s], fill=INK, width=1 * s)
    d.line([cx, cy, cx + 4 * s, cy + 2 * s], fill=INK, width=1 * s)
    d.ellipse([cx, cy - 1 * s, cx + 2 * s, cy + 1 * s], fill=INK)
    d.ellipse([cx + cr - 4 * s, cy + cr - 6 * s, cx + cr + 4 * s, cy + cr + 2 * s],
              fill=(178, 30, 45))
    xf = F("sans", 7 * s, True)
    d.text((cx + cr - 4 * s + 2 * s, cy + cr - 6 * s + 1 * s), "X", font=xf, fill=(255, 255, 255))
    # thermometer with tick marks
    tx = W * 0.72
    d.rectangle([tx - 3 * s, top + 6 * s, tx + 3 * s, top + (H - top) * 0.75],
                fill=(255, 255, 255), outline=INK, width=1 * s)
    d.rectangle([tx - 2 * s, top + (H - top) * 0.45, tx + 2 * s, top + (H - top) * 0.75],
                fill=(220, 50, 45))
    d.ellipse([tx - 5 * s, top + (H - top) * 0.72, tx + 5 * s, top + (H - top) * 0.85],
              fill=(220, 50, 45))
    for j in range(4):
        yy = top + (H - top) * (0.20 + j * 0.12)
        d.line([tx + 3 * s, yy, tx + 6 * s, yy], fill=INK, width=1 * s)
    # delegate figures: heads, shoulders, lanyards
    for i, fx in enumerate((0.84, 0.90, 0.96)):
        px = W * fx
        py = H
        _person(d, px, py, 13 * s, (60, 70, 90) if i != 1 else (140, 60, 60),
                arm_up=False)
        d.line([px - 1 * s, py - 13 * s * 0.78, px + 1 * s, py - 13 * s * 0.60],
               fill=(255, 210, 60), width=1 * s)
    d.text((W * 0.42, top + 1 * s), "T\u00dcRK\u0130YE", font=F("sans", 8 * s, True), fill=(18, 18, 18))


def scene_poland(d, W, H, top):
    s = S3
    d.rectangle([0, top, W, H], fill=(132, 183, 230))
    # fluffy clouds
    for (fx, fy) in [(0.10, 0.08), (0.58, 0.05), (0.84, 0.12)]:
        d.ellipse([W * fx, top + (H - top) * fy, W * fx + 18 * s, top + (H - top) * fy + 6 * s],
                  fill=(255, 255, 255))
        d.ellipse([W * fx + 4 * s, top + (H - top) * fy - 3 * s,
                   W * fx + 13 * s, top + (H - top) * fy + 3 * s], fill=(255, 255, 255))
    # fields: near field, far field, dirt track, bushes
    d.rectangle([0, top + (H - top) * 0.55, W, H], fill=(96, 168, 84))
    d.rectangle([0, top + (H - top) * 0.72, W, H], fill=(72, 142, 66))
    d.polygon([(0, H), (W * 0.30, top + (H - top) * 0.72), (W * 0.42, top + (H - top) * 0.72),
               (W * 0.18, H)], fill=(170, 140, 95))
    for (fx, fy) in [(0.12, 0.60), (0.66, 0.58), (0.90, 0.66)]:
        _tree(d, W * fx, top + (H - top) * fy + 6 * s, 4 * s)
    # border fence: three wires + posts with barbed X
    fy = top + (H - top) * 0.62
    for dy in (0, 5 * s, 10 * s):
        d.line([0, fy + dy, W, fy + dy], fill=(58, 58, 58), width=1 * s)
    for fx in (0.1, 0.3, 0.5, 0.7, 0.9):
        d.line([W * fx, fy - 4 * s, W * fx, fy + 12 * s], fill=(58, 58, 58), width=1 * s)
        d.line([W * fx - 2 * s, fy + 2 * s, W * fx + 2 * s, fy + 6 * s], fill=(58, 58, 58), width=1 * s)
    # watchtower: cross-braced legs, cabin with windows, roof
    wx = W * 0.82
    d.line([wx - 6 * s, fy + 12 * s, wx - 2 * s, top + (H - top) * 0.32], fill=(110, 82, 52), width=2 * s)
    d.line([wx + 6 * s, fy + 12 * s, wx + 2 * s, top + (H - top) * 0.32], fill=(110, 82, 52), width=2 * s)
    d.line([wx - 6 * s, fy + 12 * s, wx + 2 * s, top + (H - top) * 0.32], fill=(110, 82, 52), width=1 * s)
    d.line([wx + 6 * s, fy + 12 * s, wx - 2 * s, top + (H - top) * 0.32], fill=(110, 82, 52), width=1 * s)
    d.rectangle([wx - 9 * s, top + (H - top) * 0.22, wx + 9 * s, top + (H - top) * 0.32],
                fill=(88, 62, 38))
    d.rectangle([wx - 6 * s, top + (H - top) * 0.24, wx + 6 * s, top + (H - top) * 0.30],
                fill=(255, 220, 130))
    d.polygon([(wx - 10 * s, top + (H - top) * 0.22), (wx, top + (H - top) * 0.14),
               (wx + 10 * s, top + (H - top) * 0.22)], fill=(70, 50, 30))
    # quadcopter drone: body, camera, four rotors with blur discs
    dx, dy = W * 0.45, top + (H - top) * 0.35
    d.rectangle([dx - 6 * s, dy - 2 * s, dx + 6 * s, dy + 2 * s], fill=(38, 38, 38))
    d.ellipse([dx - 2 * s, dy - 1 * s, dx + 2 * s, dy + 1 * s], fill=(120, 200, 230))
    for ox in (-10, 10):
        for oy in (-4, 4):
            d.ellipse([dx + ox * s - 5 * s, dy + oy * s - 1 * s,
                       dx + ox * s + 5 * s, dy + oy * s + 1 * s],
                      outline=(38, 38, 38), width=1 * s)
    d.ellipse([dx - 4 * s, dy + 12 * s, dx + 4 * s, dy + 16 * s], fill=(0, 0, 0, 60))
    # radar: arcs, sweep wedge, small dish
    rx, ry = W * 0.15, top + (H - top) * 0.40
    for r in (8 * s, 13 * s, 18 * s):
        d.arc([rx - r, ry - r, rx + r, ry + r], 300, 60, fill=(255, 255, 255), width=1 * s)
    d.polygon([(rx, ry), (rx + 12 * s, ry - 8 * s), (rx + 14 * s, ry - 2 * s)],
              fill=(255, 255, 255, 90))
    d.arc([rx - 4 * s, ry - 10 * s, rx + 4 * s, ry - 2 * s], 180, 360, fill=(200, 200, 210), width=1 * s)
    chip(d, 6 * s, H - 13 * s, "THE BORDER", F("sans", 7 * s, True),
         (18, 18, 18), (255, 255, 255))


def scene_iraq(d, W, H, top):
    s = S3
    # hazy desert sky: pale top, warm band at the horizon
    d.rectangle([0, top, W, top + (H - top) * 0.45], fill=(238, 222, 180))
    d.rectangle([0, top + (H - top) * 0.45, W, H], fill=(228, 206, 152))
    # sun with halo
    sx, sy = W * 0.85, top + (H - top) * 0.22
    d.ellipse([sx - 11 * s, sy - 11 * s, sx + 11 * s, sy + 11 * s], fill=(255, 215, 130))
    d.ellipse([sx - 8 * s, sy - 8 * s, sx + 8 * s, sy + 8 * s], fill=(255, 200, 80))
    # mountains: near ridge with shaded face, far ridge
    d.polygon([(0, H - 14 * s), (W * 0.20, top + (H - top) * 0.55),
               (W * 0.38, H - 14 * s)], fill=(182, 142, 92))
    d.polygon([(W * 0.20, top + (H - top) * 0.55), (W * 0.28, top + (H - top) * 0.66),
               (W * 0.38, H - 14 * s), (W * 0.30, H - 14 * s)], fill=(158, 118, 74))
    d.polygon([(W * 0.30, H - 14 * s), (W * 0.55, top + (H - top) * 0.45),
               (W * 0.75, H - 14 * s)], fill=(166, 126, 80))
    # desert floor with dune curves and rocks
    d.rectangle([0, H - 14 * s, W, H], fill=(215, 185, 130))
    d.arc([W * 0.10, H - 10 * s, W * 0.45, H + 6 * s], 200, 340, fill=(190, 158, 105), width=1 * s)
    for (fx, fy) in [(0.42, 0.90), (0.68, 0.94), (0.95, 0.88)]:
        d.ellipse([W * fx - 2 * s, top + (H - top) * fy - 1 * s,
                   W * fx + 2 * s, top + (H - top) * fy + 1 * s], fill=(170, 135, 90))
    # two army trucks: cab, windshield with glare, grille, headlights, wheels
    for fx in (0.08, 0.50):
        tx, ty = W * fx, H - 16 * s
        # dust cloud behind
        _puff(d, tx - 2 * s, ty + 6 * s, 0, [
            (0, 0, 5 * s, (222, 198, 152)), (6 * s, -2 * s, 4 * s, (228, 206, 160)),
            (-5 * s, 2 * s, 4 * s, (214, 190, 144))])
        d.rectangle([tx, ty, tx + 34 * s, ty + 10 * s], fill=(112, 112, 82))
        d.rectangle([tx, ty, tx + 34 * s, ty + 2 * s], fill=(128, 128, 96))
        d.rectangle([tx + 22 * s, ty - 6 * s, tx + 32 * s, ty], fill=(112, 112, 82))
        d.rectangle([tx + 24 * s, ty - 5 * s, tx + 30 * s, ty - 1 * s], fill=(178, 218, 233))
        d.line([tx + 25 * s, ty - 5 * s, tx + 27 * s, ty - 1 * s], fill=(240, 250, 255), width=1 * s)
        d.rectangle([tx + 32 * s, ty + 2 * s, tx + 34 * s, ty + 6 * s], fill=(240, 230, 160))
        d.rectangle([tx + 2 * s, ty + 2 * s, tx + 20 * s, ty + 8 * s], fill=(98, 98, 70))
        for wx in (6, 16, 28):
            d.ellipse([tx + wx * s - 3 * s, ty + 8 * s, tx + wx * s + 3 * s, ty + 14 * s],
                      fill=(28, 28, 28))
            d.ellipse([tx + wx * s - 1 * s, ty + 10 * s, tx + wx * s + 1 * s, ty + 12 * s],
                      fill=(200, 200, 200))
    # helicopter: body, cockpit glass, tail, rotor, skids
    hx, hy = W * 0.78, top + (H - top) * 0.30
    d.ellipse([hx - 8 * s, hy - 3 * s, hx + 8 * s, hy + 3 * s], fill=(92, 92, 72))
    d.ellipse([hx - 7 * s, hy - 2 * s, hx - 1 * s, hy + 2 * s], fill=(178, 218, 233))
    d.line([hx - 15 * s, hy - 5 * s, hx + 15 * s, hy - 5 * s], fill=(60, 60, 60), width=1 * s)
    d.ellipse([hx - 15 * s, hy - 6 * s, hx + 15 * s, hy - 4 * s], outline=(90, 90, 90), width=1 * s)
    d.line([hx + 8 * s, hy, hx + 15 * s, hy - 2 * s], fill=(60, 60, 60), width=1 * s)
    d.line([hx - 5 * s, hy + 3 * s, hx - 5 * s, hy + 6 * s], fill=(60, 60, 60), width=1 * s)
    d.line([hx + 5 * s, hy + 3 * s, hx + 5 * s, hy + 6 * s], fill=(60, 60, 60), width=1 * s)
    d.line([hx - 6 * s, hy + 6 * s, hx + 6 * s, hy + 6 * s], fill=(60, 60, 60), width=1 * s)
    chip(d, 6 * s, top + 3 * s, "JURF AL-SAKHAR", F("sans", 7 * s, True),
         (18, 18, 18), (255, 255, 255))


def scene_italy(d, W, H, top):
    s = S3
    d.rectangle([0, top, W, H], fill=(148, 188, 228))
    # clouds
    for (fx, fy) in [(0.08, 0.05), (0.70, 0.08)]:
        d.ellipse([W * fx, top + (H - top) * fy, W * fx + 16 * s, top + (H - top) * fy + 5 * s],
                  fill=(255, 255, 255))
    # background facades with shuttered windows
    for (fx, fw, fh, col) in [(0.02, 0.20, 0.30, (205, 165, 120)),
                              (0.26, 0.18, 0.36, (190, 150, 110)),
                              (0.78, 0.20, 0.32, (200, 170, 125))]:
        bx0 = W * fx
        by0 = top + (H - top) * (0.62 - fh)
        d.rectangle([bx0, by0, bx0 + W * fw, top + (H - top) * 0.62], fill=col)
        d.rectangle([bx0, by0, bx0 + W * fw, by0 + 2 * s], fill=(150, 115, 80))
        _win_grid(d, bx0 + 2 * s, by0 + 4 * s, bx0 + W * fw - 2 * s,
                  top + (H - top) * 0.60, 3, 2, (90, 70, 55), (120, 95, 70), seed=int(fx * 100))
    # cobbled street
    d.rectangle([0, top + (H - top) * 0.62, W, H], fill=(168, 158, 140))
    for i in range(8):
        d.line([W * (0.05 + i * 0.12), top + (H - top) * 0.66,
                W * (0.02 + i * 0.12), H], fill=(150, 140, 122), width=1 * s)
    # two rows of marchers, real figures with raised arms
    cols = [(200, 60, 60), (60, 120, 200), (60, 160, 80), (220, 160, 40),
            (150, 90, 180), (60, 60, 60)]
    for row, yy, hg in [(0, 0.68, 15), (1, 0.86, 18)]:
        for i in range(6):
            fx = 0.07 + i * 0.15 + (0.05 if row else 0)
            px = W * fx
            py = top + (H - top) * yy
            _person(d, px, py, hg * s, cols[(i + row) % 6],
                    hair=[(40, 30, 25), (20, 20, 20), (120, 90, 50)][(i + row) % 3],
                    arm_up=(i % 2 == 0))
    # placards on sticks with text lines
    for fx in (0.25, 0.70):
        px = W * fx
        d.line([px, top + (H - top) * 0.45, px, top + (H - top) * 0.66], fill=(60, 60, 60), width=1 * s)
        d.rectangle([px - 8 * s, top + (H - top) * 0.34, px + 8 * s, top + (H - top) * 0.45],
                    fill=(255, 255, 255), outline=INK, width=1 * s)
        d.line([px - 5 * s, top + (H - top) * 0.38, px + 5 * s, top + (H - top) * 0.38],
               fill=(90, 90, 90), width=1 * s)
        d.line([px - 5 * s, top + (H - top) * 0.41, px + 2 * s, top + (H - top) * 0.41],
               fill=(90, 90, 90), width=1 * s)
    # megaphone
    mx, my = W * 0.45, top + (H - top) * 0.60
    d.polygon([(mx, my), (mx + 11 * s, my - 4 * s), (mx + 11 * s, my + 4 * s)], fill=(200, 60, 60))
    d.rectangle([mx - 3 * s, my - 1 * s, mx, my + 4 * s], fill=(120, 40, 40))
    # two tricolour flags, waving (vertical green-white-red)
    for fx in (0.55, 0.88):
        px = W * fx
        d.line([px, top + (H - top) * 0.30, px, top + (H - top) * 0.58], fill=(60, 60, 60), width=1 * s)
        fy0 = top + (H - top) * 0.30
        for j, c in enumerate([(0, 140, 60), (255, 255, 255), (200, 40, 40)]):
            d.rectangle([px, fy0 + j * 3 * s, px + 12 * s, fy0 + (j + 1) * 3 * s], fill=c)
        d.rectangle([px, fy0, px + 12 * s, fy0 + 9 * s], outline=INK, width=1 * s)
    # SCIOPERO banner across the crowd
    bf = F("sans", 8 * s, True)
    btw = bf.getlength("SCIOPERO")
    bx0 = (W - btw - 12 * s) / 2
    d.rectangle([bx0, top + (H - top) * 0.28, bx0 + btw + 12 * s, top + (H - top) * 0.28 + 11 * s],
                fill=(178, 30, 45))
    d.text((bx0 + 6 * s, top + (H - top) * 0.28 + 1 * s), "SCIOPERO", font=bf, fill=(255, 255, 255))


def scene_seoul(d, W, H, top):
    s = S3
    d.rectangle([0, top, W, H], fill=(168, 198, 224))
    # soft clouds
    for (fx, fy) in [(0.55, 0.06), (0.85, 0.12)]:
        d.ellipse([W * fx, top + (H - top) * fy, W * fx + 14 * s, top + (H - top) * fy + 5 * s],
                  fill=(255, 255, 255))
    # stone plaza
    d.rectangle([0, top + (H - top) * 0.78, W, H], fill=(200, 195, 185))
    for i in range(6):
        d.line([W * (0.08 + i * 0.16), top + (H - top) * 0.80,
                W * (0.06 + i * 0.16), H], fill=(180, 175, 165), width=1 * s)
    # columned courthouse: pediment with emblem, columns with capitals, steps
    cx = W * 0.30
    d.polygon([(cx - 34 * s, top + (H - top) * 0.30), (cx, top + (H - top) * 0.14),
               (cx + 34 * s, top + (H - top) * 0.30)], fill=(198, 198, 188))
    d.ellipse([cx - 4 * s, top + (H - top) * 0.20, cx + 4 * s, top + (H - top) * 0.28],
              fill=(150, 140, 120))
    d.rectangle([cx - 34 * s, top + (H - top) * 0.30, cx + 34 * s, top + (H - top) * 0.34],
                fill=(225, 225, 215))
    for i in range(3):
        colx = cx - 22 * s + i * 22 * s
        d.rectangle([colx - 4 * s, top + (H - top) * 0.30, colx + 4 * s, top + (H - top) * 0.34],
                    fill=(240, 240, 230))
        d.rectangle([colx - 3 * s, top + (H - top) * 0.34, colx + 3 * s,
                     top + (H - top) * 0.70], fill=(242, 242, 232))
        d.line([colx - 3 * s, top + (H - top) * 0.36, colx - 3 * s, top + (H - top) * 0.68],
               fill=(200, 200, 190), width=1 * s)
        d.rectangle([colx - 4 * s, top + (H - top) * 0.70, colx + 4 * s, top + (H - top) * 0.72],
                    fill=(240, 240, 230))
    # tall windows between the columns
    for i in range(2):
        wx0 = cx - 13 * s + i * 24 * s
        d.rectangle([wx0, top + (H - top) * 0.40, wx0 + 6 * s, top + (H - top) * 0.68],
                    fill=(70, 85, 110))
        d.line([wx0 + 3 * s, top + (H - top) * 0.40, wx0 + 3 * s, top + (H - top) * 0.68],
               fill=(200, 210, 225), width=1 * s)
    d.rectangle([cx - 36 * s, top + (H - top) * 0.72, cx + 36 * s,
                 top + (H - top) * 0.76], fill=(210, 210, 200))
    for j in range(3):
        d.rectangle([cx - 40 * s, top + (H - top) * (0.76 + j * 0.06),
                     cx + 40 * s, top + (H - top) * (0.80 + j * 0.06)], fill=(190, 190, 180))
    # scales of justice: brass post, beam, chains, two pans
    sx, sy = W * 0.72, H - 4 * s
    d.line([sx, sy - 20 * s, sx, sy], fill=(90, 75, 40), width=2 * s)
    d.ellipse([sx - 2 * s, sy - 22 * s, sx + 2 * s, sy - 18 * s], fill=(200, 170, 60))
    d.line([sx - 13 * s, sy - 18 * s, sx + 13 * s, sy - 18 * s], fill=(90, 75, 40), width=1 * s)
    for sgn in (-1, 1):
        px = sx + sgn * 12 * s
        d.line([px, sy - 18 * s, px - 3 * s, sy - 11 * s], fill=(90, 75, 40), width=1 * s)
        d.line([px, sy - 18 * s, px + 3 * s, sy - 11 * s], fill=(90, 75, 40), width=1 * s)
        d.arc([px - 4 * s, sy - 12 * s, px + 4 * s, sy - 6 * s], 0, 180, fill=(200, 170, 60), width=2 * s)
    # document stamped with an X (bottom-left): paper, text lines, red X + ring
    dx, dy = 6 * s, H - 17 * s
    d.rectangle([dx, dy, dx + 17 * s, dy + 13 * s], fill=(255, 255, 255), outline=INK, width=1 * s)
    for j in range(2):
        d.line([dx + 2 * s, dy + 2 * s + j * 3 * s, dx + 12 * s, dy + 2 * s + j * 3 * s],
               fill=(150, 150, 150), width=1 * s)
    xf = F("sans", 10 * s, True)
    d.text((dx + 5 * s, dy + 3 * s), "X", font=xf, fill=(178, 30, 45))
    d.ellipse([dx + 3 * s, dy + 2 * s, dx + 14 * s, dy + 12 * s], outline=(178, 30, 45), width=1 * s)
    # Korean flag: white field, taegeuk, four trigrams
    fx = W * 0.92
    d.line([fx, top + (H - top) * 0.30, fx, top + (H - top) * 0.62], fill=(60, 60, 60), width=1 * s)
    d.rectangle([fx, top + (H - top) * 0.30, fx + 15 * s, top + (H - top) * 0.40],
                fill=(255, 255, 255), outline=INK, width=1 * s)
    d.pieslice([fx + 5 * s, top + (H - top) * 0.32, fx + 10 * s, top + (H - top) * 0.38],
               90, 270, fill=(200, 40, 40))
    d.pieslice([fx + 5 * s, top + (H - top) * 0.32, fx + 10 * s, top + (H - top) * 0.38],
               270, 90, fill=(0, 60, 160))
    for (tx0, ty0) in [(1, 0), (11, 0), (1, 7), (11, 7)]:
        d.rectangle([fx + tx0 * s, top + (H - top) * 0.30 + ty0 * s,
                     fx + (tx0 + 3) * s, top + (H - top) * 0.30 + (ty0 + 1) * s], fill=INK)
    # trees
    _tree(d, W * 0.60, H - 2 * s, 5 * s)
    _tree(d, W * 0.97, H - 2 * s, 4 * s)
    chip(d, 6 * s, top + 3 * s, "SEOUL", F("sans", 7 * s, True),
         (18, 18, 18), (255, 255, 255))


def scene_sudan(d, W, H, top):
    s = S3
    # dusty sky with haze band and sun
    d.rectangle([0, top, W, top + (H - top) * 0.45], fill=(238, 220, 178))
    d.rectangle([0, top + (H - top) * 0.45, W, H], fill=(230, 208, 158))
    for (fx, fy) in [(0.12, 0.12), (0.52, 0.06), (0.82, 0.16)]:
        d.ellipse([W * fx, top + (H - top) * fy, W * fx + 15 * s, top + (H - top) * fy + 5 * s],
                  fill=(224, 198, 152))
    sx, sy = W * 0.88, top + (H - top) * 0.20
    d.ellipse([sx - 10 * s, sy - 10 * s, sx + 10 * s, sy + 10 * s], fill=(255, 212, 120))
    d.ellipse([sx - 7 * s, sy - 7 * s, sx + 7 * s, sy + 7 * s], fill=(255, 200, 80))
    # terraced mine pit: benches with shaded faces and a haul road
    for j in range(3):
        y0 = top + (H - top) * (0.55 + j * 0.12)
        x0 = W * (0.05 + j * 0.10)
        x1 = W * (0.55 - j * 0.05)
        d.rectangle([x0, y0, x1, y0 + 6 * s], fill=(172 - j * 22, 122 - j * 12, 72))
        d.rectangle([x0, y0, x1, y0 + 2 * s], fill=(196 - j * 22, 148 - j * 12, 92))
        d.line([x0, y0 + 6 * s, x1, y0 + 6 * s], fill=(120, 85, 50), width=1 * s)
    d.line([W * 0.12, top + (H - top) * 0.56, W * 0.45, top + (H - top) * 0.90],
           fill=(210, 175, 120), width=2 * s)
    # headframe (A-frame with cross-bracing) + sheave wheel + cable
    hx = W * 0.62
    d.line([hx - 9 * s, H - 6 * s, hx, top + (H - top) * 0.30], fill=(60, 50, 40), width=2 * s)
    d.line([hx + 9 * s, H - 6 * s, hx, top + (H - top) * 0.30], fill=(60, 50, 40), width=2 * s)
    d.line([hx - 6 * s, top + (H - top) * 0.62, hx + 6 * s, top + (H - top) * 0.50],
           fill=(60, 50, 40), width=1 * s)
    d.line([hx - 6 * s, top + (H - top) * 0.50, hx + 6 * s, top + (H - top) * 0.62],
           fill=(60, 50, 40), width=1 * s)
    d.ellipse([hx - 5 * s, top + (H - top) * 0.28, hx + 5 * s, top + (H - top) * 0.38],
              outline=(60, 50, 40), width=2 * s)
    d.ellipse([hx - 2 * s, top + (H - top) * 0.31, hx + 2 * s, top + (H - top) * 0.35],
              fill=(60, 50, 40))
    d.line([hx, top + (H - top) * 0.36, hx, top + (H - top) * 0.58], fill=(60, 50, 40), width=1 * s)
    # conveyor with rollers + ore lumps, rising to the headframe
    d.line([W * 0.60, H - 10 * s, W * 0.85, top + (H - top) * 0.55], fill=(80, 70, 55), width=2 * s)
    for i in range(4):
        t = i / 3.0
        px = W * 0.60 + (W * 0.85 - W * 0.60) * t
        py = H - 10 * s + (top + (H - top) * 0.55 - (H - 10 * s)) * t
        d.ellipse([px - 1 * s, py - 1 * s, px + 1 * s, py + 1 * s], fill=(60, 50, 40))
    # mine cart on rails with a gold pile
    cx, cy = W * 0.78, H - 12 * s
    d.line([W * 0.62, H - 3 * s, W * 0.94, H - 3 * s], fill=(70, 60, 45), width=1 * s)
    for rx in range(int(W * 0.64), int(W * 0.94), 6 * s):
        d.line([rx, H - 5 * s, rx, H - 1 * s], fill=(70, 60, 45), width=1 * s)
    d.rectangle([cx - 10 * s, cy - 4 * s, cx + 10 * s, cy + 4 * s], fill=(92, 82, 62))
    d.polygon([(cx - 8 * s, cy - 4 * s), (cx, cy - 11 * s), (cx + 8 * s, cy - 4 * s)],
              fill=(255, 210, 60))
    d.polygon([(cx - 5 * s, cy - 4 * s), (cx - 1 * s, cy - 8 * s), (cx + 3 * s, cy - 4 * s)],
              fill=(255, 228, 120))
    for wx in (-6, 6):
        d.ellipse([cx + wx * s - 2 * s, cy + 4 * s, cx + wx * s + 2 * s, cy + 8 * s], fill=(30, 30, 30))
    # gold nuggets + sparkles on the pit floor
    for (fx, fy) in [(0.30, 0.85), (0.40, 0.92), (0.50, 0.88), (0.22, 0.90)]:
        d.ellipse([W * fx - 2 * s, top + (H - top) * fy - 1 * s,
                   W * fx + 2 * s, top + (H - top) * fy + 1 * s], fill=(255, 210, 60))
        star(d, W * fx, top + (H - top) * fy, 1 * s, (255, 240, 150))
    # drone with dotted smoke trail to an impact burst + dust
    dx, dy = W * 0.35, top + (H - top) * 0.25
    d.rectangle([dx - 5 * s, dy - 2 * s, dx + 5 * s, dy + 2 * s], fill=(40, 40, 40))
    for ox in (-8, 8):
        d.ellipse([dx + ox * s - 4 * s, dy - 5 * s, dx + ox * s + 4 * s, dy - 1 * s],
                  outline=(40, 40, 40), width=1 * s)
    ix, iy = W * 0.45, top + (H - top) * 0.55
    for i in range(7):
        px = dx + (ix - dx) * i / 6
        py = dy + (iy - dy) * i / 6 + 2 * s * math.sin(i)
        d.ellipse([px - 1 * s, py - 1 * s, px + 1 * s, py + 1 * s], fill=(120, 120, 120))
    for ang in range(0, 360, 45):
        d.line([ix, iy, ix + 6 * s * math.cos(math.radians(ang)),
                iy + 6 * s * math.sin(math.radians(ang))], fill=(255, 170, 40), width=1 * s)
    d.ellipse([ix - 4 * s, iy - 4 * s, ix + 4 * s, iy + 4 * s], fill=(255, 190, 70))
    _puff(d, ix + 4 * s, iy + 6 * s, 0, [
        (0, 0, 4 * s, (210, 185, 140)), (5 * s, 1 * s, 3 * s, (225, 200, 155))])
    chip(d, 6 * s, H - 13 * s, "THE GOLD MINE", F("sans", 7 * s, True),
         (18, 18, 18), (255, 210, 60))


def scene_colombia(d, W, H, top):
    s = S3
    d.rectangle([0, top, W, H], fill=(148, 193, 228))
    # clouds
    for (fx, fy) in [(0.08, 0.06), (0.68, 0.04)]:
        d.ellipse([W * fx, top + (H - top) * fy, W * fx + 16 * s, top + (H - top) * fy + 5 * s],
                  fill=(255, 255, 255))
        d.ellipse([W * fx + 4 * s, top + (H - top) * fy - 3 * s,
                   W * fx + 12 * s, top + (H - top) * fy + 3 * s], fill=(255, 255, 255))
    # Monserrate hill: shaded slope, church, cable-car line
    d.polygon([(0, H), (W * 0.30, top + (H - top) * 0.30), (W * 0.62, H)],
              fill=(58, 128, 68))
    d.polygon([(W * 0.30, top + (H - top) * 0.30), (W * 0.46, top + (H - top) * 0.62),
               (W * 0.62, H), (W * 0.30, H)], fill=(48, 110, 58))
    hx, hy = W * 0.30, top + (H - top) * 0.30
    d.rectangle([hx - 6 * s, hy - 9 * s, hx + 6 * s, hy], fill=(242, 232, 202))
    d.polygon([(hx - 7 * s, hy - 9 * s), (hx, hy - 14 * s), (hx + 7 * s, hy - 9 * s)],
              fill=(182, 62, 52))
    d.rectangle([hx - 2 * s, hy - 6 * s, hx + 2 * s, hy - 1 * s], fill=(90, 70, 50))
    d.line([hx + 8 * s, hy - 2 * s, hx + 8 * s, hy - 12 * s], fill=(150, 120, 80), width=1 * s)
    d.line([hx + 8 * s, hy - 12 * s, hx + 11 * s, hy - 12 * s], fill=(150, 120, 80), width=1 * s)
    d.line([W * 0.02, H - 6 * s, hx - 4 * s, hy + 2 * s], fill=(60, 60, 60), width=1 * s)
    d.rectangle([W * 0.10, H - 12 * s, W * 0.10 + 6 * s, H - 6 * s], fill=(200, 60, 60))
    # city skyline with lit windows, one tower with antenna
    for (fx, fw, fh, col) in [(0.60, 0.08, 0.30, (118, 128, 148)),
                              (0.70, 0.10, 0.42, (100, 110, 132)),
                              (0.82, 0.08, 0.34, (128, 138, 158))]:
        bx0 = W * fx
        by0 = H - (H - top) * fh
        d.rectangle([bx0, by0, W * (fx + fw), H], fill=col)
        _win_grid(d, bx0 + 1 * s, by0 + 2 * s, W * (fx + fw) - 1 * s, H - 2 * s,
                  2, 3, (255, 214, 130), (80, 88, 110), seed=int(fx * 100))
    d.line([W * 0.75, H - (H - top) * 0.42, W * 0.75, H - (H - top) * 0.42 - 6 * s],
           fill=(80, 88, 110), width=1 * s)
    # crowd with raised arms, banner, confetti, flag band
    for i in range(7):
        fx = 0.08 + i * 0.09
        px = W * fx
        py = H - 2 * s
        _person(d, px, py, 11 * s,
                [(230, 200, 40), (0, 90, 180), (200, 40, 40)][i % 3],
                arm_up=(i % 2 == 0))
    d.rectangle([W * 0.30, H - 24 * s, W * 0.70, H - 15 * s], fill=(255, 255, 255), outline=INK, width=1 * s)
    bf = F("sans", 6 * s, True)
    d.text((W * 0.30 + 4 * s, H - 23 * s), "NO A LA REFORMA", font=bf, fill=INK)
    rnd = random.Random(11)
    for _ in range(14):
        fx = rnd.random()
        fy = 0.08 + rnd.random() * 0.30
        c = [(230, 200, 40), (0, 90, 180), (200, 40, 40), (60, 160, 80)][rnd.randrange(4)]
        d.rectangle([W * fx, top + (H - top) * fy, W * fx + 2 * s, top + (H - top) * fy + 1 * s],
                    fill=c)
    for j, c in enumerate([(230, 200, 40), (0, 90, 180), (200, 40, 40)]):
        d.rectangle([W * 0.88, top + (H - top) * (0.55 + j * 0.05),
                     W * 0.97, top + (H - top) * (0.60 + j * 0.05)], fill=c)
    d.line([W * 0.88, top + (H - top) * 0.55, W * 0.88, top + (H - top) * 0.72],
           fill=(60, 60, 60), width=1 * s)
    bf2 = F("sans", 7 * s, True)
    tw_ = bf2.getlength("COLOMBIA")
    d.text(((W - tw_) / 2, top + 2 * s), "COLOMBIA", font=bf2, fill=(18, 18, 18))


def scene_gaza(d, W, H, top):
    s = S3
    # dusk sky: warm band near the horizon
    d.rectangle([0, top, W, top + (H - top) * 0.50], fill=(232, 214, 180))
    d.rectangle([0, top + (H - top) * 0.50, W, H], fill=(222, 198, 158))
    # sun + birds
    sx, sy = W * 0.88, top + (H - top) * 0.18
    d.ellipse([sx - 10 * s, sy - 10 * s, sx + 10 * s, sy + 10 * s], fill=(255, 212, 120))
    d.ellipse([sx - 7 * s, sy - 7 * s, sx + 7 * s, sy + 7 * s], fill=(255, 200, 80))
    for (fx, fy) in [(0.55, 0.12), (0.70, 0.08), (0.40, 0.06)]:
        d.arc([W * fx - 5 * s, top + (H - top) * fy - 3 * s, W * fx + 5 * s,
               top + (H - top) * fy + 3 * s], 200, 340, fill=(60, 60, 60), width=1 * s)
    # apartment blocks: shaded facades, window grids, rooftop tanks
    for (fx, fw, lean, col) in [(0.06, 0.20, 0, (152, 142, 126)),
                                (0.30, 0.20, 4, (140, 130, 114)),
                                (0.55, 0.20, 0, (160, 150, 134))]:
        bx0, by0 = W * fx, top + (H - top) * (0.35 if not lean else 0.40)
        d.polygon([(bx0, H), (bx0 + W * lean * 0.01, by0),
                   (bx0 + W * fw + W * lean * 0.01, by0), (bx0 + W * fw, H)], fill=col)
        # shaded side
        d.polygon([(bx0 + W * fw * 0.75, H), (bx0 + W * fw * 0.75 + W * lean * 0.01, by0),
                   (bx0 + W * fw + W * lean * 0.01, by0), (bx0 + W * fw, H)],
                  fill=(128, 118, 102))
        rnd = random.Random(int(fx * 100))
        for r in range(3):
            for c in range(3):
                wx = bx0 + W * fw * (0.14 + c * 0.30) + W * lean * 0.005
                wy = by0 + (H - by0) * (0.14 + r * 0.28)
                lit = rnd.random() < 0.4
                d.rectangle([wx, wy, wx + 4 * s, wy + 4 * s],
                            fill=(255, 214, 130) if lit else (58, 68, 78))
        # rooftop water tank
        d.rectangle([bx0 + W * fw * 0.30, by0 - 5 * s, bx0 + W * fw * 0.55, by0],
                    fill=(110, 105, 95))
    # cracked, leaning block: jagged crack + rubble at its base
    bx0 = W * 0.30
    by0 = top + (H - top) * 0.40
    d.line([bx0 + 6 * s, by0 + 4 * s, bx0 + 10 * s, by0 + 14 * s, bx0 + 7 * s, by0 + 24 * s,
            bx0 + 12 * s, by0 + 34 * s], fill=(90, 82, 68), width=1 * s)
    for (ox, oy, ow, oh) in [(2, -2, 8, 3), (10, -1, 6, 2), (16, -3, 9, 3)]:
        d.polygon([(bx0 + ox * s, H + oy * s), (bx0 + (ox + ow // 2) * s, H + (oy - oh) * s),
                   (bx0 + (ox + ow) * s, H + oy * s)], fill=(120, 110, 94))
    # minaret with balcony and cap
    mx = W * 0.78
    d.rectangle([mx - 3 * s, top + (H - top) * 0.25, mx + 3 * s, H], fill=(202, 192, 172))
    d.rectangle([mx - 5 * s, top + (H - top) * 0.40, mx + 5 * s, top + (H - top) * 0.44],
                fill=(180, 168, 148))
    d.polygon([(mx - 5 * s, top + (H - top) * 0.25), (mx, top + (H - top) * 0.15),
               (mx + 5 * s, top + (H - top) * 0.25)], fill=(150, 120, 80))
    d.line([mx, top + (H - top) * 0.15, mx, top + (H - top) * 0.10], fill=(150, 120, 80), width=1 * s)
    # white dove with olive twig, wings spread
    dx, dy = W * 0.45, top + (H - top) * 0.18
    d.ellipse([dx - 7 * s, dy - 3 * s, dx + 7 * s, dy + 3 * s], fill=(255, 255, 255))
    d.ellipse([dx - 2 * s, dy - 2 * s, dx + 2 * s, dy + 2 * s], fill=(235, 235, 235))
    d.polygon([(dx + 6 * s, dy), (dx + 13 * s, dy - 4 * s), (dx + 12 * s, dy + 2 * s)],
              fill=(255, 255, 255))
    d.polygon([(dx - 6 * s, dy - 2 * s), (dx - 13 * s, dy - 7 * s), (dx - 12 * s, dy + 1 * s)],
              fill=(242, 242, 242))
    d.ellipse([dx - 8 * s, dy - 1 * s, dx - 6 * s, dy + 1 * s], fill=(40, 40, 40))
    d.line([dx + 12 * s, dy + 2 * s, dx + 18 * s, dy + 6 * s], fill=(60, 130, 60), width=1 * s)
    for (ox, oy) in [(14, 3), (16, 5)]:
        d.ellipse([dx + ox * s - 1 * s, dy + oy * s - 1 * s,
                   dx + ox * s + 1 * s, dy + oy * s + 1 * s], fill=(70, 140, 70))
    # striped fence flag
    fx = W * 0.92
    d.line([fx, top + (H - top) * 0.55, fx, top + (H - top) * 0.85], fill=(60, 60, 60), width=1 * s)
    for j, c in enumerate([(255, 255, 255), (178, 30, 45), (255, 255, 255)]):
        d.rectangle([fx, top + (H - top) * (0.55 + j * 0.05), fx + 10 * s,
                     top + (H - top) * (0.60 + j * 0.05)], fill=c)
    d.rectangle([fx, top + (H - top) * 0.55, fx + 10 * s, top + (H - top) * 0.70],
                outline=INK, width=1 * s)
    chip(d, 6 * s, top + 3 * s, "THE CEASEFIRE LINE", F("sans", 7 * s, True),
         (18, 18, 18), (255, 255, 255))


def scene_phillips(d, W, H, top):
    s = S3
    # outfield with mowing stripes
    d.rectangle([0, top, W, H], fill=(58, 138, 68))
    for i in range(5):
        d.rectangle([W * i / 5, top, W * (i + 1) / 5, H],
                    fill=(58, 138, 68) if i % 2 == 0 else (66, 150, 76))
    # stadium stand: tiered rows of crowd dots
    d.rectangle([0, top, W, top + (H - top) * 0.30], fill=(88, 88, 108))
    d.rectangle([0, top + (H - top) * 0.28, W, top + (H - top) * 0.32], fill=(60, 60, 80))
    rnd = random.Random(5)
    for r in range(3):
        for c in range(18):
            fx = 0.02 + c * 0.054 + (0.02 if r % 2 else 0)
            fy = 0.05 + r * 0.08
            col = [(255, 255, 255), (255, 210, 60), (200, 60, 60), (80, 140, 220)][rnd.randrange(4)]
            d.ellipse([W * fx - 1 * s, top + (H - top) * fy - 1 * s,
                       W * fx + 1 * s, top + (H - top) * fy + 1 * s], fill=col)
    # floodlight towers with light beams
    for fx in (0.05, 0.95):
        d.line([W * fx, top + 2 * s, W * fx, top + (H - top) * 0.28], fill=(38, 38, 38), width=2 * s)
        d.rectangle([W * fx - 5 * s, top, W * fx + 5 * s, top + 4 * s], fill=(40, 40, 40))
        for k in range(3):
            d.ellipse([W * fx - 4 * s + k * 4 * s - 1 * s, top + 1 * s,
                       W * fx - 4 * s + k * 4 * s + 1 * s, top + 3 * s], fill=(255, 242, 170))
        d.polygon([(W * fx - 4 * s, top + 4 * s), (W * fx + 4 * s, top + 4 * s),
                   (W * fx + 22 * s if fx < 0.5 else W * fx - 22 * s, top + (H - top) * 0.42)],
                  fill=(255, 245, 190, 40))
    # ad boards with simple blocks
    for (fx, c) in [(0.05, (255, 255, 255)), (0.30, (255, 210, 60)), (0.75, (200, 60, 60))]:
        d.rectangle([W * fx, top + (H - top) * 0.32, W * fx + W * 0.18, top + (H - top) * 0.40],
                    fill=c)
        d.rectangle([W * fx + 2 * s, top + (H - top) * 0.34, W * fx + W * 0.18 - 2 * s,
                     top + (H - top) * 0.36], fill=(0, 0, 0, 30))
    # central pitch strip with crease lines
    px0, px1 = W * 0.38, W * 0.62
    d.rectangle([px0, top + (H - top) * 0.42, px1, H - 4 * s], fill=(212, 192, 142))
    d.rectangle([px0, top + (H - top) * 0.42, px1, top + (H - top) * 0.46], fill=(198, 176, 126))
    for yy in (0.55, 0.80):
        d.line([px0, top + (H - top) * yy, px1, top + (H - top) * yy],
               fill=(255, 255, 255), width=1 * s)
    # batsman: helmet, pads, bat, stance
    bx, by = W * 0.44, H - 10 * s
    d.ellipse([bx - 3 * s, by - 14 * s, bx + 3 * s, by - 8 * s], fill=(240, 200, 160))
    d.ellipse([bx - 3 * s, by - 14 * s, bx + 3 * s, by - 10 * s], fill=(30, 60, 120))
    d.rectangle([bx - 4 * s, by - 8 * s, bx + 4 * s, by + 1 * s], fill=(255, 255, 255))
    d.rectangle([bx - 4 * s, by - 8 * s, bx + 4 * s, by - 5 * s], fill=(230, 230, 235))
    d.rectangle([bx - 5 * s, by + 1 * s, bx - 1 * s, by + 8 * s], fill=(255, 255, 255))
    d.rectangle([bx + 1 * s, by + 1 * s, bx + 5 * s, by + 8 * s], fill=(255, 255, 255))
    d.line([bx + 4 * s, by - 5 * s, bx + 13 * s, by - 14 * s], fill=(182, 142, 82), width=2 * s)
    d.ellipse([bx + 14 * s - 2 * s, by - 15 * s, bx + 14 * s + 2 * s, by - 11 * s],
              fill=(200, 40, 40))
    # small fielder, left of the pitch
    fx2, fy2 = W * 0.30, H - 8 * s
    _person(d, fx2, fy2, 11 * s, (40, 90, 160), arm_up=False)
    # stumps + bails
    for ox in (-3, 0, 3):
        d.line([W * 0.58 + ox * s, H - 12 * s, W * 0.58 + ox * s, H - 4 * s],
               fill=(232, 202, 122), width=1 * s)
    d.line([W * 0.58 - 3 * s, H - 13 * s, W * 0.58 + 3 * s, H - 13 * s],
           fill=(232, 202, 122), width=1 * s)
    # big number 118 with a soft shadow
    nf = F("sans", 22 * s, True)
    d.text((W * 0.66 + 1 * s, top + (H - top) * 0.55 + 1 * s), "118", font=nf, fill=(30, 80, 40))
    d.text((W * 0.66, top + (H - top) * 0.55), "118", font=nf, fill=(255, 255, 255))
    # scoreboard box bottom-left
    sf = F("sans", 7 * s, True)
    st = "NZ 368 \u00b7 IND 159/1"
    sw = sf.getlength(st)
    d.rectangle([6 * s, H - 13 * s, 6 * s + sw + 8 * s, H - 2 * s], fill=(20, 30, 50))
    d.text((6 * s + 4 * s, H - 12 * s), st, font=sf, fill=(255, 255, 255))


SCENES = {1: scene_kyiv, 2: scene_akvan, 3: scene_markets, 4: scene_ukeu,
          5: scene_cop31, 6: scene_poland, 7: scene_iraq, 8: scene_italy,
          9: scene_seoul, 10: scene_sudan, 11: scene_colombia,
          12: scene_gaza, 13: scene_phillips}


# ---------------------------------------------------------------- panels

def draw_banner(d, x, y, w, h, reg, keyword, badge, kw_size, badge_size):
    col = REGCOL[reg]
    d.rectangle([x, y, x + w, y + h], fill=col)
    kf = F("sans", kw_size, True)
    d.text((x + 6, y + (h - kw_size) / 2 - 1), keyword, font=kf, fill=(255, 255, 255))
    bf = F("sans", badge_size, True)
    bw = bf.getlength(badge)
    d.text((x + w - 5 - bw, y + (h - badge_size) / 2 - 1), badge, font=bf, fill=PINK)


def draw_lead(d, page, x, story):
    y0, w, h = 258, 325, 236
    reg = story["reg"]
    # scene (own 3x layer; content below banner 34 + descriptor 13)
    layer, ld = scene_layer(w, 126)
    SCENES[story["n"]](ld, w * S3, 126 * S3, (34 + 13) * S3)
    paste_scene(page, layer, x, y0, w, 126)
    draw_banner(d, x, y0, w, 34, reg, story["banner"], story["badge"], 21, 8.5)
    # descriptor strip
    d.rectangle([x, y0 + 34, x + w, y0 + 47], fill=PAPER)
    df = F("sans", 11.5, True)
    d.text((x + 6, y0 + 34 + 1), story["desc"], font=df, fill=INK)
    # kicker
    kf = F("sans", 11, True)
    d.text((x + 4, y0 + 130), story["kicker"], font=kf, fill=REGCOL[reg])
    # headline Serif-Bold 25, max 2 lines
    hf = F("serif", 25, True)
    lines = wrap(d, story["head"], hf, w - 8)
    assert len(lines) <= 2, f"lead {story['n']} headline wraps to {len(lines)}"
    yy = y0 + 146
    for ln in lines:
        d.text((x + 4, yy), ln, font=hf, fill=INK)
        yy += 29
    # summary Sans 12, max 2 lines (trim lead 1 only if it overflows)
    sf = F("sans", 12, False)
    text = story["summ"]
    lines = wrap(d, text, sf, w - 8)
    if len(lines) > 2 and "summ_trim" in story:
        text = story["summ_trim"]
        lines = wrap(d, text, sf, w - 8)
    assert len(lines) <= 2, f"lead {story['n']} summary wraps to {len(lines)}"
    yy = y0 + 205
    for ln in lines:
        d.text((x + 4, yy), ln, font=sf, fill=DARK)
        yy += 15
    d.rectangle([x, y0, x + w, y0 + h], outline=FRAME, width=1)


def draw_medium(d, page, x, y0, story):
    w, h = 192, 162
    reg = story["reg"]
    layer, ld = scene_layer(w, 70)
    SCENES[story["n"]](ld, w * S3, 70 * S3, 30 * S3)
    paste_scene(page, layer, x, y0, w, 70)
    draw_banner(d, x, y0, w, 30, reg, story["banner"],
                "REPORTED \u00b7 " + story["src"], 16.5, 7)
    kf = F("sans", 11, True)
    d.text((x + 4, y0 + 74), story["kicker"], font=kf, fill=REGCOL[reg])
    hf = F("sans", 18, True)
    lines = wrap(d, story["head"], hf, w - 4)
    assert len(lines) <= 2, f"medium {story['n']} headline wraps to {len(lines)}"
    yy = y0 + 88
    for ln in lines:
        d.text((x + 2, yy), ln, font=hf, fill=INK)
        yy += 22
    sf = F("sans", 11, False)
    lines = wrap(d, story["summ"], sf, w - 4)
    assert len(lines) <= 2, f"medium {story['n']} summary wraps to {len(lines)}"
    yy = y0 + 130
    for ln in lines:
        d.text((x + 2, yy), ln, font=sf, fill=DARK)
        yy += 14
    d.rectangle([x, y0, x + w, y0 + h], outline=FRAME, width=1)


# ---------------------------------------------------------------- page top

def draw_top(d):
    # kicker row y=10
    d.text((M, 10), "ONE DAY OF WORLD NEWS, ONE PICTURE",
           font=F("sans", 13, True), fill=RED)
    rk = F("sans", 11, True)
    rt = "35 STORIES \u00b7 6 REGIONS \u00b7 ALL THIS FRIDAY"
    d.text((M + CW - rk.getlength(rt), 11), rt, font=rk, fill=DARK)
    # date, centred, as large as fits
    size = fit_size("Friday 20 November 2026", "serif", 96, CW, bold=True)
    df = F("serif", size, True)
    dt = "Friday 20 November 2026"
    d.text(((W - df.getlength(dt)) / 2, 30), dt, font=df, fill=INK)
    # double rule
    d.rectangle([M, 116, M + CW, 120], fill=INK)
    d.rectangle([M, 121, M + CW, 122], fill=INK)


def draw_strip1(d):
    y0, y1 = 126, 172
    d.rectangle([M, y0, M + 84, y1], fill=RED)
    lf = F("sans", 10.5, True)
    for i, t in enumerate(["THE DAY", "AS IT", "UNFOLDED"]):
        d.text((M + 8, y0 + 4 + i * 14), t, font=lf, fill=(255, 255, 255))
    x0 = M + 84
    colw = (M + CW - x0) / 7.0
    for i, (head, cap) in enumerate(STRIP1):
        cx = x0 + i * colw
        hs = fit_size(head, "serif", 15, colw - 8, bold=True)
        hf = F("serif", hs, True)
        d.text((cx + 4, y0 + 3), head, font=hf, fill=RED)
        cf = F("sans", 9.5, False)
        lines = wrap(d, cap, cf, colw - 8)
        assert len(lines) <= 2
        yy = y0 + 23
        for ln in lines:
            d.text((cx + 4, yy), ln, font=cf, fill=DARK)
            yy += 12
        if i:
            d.line([cx, y0, cx, y1], fill=DIV, width=1)
    d.rectangle([M, y0, M + CW, y1], outline=INK, width=1)


def draw_strip2(d):
    y0, y1 = 172, 226
    d.rectangle([M, y0, M + 84, y1], fill=RED)
    lf = F("sans", 10.5, True)
    for i, t in enumerate(["THE DAY", "IN", "NUMBERS"]):
        d.text((M + 8, y0 + 6 + i * 14), t, font=lf, fill=(255, 255, 255))
    x0 = M + 84
    colw = (M + CW - x0) / 6.0
    for i, (num, cap) in enumerate(STRIP2):
        cx = x0 + i * colw
        ns = fit_size(num, "serif", 24, colw - 8, bold=True)
        nf = F("serif", ns, True)
        d.text((cx + 4, y0 + 3), num, font=nf, fill=RED)
        cf = F("sans", 9.5, False)
        lines = wrap(d, cap, cf, colw - 8)
        assert len(lines) <= 2
        yy = y0 + 31
        for ln in lines:
            d.text((cx + 4, yy), ln, font=cf, fill=DARK)
            yy += 12
        if i:
            d.line([cx, y0, cx, y1], fill=DIV, width=1)
    d.rectangle([M, y0, M + CW, y1], outline=INK, width=1)


def draw_region_bar(d):
    y0, y1 = 232, 252
    x = M
    total = sum(c for _, c in REGCOUNT)
    for reg, cnt in REGCOUNT:
        wseg = CW * cnt / total
        d.rectangle([x, y0 + 2, x + wseg, y1 - 2], fill=BARCOL[reg])
        lab = f"{REGNAME[reg]} {cnt}"
        ls = fit_size(lab, "sans", 11, wseg - 6, bold=True)
        lf = F("sans", ls, True)
        d.text((x + (wseg - lf.getlength(lab)) / 2, y0 + 2 + (16 - ls) / 2), lab,
               font=lf, fill=(255, 255, 255))
        x += wseg
    d.rectangle([M, y0, M + CW, y1], outline=FRAME, width=1)


# ---------------------------------------------------------------- map

def draw_map(d):
    x0, y0, w, h = M, 824, 396, 140
    d.rectangle([x0, y0, x0 + w, y0 + h], fill=MAPFILL, outline=INK, width=1)
    tf = F("sans", 11, True)
    d.text((x0 + 8, y0 + 4), "WHERE IT HAPPENED", font=tf, fill=INK)
    mx, my, mw, mh = x0 + 8, y0 + 20, 380, 84

    def proj(lon, lat):
        px = (lon + 180) / 360.0 * mw
        py = (80 - lat) / 130.0 * mh
        return (mx + max(0.0, min(mw, px)), my + max(0.0, min(mh, py)))

    for poly, reg in zip(CONTINENTS_LL, POLY_REG):
        d.polygon([proj(lon, lat) for lon, lat in poly], fill=REGCOL[reg])
    # white numbered pins, navy outline
    pf = F("sans", 7, True)
    for n, px, py in MAP_PINS:
        cx, cy = mx + px, my + py
        d.ellipse([cx - 7, cy - 7, cx + 7, cy + 7], fill=(255, 255, 255),
                  outline=NAVY, width=1)
        t = str(n)
        d.text((cx - pf.getlength(t) / 2, cy - 5), t, font=pf, fill=NAVY)
    cf = F("sans", 9, False)
    d.text((x0 + 8, y0 + 108), "Each number is the story with that number on this page.",
           font=cf, fill=GREY)
    # legend row
    lf = F("sans", 8, True)
    lx = x0 + 8
    ly = y0 + 124
    for reg, cnt in REGCOUNT:
        lab = f"{REGNAME[reg]} {cnt}"
        d.ellipse([lx, ly, lx + 7, ly + 7], fill=REGCOL[reg])
        lx += 10
        d.text((lx, ly - 1), lab, font=lf, fill=DARK)
        lx += lf.getlength(lab) + 8


# ---------------------------------------------------------------- compact list

def compact_font_size(d):
    for size in (10.5, 10, 9.5, 9, 8.5):
        bf = F("sans", size, True)
        rf = F("sans", size, False)
        ok = True
        for n, reg, dl, det in COMPACT:
            wdt = 11 + 3 + bf.getlength(dl) + bf.getlength(" \u2014 ") + rf.getlength(det)
            if wdt > 286:
                ok = False
                break
        if ok:
            return size
    return 8.5


def draw_compact(d):
    x0, y0, x1 = 420, 824, 1010
    tf = F("sans", 12, True)
    d.text((x0, y0 + 2), "ALSO ON FRIDAY 20 NOVEMBER \u2014 22 MORE STORIES",
           font=tf, fill=INK)
    d.line([x0, y0 + 18, x1, y0 + 18], fill=INK, width=1)
    size = compact_font_size(d)
    bf = F("sans", size, True)
    rf = F("sans", size, False)
    nf = F("sans", 7.5, True)
    colw = 286
    for i, (n, reg, dl, det) in enumerate(COMPACT):
        col = i // 11
        row = i % 11
        cx = x0 + 4 + col * (colw + 10)
        top = 843 + row * 11.4
        cy = top + 5
        d.ellipse([cx, cy - 5.5, cx + 11, cy + 5.5], fill=REGCOL[reg])
        t = str(n)
        d.text((cx + 5.5 - nf.getlength(t) / 2, cy - 5), t, font=nf, fill=(255, 255, 255))
        tx = cx + 14
        d.text((tx, top), dl, font=bf, fill=REGCOL[reg])
        tx += bf.getlength(dl) + bf.getlength(" \u2014 ")
        d.text((tx, top), det, font=rf, fill=DARK)
    d.rectangle([x0, y0, x1, 972], outline=FRAME, width=1)


# ---------------------------------------------------------------- bottom

def draw_bottom(d):
    # DATE CHECK box y=972..1006, black outline 2px, all black
    d.rectangle([M, 972, M + CW, 1006], outline=(0, 0, 0), width=2)
    bf = F("sans", 10, True)
    rf = F("sans", 10, False)
    rest = DATECHECK[len("DATE CHECK \u2014 "):]
    segs = [("DATE CHECK \u2014 ", bf), (rest, rf)]
    lines = wrap_segments(d, segs, None, CW - 16)
    assert len(lines) <= 2, f"DATE CHECK wraps to {len(lines)}"
    yy = 976
    for line in lines:
        cx = M + 8
        for j, (t, font) in enumerate(line):
            d.text((cx, yy), t, font=font, fill=INK)
            cx += font.getlength(t)
            if j < len(line) - 1:
                cx += font.getlength(" ")
        yy += 13
    # footer centred Serif 9.5 grey
    ff = F("serif", 9.5, False)
    d.text(((W - ff.getlength(FOOTER)) / 2, 1010), FOOTER, font=ff, fill=GREY)


# ---------------------------------------------------------------- build

def build():
    page = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(page)
    draw_top(d)
    draw_strip1(d)
    draw_strip2(d)
    draw_region_bar(d)
    for i, st in enumerate(LEADS):
        draw_lead(d, page, M + i * 335, st)
    for i, st in enumerate(MEDIUMS):
        row, col = divmod(i, 5)
        draw_medium(d, page, M + col * 201, 494 + row * 162, st)
    draw_map(d)
    draw_compact(d)
    draw_bottom(d)
    # 35 ids exactly once
    ids = [s["n"] for s in LEADS] + [s["n"] for s in MEDIUMS] + [c[0] for c in COMPACT]
    assert sorted(ids) == list(range(1, 36)), ids
    return page


if __name__ == "__main__":
    out = os.environ.get("MAKEFUN_OUTPUT_DIR", "/tmp/v21-out")
    os.makedirs(out, exist_ok=True)
    img = build()
    img.save(os.path.join(out, "entry.png"))
    print("saved", os.path.join(out, "entry.png"), img.size)
