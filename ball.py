"""
Battle Ball — 1v1  |  ball.py
공 클래스 — z축 포물선 + 원근 렌더링
"""

import math
import pygame
from settings import (
    CX1, CX2, CY1, CY2, CH, B_RADIUS,
    GRAVITY, THROW_SPD, THROW_VZ, BOUNCE_K, ROLL_DAMP,
    C_BALL, C_BALLD, C_SHADOW,
    w2s, persp_r, persp_z_scale,
)

LOOSE  = "loose"
HELD   = "held"
THROWN = "thrown"


class Ball:
    def __init__(self, x, y, bid):
        self.bid = bid
        self.x   = float(x);  self.y  = float(y);  self.z  = 0.0
        self.vx  = 0.0;       self.vy = 0.0;        self.vz = 0.0
        self.state     = LOOSE
        self.owner     = None
        self.thrown_by = None

    def throw(self, dx, dy):
        self.state = THROWN
        self.vx    = dx * THROW_SPD
        self.vy    = dy * THROW_SPD * 0.38
        self.vz    = THROW_VZ
        self.owner = None

    def update(self, dt):
        if self.state == HELD:
            return
        self.vz -= GRAVITY * dt
        self.z  += self.vz  * dt
        self.x  += self.vx  * dt
        self.y  += self.vy  * dt

        if self.x < CX1 + B_RADIUS: self.x = CX1 + B_RADIUS; self.vx =  abs(self.vx) * 0.55
        if self.x > CX2 - B_RADIUS: self.x = CX2 - B_RADIUS; self.vx = -abs(self.vx) * 0.55
        if self.y < CY1 + B_RADIUS: self.y = CY1 + B_RADIUS; self.vy =  abs(self.vy) * 0.55
        if self.y > CY2 - B_RADIUS: self.y = CY2 - B_RADIUS; self.vy = -abs(self.vy) * 0.55

        if self.z <= 0.0:
            self.z = 0.0
            if self.state == THROWN:
                self.state = LOOSE; self.thrown_by = None
                self.vz = -self.vz * BOUNCE_K if abs(self.vz) > 90 else 0.0
            elif self.state == LOOSE:
                if abs(self.vz) > 50:
                    self.vz = -self.vz * BOUNCE_K
                else:
                    self.vz = 0.0
                    spd = math.hypot(self.vx, self.vy)
                    if spd > 3:
                        f = max(0.0, 1.0 - ROLL_DAMP * dt)
                        self.vx *= f; self.vy *= f
                    else:
                        self.vx = self.vy = 0.0

    def draw_shadow(self, screen):
        sx, sy = w2s(self.x, self.y)
        base_r = persp_r(self.y, B_RADIUS)
        sr = max(3, int(base_r * max(0.2, 1.0 - self.z * 0.007)))
        pygame.draw.ellipse(screen, C_SHADOW,
                            (sx - sr, sy - sr // 2 + 2, sr * 2, sr))

    def draw(self, screen):
        sx, sy = w2s(self.x, self.y)
        r      = persp_r(self.y, B_RADIUS)
        zs     = persp_z_scale(self.y)
        bsy    = sy - int(self.z * zs)

        if self.z > 14:
            step = max(8, int(self.z / 4))
            for h in range(step, int(self.z * zs), step):
                pygame.draw.circle(screen, (45, 75, 44), (sx, sy - h), 1)

        r_fly = max(4, int(r * (1.0 + self.z * 0.0006)))
        pygame.draw.circle(screen, C_BALLD, (sx, bsy + 2), r_fly)
        pygame.draw.circle(screen, C_BALL,  (sx, bsy),     r_fly)
        hl = max(2, r_fly // 3)
        pygame.draw.circle(screen, (255, 130, 130),
                           (sx - r_fly // 3, bsy - r_fly // 3), hl)

    def dist_sq(self, px, py):
        return (self.x - px) ** 2 + (self.y - py) ** 2