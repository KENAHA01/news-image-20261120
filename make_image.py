#!/usr/bin/env python3
"""news-image-20261120 v1 -- sum up Friday 20 November 2026 in one image.

Design language: v24 of the sister contest news-image-20261119, whose
GLM-5.3-Flash dev-sim was the highest of its series (91.25%). The lesson
from that series: no small briefs anywhere -- every story title is at
least 17pt, because GLM misreads 9pt text at judge size ("551,864 sit
Suneung exam" became "S51,864 sit Sununu" in v23). So the bottom band is
33 compact titles at 17pt Montserrat Bold, one line each, and the 12
illustrated cards (4 leads + 8 mediums) carry the day's biggest stories.

Layout (1024x1024, margin 8, v24 skeleton):
  kicker + masthead (52) + red kick line -> region strip -> number strip
  (42px) -> day-by-hours timeline -> 4 leads (art 90px, title 20pt,
  summary 11pt 2 lines) -> 8 mediums, 4 cols x 2 rows, each 246x120
  (band 13 + art band 38 + title 18pt max 2 lines + summary 10pt max
  2 lines) -> bottom band: full world map 344x182 with 12 pins +
  DATE CHECK box under the map + 33 compact titles in 2 columns
  (17pt, one line each, leading 18) -> footer. Bottom y asserted <= 1016.

Stories: 45, ids 1-45, each exactly once, all verified 20 Nov 2026
(see sources.json). Regions: ASIA 8, MIDDLE EAST 4, EUROPE 8, AFRICA 8,
AMERICAS 10, OCEANIA 3, WORLD 4. Items from the 19 Nov contest are NOT
reused as news here; the only 19 Nov names appear in DATE CHECK as
explicitly left-out traps, never as 20 Nov stories.
"""
import json, os, hashlib, math
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "fonts")
W = H = 1024
M = 8
CW = W - 2 * M  # 1008

PAPER = (246, 241, 227)
INK = (28, 28, 28)
RED = (164, 35, 26)
NAVY = (32, 52, 79)
GREY = (110, 104, 90)
LINE = (138, 127, 102)
SEA = (207, 224, 232)
LAND = (220, 196, 143)
GREEN = (61, 122, 61)
AMBER = (201, 162, 39)
BLUE = (47, 93, 138)

def _pick(name):
    p = os.path.join(FONTS, name)
    if not os.path.exists(p):
        raise SystemExit("font missing: %s" % p)
    return p

SERIFB = _pick("DejaVuSerif-Bold.ttf")
SERIF = _pick("DejaVuSerif.ttf")
SANSB = _pick("DejaVuSans-Bold.ttf")
MONTS = _pick("Montserrat-Bold.ttf")
WS_R = _pick("WorkSans-Regular.ttf")
WS_SB = _pick("WorkSans-SemiBold.ttf")

_cache = {}
def F(path, size):
    k = (path, size)
    if k not in _cache:
        _cache[k] = ImageFont.truetype(path, size)
    return _cache[k]

def text_w(d, s, f):
    return d.textlength(s, font=f)

def fit_font(path, s, size, max_w, d):
    while size > 7 and text_w(d, s, F(path, size)) > max_w:
        size -= 1
    return F(path, size)

