"""
Battle Ball — 1v1  |  player.py
플레이어: 사다리꼴 경계 / 사람 형태 / 걷기 + 던지기 + 앞구르기 모션
"""

import math
import pygame
from settings import (
    CX1, CX2, CY1, CY2, MID_X,
    P_RADIUS, B_RADIUS, PLAYER_SPD, KNOCK_DUR, MAX_SPIN,
    C_CYAN, C_WHITE, C_GOLD, C_SHADOW, C_BALL, C_BALLD,
    w2s, persp_r, court_x_limits,
)

ALIVE   = "alive"
KNOCKED = "knocked"
BLINK   = "blink"
ROLLING = "rolling"

THROW_DUR     = 0.34
ROLL_DUR      = 0.42    # 구르기 지속 시간 (초)
ROLL_SPEED    = 430.0   # 구르기 이동 속도
ROLL_COOLDOWN = 1.5     # 다음 구르기까지 대기 시간


class Player:
    def __init__(self, pid: int, x: float, y: float,
                 keys: dict, color: tuple, color_dark: tuple):
        self.pid    = pid
        self.x      = float(x);  self.y  = float(y)
        self.__spin = 0.0
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

        # 구르기
        self._roll_t   = 0.0   # 남은 구르기 시간
        self._roll_cd  = 0.0   # 쿨다운
        self._roll_vx  = 0.0   # 구르기 방향 x
        self._roll_vy  = 0.0   # 구르기 방향 y
        self._roll_ang = 0.0   # 회전 애니메이션 각도

    @property
    def spin(self):
        return self.__spin
    @spin.setter
    def spin(self, value):
        self.__spin = max(-MAX_SPIN, min(value, MAX_SPIN))

    # ── Update ───────────────────────────────────────────────────────────────

    def update(self, dt: float, pressed):
        self._ring_a += dt * 3.2
        if self._flash   > 0: self._flash   = max(0.0, self._flash   - dt)
        if self._throw_t > 0: self._throw_t = max(0.0, self._throw_t - dt)
        if self._roll_cd > 0: self._roll_cd = max(0.0, self._roll_cd - dt)

        # ── 구르기 상태 (이동 제어 별도 처리) ────────
        if self.state == ROLLING:
            self._roll_t   -= dt
            self._roll_ang += dt * 18.0   # 빠른 회전

            self.x += self._roll_vx * ROLL_SPEED * dt
            self.y += self._roll_vy * ROLL_SPEED * dt

            x_min, x_max = court_x_limits(self.y, P_RADIUS)
            self.x = max(x_min, min(x_max, self.x))
            self.y = max(CY1 + P_RADIUS, min(CY2 - P_RADIUS, self.y))
            if self.pid == 1: self.x = min(self.x, MID_X - P_RADIUS - 2)
            else:             self.x = max(self.x, MID_X + P_RADIUS + 2)

            if self.held:
                self.held.x = self.x
                self.held.y = self.y

            if self._roll_t <= 0:
                self.state    = ALIVE
                self._roll_cd = ROLL_COOLDOWN
            return   # 구르기 중에는 일반 이동 코드 건너뜀

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
        if pressed[self.keys['ls']] and self.held:
            if self.spin >= 0 :
                self.spin += 3
            else:
                self.spin = 0
                self.spin += 3
        if pressed[self.keys['rs']] and self.held:
            if self.spin <= 0 :
                self.spin -=3
            else:
                self.spin = 0
                self.spin -= 3

        if self.spin != 0:
            if self.spin>0:
                self.spin -= 1
            else:
                self.spin += 1
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

        x_min, x_max = court_x_limits(self.y, P_RADIUS)
        self.x = max(x_min, min(x_max, self.x))
        self.y = max(CY1 + P_RADIUS, min(CY2 - P_RADIUS, self.y))
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
        ball.throw(fx, fy, self.spin)
        self.spin = 0
        self.held     = None
        self._throw_t = THROW_DUR
        return True

    def try_roll(self) -> bool:
        """앞구르기 시작. ALIVE 상태이고 쿨다운이 없을 때만 가능."""
        if self.state != ALIVE or self._roll_cd > 0:
            return False
        self._roll_vx  = self.facing[0]
        self._roll_vy  = self.facing[1]
        self.state     = ROLLING
        self._roll_t   = ROLL_DUR
        return True

    def get_hit(self):
        # ROLLING, BLINK 상태는 무적
        if self.state in (KNOCKED, BLINK, ROLLING):
            return
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

        if self.state == ROLLING:
            # 구르기 중: 방향으로 늘어난 납작한 그림자
            sw = max(5, int(r * 1.30))
            sh = max(2, int(r * 0.30))
            pygame.draw.ellipse(screen, C_SHADOW,
                                (sx - sw, sy + int(r * 0.08), sw * 2, sh * 2))
        else:
            pygame.draw.ellipse(screen, C_SHADOW,
                                (sx - r, sy + int(r * 0.22),
                                 r * 2, max(3, int(r * 0.40))))

    def draw_power_bar(self, screen):
        # 게이지 바 크기
        BAR_WIDTH = persp_r(self.y, 12)
        BAR_HEIGHT = persp_r(self.y, 60)

        # 플레이어 옆 위치
        if self.spin > 10:
            spin = self.spin
            bar_x, bar_y = w2s(self.x - 30, self.y - BAR_HEIGHT // 2)
        elif self.spin < -10:
            spin = -self.spin
            bar_x, bar_y = w2s(self.x + 30, self.y - BAR_HEIGHT // 2)
        else:
            return

        # 배경 (회색)
        pygame.draw.rect(
            screen,
            (100, 100, 100),
            (bar_x, bar_y, BAR_WIDTH, BAR_HEIGHT)
        )

        # power 비율
        ratio = max(0, min(1, spin / MAX_SPIN))

        # 채워질 높이
        fill_height = int(BAR_HEIGHT * ratio)

        # 색상 보간
        # power=0 -> 초록(0,255,0)
        # power=1 -> 빨강(255,0,0)
        r = int(255 * ratio)
        g = int(255 * (1 - ratio))
        color = (r, g, 0)

        # 아래에서 위로 차오르도록
        fill_rect = pygame.Rect(
            bar_x,
            bar_y + BAR_HEIGHT - fill_height,
            BAR_WIDTH,
            fill_height
        )

        pygame.draw.rect(screen, color, fill_rect)

        # 테두리
        pygame.draw.rect(
            screen,
            (255, 255, 255),
            (bar_x, bar_y, BAR_WIDTH, BAR_HEIGHT),
            2
        )

    def draw(self, screen):
        if not self._bvis: return
        sx, sy = w2s(self.x, self.y)
        r  = persp_r(self.y, P_RADIUS)
        fx, fy = self.facing

        # ── 구르기 ──────────────────────────────────
        if self.state == ROLLING:
            self._draw_rolling(screen, sx, sy, r)
            return

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

        head_r  = max(4, int(r * 0.48))
        body_w  = max(3, int(r * 0.37))
        body_h  = max(4, int(r * 0.58))
        leg_len = max(5, int(r * 0.82))
        leg_spr = max(2, int(r * 0.30))
        arm_len = max(4, int(r * 0.60))
        arm_spr = max(2, int(r * 0.28))
        lw      = max(1, int(r * 0.18))

        hip_y   = sy + int(r * 0.20)
        chest_y = hip_y  - body_h * 2
        sh_y    = chest_y + int(body_h * 0.28)
        head_cy = chest_y - head_r - max(1, int(r * 0.08))

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
                t    = prog / 0.35
                ease = t * t
                tex  = throw_ax - int(fx * arm_len * 1.0 * ease)
                tey  = throw_ay - int(r  * 0.65 * ease)
            elif prog < 0.72:
                t    = (prog - 0.35) / 0.37
                ease = 1.0 - (1.0 - t) ** 3
                tex  = throw_ax - int(fx * arm_len * (1.0 - ease)) \
                                + int(fx * arm_len * 1.3 * ease)
                tey  = throw_ay - int(r * 0.65 * (1.0 - ease)) \
                                + int(r * 0.18 * ease)
            else:
                t   = (prog - 0.72) / 0.28
                tex = throw_ax + int(fx * arm_len * (1.3 - t * 0.6))
                tey = throw_ay + int(r  * 0.18 * (1.0 - t))
        elif self.held:
            tex = throw_ax + int(fx * arm_len * 0.88) + int(ts * arm_spr * 0.25)
            tey = throw_ay + int(fy * arm_len * 0.40)
        else:
            tex = throw_ax + int(ts * arm_spr)
            tey = sh_y + arm_len - int(ws * ts * arm_len * 0.45)

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

        self.draw_power_bar(screen)

    # ── 구르기 전용 렌더링 ────────────────────────────────────────────────────

    def _draw_rolling(self, screen, sx, sy, r):
        """납작한 회전 타원 + 잔상 + 회전 마크."""
        c  = self.color
        ra = math.atan2(self._roll_vy, self._roll_vx)   # 구르기 방향 각도

        # ── 잔상 (trail) ──────────────────────────────
        for i in range(1, 5):
            px = self.x - self._roll_vx * ROLL_SPEED * i * 0.028
            py = self.y - self._roll_vy * ROLL_SPEED * i * 0.028
            tsx, tsy = w2s(px, py)
            tr   = max(1, int(persp_r(py, P_RADIUS) * 0.58 * (1 - i * 0.20)))
            frac = max(0.0, 0.42 - i * 0.09)
            pygame.draw.circle(screen,
                               tuple(int(v * frac) for v in c),
                               (tsx, tsy), tr)

        # ── 회전 타원 (납작하게 구르는 형태) ─────────
        a_ax = max(5, int(r * 1.30))   # 구르기 방향 반지름
        b_ax = max(3, int(r * 0.48))   # 수직 방향 반지름

        pts_dark = _ellipse_pts(sx, sy + 1, a_ax, b_ax, ra)
        pts_fill = _ellipse_pts(sx, sy,     a_ax, b_ax, ra)
        if len(pts_dark) >= 3:
            pygame.draw.polygon(screen, self.cdark, pts_dark)
            pygame.draw.polygon(screen, c,          pts_fill)

        # ── 회전 마크 (2개 선분 — X 형태로 회전) ─────
        for i in range(2):
            sa   = self._roll_ang + i * math.pi / 2
            cos_ra, sin_ra = math.cos(ra), math.sin(ra)
            cos_sa, sin_sa = math.cos(sa), math.sin(sa)
            # 타원 내부에서 회전하는 선의 끝점
            ex = sx + int((a_ax * cos_sa * cos_ra - b_ax * sin_sa * sin_ra) * 0.62)
            ey = sy + int((a_ax * cos_sa * sin_ra + b_ax * sin_sa * cos_ra) * 0.62)
            pygame.draw.line(screen, self.cdark,
                             (sx, sy), (ex, ey), max(1, r // 7))

        # ── 쿨다운 표시 (구르기 끝난 뒤 잠깐) ────────
        if self._roll_cd > 0 and self.state != ROLLING:
            frac = self._roll_cd / ROLL_COOLDOWN
            arc_r = r + 5
            arc_c = (80, 80, 80)
            pygame.draw.circle(screen, arc_c, (sx, sy), arc_r, 1)


def _ellipse_pts(cx, cy, a, b, angle, n=14):
    """회전 타원의 꼭짓점 좌표 반환."""
    cos_a, sin_a = math.cos(angle), math.sin(angle)
    pts = []
    for j in range(n):
        t   = j * math.tau / n
        ct  = math.cos(t)
        st  = math.sin(t)
        pts.append((int(cx + a * ct * cos_a - b * st * sin_a),
                    int(cy + a * ct * sin_a + b * st * cos_a)))
    return pts