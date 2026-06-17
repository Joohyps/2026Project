"""
Battle Ball — 1v1  |  effects.py
파티클 시스템 — 명중 이펙트 / 폭발 이펙트 / 황금 중앙선
"""

import math, random
import pygame
from settings import (
    CX1, CX2, CY1, CY2, MID_X,
    C_GOLD, C_GOLD2, C_WHITE,
    EXPLOSION_RADIUS,
    w2s,
)

_CL_TOP = w2s(MID_X, CY1)
_CL_BOT = w2s(MID_X, CY2)


class _Particle:
    __slots__ = ('x','y','vx','vy','color','life','max_life','r','grav')
    def __init__(self, x, y, vx, vy, color, life, r=3, grav=180.0):
        self.x=float(x); self.y=float(y); self.vx=vx; self.vy=vy
        self.color=color; self.life=life; self.max_life=life; self.r=r; self.grav=grav
    def update(self, dt):
        self.vy += self.grav*dt; self.x += self.vx*dt; self.y += self.vy*dt
        self.life -= dt; return self.life > 0
    def draw(self, surf):
        a = max(0.0, self.life/self.max_life)
        r = max(1, int(self.r*a))
        pygame.draw.circle(surf, tuple(int(v*a) for v in self.color),
                           (int(self.x), int(self.y)), r)


class ExplosionEffect:
    """폭발 원형 이펙트."""

    def __init__(self, x: int, y: int):
        self.x = x;  self.y = y
        self.life     = 0.55
        self.max_life = 0.55

    def update(self, dt):
        self.life -= dt

    @property
    def dead(self):
        return self.life <= 0

    def draw(self, screen):
        t = 1.0 - (self.life / self.max_life)
        r = int((20 + 120 * t) / 140 * EXPLOSION_RADIUS)

        pygame.draw.circle(screen, (255, 180, 0),   (self.x, self.y), max(5, r), 6)
        pygame.draw.circle(screen, (255, 255, 100), (self.x, self.y), max(3, r // 2), 3)


class Effects:
    def __init__(self):
        self._particles    = []
        self._explosions   = []
        self._cl_particles = []
        self._cl_timer     = 0.0

    def spawn_hit(self, x, y):
        for _ in range(22):
            ang   = random.uniform(0, math.tau)
            spd   = random.uniform(55, 210)
            color = random.choice([C_WHITE, C_GOLD, (255,200,100), (255,255,150)])
            life  = random.uniform(0.25, 0.65)
            r     = random.randint(2, 6)
            self._particles.append(
                _Particle(x, y, math.cos(ang)*spd, math.sin(ang)*spd-60, color, life, r))

    def spawn_explosion(self, x, y):
        """폭발 원형 이펙트 + 불꽃 파편."""
        self._explosions.append(ExplosionEffect(int(x), int(y)))
        for _ in range(3):
            self.spawn_hit(x, y)

    def update(self, dt):
        self._particles    = [p for p in self._particles    if p.update(dt)]
        self._cl_particles = [p for p in self._cl_particles if p.update(dt)]
        for e in self._explosions: e.update(dt)
        self._explosions   = [e for e in self._explosions if not e.dead]

        self._cl_timer += dt
        if self._cl_timer > 0.03:
            self._cl_timer = 0.0
            sy  = random.uniform(_CL_TOP[1], _CL_BOT[1])
            col = random.choice([C_GOLD, C_GOLD2, (255,228,100)])
            self._cl_particles.append(
                _Particle(_CL_TOP[0], sy,
                          random.uniform(-20,20), random.uniform(-95,-30),
                          col, 0.85, random.randint(2,4), grav=50.0))

    def draw_center(self, screen):
        pygame.draw.line(screen, C_GOLD2, _CL_TOP, _CL_BOT, 3)
        pygame.draw.line(screen, C_GOLD,  _CL_TOP, _CL_BOT, 1)
        for p in self._cl_particles: p.draw(screen)

    def draw(self, screen):
        for p in self._particles:  p.draw(screen)
        for e in self._explosions: e.draw(screen)