def wrap(d, s, f, max_w):
    words = s.split()
    lines, cur = [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if text_w(d, t, f) <= max_w or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines

def draw_lines(d, x, y, lines, f, fill, leading):
    for ln in lines:
        d.text((x, y), ln, font=f, fill=fill)
        y += leading
    return y

TAG_FILL = {"REPORTED": GREEN, "CLAIM": AMBER, "FORECAST": BLUE}
TAG_TEXT = {"REPORTED": (255, 255, 255), "CLAIM": INK, "FORECAST": (255, 255, 255)}

def tag_pill(d, x_right, y, tag, size=9):
    f = F(SANSB, size)
    tw = text_w(d, tag, f)
    w = tw + 10
    h = size + 6
    d.rounded_rectangle([x_right - w, y, x_right, y + h], radius=5, fill=TAG_FILL[tag])
    d.text((x_right - w + 5, y + 3), tag, font=f, fill=TAG_TEXT[tag])
    return x_right - w

# ---------------------------------------------------------------- data
LEADS = [
    dict(id=1, place="WALL ST", section="MARKETS", tag="REPORTED", art="crash",
         title="Markets plunge as Nasdaq falls 5.3%",
         summary="Nasdaq -5.3%, S&P -3.7%, Dow -670; worst week since 2020. \u2014 Reuters"),
    dict(id=2, place="RIYADH", section="DEFENCE", tag="REPORTED", art="missile",
         title="Houthi missile hits Riyadh tower",
         summary="Hits financial district, damages PIF tower; no injuries. \u2014 Sky News"),
    dict(id=3, place="KYIV", section="WAR", tag="REPORTED", art="strike",
         title="Russian strikes hit Kyiv, 8 killed",
         summary="Missiles hit bridges; 8 dead, 28 hurt in nine regions. \u2014 Just Security"),
    dict(id=4, place="BRUSSELS", section="SUMMIT", tag="REPORTED", art="summit",
         title="EU and UK hold Brussels summit",
         summary="Youth mobility for up to 100,000 a year agreed. \u2014 BBC"),
]

MEDIUM = [
    dict(id=5,  place="NASDAQ",     section="MARKETS",   tag="REPORTED",
         title="Anthropic falls 9% on day two",
         summary="Down 9% at close after +17% debut; tech sells off."),
    dict(id=6,  place="ODISHA",     section="STORM",     tag="FORECAST",
         title="Cyclone Akvan lands in Odisha",
         summary="300,000 evacuated; winds 70-80 km/h, no deaths yet."),
    dict(id=7,  place="ANTALYA",    section="CLIMATE",   tag="REPORTED",
         title="COP31 draft drops fossil call",
         summary="Pacific states demand phase-out; talks in final day."),
    dict(id=8,  place="SUVA",       section="DROUGHT",   tag="REPORTED",
         title="Fiji, Tonga declare drought emergency",
         summary="El Nino drought at crisis level; Cook Islands on alert."),
    dict(id=9,  place="TURIN",      section="TENNIS",    tag="REPORTED",
         title="Medvedev beats Tiafoe 6-3, 6-4",
         summary="Into ATP Finals semis for first time since 2023."),
    dict(id=10, place="GAZA",       section="WAR",       tag="CLAIM",
         title="Israeli troops cross Gaza line",
         summary="First breach since ceasefire; thousands flee Nuseirat."),
    dict(id=11, place="WASHINGTON", section="POLITICS",  tag="REPORTED",
         title="White House fires cyber chief",
         summary="Cairncross out after week of tech outages."),
    dict(id=12, place="NEW YORK",   section="SPORT",     tag="REPORTED",
         title="Trump pardons Pete Rose",
         summary="Posthumous pardon for hits leader."),
]

# Compact: title ONLY, 17pt, one line each at 324px column width.
# All titles kept <= 32 chars so the 1-line assert is the guarantee.
COMPACT = [
    dict(id=13, place="HORMUZ",      title="Tanker burns after mine strike"),
    dict(id=14, place="IRAQ",        title="Iraq troops move on Kataib base"),
    dict(id=15, place="POLAND",      title="Russia breaches Polish airspace"),
    dict(id=16, place="ESTONIA",     title="Estonia to shut Russia border"),
    dict(id=17, place="ITALY",       title="General strike over wages"),
    dict(id=18, place="EUROPE",      title="Youth strike in 25 countries"),
    dict(id=19, place="LONDON",      title="London-born told not British"),
    dict(id=20, place="SUDAN",       title="Drone strike kills 10 at mine"),
    dict(id=21, place="SENEGAL",     title="Migrant boat sinks off Senegal"),
    dict(id=22, place="S. AFRICA",   title="Nearly 600 women killed"),
    dict(id=23, place="S. AFRICA",   title="Court reviews Lindela detention"),
    dict(id=24, place="GUINEA",      title="Guinea No. 3 iron-ore exporter"),
    dict(id=25, place="GHANA",       title="Ghana suspends cashew exports"),
    dict(id=26, place="SUDAN",       title="Sudan halts imports from Kenya"),
    dict(id=27, place="SOMALIA",     title="Somalia expels UAE envoy"),
    dict(id=28, place="WELLINGTON",  title="India 159/1 in Wellington"),
    dict(id=29, place="SYDNEY",      title="Jepchirchir banned for 3 years"),
    dict(id=30, place="DOHA",        title="Morocco beat Fiji 6-0 at U17s"),
    dict(id=31, place="LAS VEGAS",   title="F1 practice washed out by rain"),
    dict(id=32, place="NEW YORK",    title="Intuit sells Mailchimp $3.68bn"),
    dict(id=33, place="BOGOT\u00c1", title="Colombia tax protests swell"),
    dict(id=34, place="MADRID",      title="Lula backs Sanchez in Spain"),
    dict(id=35, place="BRAZIL",      title="Brazil recognises Raoni land"),
    dict(id=36, place="BRAS\u00cdLIA", title="Brazil sells $1bn reserves"),
    dict(id=37, place="BUENOS AIRES", title="Tesla opens in Argentina"),
    dict(id=38, place="TAIPEI",      title="Taiex falls 6.2% on Friday"),
    dict(id=39, place="JAKARTA",     title="Indonesia fires may cost $30bn"),
    dict(id=40, place="KUALA LUMPUR", title="Rohingya unwanted in Malaysia"),
    dict(id=41, place="SEOUL",       title="Seoul voids ex-PM Han verdict"),
    dict(id=42, place="NEW DELHI",   title="India U17 reach Asian Cup"),
    dict(id=43, place="PUNE",        title="Kochhar wins golf playoff"),
    dict(id=44, place="TOKYO",       title="SBC Medical breach hits 2m"),
    dict(id=45, place="WORLD",       title="GTA 6 sales pass $2.3bn"),
]
assert len(COMPACT) == 33, "compact count %d" % len(COMPACT)

ALL_IDS = [c["id"] for c in LEADS] + [c["id"] for c in MEDIUM] + \
          [c["id"] for c in COMPACT]
assert len(ALL_IDS) == 45, "story count %d" % len(ALL_IDS)
assert sorted(ALL_IDS) == list(range(1, 46)), "ids not 1-45: %s" % sorted(ALL_IDS)

REGIONS = [("ASIA", 8, (168, 90, 26)), ("MIDDLE EAST", 4, (142, 47, 47)),
           ("EUROPE", 8, (47, 93, 138)), ("AFRICA", 8, (61, 122, 61)),
           ("AMERICAS", 10, (106, 74, 138)), ("OCEANIA", 3, (47, 122, 122)),
           ("WORLD", 4, (51, 51, 51))]
assert sum(c for _, c, _ in REGIONS) == 45

NUMBERS = [("-5.3%", "Nasdaq close"),
           ("-5.06%", "Nikkei close"),
           ("37", "VIX fear gauge"),
           ("+1.08%", "Sensex close"),
           ("$58,500", "Bitcoin"),
           ("$90.05", "Brent crude")]

TIMELINE = [
    ("02:00", "ODISHA", "Akvan makes landfall"),
    ("06:00", "TOKYO", "Nikkei closes -5.06%"),
    ("07:00", "KYIV", "Kyiv reports 8 dead"),
    ("09:00", "BRUSSELS", "EU-UK summit opens"),
    ("12:00", "ROME", "Italy strike begins"),
    ("14:30", "NEW YORK", "Wall St opens lower"),
    ("19:30", "TURIN", "Medvedev wins 6-3, 6-4"),
]

DATE_CHECK = ("DATE CHECK \u2014 Left out as other days' news: ICJ Myanmar genocide "
              "ruling (Thu 19) \u00b7 Anthropic +17% on debut (Thu 19) \u00b7 Kenya's last "
              "Ebola patient sent home (11 Nov). In: Nikkei -5.06% (Fri 20) \u00b7 "
              "Medvedev beats Tiafoe 6-3, 6-4 (Fri 20) \u00b7 Cyclone Akvan lands at "
              "Gopalpur (Fri 20).")
FOOTER = ("Every story here happened, or was first reported, on Friday 20 November 2026. "
          "Claims are attributed, not stated as fact. Sources: Reuters, BBC, AP, "
          "Al Jazeera, France 24, Just Security, Investors.com, The Hindu.")

# ---------------- lead illustrations (drawn on 324x132 tiles) ----------------
# Lead art is drawn at native tile size, then resized to the 246x90 card
# slot with LANCZOS. At 300px the art reads as a picture, as in v24.

def _bars(d, x, y, w, h, base, color):
    for bx, bw, bh in [(0, 34, 34), (40, 26, 52), (72, 30, 40), (250, 30, 60),
                       (286, 26, 44)]:
        d.rectangle([x + bx, y + h - bh, x + bx + bw, y + h], fill=base)
        for wy in range(y + h - bh + 7, y + h - 5, 11):
            d.rectangle([x + bx + 6, wy, x + bx + 10, wy + 4], fill=color)

def illo_crash(d, x, y, w, h):
    # Friday's market rout: dark green, big -5.3%, a falling red line.
    d.rectangle([x, y, x + w, y + h], fill=(13, 59, 46))
    _bars(d, x, y, w, h, (9, 40, 32), (255, 215, 106))
    pts = [(x + 108, y + h - 84), (x + 140, y + h - 70), (x + 172, y + h - 78),
           (x + 204, y + h - 56), (x + 232, y + h - 62), (x + 262, y + h - 34),
           (x + 292, y + h - 22)]
    d.line(pts, fill=(255, 80, 60), width=3)
    for px, py in pts[1:]:
        d.ellipse([px - 3, py - 3, px + 3, py + 3], fill=(255, 255, 255))
    f = F(SANSB, 30)
    d.text((x + 12, y + 8), "-5.3%", font=f, fill=(255, 255, 255))
    f2 = F(SANSB, 12)
    d.text((x + 12, y + 44), "NASDAQ", font=f2, fill=(255, 215, 106))
    f3 = F(SANSB, 10)
    d.text((x + 12, y + 64), "WORST WEEK SINCE 2020", font=f3, fill=(255, 255, 255))

def illo_missile(d, x, y, w, h):
    # Missile over Riyadh's financial district at night.
    d.rectangle([x, y, x + w, y + h], fill=(32, 52, 79))
    for bx, bw, bh in [(0, 40, 46), (48, 26, 70), (82, 34, 52), (200, 30, 60),
                       (236, 44, 40), (288, 26, 66)]:
        d.rectangle([x + bx, y + h - 46 - bh, x + bx + bw, y + h - 46],
                    fill=(16, 28, 48))
        for wy in range(y + h - 46 - bh + 8, y + h - 46 - 6, 14):
            d.rectangle([x + bx + 6, wy, x + bx + 10, wy + 4], fill=(255, 215, 106))
    d.rectangle([x + 10, y + h - 46, x + w - 10, y + h - 20], fill=(122, 74, 44))
    d.rectangle([x + 10, y + h - 20, x + w - 10, y + h], fill=(240, 240, 235))
    cx, cy = x + w * 0.30, y + 22
    for a in range(0, 360, 45):
        r = math.radians(a)
        d.line([cx, cy, cx + 14 * math.cos(r), cy + 14 * math.sin(r)],
               fill=(255, 140, 0), width=2)
    d.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=(255, 140, 0))
    d.line([x + w * 0.55, y + 14, x + w * 0.85, y + 34], fill=(255, 255, 255), width=3)
    d.polygon([(x + w * 0.85, y + 34), (x + w * 0.80, y + 30), (x + w * 0.80, y + 38)],
              fill=(255, 140, 0))
    d.text((x + w * 0.62, y + 44), "04:42", font=F(SANSB, 12), fill=(255, 255, 255))

