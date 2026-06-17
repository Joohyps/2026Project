"""
Battle Ball — 1v1  |  ball.py
공 클래스 — z축 포물선 물리 + 원근 투영 렌더링
HELD 상태일 때는 player.draw()에서 직접 그림
"""

import math
import pygame
from settings import (
    CX1, CX2, CY1, CY2, B_RADIUS, SPIN_K,
    GRAVITY, THROW_SPD, THROW_VZ, BOUNCE_K, ROLL_DAMP,
    C_BALL, C_BALLD, C_SHADOW,
    w2s, persp_r, persp_z_scale,ARM_TIME,EXPLOSION_RADIUS,FLASH_PERIOD,
)

LOOSE  = "loose"
HELD   = "held"
THROWN = "thrown"


class Ball:
    def __init__(self, x: float, y: float, bid: int):
        self.bid = bid
        self.x   = float(x);  self.y  = float(y);  self.z  = 0.0
        self.vx  = 0.0;       self.vy = 0.0;        self.vz = 0.0
        self.w = 0.0
        self.state     = LOOSE
        self.owner     = None
        self.thrown_by = None

    def throw(self, dx: float, dy: float, spin:float):
        self.state = THROWN
        self.vx    = dx * THROW_SPD
        self.vy    = dy * THROW_SPD
        self.vz    = THROW_VZ
        self.w     = spin
        self.owner = None

    def update(self, dt: float):
        if self.state == HELD:
            return

        self.vz -= GRAVITY * dt
        self.z  += self.vz  * dt
        self.x  += self.vx  * dt
        self.y  += self.vy  * dt

        if abs(self.w) >= 10:
            v_perp_norm = (self.vy**2 + self.vx**2)**(1/2)
            if v_perp_norm <= 0.1:
                v_perp_norm = 10
            v_perp_x = self.vy / v_perp_norm
            v_perp_y = -self.vx / v_perp_norm

            spin_force = SPIN_K * (self.vx**2 + self.vy**2)**(1/2) * self.w
            self.vx += v_perp_x * spin_force * dt
            self.vy += v_perp_y * spin_force * dt

            self.w = self.w * 0.99

        if self.x < CX1 + B_RADIUS: self.x = CX1 + B_RADIUS; self.vx =  abs(self.vx) * 0.55
        if self.x > CX2 - B_RADIUS: self.x = CX2 - B_RADIUS; self.vx = -abs(self.vx) * 0.55
        if self.y < CY1 + B_RADIUS: self.y = CY1 + B_RADIUS; self.vy =  abs(self.vy) * 0.55
        if self.y > CY2 - B_RADIUS: self.y = CY2 - B_RADIUS; self.vy = -abs(self.vy) * 0.55

        if self.z <= 0.0:
            self.z = 0.0
            if self.state == THROWN:
                self.state     = LOOSE
                self.thrown_by = None
                self.vz = -self.vz * BOUNCE_K if abs(self.vz) > 90 else 0.0
            elif self.state == LOOSE:
                if abs(self.vz) > 50:
                    self.vz = -self.vz * BOUNCE_K
                else:
                    self.vz = 0.0
                    spd = math.hypot(self.vx, self.vy)
                    if spd > 3:
                        f = max(0.0, 1.0 - ROLL_DAMP * dt)
                        self.vx *= f;  self.vy *= f
                    else:
                        self.vx = self.vy = 0.0

    def draw_shadow(self, screen):
        if self.state == HELD:
            return   # 소지 중엔 그림자 없음 (플레이어 그림자로 대체)
        sx, sy = w2s(self.x, self.y)
        base_r = persp_r(self.y, B_RADIUS)
        sr = max(3, int(base_r * max(0.2, 1.0 - self.z * 0.007)))
        pygame.draw.ellipse(screen, C_SHADOW,
                            (sx - sr, sy - sr // 2 + 2, sr * 2, sr))

    def draw(self, screen):
        if self.state == HELD:
            return   # player.draw()에서 손 위치에 직접 그림
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

    def dist_sq(self, px: float, py: float) -> float:
        return (self.x - px) ** 2 + (self.y - py) ** 2





class Bomb(Ball):

    def __init__(self, x, y, bid):
        super().__init__(x, y, bid)

        self.armed = False
        self.exploded = False
        self.explosion_radius = EXPLOSION_RADIUS
        self.timer = 0.0
        self.explosion_spawned = False

    def update(self, dt):

        if self.exploded:
            return

        prev_z = self.z

        super().update(dt)

        # 최초 착지 감지
        if (not self.armed
                and prev_z > 0
                and self.z == 0
                and self.state != THROWN):

            self.armed = True
            self.timer = ARM_TIME

            self.vx = 0
            self.vy = 0
            self.vz = 0

        # 카운트다운
        if self.armed:

            self.timer -= dt

            if self.timer <= 0:
                self.explode()

    def explode(self):

        self.exploded = True


    def draw(self, screen):

        if self.exploded:
            return

        if self.state == HELD:
            return

        sx, sy = w2s(self.x, self.y)

        r = persp_r(self.y, B_RADIUS)

        zs = persp_z_scale(self.y)

        bsy = sy - int(self.z * zs)

        color = (0, 0, 0)

        if self.armed:

            progress = 1.0 - (self.timer / ARM_TIME)
            progress = max(0.0, min(1.0, progress))

            # 0.30초 → 0.03초로 점점 빨라짐
            flash_period = 0.30 - 0.27 * progress

            phase = int(pygame.time.get_ticks() /
                        (flash_period * 1000)) % 2

            if phase == 0:
                color = (0, 0, 0)
            else:
                color = (255, 40, 40)

        pygame.draw.circle(screen, color, (sx, bsy), r)