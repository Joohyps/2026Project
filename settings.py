"""
전역변수:
- WIDTH, HEIGHT : 화면 크기
- FPS           : 목표 프레임
- CX1~CY2       : 경기장 영역
- MID_X         : 경기장 중앙선
- PLAYER_SPD    : 플레이어 이동 속도
- THROW_SPD     : 공 투척 속도
- THROW_VZ      : 공 투척 수직 속도
- GRAVITY       : 중력 가속도
- BOUNCE_K      : 공 반발 계수
- ROLL_DAMP     : 공 구름 감쇠 계수
- MAX_SPIN      : 최대 스핀량
- SPIN_K        : 스핀 계수
- ARM_TIME      : 폭탄 폭발 대기 시간
- EXPLOSION_RADIUS : 폭발 반경
- GAME_SECS     : 경기 시간
- PICKUP_R      : 공 줍기 범위
- P_RADIUS      : 플레이어 반지름
- B_RADIUS      : 공 반지름
- HIT_Z_MAX     : 피격 가능한 최대 높이
- P1_START      : 플레이어 1 시작 위치
- P2_START      : 플레이어 2 시작 위치
- C_뭐시기           : 게임 색상 상수

메서드:
- w2s(gx, gy)                    : 월드 좌표를 화면 좌표로 변환
- persp_r(gy, base)              : 원근감을 고려한 반지름 계산
- persp_z_scale(gy)              : 높이(z) 표시 스케일 계산
- court_x_limits(gy, r_base)     : 해당 y 위치에서 이동 가능한 x 범위 계산
"""

WIDTH, HEIGHT = 1280, 720
FPS = 60

CX1, CY1 = 130,  90
CX2, CY2 = 1150, 645
CW  = CX2 - CX1
CH  = CY2 - CY1
MID_X = (CX1 + CX2) // 2

FENCE_D = 30

GRAVITY     = 920.0
PLAYER_SPD  = 220.0
THROW_SPD   = 850.0
THROW_VZ    = 310.0
BOUNCE_K    = 0.28
ROLL_DAMP   = 3.5
MAX_SPIN = 100.0
SPIN_K = 0.01

_SAFE_SPEED = 100.0

BOMB_RESPAWN = 3.0

ARM_TIME = 2.0          # 폭발까지 시간
EXPLOSION_RADIUS = 120
FLASH_PERIOD = 0.15

GAME_SECS  = 120
N_BALLS    = 4
KNOCK_DUR  = 1.8
PICKUP_R   = 38
P_RADIUS   = 20
B_RADIUS   = 7
HIT_Z_MAX  = 65

P1_START = (CX1 + CW // 4,     CY1 + CH // 2)
P2_START = (CX1 + 3 * CW // 4, CY1 + CH // 2)

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
C_BOMB = (0, 0, 0)
C_BOMBD = (10, 10, 10)

C_GOLD   = (255, 208, 22)
C_GOLD2  = (255, 168,  0)
C_CYAN   = (78,  222, 222)
C_WHITE  = (255, 255, 255)
C_SHADOW = (14,  44,  13)

C_SCORE1 = (95,  160, 242)
C_SCORE2 = (242, 78,  78)
C_TIMER  = (228, 228, 228)

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


def court_x_limits(gy: float, r_base: float) -> tuple:
    """원근 사다리꼴 기준 x 이동 범위 반환."""
    t  = (gy - CY1) / CH
    hw = _PNEAR * 0.5 * (_PFAR + (1.0 - _PFAR) * t)
    r_screen = persp_r(gy, r_base)
    margin = r_screen * (CW * 0.5) / hw
    return CX1 + margin, CX2 - margin