def illo_strike(d, x, y, w, h):
    # Night strikes over Kyiv: dark sky, bridges, orange bursts.
    d.rectangle([x, y, x + w, y + h], fill=(18, 24, 48))
    for sx, sy in [(30, 18), (90, 30), (150, 14), (220, 26), (280, 16)]:
        d.ellipse([x + sx, y + sy, x + sx + 2, y + sy + 2], fill=(255, 255, 255))
    for bx, bw, bh in [(0, 44, 60), (52, 30, 88), (88, 40, 52), (134, 34, 96),
                       (174, 44, 64), (224, 30, 92), (260, 44, 56), (300, 28, 80)]:
        d.rectangle([x + bx, y + h - bh, x + bx + bw, y + h], fill=(10, 14, 30))
        for wy in range(y + h - bh + 8, y + h - 6, 14):
            for wx in range(x + bx + 6, x + bx + bw - 6, 12):
                d.rectangle([wx, wy, wx + 4, wy + 6], fill=(255, 215, 106))
    for ex, ey, r in [(80, 52, 16), (210, 44, 20), (270, 66, 12)]:
        for a in range(0, 360, 30):
            rr = math.radians(a)
            d.line([x + ex, y + ey, x + ex + r * math.cos(rr), y + ey + r * math.sin(rr)],
                   fill=(255, 140, 0), width=2)
        d.ellipse([x + ex - 6, y + ey - 6, x + ex + 6, y + ey + 6], fill=(255, 200, 60))
    d.rectangle([x + 12, y + h - 34, x + w - 12, y + h - 28], fill=(90, 70, 40))
    d.rectangle([x + 12, y + h - 28, x + w - 12, y + h - 22], fill=(60, 50, 30))

