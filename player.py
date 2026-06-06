"""
Battle Ball — 1v1  |  player.py
플레이어: 사다리꼴 경계 / 사람 형태 /
          걷기 애니메이션 / 공 소지 → 손에 들기 / 3단계 던지기 모션
"""

import math
import pygame
from settings import (
    CX1, CX2, CY1, CY2, MID_X,
    P_RADIUS, B_RADIUS, PLAYER_SPD, KNOCK_DUR,
    C_CYAN, C_WHITE, C_GOLD, C_SHADOW, C_BALL, C_BALLD,
    w2s, persp_r, court_x_limits,
)

ALIVE   = "alive"
KNOCKED = "knocked"
BLINK   = "blink"

THROW_DUR = 0.34


class Player:
    def __init__(self, pid: int, x: float, y: float,
                 keys: dict, color: tuple, color_dark: tuple):
        self.pid    = pid
        self.x      = float(x);  self.y  = float(y)
        self._sx    = float(x);  self._sy = float(y)

        self.state  = ALIVE
        self._kt    = 0.0;  self._bt = 0.0;  self._bvis = True

        self.score  = 0
        self.color  = color;  self.cdark = color_dark
        self.keys   = keys

        self.held   = None
        self.facing = (1.0 if pid == 1 else -1.0, 0.0)

        self._ring_a    = 0.0
        self._flash     = 0.0
        self._walk_t    = 0.0
        self._is_moving = False
        self._throw_t   = 0.0

    # ── Update ───────────────────────────────────────────────────────────────

    def update(self, dt: float, pressed):
        self._ring_a += dt * 3.2
        if self._flash   > 0: self._flash   = max(0.0, self._flash   - dt)
        if self._throw_t > 0: self._throw_t = max(0.0, self._throw_t - dt)

        if self.state == KNOCKED:
            self._kt -= dt
            if self._kt <= 0: self._respawn()
            return

        if self.state == BLINK:
            self._bt -= dt
            self._bvis = int(self._bt * 9) % 2 == 0
            if self._bt <= 0:
                self.state = ALIVE
                self._bvis = True

        dx = dy = 0.0
        if pressed[self.keys['u']]: dy -= 1
        if pressed[self.keys['d']]: dy += 1
        if pressed[self.keys['l']]: dx -= 1
        if pressed[self.keys['r']]: dx += 1
        sp = math.hypot(dx, dy)
        if sp > 0:
            dx /= sp; dy /= sp
            self.facing     = (dx, dy)
            self._walk_t   += dt
            self._is_moving = True
        else:
            self._is_moving = False

        self.x += dx * PLAYER_SPD * dt
        self.y += dy * PLAYER_SPD * dt

        # 원근 사다리꼴 경계
        x_min, x_max = court_x_limits(self.y, P_RADIUS)
        self.x = max(x_min, min(x_max, self.x))
        self.y = max(CY1 + P_RADIUS, min(CY2 - P_RADIUS, self.y))

        # 중앙선 제한
        if self.pid == 1: self.x = min(self.x, MID_X - P_RADIUS - 2)
        else:             self.x = max(self.x, MID_X + P_RADIUS + 2)

        if self.held:
            self.held.x = self.x
            self.held.y = self.y

    # ── Actions ──────────────────────────────────────────────────────────────

    def try_throw(self) -> bool:
        if not self.held or self.state == KNOCKED:
            return False
        ball = self.held
        fx, fy = self.facing
        ball.thrown_by = self
        ball.x = self.x + fx * (P_RADIUS + B_RADIUS + 6)
        ball.y = self.y + fy * (P_RADIUS + B_RADIUS + 6)
        ball.throw(fx, fy)
        self.held     = None
        self._throw_t = THROW_DUR
        return True

    def get_hit(self):
        if self.state != ALIVE: return
        if self.held:
            self.held.state     = "loose"
            self.held.vx        = 0.0
            self.held.vy        = 0.0
            self.held.vz        = 110.0
            self.held.thrown_by = None
            self.held           = None
        self.state = KNOCKED;  self._kt = KNOCK_DUR;  self._flash = 0.3

    def _respawn(self):
        self.x = self._sx;  self.y = self._sy
        self.state = BLINK;  self._bt = 1.3;  self._bvis = True

    @property
    def _throw_side(self) -> int:
        if self.facing[0] > 0.1:  return  1
        if self.facing[0] < -0.1: return -1
        return 1 if self.pid == 1 else -1

    # ── Draw ─────────────────────────────────────────────────────────────────

    def draw_shadow(self, screen):
        if not self._bvis: return
        sx, sy = w2s(self.x, self.y)
        r = persp_r(self.y, P_RADIUS)
        pygame.draw.ellipse(screen, C_SHADOW,
                            (sx - r, sy + int(r * 0.22),
                             r * 2, max(3, int(r * 0.40))))

    def draw(self, screen):
        if not self._bvis: return
        sx, sy = w2s(self.x, self.y)
        r  = persp_r(self.y, P_RADIUS)
        fx, fy = self.facing

        # ── 넘어짐 ──────────────────────────────────
        if self.state == KNOCKED:
            pygame.draw.ellipse(screen, self.cdark,
                                (sx - r*2+1, sy - r//2+1, r*4, r+2))
            pygame.draw.ellipse(screen, self.color,
                                (sx - r*2,   sy - r//2,   r*4, r))
            for i in range(3):
                a  = self._ring_a * 2.5 + i * math.tau / 3
                rx = sx + int(math.cos(a) * (r + 10))
                ry = sy - r//2 + int(math.sin(a) * 6)
                pygame.draw.circle(screen, C_GOLD, (rx, ry), max(2, r // 4))
            return

        c = C_WHITE if (self._flash > 0 and int(self._flash * 22) % 2) else self.color

        # ── 비율 계산 ─────────────────────────────────
        head_r  = max(4, int(r * 0.48))
        body_w  = max(3, int(r * 0.37))
        body_h  = max(4, int(r * 0.58))
        leg_len = max(5, int(r * 0.82))
        leg_spr = max(2, int(r * 0.30))
        arm_len = max(4, int(r * 0.60))
        arm_spr = max(2, int(r * 0.28))
        lw      = max(1, int(r * 0.18))

        # Y 위치
        hip_y   = sy + int(r * 0.20)
        chest_y = hip_y  - body_h * 2
        sh_y    = chest_y + int(body_h * 0.28)
        head_cy = chest_y - head_r - max(1, int(r * 0.08))

        # 걷기 스윙
        ws = math.sin(self._walk_t * 8.5) * (1.0 if self._is_moving else 0.0)

        ts       = self._throw_side
        throw_ax = sx + ts * body_w
        throw_ay = sh_y

        # ── 다리 ─────────────────────────────────────
        for side in (-1, 1):
            s      = ws * side
            foot_x = sx + int(s * leg_spr)
            foot_y = hip_y + leg_len - int(abs(s) * leg_len * 0.10)
            pygame.draw.line(screen, self.cdark, (sx, hip_y), (foot_x, foot_y), lw + 1)
            pygame.draw.line(screen, c,          (sx, hip_y), (foot_x, foot_y), lw)
            pygame.draw.circle(screen, c, (foot_x, foot_y), max(1, lw))

        # ── 몸통 ─────────────────────────────────────
        pygame.draw.ellipse(screen, self.cdark,
                            (sx - body_w, chest_y - 1, body_w*2, body_h*2 + 2))
        pygame.draw.ellipse(screen, c,
                            (sx - body_w, chest_y,     body_w*2, body_h*2))

        # ── 비 던지는 팔 ──────────────────────────────
        other_side = -ts
        oth_ax = sx + other_side * body_w
        oth_ex = oth_ax + int(other_side * arm_spr)
        oth_ey = sh_y + arm_len - int(-ws * other_side * arm_len * 0.45)
        pygame.draw.line(screen, self.cdark, (oth_ax, sh_y), (oth_ex, oth_ey), lw+1)
        pygame.draw.line(screen, c,          (oth_ax, sh_y), (oth_ex, oth_ey), lw)
        pygame.draw.circle(screen, c, (oth_ex, oth_ey), max(1, lw))

        # ── 던지는 팔 위치 계산 ───────────────────────
        if self._throw_t > 0:
            prog = 1.0 - self._throw_t / THROW_DUR

            if prog < 0.35:
                # 1단계: 와인드업 — 뒤로 당기고 위로
                t    = prog / 0.35
                ease = t * t
                tex  = throw_ax - int(fx * arm_len * 1.0 * ease)
                tey  = throw_ay - int(r  * 0.65 * ease)

            elif prog < 0.72:
                # 2단계: 릴리즈 — 앞으로 힘차게
                t    = (prog - 0.35) / 0.37
                ease = 1.0 - (1.0 - t) ** 3
                tex  = throw_ax - int(fx * arm_len * (1.0 - ease)) \
                                + int(fx * arm_len * 1.3 * ease)
                tey  = throw_ay - int(r * 0.65 * (1.0 - ease)) \
                                + int(r * 0.18 * ease)

            else:
                # 3단계: 팔로우스루 — 자연스럽게 복귀
                t   = (prog - 0.72) / 0.28
                tex = throw_ax + int(fx * arm_len * (1.3 - t * 0.6))
                tey = throw_ay + int(r  * 0.18 * (1.0 - t))

        elif self.held:
            # 공 소지: 팔 앞으로 뻗어 손에 들기
            tex = throw_ax + int(fx * arm_len * 0.88) + int(ts * arm_spr * 0.25)
            tey = throw_ay + int(fy * arm_len * 0.40)

        else:
            # 일반 걷기 스윙
            tex = throw_ax + int(ts * arm_spr)
            tey = sh_y + arm_len - int(ws * ts * arm_len * 0.45)

        # 던지는 팔 그리기
        pygame.draw.line(screen, self.cdark, (throw_ax, throw_ay), (tex, tey), lw+1)
        pygame.draw.line(screen, c,          (throw_ax, throw_ay), (tex, tey), lw)

        # ── 손에 든 공 ───────────────────────────────
        if self.held:
            br = persp_r(self.y, B_RADIUS)
            for i in range(8):
                a   = self._ring_a * 1.8 + i * math.tau / 8
                rx  = tex + int(math.cos(a) * (br + 5))
                ry  = tey + int(math.sin(a) * (br + 5) * 0.55)
                t_v = abs(math.sin(a + self._ring_a)) ** 2
                rc  = tuple(int(cv * (0.35 + 0.65 * t_v)) for cv in C_CYAN)
                pygame.draw.circle(screen, rc, (rx, ry), max(1, br // 3 + 1))
            pygame.draw.circle(screen, C_BALLD, (tex, tey + 1), br)
            pygame.draw.circle(screen, C_BALL,  (tex, tey),     br)
            hl = max(1, br // 3)
            pygame.draw.circle(screen, (255, 130, 130), (tex - hl, tey - hl), hl)
        else:
            pygame.draw.circle(screen, c, (tex, tey), max(1, lw))

        # ── 머리 ─────────────────────────────────────
        head_c = tuple(min(255, v + 28) for v in c)
        pygame.draw.circle(screen, self.cdark, (sx, head_cy + 1), head_r)
        pygame.draw.circle(screen, head_c,     (sx, head_cy),     head_r)
        eye_x = sx + int(fx * head_r * 0.55)
        eye_y = head_cy + int(fy * head_r * 0.45)
        pygame.draw.circle(screen, C_WHITE, (eye_x, eye_y), max(1, head_r // 3))