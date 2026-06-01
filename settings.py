"""
Battle Ball — 1v1  |  settings.py
모든 상수 정의
"""

# ── Screen ───────────────────────────────────────────────────────────────────
WIDTH, HEIGHT = 1280, 720
FPS = 60

# ── Court (inner play-field bounds) ──────────────────────────────────────────
CX1, CY1 = 130,  90     # top-left corner
CX2, CY2 = 1150, 645    # bottom-right corner
CW  = CX2 - CX1         # 1020
CH  = CY2 - CY1         # 555
MID_X = (CX1 + CX2) // 2

WALL_V = 22             # visual wall thickness (px)

# ── Physics ──────────────────────────────────────────────────────────────────
GRAVITY     = 920.0     # px / s²  (z-axis gravity)
PLAYER_SPD  = 220.0     # px / s
THROW_SPD   = 1000.0     # px / s   (horizontal)
THROW_VZ    = 210.0     # px / s   (initial upward velocity)
BOUNCE_K    = 0.28      # velocity kept after first bounce
ROLL_DAMP   = 3.5       # rolling friction coefficient

# ── Game rules ───────────────────────────────────────────────────────────────
GAME_SECS  = 120        # match duration (seconds)
N_BALLS    = 4          # balls on court
KNOCK_DUR  = 1.8        # seconds player stays knocked down
PICKUP_R   = 38         # auto-pickup radius (px)
P_RADIUS   = 15         # player collision radius
B_RADIUS   = 10         # ball collision radius
HIT_Z_MAX  = 65         # ball's z must be below this to register a hit

# Spawn positions (game world coordinates)
P1_START = (CX1 + CW // 4,     CY1 + CH // 2)   # left-centre
P2_START = (CX1 + 3 * CW // 4, CY1 + CH // 2)   # right-centre

# ── Colours ──────────────────────────────────────────────────────────────────
C_BG      = (20,  42,  18)   # outer background
C_GRASS   = (44,  96,  42)   # even stripes
C_GRASS2  = (40,  88,  38)   # odd  stripes
C_FENCE   = (82,  52,  22)
C_FENCE_F = (106, 70,  34)   # front-face (lighter)
C_FENCE_T = (58,  34,  10)   # top-face   (darker)

C_P1  = (92,  158, 238)      # player-1 blue
C_P1D = (52,  108, 178)
C_P2  = (238, 78,  78)       # player-2 red
C_P2D = (178, 38,  38)

C_BALL  = (218, 54,  54)
C_BALLD = (148, 18,  18)

C_GOLD   = (255, 208,  22)   # centre-line gold
C_GOLD2  = (255, 168,   0)
C_CYAN   = (78,  222, 222)   # holding-ring cyan
C_WHITE  = (255, 255, 255)
C_SHADOW = (18,  50,   17)   # ground-shadow colour (dark grass)

C_SCORE1 = (95,  160, 242)
C_SCORE2 = (242,  78,  78)
C_TIMER  = (228, 228, 228)