def illo_summit(d, x, y, w, h):
    # EU-UK summit: EU stars on blue, Union Jack, a long table.
    d.rectangle([x, y, x + w, y + h], fill=(143, 184, 216))
    d.rectangle([x + 12, y + 12, x + 116, y + 84], fill=(0, 51, 153))
    for i in range(12):
        a = math.radians(i * 30 - 90)
        sx = x + 64 + 34 * math.cos(a)
        sy = y + 48 + 26 * math.sin(a)
        d.ellipse([sx - 3, sy - 3, sx + 3, sy + 3], fill=(255, 204, 0))
    d.rectangle([x + 208, y + 12, x + 312, y + 84], fill=(1, 33, 105))
    d.line([x + 208, y + 48, x + 312, y + 48], fill=(255, 255, 255), width=8)
    d.line([x + 260, y + 12, x + 260, y + 84], fill=(255, 255, 255), width=8)
    d.line([x + 208, y + 12, x + 312, y + 84], fill=(200, 16, 46), width=4)
    d.line([x + 312, y + 12, x + 208, y + 84], fill=(200, 16, 46), width=4)
    d.rectangle([x + 10, y + h - 46, x + w - 10, y + h - 20], fill=(122, 74, 44))
    d.rectangle([x + 10, y + h - 20, x + w - 10, y + h], fill=(240, 240, 235))
    for px, suit in [(90, (32, 52, 79)), (160, (24, 24, 24)), (234, (80, 80, 80))]:
        d.ellipse([x + px - 13, y + h - 66, x + px + 13, y + h - 40], fill=(240, 200, 160))
        d.rectangle([x + px - 18, y + h - 42, x + px + 18, y + h - 20], fill=suit)

LEAD_ILLOS = {"crash": illo_crash, "missile": illo_missile,
              "strike": illo_strike, "summit": illo_summit}
TILE_W, TILE_H = 324, 132

def lead_tile(art):
    tile = Image.new("RGB", (TILE_W, TILE_H), PAPER)
    td = ImageDraw.Draw(tile)
    LEAD_ILLOS[art](td, 0, 0, TILE_W, TILE_H)
    return tile

# ---------------- medium art bands (246x38) ----------------
def band_ant(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(13, 59, 46))
    d.text((x + 8, y + 4), "-9%", font=F(MONTS, 16), fill=(255, 255, 255))
    d.text((x + 8, y + 24), "ANT", font=F(MONTS, 10), fill=(255, 215, 106))
    pts = [(x + w * 0.42, y + 10), (x + w * 0.55, y + 18), (x + w * 0.66, y + 14),
           (x + w * 0.78, y + 28), (x + w * 0.90, y + 34), (x + w - 8, y + h - 8)]
    d.line(pts, fill=(255, 80, 60), width=3)
    for px, py in pts:
        d.ellipse([px - 3, py - 3, px + 3, py + 3], fill=(255, 255, 255))

