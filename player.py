"""
Battle Ball — 1v1  |  player.py
플레이어 클래스 — 원근 렌더링 + 상태머신
"""

import math
import pygame
from settings import (
    CX1, CX2, CY1, CY2, MID_X,
    P_RADIUS, B_RADIUS, PLAYER_SPD, THROW_VZ, KNOCK_DUR,
    C_CYAN, C_WHITE, C_GOLD, C_SHADOW,
    w2s, persp_r,
)

ALIVE   = "alive"
KNOCKED = "knocked"
BLINK   = "blink"


class Player:
    def __init__(self, pid, x, y, keys, color, color_dark):
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
        self._ra    = 0.0
        self._flash = 0.0

    def update(self, dt, pressed):
        self._ra += dt * 3.2
        if self._flash > 0:
            self._flash = max(0.0, self._flash - dt)

        if self.state == KNOCKED:
            self._kt -= dt
            if self._kt <= 0: self._respawn()
            return

        if self.state == BLINK:
            self._bt -= dt
            self._bvis = int(self._bt * 9) % 2 == 0
            if self._bt <= 0: self.state = ALIVE; self._bvis = True

        dx = dy = 0.0
        if pressed[self.keys['u']]: dy -= 1
        if pressed[self.keys['d']]: dy += 1
        if pressed[self.keys['l']]: dx -= 1
        if pressed[self.keys['r']]: dx += 1
        sp = math.hypot(dx, dy)
        if sp > 0:
            dx /= sp; dy /= sp
            self.facing = (dx, dy)

        self.x += dx * PLAYER_SPD * dt
        self.y += dy * PLAYER_SPD * dt
        self.x = max(CX1 + P_RADIUS, min(CX2 - P_RADIUS, self.x))
        self.y = max(CY1 + P_RADIUS, min(CY2 - P_RADIUS, self.y))
        if self.pid == 1: self.x = min(self.x, MID_X - P_RADIUS - 2)
        else:             self.x = max(self.x, MID_X + P_RADIUS + 2)

        if self.held:
            self.held.x = self.x + self.facing[0] * (P_RADIUS + B_RADIUS)
            self.held.y = self.y + self.facing[1] * (P_RADIUS + B_RADIUS)

    def try_throw(self):
        if not self.held or self.state == KNOCKED: return False
        b = self.held
        fx, fy = self.facing
        if self.pid == 1 and fx <= 0:  fx, fy = 1.0, 0.0
        elif self.pid == 2 and fx >= 0: fx, fy = -1.0, 0.0
        b.thrown_by = self
        b.x = self.x + fx * (P_RADIUS + B_RADIUS + 6)
        b.y = self.y + fy * (P_RADIUS + B_RADIUS + 6)
        b.throw(fx, fy)
        self.held = None
        return True

    def get_hit(self):
        if self.state != ALIVE: return
        if self.held:
            self.held.state = "loose"
            self.held.vx = self.held.vy = 0.0
            self.held.vz = 110.0
            self.held.thrown_by = None
            self.held = None
        self.state = KNOCKED; self._kt = KNOCK_DUR; self._flash = 0.3

    def _respawn(self):
        self.x = self._sx; self.y = self._sy
        self.state = BLINK; self._bt = 1.3; self._bvis = True

    def draw_shadow(self, screen):
        if not self._bvis: return
        sx, sy = w2s(self.x, self.y)
        r = persp_r(self.y, P_RADIUS)
        pygame.draw.ellipse(screen, C_SHADOW,
                            (sx - r + 2, sy + r - 4,
                             r * 2 - 3, max(3, r - 5)))

    def draw(self, screen):
        if not self._bvis: return
        sx, sy = w2s(self.x, self.y)
        r = persp_r(self.y, P_RADIUS)

        if self.state == KNOCKED:
            pygame.draw.ellipse(screen, self.cdark,
                                (sx - r*2+1, sy - r//2+1, r*4, r+2))
            pygame.draw.ellipse(screen, self.color,
                                (sx - r*2,   sy - r//2,   r*4, r))
            for i in range(3):
                a  = self._ra * 2.5 + i * math.tau / 3
                rx = sx + int(math.cos(a) * (r + 8))
                ry = sy - r // 2 + int(math.sin(a) * 5)
                pygame.draw.circle(screen, C_GOLD, (rx, ry), max(2, r // 4))
            return

        if self.held:
            for i in range(10):
                a  = self._ra + i * math.tau / 10
                rx = sx + int(math.cos(a) * (r + 9))
                ry = sy + int(math.sin(a) * (r + 9))
                t  = abs(math.sin(a + self._ra)) ** 2
                rc = tuple(int(c * (0.3 + 0.7 * t)) for c in C_CYAN)
                pygame.draw.circle(screen, rc, (rx, ry), max(2, r // 4 + 1))

        c = C_WHITE if (self._flash > 0 and int(self._flash * 22) % 2) else self.color
        pygame.draw.circle(screen, self.cdark, (sx, sy + max(1, r//6)), r)
        pygame.draw.circle(screen, c,          (sx, sy), r)
        hl_r = max(2, r // 3)
        hl_c = tuple(min(255, v + 60) for v in c)
        pygame.draw.circle(screen, hl_c, (sx - hl_r, sy - hl_r), hl_r)
        nx = sx + int(self.facing[0] * (r - max(4, r // 3)))
        ny = sy + int(self.facing[1] * (r - max(4, r // 3)))
        pygame.draw.circle(screen, C_WHITE, (nx, ny), max(2, r // 4))