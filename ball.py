"""
Battle Ball — 1v1  |  ball.py
날아오는 공은 속도가 줄기 전까지 절대 줍지 못함 (닿으면 무조건 사망)
"""

import math
import pygame
from settings import (
    CX1, CX2, CY1, CY2, B_RADIUS, SPIN_K,
    GRAVITY, THROW_SPD, THROW_VZ, BOUNCE_K, ROLL_DAMP,
    C_BALL, C_BALLD, C_SHADOW,
    w2s, persp_r, persp_z_scale,
)

LOOSE  = "loose"
HELD   = "held"
THROWN = "thrown"

# 이 속도 이하로 줄어야 공을 집을 수 있음
_SAFE_SPEED = 80.0


class Ball:
    def __init__(self, x: float, y: float, bid: int):
        self.bid = bid
        self.x   = float(x);  self.y  = float(y);  self.z  = 0.0
        self.vx  = 0.0;       self.vy = 0.0;        self.vz = 0.0
        self.w   = 0.0
        self.state     = LOOSE
        self.owner     = None
        self.thrown_by = None   # 공을 던진 플레이어 (느려질 때까지 유지)

    def throw(self, dx: float, dy: float, spin: float):
        self.state     = THROWN
        self.vx        = dx * THROW_SPD
        self.vy        = dy * THROW_SPD
        self.vz        = THROW_VZ
        self.w         = spin
        self.owner     = None

    def update(self, dt: float):
        if self.state == HELD:
            return

        self.vz -= GRAVITY * dt
        self.z  += self.vz  * dt
        self.x  += self.vx  * dt
        self.y  += self.vy  * dt

        # 스핀
        if abs(self.w) >= 10:
            v_norm = (self.vy**2 + self.vx**2) ** 0.5
            if v_norm <= 0.1: v_norm = 10
            v_perp_x =  self.vy / v_norm
            v_perp_y = -self.vx / v_norm
            spin_force = SPIN_K * (self.vx**2 + self.vy**2) ** 0.5 * self.w
            self.vx += v_perp_x * spin_force * dt
            self.vy += v_perp_y * spin_force * dt
            self.w  *= 0.99

        if self.x < CX1 + B_RADIUS: self.x = CX1 + B_RADIUS; self.vx =  abs(self.vx) * 0.55
        if self.x > CX2 - B_RADIUS: self.x = CX2 - B_RADIUS; self.vx = -abs(self.vx) * 0.55
        if self.y < CY1 + B_RADIUS: self.y = CY1 + B_RADIUS; self.vy =  abs(self.vy) * 0.55
        if self.y > CY2 - B_RADIUS: self.y = CY2 - B_RADIUS; self.vy = -abs(self.vy) * 0.55

        if self.z <= 0.0:
            self.z = 0.0
            if self.state == THROWN:
                # ★ 착지해도 thrown_by 유지 — 아직 위험한 공
                self.state = LOOSE
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

            # ★ 속도가 충분히 줄어야 thrown_by 해제 (줍기 가능 상태)
            if self.state == LOOSE and self.thrown_by is not None:
                spd = math.hypot(self.vx, self.vy)
                if spd < _SAFE_SPEED:
                    self.thrown_by = None

    def draw_shadow(self, screen):
        if self.state == HELD:
            return
        sx, sy = w2s(self.x, self.y)
        base_r = persp_r(self.y, B_RADIUS)
        sr = max(3, int(base_r * max(0.2, 1.0 - self.z * 0.007)))
        pygame.draw.ellipse(screen, C_SHADOW,
                            (sx - sr, sy - sr // 2 + 2, sr * 2, sr))

    def draw(self, screen):
        if self.state == HELD:
            return
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

    @property
    def is_dangerous(self) -> bool:
        """True면 닿으면 맞음 — 줍기 불가."""
        return self.thrown_by is not None

# ── 기존 Ball 클래스 아래에 추가 ─────────────────────────────────────────────

from settings import ARM_TIME, EXPLOSION_RADIUS, C_BOMB, C_BOMBD


class Bomb(Ball):
    """
    착지 후 ARM_TIME 초 뒤 폭발.
    직접 명중 데미지 없음 — 폭발 범위 안에 있으면 피해.
    들고 있을 때도 타이머 계속 진행 → 빨리 던져야 함.
    """

    def __init__(self, x: float, y: float, bid: int):
        super().__init__(x, y, bid)
        self.armed             = False
        self.exploded          = False
        self.explosion_radius  = EXPLOSION_RADIUS
        self.timer             = 0.0
        self.explosion_spawned = False

    @property
    def is_dangerous(self) -> bool:
        return False   # 직접 충돌 데미지 없음

    def update(self, dt: float):
        if self.exploded:
            return

        prev_z = self.z
        super().update(dt)   # Ball 물리 (HELD면 내부에서 바로 return)

        # 최초 착지 감지 → 점화
        if (not self.armed
                and prev_z > 0
                and self.z == 0
                and self.state != THROWN):
            self.armed = True
            self.timer = ARM_TIME
            self.vx = self.vy = self.vz = 0.0

        # 카운트다운 (HELD 중에도 계속!)
        if self.armed:
            self.timer -= dt
            if self.timer <= 0:
                self.exploded = True

    def draw_shadow(self, screen):
        if self.exploded or self.state == HELD:
            return
        sx, sy = w2s(self.x, self.y)
        r = persp_r(self.y, B_RADIUS)
        sr = max(3, int(r * max(0.2, 1.0 - self.z * 0.007)))
        pygame.draw.ellipse(screen, C_SHADOW,
                            (sx - sr, sy - sr // 2 + 2, sr * 2, sr))

    def draw(self, screen):
        if self.exploded or self.state == HELD:
            return

        sx, sy = w2s(self.x, self.y)
        r      = persp_r(self.y, B_RADIUS)
        zs     = persp_z_scale(self.y)
        bsy    = sy - int(self.z * zs)

        # 점화 전: 검정, 점화 후: 빠르게 깜빡임
        if self.armed:
            progress     = max(0.0, min(1.0, 1.0 - self.timer / ARM_TIME))
            flash_period = max(0.03, 0.30 - 0.27 * progress)
            phase        = int(pygame.time.get_ticks() / (flash_period * 1000)) % 2
            color        = (255, 40, 40) if phase else C_BOMB
        else:
            color = C_BOMB

        pygame.draw.circle(screen, C_BOMBD, (sx, bsy + 2), r)
        pygame.draw.circle(screen, color,   (sx, bsy),     r)
        # 도화선 표시 (작은 흰 점)
        pygame.draw.circle(screen, (220, 220, 220),
                           (sx + r // 3, bsy - r // 2), max(2, r // 4))