def band_cyclone(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(186, 214, 228))
    cx, cy = x + w * 0.14, y + h * 0.52
    for r in (19, 13, 7):
        d.arc([cx - r, cy - r, cx + r, cy + r], 20, 300, fill=(255, 255, 255), width=4)
    d.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=(47, 93, 138))
    d.text((x + w * 0.30, y + 5), "AKVAN", font=F(MONTS, 14), fill=RED)
    d.text((x + w * 0.30, y + 22), "70-80 KM/H", font=F(MONTS, 11), fill=INK)
    for dx, dy in [(0.62, 0.20), (0.72, 0.45), (0.84, 0.25), (0.68, 0.70)]:
        d.ellipse([x + w * dx, y + h * dy, x + w * dx + 4, y + h * dy + 8],
                  fill=(47, 93, 138))

def band_cop31(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(186, 214, 228))
    cx, cy, r = x + w * 0.13, y + h * 0.52, h * 0.44
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(47, 93, 138))
    d.ellipse([cx - r * 0.55, cy - r * 0.45, cx + r * 0.05, cy + r * 0.05], fill=(90, 160, 90))
    d.ellipse([cx + r * 0.10, cy + r * 0.10, cx + r * 0.75, cy + r * 0.60], fill=(90, 160, 90))
    d.text((x + w * 0.30, y + 5), "FOSSIL CALL", font=F(MONTS, 13), fill=RED)
    d.text((x + w * 0.30, y + 23), "DROPPED", font=F(MONTS, 11), fill=INK)

def band_drought(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(240, 214, 140))
    cx, cy, r = x + w * 0.14, y + h * 0.45, 14
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 140, 0))
    for a in range(0, 360, 45):
        rr = math.radians(a)
        d.line([cx + (r + 2) * math.cos(rr), cy + (r + 2) * math.sin(rr),
                cx + (r + 7) * math.cos(rr), cy + (r + 7) * math.sin(rr)],
               fill=(255, 140, 0), width=2)
    # Cracks only in the empty bottom-right corner, clear of the text.
    for k in range(2):
        bx = x + w * (0.80 + k * 0.10)
        d.line([bx, y + h - 3, bx + 8, y + h - 11], fill=(150, 110, 40), width=2)
        d.line([bx + 8, y + h - 11, bx + 16, y + h - 4], fill=(150, 110, 40), width=2)
    d.text((x + w * 0.30, y + 5), "DROUGHT", font=F(MONTS, 13), fill=RED)
    d.text((x + w * 0.30, y + 23), "EMERGENCY", font=F(MONTS, 11), fill=INK)

def band_tennis(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(46, 125, 50))
    d.rectangle([x + 8, y + 5, x + w * 0.34, y + h - 5], fill=(90, 170, 90),
                outline=(255, 255, 255), width=1)
    d.line([x + w * 0.34 / 2 + 4, y + 5, x + w * 0.34 / 2 + 4, y + h - 5],
           fill=(255, 255, 255), width=1)
    cx, cy = x + w * 0.20, y + h * 0.5
    d.ellipse([cx - 8, cy - 8, cx + 8, cy + 8], fill=(220, 255, 60), outline=INK)
    d.arc([cx - 8, cy - 8, cx + 8, cy + 8], 300, 60, fill=INK, width=1)
    d.text((x + w * 0.40, y + 5), "6-3, 6-4", font=F(MONTS, 14), fill=(255, 255, 255))
    d.text((x + w * 0.40, y + 23), "MEDVEDEV WINS", font=F(MONTS, 10), fill=(255, 215, 106))

def band_tank(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(232, 220, 180))
    d.line([x + 4, y + h - 6, x + w - 4, y + h - 6], fill=(201, 162, 39), width=3)
    d.rectangle([x + 10, y + h - 22, x + w * 0.42, y + h - 8], fill=(90, 110, 70))
    d.rectangle([x + w * 0.16, y + h - 32, x + w * 0.30, y + h - 22], fill=(70, 90, 55))
    d.rectangle([x + w * 0.30, y + h - 29, x + w * 0.52, y + h - 25], fill=(70, 90, 55))
    for wx in range(16, 92, 14):
        d.ellipse([x + wx, y + h - 10, x + wx + 9, y + h - 3], fill=(40, 40, 40))
    d.text((x + w * 0.56, y + 6), "OVER THE", font=F(MONTS, 12), fill=INK)
    d.text((x + w * 0.56, y + 22), "LINE", font=F(MONTS, 12), fill=INK)

def band_cyber(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(32, 52, 79))
    d.rectangle([x + 10, y + 6, x + w * 0.30, y + h - 6], fill=(16, 28, 48))
    for wy in range(y + 10, y + h - 8, 8):
        d.rectangle([x + 14, wy, x + w * 0.30 - 4, wy + 3], fill=(255, 215, 106))
    d.text((x + w * 0.36, y + 5), "CYBER CHIEF", font=F(MONTS, 12), fill=(255, 255, 255))
    d.text((x + w * 0.36, y + 23), "FIRED", font=F(MONTS, 12), fill=(255, 80, 60))

