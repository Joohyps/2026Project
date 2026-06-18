"""
Battle Ball — 1v1  |  player.py
사람 형태 / 걷기 + 던지기 + 구르기 / 스핀 / AI 외부 제어 지원
"""

import math
import pygame
from settings import (
    CX1, CX2, CY1, CY2, MID_X,
    P_RADIUS, B_RADIUS, PLAYER_SPD, KNOCK_DUR, MAX_SPIN,
    C_CYAN, C_WHITE, C_GOLD, C_SHADOW, C_BALL, C_BALLD, C_BOMB, C_BOMBD,
    w2s, persp_r, court_x_limits, ARM_TIME
)
from ball import Ball, Bomb

ALIVE   = "alive"
KNOCKED = "knocked"
BLINK   = "blink"
ROLLING = "rolling"

THROW_DUR     = 0.34
ROLL_DUR      = 0.42
ROLL_SPEED    = 430.0
ROLL_COOLDOWN = 1.5


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

        # 구르기
        self._roll_t   = 0.0
        self._roll_cd  = 0.0
        self._roll_vx  = 0.0
        self._roll_vy  = 0.0
        self._roll_ang = 0.0

        # 스핀 (Q/E, U/O 키)
        self._spin = 0.0

        # AI 외부 제어
        self.ext_control = False   # True = AI 모드
        self.ext_dx      = 0.0    # AI 이동 방향 x
        self.ext_dy      = 0.0    # AI 이동 방향 y

    # ── Update ───────────────────────────────────────────────────────────────

    def update(self, dt: float, pressed):
        self._ring_a += dt * 3.2
        if self._flash   > 0: self._flash   = max(0.0, self._flash   - dt)
        if self._throw_t > 0: self._throw_t = max(0.0, self._throw_t - dt)
        if self._roll_cd > 0: self._roll_cd = max(0.0, self._roll_cd - dt)

        # ── 구르기 ──────────────────────────────────
        if self.state == ROLLING:
            self._roll_t   -= dt
            self._roll_ang += dt * 18.0
            self.x += self._roll_vx * ROLL_SPEED * dt
            self.y += self._roll_vy * ROLL_SPEED * dt
            x_min, x_max = court_x_limits(self.y, P_RADIUS)
            self.x = max(x_min, min(x_max, self.x))
            self.y = max(CY1 + P_RADIUS, min(CY2 - P_RADIUS, self.y))
            if self.pid == 1: self.x = min(self.x, MID_X - P_RADIUS - 2)
            else:             self.x = max(self.x, MID_X + P_RADIUS + 2)
            if self.held:
                self.held.x = self.x;  self.held.y = self.y
            if self._roll_t <= 0:
                self.state    = ALIVE
                self._roll_cd = ROLL_COOLDOWN
            return

        if self.state == KNOCKED:
            self._kt -= dt
            if self._kt <= 0: self._respawn()
            return

        if self.state == BLINK:
            self._bt -= dt
            self._bvis = int(self._bt * 9) % 2 == 0
            if self._bt <= 0:
                self.state = ALIVE;  self._bvis = True

        # ── 이동 입력 ────────────────────────────────
        if self.ext_control:
            # AI 제어
            dx, dy = self.ext_dx, self.ext_dy
            sp = math.hypot(dx, dy)
            if sp > 0:
                self.facing     = (dx, dy)
                self._walk_t   += dt
                self._is_moving = True
            else:
                self._is_moving = False
        else:
            # 사람 제어
            dx = dy = 0.0
            if pressed[self.keys['u']]: dy -= 1
            if pressed[self.keys['d']]: dy += 1
            if pressed[self.keys['l']]: dx -= 1
            if pressed[self.keys['r']]: dx += 1
            sp = math.hypot(dx, dy)
            if sp > 0:
                dx /= sp;  dy /= sp
                self.facing     = (dx, dy)
                self._walk_t   += dt
                self._is_moving = True
            else:
                self._is_moving = False

            # 스핀 입력 (ls/rs 키)
            ls_key = self.keys.get('ls', None)
            rs_key = self.keys.get('rs', None)
            if ls_key and pressed[ls_key] and self.held:
                self._spin = max(-MAX_SPIN, self._spin - 160 * dt)
            elif rs_key and pressed[rs_key] and self.held:
                self._spin = min( MAX_SPIN, self._spin + 160 * dt)
            else:
                self._spin *= max(0.0, 1.0 - 6.0 * dt)

        self.x += dx * PLAYER_SPD * dt
        self.y += dy * PLAYER_SPD * dt

        x_min, x_max = court_x_limits(self.y, P_RADIUS)
        self.x = max(x_min, min(x_max, self.x))
        self.y = max(CY1 + P_RADIUS, min(CY2 - P_RADIUS, self.y))
        if self.pid == 1: self.x = min(self.x, MID_X - P_RADIUS - 2)
        else:             self.x = max(self.x, MID_X + P_RADIUS + 2)

        if self.held:
            self.held.x = self.x;  self.held.y = self.y

    # ── Actions ──────────────────────────────────────────────────────────────

    def try_throw(self, spin_override: float = None) -> bool:
        if not self.held or self.state == KNOCKED:
            return False
        ball = self.held
        fx, fy = self.facing
        spin = spin_override if spin_override is not None else self._spin
        ball.thrown_by = self
        ball.x = self.x + fx * (P_RADIUS + B_RADIUS + 6)
        ball.y = self.y + fy * (P_RADIUS + B_RADIUS + 6)
        ball.throw(fx, fy, spin)
        self.held     = None
        self._spin    = 0.0
        self._throw_t = THROW_DUR
        return True

    def try_roll(self) -> bool:
        if self.state != ALIVE or self._roll_cd > 0:
            return False
        self._roll_vx  = self.facing[0]
        self._roll_vy  = self.facing[1]
        self.state     = ROLLING
        self._roll_t   = ROLL_DUR
        return True

    def get_hit(self):
        if self.state in (KNOCKED, BLINK, ROLLING):
            return
        if self.held:
            self.held.state     = "loose"
            self.held.vx        = 0.0;  self.held.vy = 0.0
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
            sw = max(5, int(r * 1.30));  sh = max(2, int(r * 0.30))
            pygame.draw.ellipse(screen, C_SHADOW,
                                (sx - sw, sy + int(r * 0.08), sw * 2, sh * 2))
        else:
            pygame.draw.ellipse(screen, C_SHADOW,
                                (sx - r, sy + int(r * 0.22),
                                 r * 2, max(3, int(r * 0.40))))

    def draw(self, screen):
        if not self._bvis: return
        sx, sy = w2s(self.x, self.y)
        r  = persp_r(self.y, P_RADIUS)
        fx, fy = self.facing

        if self.state == ROLLING:
            self._draw_rolling(screen, sx, sy, r)
            return

        if self.state == KNOCKED:
            pygame.draw.ellipse(screen, self.cdark,
                                (sx-r*2+1, sy-r//2+1, r*4, r+2))
            pygame.draw.ellipse(screen, self.color,
                                (sx-r*2, sy-r//2, r*4, r))
            for i in range(3):
                a  = self._ring_a * 2.5 + i * math.tau / 3
                rx = sx + int(math.cos(a) * (r + 10))
                ry = sy - r//2 + int(math.sin(a) * 6)
                pygame.draw.circle(screen, C_GOLD, (rx, ry), max(2, r // 4))
            return

        c = C_WHITE if (self._flash > 0 and int(self._flash * 22) % 2) else self.color

        head_r  = max(4, int(r * 0.48));  body_w  = max(3, int(r * 0.37))
        body_h  = max(4, int(r * 0.58));  leg_len = max(5, int(r * 0.82))
        leg_spr = max(2, int(r * 0.30));  arm_len = max(4, int(r * 0.60))
        arm_spr = max(2, int(r * 0.28));  lw      = max(1, int(r * 0.18))

        hip_y   = sy + int(r * 0.20);  chest_y = hip_y  - body_h * 2
        sh_y    = chest_y + int(body_h * 0.28)
        head_cy = chest_y - head_r - max(1, int(r * 0.08))

        ws = math.sin(self._walk_t * 8.5) * (1.0 if self._is_moving else 0.0)
        ts = self._throw_side
        throw_ax = sx + ts * body_w;  throw_ay = sh_y

        for side in (-1, 1):
            s = ws * side
            foot_x = sx + int(s * leg_spr)
            foot_y = hip_y + leg_len - int(abs(s) * leg_len * 0.10)
            pygame.draw.line(screen, self.cdark, (sx, hip_y), (foot_x, foot_y), lw+1)
            pygame.draw.line(screen, c,          (sx, hip_y), (foot_x, foot_y), lw)
            pygame.draw.circle(screen, c, (foot_x, foot_y), max(1, lw))

        pygame.draw.ellipse(screen, self.cdark,
                            (sx-body_w, chest_y-1, body_w*2, body_h*2+2))
        pygame.draw.ellipse(screen, c,
                            (sx-body_w, chest_y,   body_w*2, body_h*2))

        other_side = -ts
        oth_ax = sx + other_side * body_w
        oth_ex = oth_ax + int(other_side * arm_spr)
        oth_ey = sh_y + arm_len - int(-ws * other_side * arm_len * 0.45)
        pygame.draw.line(screen, self.cdark, (oth_ax, sh_y), (oth_ex, oth_ey), lw+1)
        pygame.draw.line(screen, c,          (oth_ax, sh_y), (oth_ex, oth_ey), lw)
        pygame.draw.circle(screen, c, (oth_ex, oth_ey), max(1, lw))

        if self._throw_t > 0:
            prog = 1.0 - self._throw_t / THROW_DUR
            if prog < 0.35:
                t = prog / 0.35;  ease = t * t
                tex = throw_ax - int(fx * arm_len * 1.0 * ease)
                tey = throw_ay - int(r  * 0.65 * ease)
            elif prog < 0.72:
                t = (prog-0.35)/0.37;  ease = 1.0 - (1.0-t)**3
                tex = throw_ax - int(fx*arm_len*(1.0-ease)) + int(fx*arm_len*1.3*ease)
                tey = throw_ay - int(r*0.65*(1.0-ease)) + int(r*0.18*ease)
            else:
                t = (prog-0.72)/0.28
                tex = throw_ax + int(fx * arm_len * (1.3 - t*0.6))
                tey = throw_ay + int(r  * 0.18 * (1.0-t))
        elif self.held:
            tex = throw_ax + int(fx*arm_len*0.88) + int(ts*arm_spr*0.25)
            tey = throw_ay + int(fy*arm_len*0.40)
        else:
            tex = throw_ax + int(ts * arm_spr)
            tey = sh_y + arm_len - int(ws*ts*arm_len*0.45)

        pygame.draw.line(screen, self.cdark, (throw_ax, throw_ay), (tex, tey), lw+1)
        pygame.draw.line(screen, c,          (throw_ax, throw_ay), (tex, tey), lw)

        if self.held:
            br = persp_r(self.y, B_RADIUS)
            for i in range(8):
                a   = self._ring_a * 1.8 + i * math.tau / 8
                rx  = tex + int(math.cos(a) * (br + 5))
                ry  = tey + int(math.sin(a) * (br + 5) * 0.55)
                t_v = abs(math.sin(a + self._ring_a)) ** 2
                if isinstance(self.held, Bomb):
                    rc  = tuple(int(cv * (0.35 + 0.65*t_v)) for cv in C_GOLD)
                else:
                    rc = tuple(int(cv * (0.35 + 0.65 * t_v)) for cv in C_CYAN)
                pygame.draw.circle(screen, rc, (rx, ry), max(1, br//3+1))

            if isinstance(self.held, Bomb):
                if self.held.armed:
                    progress = max(0.0, min(1.0, 1.0 - self.held.timer / ARM_TIME))
                    flash_period = max(0.03, 0.30 - 0.27 * progress)
                    phase = int(pygame.time.get_ticks() / (flash_period * 1000)) % 2
                    color = (255, 40, 40) if phase else C_BOMB
                else:
                    color = C_BOMB
                pygame.draw.circle(screen, color, (tex, tey + 1), br)
                pygame.draw.circle(screen, color, (tex, tey), br)
            else:
                pygame.draw.circle(screen, C_BALLD, (tex, tey + 1), br)
                pygame.draw.circle(screen, C_BALL, (tex, tey), br)
            hl = max(1, br//3)
            pygame.draw.circle(screen, (255,130,130), (tex-hl, tey-hl), hl)
        else:
            pygame.draw.circle(screen, c, (tex, tey), max(1, lw))

        # 스핀 게이지 (사람이 조종할 때만 표시)
        if not self.ext_control and abs(self._spin) > 5:
            spin_r = r + 8
            spin_color = (100, 200, 255) if self._spin > 0 else (255, 150, 80)
            frac = abs(self._spin) / MAX_SPIN
            if self._spin >= 0:
                arc_pts = [
                    (sx + int(math.cos(math.pi + i * math.pi * frac / 10) * spin_r),
                     sy + int(math.sin(math.pi + i * math.pi * frac / 10) * spin_r))
                    for i in range(11)
                ]
            else:
                arc_pts = [
                    (sx + int(math.cos( -i * math.pi * frac / 10) * spin_r),
                     sy + int(math.sin( -i * math.pi * frac / 10) * spin_r))
                    for i in range(11)
                ]
            if len(arc_pts) >= 2:
                pygame.draw.lines(screen, spin_color, False, arc_pts, 5)

        head_c = tuple(min(255, v+28) for v in c)
        pygame.draw.circle(screen, self.cdark, (sx, head_cy+1), head_r)
        pygame.draw.circle(screen, head_c,     (sx, head_cy),   head_r)
        eye_x = sx + int(fx * head_r * 0.55)
        eye_y = head_cy + int(fy * head_r * 0.45)
        pygame.draw.circle(screen, C_WHITE, (eye_x, eye_y), max(1, head_r//3))

        # AI 표시 (오른쪽 플레이어가 AI일 때)
        if self.ext_control:
            label_surf = pygame.font.Font(None, 18).render("AI", True, C_GOLD)
            screen.blit(label_surf, (sx - 8, head_cy - head_r - 14))

    # ── 구르기 렌더링 ─────────────────────────────────────────────────────────

    def _draw_rolling(self, screen, sx, sy, r):
        c  = self.color
        ra = math.atan2(self._roll_vy, self._roll_vx)

        for i in range(1, 5):
            px = self.x - self._roll_vx * ROLL_SPEED * i * 0.028
            py = self.y - self._roll_vy * ROLL_SPEED * i * 0.028
            tsx, tsy = w2s(px, py)
            tr   = max(1, int(persp_r(py, P_RADIUS) * 0.58 * (1 - i*0.20)))
            frac = max(0.0, 0.42 - i * 0.09)
            pygame.draw.circle(screen, tuple(int(v*frac) for v in c), (tsx, tsy), tr)

        a_ax = max(5, int(r * 1.30));  b_ax = max(3, int(r * 0.48))
        pts_dark = _ellipse_pts(sx, sy+1, a_ax, b_ax, ra)
        pts_fill = _ellipse_pts(sx, sy,   a_ax, b_ax, ra)
        if len(pts_dark) >= 3:
            pygame.draw.polygon(screen, self.cdark, pts_dark)
            pygame.draw.polygon(screen, c,          pts_fill)

        for i in range(2):
            sa = self._roll_ang + i * math.pi / 2
            cos_ra, sin_ra = math.cos(ra), math.sin(ra)
            cos_sa, sin_sa = math.cos(sa), math.sin(sa)
            ex = sx + int((a_ax*cos_sa*cos_ra - b_ax*sin_sa*sin_ra) * 0.62)
            ey = sy + int((a_ax*cos_sa*sin_ra + b_ax*sin_sa*cos_ra) * 0.62)
            pygame.draw.line(screen, self.cdark, (sx, sy), (ex, ey), max(1, r//7))


def _ellipse_pts(cx, cy, a, b, angle, n=14):
    cos_a, sin_a = math.cos(angle), math.sin(angle)
    return [(int(cx + a*math.cos(j*math.tau/n)*cos_a - b*math.sin(j*math.tau/n)*sin_a),
             int(cy + a*math.cos(j*math.tau/n)*sin_a + b*math.sin(j*math.tau/n)*cos_a))
            for j in range(n)]