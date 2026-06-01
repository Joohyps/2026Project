"""
Battle Ball — 1v1  |  effects.py
파티클 시스템 — 명중 이펙트 / 골든 중앙선 파티클
"""

import math
import random
import pygame
from settings import (
    CX1, CX2, CY1, CY2, MID_X,
    C_GOLD, C_GOLD2, C_WHITE,
)


class _Particle:
    __slots__ = ('x', 'y', 'vx', 'vy', 'color', 'life', 'max_life', 'r', 'grav')

    def __init__(self, x, y, vx, vy, color, life, r=3, grav=180.0):
        self.x = float(x); self.y = float(y)
        self.vx = vx;       self.vy = vy
        self.color = color
        self.life = life;   self.max_life = life
        self.r = r
        self.grav = grav

    def update(self, dt: float) -> bool:
        self.vy  += self.grav * dt
        self.x   += self.vx  * dt
        self.y   += self.vy  * dt
        self.life -= dt
        return self.life > 0

    def draw(self, surf):
        alpha = max(0.0, self.life / self.max_life)
        r = max(1, int(self.r * alpha))
        c = tuple(int(v * alpha) for v in self.color)
        pygame.draw.circle(surf, c, (int(self.x), int(self.y)), r)


class Effects:
    """
    - spawn_hit(x, y)     : 명중 위치에 흰/금 파티클 폭발
    - update(dt)          : 모든 파티클 + 중앙선 파티클 갱신
    - draw_center(screen) : 중앙선 + 금빛 파티클 렌더링
    - draw(screen)        : 명중 파티클 렌더링
    """

    def __init__(self):
        self._particles    = []   # 명중 파티클
        self._cl_particles = []   # 중앙선 파티클
        self._cl_timer     = 0.0

    # ── Spawn helpers ────────────────────────────────────────────────────────

    def spawn_hit(self, x: float, y: float):
        """공 명중 위치에 파티클 폭발."""
        for _ in range(22):
            ang  = random.uniform(0, math.tau)
            spd  = random.uniform(55, 210)
            color = random.choice([
                C_WHITE,
                C_GOLD,
                (255, 200, 100),
                (255, 255, 150),
            ])
            life  = random.uniform(0.25, 0.65)
            r     = random.randint(2, 6)
            self._particles.append(
                _Particle(x, y,
                          math.cos(ang) * spd,
                          math.sin(ang) * spd - 55,
                          color, life, r))

    # ── Update ───────────────────────────────────────────────────────────────

    def update(self, dt: float):
        self._particles    = [p for p in self._particles    if p.update(dt)]
        self._cl_particles = [p for p in self._cl_particles if p.update(dt)]

        # 중앙선 파티클 생성 (일정 간격)
        self._cl_timer += dt
        if self._cl_timer > 0.03:
            self._cl_timer = 0.0
            y    = random.uniform(CY1 + 10, CY2 - 10)
            vx   = random.uniform(-18, 18)
            vy   = random.uniform(-90, -28)
            r    = random.randint(2, 4)
            col  = random.choice([C_GOLD, C_GOLD2, (255, 230, 100)])
            self._cl_particles.append(
                _Particle(MID_X, y, vx, vy, col, 0.85, r, grav=55.0))

    # ── Draw ─────────────────────────────────────────────────────────────────

    def draw_center(self, screen):
        """중앙선 본체 + 파티클."""
        # 중앙선 (황금색 두 겹)
        pygame.draw.line(screen, C_GOLD2, (MID_X, CY1), (MID_X, CY2), 3)
        pygame.draw.line(screen, C_GOLD,  (MID_X, CY1), (MID_X, CY2), 1)
        for p in self._cl_particles:
            p.draw(screen)

    def draw(self, screen):
        """명중 파티클."""
        for p in self._particles:
            p.draw(screen)