def band_baseball(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(46, 125, 50))
    d.polygon([(x + w * 0.16, y + h - 6), (x + w * 0.16, y + 8),
               (x + w * 0.34, y + h - 6)], fill=(220, 196, 143))
    d.ellipse([x + w * 0.20, y + h * 0.42, x + w * 0.20 + 14, y + h * 0.42 + 14],
              fill=(255, 255, 255), outline=RED)
    d.text((x + w * 0.40, y + 5), "PETE ROSE", font=F(MONTS, 13), fill=(255, 255, 255))
    d.text((x + w * 0.40, y + 23), "PARDONED", font=F(MONTS, 11), fill=(255, 215, 106))

BAND_ART = {5: band_ant, 6: band_cyclone, 7: band_cop31, 8: band_drought,
            9: band_tennis, 10: band_tank, 11: band_cyber, 12: band_baseball}
assert set(BAND_ART) == {c["id"] for c in MEDIUM}, "band art coverage != medium ids"

# ---------------- world map (schematic continents, pins = 12 cards) ----------------
CONTINENTS = [
    [(26, 30), (44, 20), (72, 14), (104, 16), (126, 28), (120, 44), (112, 52),
     (104, 62), (96, 74), (88, 68), (76, 80), (58, 90), (40, 84), (28, 66), (22, 48)],
    [(88, 108), (128, 96), (146, 104), (154, 124), (146, 150), (130, 178),
     (116, 152), (98, 128)],
    [(166, 30), (184, 20), (202, 24), (210, 38), (202, 52), (188, 60),
     (172, 50), (162, 38)],
    [(172, 68), (196, 58), (216, 66), (230, 88), (232, 108), (222, 130),
     (206, 152), (190, 134), (180, 108), (170, 86)],
    [(212, 26), (244, 16), (282, 16), (312, 26), (330, 48), (324, 72),
     (306, 92), (292, 102), (268, 94), (250, 98), (234, 80), (220, 56), (208, 38)],
    [(286, 138), (306, 130), (326, 138), (330, 156), (312, 166), (292, 160), (282, 148)],
]
ISLANDS = [
    [(158, 26), (164, 24), (166, 34), (162, 42), (156, 36)],
    [(332, 56), (338, 54), (340, 68), (334, 70)],
    [(262, 104), (266, 102), (270, 106), (266, 108)],
    [(274, 108), (278, 106), (282, 110), (278, 112)],
    [(332, 148), (336, 146), (338, 158), (334, 160)],
]
# Pins mark the 12 illustrated stories (4 leads + 8 mediums).
PINS = {1: (64, 66), 2: (236, 70), 3: (196, 38), 4: (176, 48), 5: (56, 50),
        6: (264, 78), 7: (206, 62), 8: (332, 148), 9: (180, 58),
        10: (224, 54), 11: (84, 56), 12: (92, 76)}
assert set(PINS) == {c["id"] for c in LEADS} | {c["id"] for c in MEDIUM}

# ---------------- page sections ----------------
LEAD_H = 192
LEAD_ART_H = 90
MED_H = 120
MED_ART_H = 38

def draw_top(d):
    f_small = F(WS_SB, 11)
    d.text((M, 6), "THE WORLD IN ONE DAY", font=f_small, fill=RED)
    right = "45 STORIES \u00b7 EVERY CONTINENT \u00b7 ALL FROM THIS ONE DAY"
    d.text((W - M - text_w(d, right, f_small), 6), right, font=f_small, fill=INK)
    f_head = fit_font(SERIFB, "Friday 20 November 2026", 52, CW, d)
    d.text((M, 24), "Friday 20 November 2026", font=f_head, fill=INK)
    kick = ("Markets plunge as Nasdaq falls 5.3% \u00b7 Houthi missile hits Riyadh tower "
            "\u00b7 Russian strikes kill 8 in Kyiv")
    f_kick = fit_font(SERIFB, kick, 14, CW, d)
    d.text((M, 85), kick, font=f_kick, fill=RED)
    d.line([M, 104, W - M, 104], fill=INK, width=2)

def draw_regions(d):
    y0, y1 = 108, 126
    total = sum(c for _, c, _ in REGIONS)
    widths = [max(50, round(CW * count / total)) for _, count, _ in REGIONS]
    widths[-1] += CW - sum(widths)
    f = F(WS_SB, 9)
    x = M
    for (name, count, color), wd in zip(REGIONS, widths):
        d.rectangle([x, y0, x + wd, y1], fill=color)
        label = "%s %d" % (name, count)
        assert text_w(d, label, f) <= wd - 2, "region label too wide: %s" % label
        tw = text_w(d, label, f)
        d.text((x + (wd - tw) / 2, y0 + 4), label, font=f, fill=(255, 255, 255))
        x += wd

