"""
Battle Ball — 1v1  |  player.py
플레이어 클래스 dmdddall— 상태머신, 애니메이션, 공 소지 링
"""
import math
import pygame
from settings import (
    CX1, CX2, CY1, CY2, MID_X,
    P_RADIUS, B_RADIUS, PLAYER_SPD, THROW_VZ, KNOCK_DUR,
    C_CYAN, C_WHITE, C_GOLD, C_SHADOW,
)

# Player states
ALIVE   = "alive"
KNOCKED = "knocked"
BLINK   = "blink"     # respawn 직후 무적 점멸


class Player:
    """
    pid=1 → 좌반 (WASD + Space)
    pid=2 → 우반 (IJKL + U)
    """

    def __init__(self, pid: int, x: float, y: float,
                 keys: dict, color: tuple, color_dark: tuple):
        self.pid      = pid
        self.x        = float(x)
        self.y        = float(y)
        self._sx      = float(x)   # spawn x
        self._sy      = float(y)   # spawn y

        self.state    = ALIVE
        self._knock_t = 0.0
        self._blink_t = 0.0
        self._bvis    = True       # blink visible?

        self.score    = 0
        self.color    = color
        self.cdark    = color_dark
        self.keys     = keys       # {'u','d','l','r'}

        self.held     = None       # Ball or None
        self.facing   = (1.0 if pid == 1 else -1.0, 0.0)

        self._ring_a  = 0.0        # cyan ring rotation angle
        self._flash   = 0.0        # hit-flash timer

    # ── Update ───────────────────────────────────────────────────────────────

    def update(self, dt: float, pressed):
        self._ring_a += dt * 3.2
        if self._flash > 0:
            self._flash = max(0.0, self._flash - dt)

        # ── Knocked down ──
        if self.state == KNOCKED:
            self._knock_t -= dt
            if self._knock_t <= 0:
                self._do_respawn()
            return   # 이동 불가

        # ── Blinking (respawn 무적) ──
        if self.state == BLINK:
            self._blink_t -= dt
            self._bvis = int(self._blink_t * 9) % 2 == 0
            if self._blink_t <= 0:
                self.state = ALIVE
                self._bvis = True
            # 점멸 중에도 이동은 가능

        # ── Movement ──
        dx = dy = 0.0
        if pressed[self.keys['u']]: dy -= 1
        if pressed[self.keys['d']]: dy += 1
        if pressed[self.keys['l']]: dx -= 1
        if pressed[self.keys['r']]: dx += 1

        spd = math.hypot(dx, dy)
        if spd > 0:
            dx /= spd
            dy /= spd
            self.facing = (dx, dy)

        self.x += dx * PLAYER_SPD * dt
        self.y += dy * PLAYER_SPD * dt

        # 코트 경계
        self.x = max(CX1 + P_RADIUS, min(CX2 - P_RADIUS, self.x))
        self.y = max(CY1 + P_RADIUS, min(CY2 - P_RADIUS, self.y))

        # 중앙선 제한
        if self.pid == 1:
            self.x = min(self.x, MID_X - P_RADIUS - 2)
        else:
            self.x = max(self.x, MID_X + P_RADIUS + 2)

        # 소지한 공은 플레이어 앞쪽에 따라움
        if self.held:
            ox = self.facing[0] * (P_RADIUS + B_RADIUS)
            oy = self.facing[1] * (P_RADIUS + B_RADIUS)
            self.held.x = self.x + ox
            self.held.y = self.y + oy

    # ── Actions ──────────────────────────────────────────────────────────────

    def try_throw(self) -> bool:
        """공 던지기. 성공 시 True 반환."""
        if self.held is None or self.state == KNOCKED:
            return False

        ball = self.held
        fx, fy = self.facing

        ball.thrown_by = self
        ball.x = self.x + fx * (P_RADIUS + B_RADIUS + 6)
        ball.y = self.y + fy * (P_RADIUS + B_RADIUS + 6)
        ball.throw(fx, fy)
        self.held = None
        return True

    def get_hit(self):
        """공에 맞았을 때 호출."""
        if self.state != ALIVE:
            return
        if self.held:
            self.held.state     = "loose"
            self.held.vx        = 0.0
            self.held.vy        = 0.0
            self.held.vz        = 110.0
            self.held.thrown_by = None
            self.held           = None

        self.state    = KNOCKED
        self._knock_t = KNOCK_DUR
        self._flash   = 0.3

    # ── Private ──────────────────────────────────────────────────────────────

    def _do_respawn(self):
        self.x        = self._sx
        self.y        = self._sy
        self.state    = BLINK
        self._blink_t = 1.3
        self._bvis    = True

    # ── Draw ─────────────────────────────────────────────────────────────────

    def draw_shadow(self, screen):
        """지면 그림자."""
        if not self._bvis:
            return
        sx, sy = int(self.x), int(self.y)
        pygame.draw.ellipse(screen, C_SHADOW,
                            (sx - P_RADIUS + 2, sy + P_RADIUS - 5,
                             P_RADIUS * 2 - 3, max(4, P_RADIUS - 6)))

    def draw(self, screen):
        if not self._bvis:
            return
        sx, sy = int(self.x), int(self.y)

        # ── 넘어진 상태 ──────────────────────────
        if self.state == KNOCKED:
            pygame.draw.ellipse(screen, self.cdark,
                                (sx - P_RADIUS * 2 + 1, sy - P_RADIUS // 2 + 1,
                                 P_RADIUS * 4, P_RADIUS + 2))
            pygame.draw.ellipse(screen, self.color,
                                (sx - P_RADIUS * 2,     sy - P_RADIUS // 2,
                                 P_RADIUS * 4, P_RADIUS))
            # 별 이펙트
            for i in range(3):
                a  = self._ring_a * 2.5 + i * math.tau / 3
                rx = sx + int(math.cos(a) * (P_RADIUS + 8))
                ry = sy - P_RADIUS // 2 + int(math.sin(a) * 5)
                pygame.draw.circle(screen, C_GOLD, (rx, ry), 3)
            return

        # ── 공 소지 청록 링 ───────────────────────
        if self.held:
            for i in range(10):
                a  = self._ring_a + i * math.tau / 10
                rx = sx + int(math.cos(a) * (P_RADIUS + 9))
                ry = sy + int(math.sin(a) * (P_RADIUS + 9))
                t  = abs(math.sin(a + self._ring_a)) ** 2
                rc = tuple(int(c * (0.3 + 0.7 * t)) for c in C_CYAN)
                pygame.draw.circle(screen, rc, (rx, ry), 3)

        # ── 플레이어 몸체 ─────────────────────────
        c = C_WHITE if (self._flash > 0 and int(self._flash * 22) % 2) else self.color

        pygame.draw.circle(screen, self.cdark, (sx, sy + 2), P_RADIUS)  # 깊이감
        pygame.draw.circle(screen, c,          (sx, sy),     P_RADIUS)

        # 하이라이트
        hl_r = max(3, P_RADIUS // 3)
        hl_c = tuple(min(255, v + 60) for v in c)
        pygame.draw.circle(screen, hl_c, (sx - hl_r, sy - hl_r), hl_r)

        # 방향 점 (facing indicator)
        nx = sx + int(self.facing[0] * (P_RADIUS - 5))
        ny = sy + int(self.facing[1] * (P_RADIUS - 5))
        pygame.draw.circle(screen, C_WHITE, (nx, ny), 3)
