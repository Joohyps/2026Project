"""
Battle Ball — 1v1  |  settings.py
모든 상수 + 원근 투영 함수 정의
"""

# ── Screen ────────────────────────────────────────────────────────────────────
WIDTH, HEIGHT = 1280, 720
FPS = 60

# ── Court (게임 로직용 평면 좌표) ─────────────────────────────────────────────
CX1, CY1 = 130,  90
CX2, CY2 = 1150, 645
CW  = CX2 - CX1
CH  = CY2 - CY1
MID_X = (CX1 + CX2) // 2

FENCE_D = 30

# ── Physics ───────────────────────────────────────────────────────────────────
GRAVITY     = 920.0
PLAYER_SPD  = 220.0
THROW_SPD   = 850.0
THROW_VZ    = 310.0
BOUNCE_K    = 0.28
ROLL_DAMP   = 3.5

# ── Game rules ────────────────────────────────────────────────────────────────
GAME_SECS  = 120
N_BALLS    = 4
KNOCK_DUR  = 1.8
PICKUP_R   = 38
P_RADIUS   = 15
B_RADIUS   = 10
HIT_Z_MAX  = 65

P1_START = (CX1 + CW // 4,     CY1 + CH // 2)
P2_START = (CX1 + 3 * CW // 4, CY1 + CH // 2)

# ── Colours ───────────────────────────────────────────────────────────────────
C_BG      = (16, 36, 14)
C_GRASS   = (44, 96, 42)
C_GRASS2  = (40, 88, 38)
C_FENCE   = (78, 50, 20)
C_FENCE_F = (104, 68, 32)
C_FENCE_T = (55, 32, 8)

C_P1  = (92,  158, 238)
C_P1D = (52,  108, 178)
C_P2  = (238, 78,  78)
C_P2D = (178, 38,  38)

C_BALL  = (218, 54,  54)
C_BALLD = (148, 18,  18)

C_GOLD   = (255, 208, 22)
C_GOLD2  = (255, 168,  0)
C_CYAN   = (78,  222, 222)
C_WHITE  = (255, 255, 255)
C_SHADOW = (14,  44,  13)

C_SCORE1 = (95,  160, 242)
C_SCORE2 = (242, 78,  78)
C_TIMER  = (228, 228, 228)

# ── Perspective projection ────────────────────────────────────────────────────
_PCX    = 640
_PHY    = 118
_PVH    = 520
_PNEAR  = 1100
_PFAR   = 0.68


def w2s(gx: float, gy: float) -> tuple:
    t   = (gy - CY1) / CH
    hw  = _PNEAR * 0.5 * (_PFAR + (1.0 - _PFAR) * t)
    sx  = int(_PCX + (gx - MID_X) * hw / (CW * 0.5))
    sy  = int(_PHY + t * _PVH)
    return sx, sy


def persp_r(gy: float, base: float) -> int:
    t = (gy - CY1) / CH
    return max(2, int(base * (0.66 + 0.34 * t)))


def persp_z_scale(gy: float) -> float:
    t = (gy - CY1) / CH
    return 0.60 + 0.40 * t