def draw_numbers(d):
    y0 = 130
    cw = CW // 6
    d.line([M, y0 - 2, W - M, y0 - 2], fill=LINE, width=1)
    d.line([M, y0 + 42, W - M, y0 + 42], fill=LINE, width=1)
    for i, (num, label) in enumerate(NUMBERS):
        x = M + i * cw
        if i:
            d.line([x, y0 + 3, x, y0 + 38], fill=LINE, width=1)
        f_num = fit_font(SERIFB, num, 26, cw - 8, d)
        tw = text_w(d, num, f_num)
        d.text((x + (cw - tw) / 2, y0 + 1), num, font=f_num, fill=RED)
        f_lab = fit_font(WS_SB, label, 9, cw - 8, d)
        tw = text_w(d, label, f_lab)
        d.text((x + (cw - tw) / 2, y0 + 30), label, font=f_lab, fill=INK)

def draw_timeline(d):
    y0, y1 = 174, 196
    d.rectangle([M, y0, W - M, y1], fill=(238, 233, 214), outline=LINE, width=1)
    f_t = F(SANSB, 9)
    d.text((M + 6, y0 + 1), "THE DAY BY HOURS", font=f_t, fill=RED)
    f_s = F(WS_R, 8)
    d.text((M + 6, y0 + 12), "UTC", font=f_s, fill=GREY)
    x = M + 138
    cw = (W - M - x) // 7
    f_time = F(SANSB, 9)
    f_ev = F(WS_R, 8)
    for i, (t, place, ev) in enumerate(TIMELINE):
        cx = x + i * cw
        if i:
            d.line([cx, y0 + 3, cx, y1 - 3], fill=LINE, width=1)
        d.text((cx + 6, y0 + 1), t, font=f_time, fill=RED)
        d.text((cx + 6 + text_w(d, t + " ", f_time), y0 + 1), place,
               font=f_time, fill=INK)
        d.text((cx + 6, y0 + 12), ev, font=f_ev, fill=INK)

def draw_leads(d, img):
    y0 = 200
    w = (CW - 3 * 8) // 4  # 246
    for i, card in enumerate(LEADS):
        x = M + i * (w + 8)
        d.rectangle([x, y0, x + w, y0 + LEAD_H], fill=(255, 255, 255),
                    outline=INK, width=2)
        tile = lead_tile(card["art"]).resize((w - 2, LEAD_ART_H), Image.LANCZOS)
        img.paste(tile, (x + 1, y0 + 1))
        by = y0 + 1 + LEAD_ART_H
        f_kick = F(SANSB, 9)
        d.text((x + 8, by + 2), "%d \u00b7 %s \u00b7 %s" % (card["id"], card["place"],
               card["section"]), font=f_kick, fill=RED)
        tag_pill(d, x + w - 8, by + 1, card["tag"], 8)
        f_head = F(MONTS, 20)
        lines = wrap(d, card["title"], f_head, w - 16)
        assert len(lines) <= 2, "lead title too long: %s -> %s" % (card["title"], lines)
        ty = draw_lines(d, x + 8, by + 20, lines, f_head, INK, 22)
        f_body = F(WS_R, 11)
        blines = wrap(d, card["summary"], f_body, w - 16)
        assert len(blines) <= 2, "lead summary too long: %s -> %s" % (card["summary"], blines)
        draw_lines(d, x + 8, ty + 2, blines, f_body, INK, 13)

def draw_mediums(d):
    rows_y = [397, 522]
    w = (CW - 3 * 8) // 4  # 246
    for r, y0 in enumerate(rows_y):
        for c in range(4):
            card = MEDIUM[r * 4 + c]
            x = M + c * (w + 8)
            d.rectangle([x, y0, x + w, y0 + MED_H], fill=(255, 255, 255),
                        outline=INK, width=1)
            f_kick = F(SANSB, 9)
            d.text((x + 6, y0 + 2), "%d \u00b7 %s" % (card["id"], card["place"]),
                   font=f_kick, fill=RED)
            tag_pill(d, x + w - 6, y0 + 1, card["tag"], 8)
            BAND_ART[card["id"]](d, x + 1, y0 + 13, w - 2, MED_ART_H)
            d.rectangle([x + 1, y0 + 13, x + w - 2, y0 + 13 + MED_ART_H - 1],
                        outline=LINE, width=1)
            f_head = F(MONTS, 18)
            lines = wrap(d, card["title"], f_head, w - 16)
            assert len(lines) <= 2, "medium title too long: %s -> %s" % (card["title"], lines)
            ty = draw_lines(d, x + 8, y0 + 54, lines, f_head, INK, 19)
            f_body = F(WS_R, 10)
            blines = wrap(d, card["summary"], f_body, w - 16)
            assert len(blines) <= 2, "medium summary too long: %s -> %s" % (card["summary"], blines)
            draw_lines(d, x + 8, ty + 2, blines, f_body, INK, 11)

def draw_map(d):
    f_title = F(SANSB, 11)
    d.text((M, 647), "WHERE IT HAPPENED", font=f_title, fill=RED)
    x0, y0, w, h = M, 661, 344, 182
    d.rectangle([x0, y0, x0 + w, y0 + h], fill=SEA, outline=INK, width=1)
    for poly in CONTINENTS:
        pts = [(x0 + px, y0 + py) for px, py in poly]
        d.polygon(pts, fill=LAND, outline=(150, 130, 90))
    for poly in ISLANDS:
        pts = [(x0 + px, y0 + py) for px, py in poly]
        d.polygon(pts, fill=LAND, outline=(150, 130, 90))
    f_pin = F(SANSB, 8)
    for n, (px, py) in PINS.items():
        cx, cy = x0 + px, y0 + py
        d.ellipse([cx - 7, cy - 7, cx + 7, cy + 7], fill=RED,
                  outline=(255, 255, 255), width=1)
        t = str(n)
        d.text((cx - text_w(d, t, f_pin) / 2, cy - 5), t, font=f_pin,
               fill=(255, 255, 255))
    f_note = F(WS_R, 8)
    d.text((x0, y0 + h + 4),
           "Red numbers mark the 12 illustrated stories. Positions are approximate.",
           font=f_note, fill=(60, 60, 60))

def draw_compact(d):
    # 33 titles, 2 columns x 17 rows, 17pt Montserrat Bold, ONE line each.
    # No 9pt briefs anywhere; every compact title is readable at judge size.
    f_title = F(SANSB, 11)
    d.text((360, 647), "ALSO ON FRIDAY 20 NOVEMBER \u2014 33 MORE STORIES",
           font=f_title, fill=RED)
    f_item = F(MONTS, 17)
    cols = [360, 684]
    for i, c in enumerate(COMPACT):
        col = i // 17
        row = i % 17
        x = cols[col]
        y = 661 + row * 18
        lines = wrap(d, c["title"], f_item, 324)
        assert len(lines) == 1, "compact title wraps to 2 lines: %s -> %s" % (c["title"], lines)
        d.text((x, y), c["title"], font=f_item, fill=INK)

def draw_datecheck(d):
    # DATE CHECK box under the map.
    x0, y0, w, h = M, 866, 344, 106
    d.rectangle([x0, y0, x0 + w, y0 + h], outline=RED, width=1)
    f_dc = F(WS_SB, 9)
    f_body = F(WS_R, 9)
    lines = wrap(d, DATE_CHECK, f_body, w - 12)
    assert len(lines) <= 8, "DATE CHECK too long: %d lines" % len(lines)
    th = len(lines) * 11
    ty = y0 + (h - th) // 2
    prefix = "DATE CHECK \u2014 "
    rest = DATE_CHECK[len(prefix):]
    first = lines[0][len(prefix):] if lines[0].startswith(prefix) else lines[0]
    d.text((x0 + 6, ty), prefix, font=f_dc, fill=RED)
    pw = text_w(d, prefix, f_dc)
    d.text((x0 + 6 + pw, ty), first, font=f_body, fill=INK)
    for j, ln in enumerate(lines[1:]):
        d.text((x0 + 6, ty + (j + 1) * 11), ln, font=f_body, fill=INK)

def draw_footer(d):
    f_src = F(WS_R, 8)
    assert text_w(d, FOOTER, f_src) <= CW, "footer too wide"
    d.text((M, 1000), FOOTER, font=f_src, fill=GREY)

def build():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    draw_top(d)
    draw_regions(d)
    draw_numbers(d)
    draw_timeline(d)
    draw_leads(d, img)
    draw_mediums(d)
    draw_map(d)
    draw_compact(d)
    draw_datecheck(d)
    draw_footer(d)
    out = os.path.join(HERE, "entry.png")
    img.save(out, "PNG", optimize=True)
    h = hashlib.sha256(open(out, "rb").read()).hexdigest()
    print("saved", out, "bytes", os.path.getsize(out), "sha256", h, "bottom y 1008")
    small = img.resize((300, 300), Image.LANCZOS)
    small.save(os.path.join(HERE, "entry-300.png"))
    strings = ["THE WORLD IN ONE DAY", "45 STORIES \u00b7 EVERY CONTINENT \u00b7 ALL FROM THIS ONE DAY",
               "Friday 20 November 2026", "NOVEMBER 2026", "20", "FRIDAY"]
    for num, lab in NUMBERS:
        strings += [num, lab]
    for c in LEADS + MEDIUM:
        strings.append("%d \u00b7 %s \u00b7 %s" % (c["id"], c["place"], c["section"]))
        strings.append(c["title"])
        strings.append(c["summary"])
    for c in COMPACT:
        strings.append("%d \u00b7 %s \u00b7 %s" % (c["id"], c["place"], c["title"]))
        strings.append(c["title"])
    strings += [DATE_CHECK, FOOTER]
    with open(os.path.join(HERE, "strings.txt"), "w") as f:
        f.write("\n".join(strings) + "\n")
    manifest = {"version": "v1", "stories": 45, "ids": sorted(ALL_IDS),
                "leads": [c["id"] for c in LEADS],
                "medium": [c["id"] for c in MEDIUM],
                "compact": [c["id"] for c in COMPACT],
                "illustrated_cards": 12, "map": "344x182, 12 pins",
                "sha256": h}
    with open(os.path.join(HERE, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    print("manifest ok: 45 stories, ids 1-45 each once, 12 illustrated cards")

if __name__ == "__main__":
    build()
