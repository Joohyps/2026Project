"""
Battle Ball — 1v1  |  bot.py
스크립트 봇 — 적당히 허점 있음
"""

import math
import random
from player import ALIVE, KNOCKED, ROLLING
from ball   import LOOSE


class ScriptedBot:
    def __init__(self):
        self._throw_timer = 0.0
        self._wander_t    = 0.0   # 가끔 엉뚱한 방향으로 이동
        self._wander_dx   = 0.0
        self._wander_dy   = 0.0

    def update(self, dt: float, me, opponent, balls):
        if me.state == KNOCKED:
            me.ext_dx = 0.0;  me.ext_dy = 0.0
            return

        # ── 회피: 25% 확률, 공이 매우 가까울 때만 ──────
        if me._roll_cd <= 0:
            for b in balls:
                if not b.is_dangerous: continue
                if b.thrown_by is not opponent: continue
                dist = math.hypot(b.x - me.x, b.y - me.y)
                if dist < 40 and random.random() < 0.25:   # 가까울 때 25%
                    me.try_roll()
                    break

        if me.held:
            # ── 공 소지: 조준 후 던지기 ──────────────────
            dx = opponent.x - me.x
            dy = opponent.y - me.y
            n  = math.hypot(dx, dy)
            if n > 0:
                me.facing = (dx / n, dy / n)
            me.ext_dx = 0.0;  me.ext_dy = 0.0

            self._throw_timer -= dt
            if self._throw_timer <= 0:
                me.try_throw(spin_override=0.0)
                # 다음 던지기까지 0.5~1.2초 대기
                self._throw_timer = random.uniform(0.5, 1.2)
        else:
            # ── 공 없음: 가장 가까운 루즈 볼로 이동 ──────
            # 가끔 (15%) 잠깐 엉뚱한 방향으로 이동
            self._wander_t -= dt
            if self._wander_t <= 0:
                if random.random() < 0.15:
                    angle = random.uniform(0, math.tau)
                    self._wander_dx = math.cos(angle)
                    self._wander_dy = math.sin(angle)
                    self._wander_t  = random.uniform(0.3, 0.6)
                else:
                    self._wander_dx = 0.0
                    self._wander_dy = 0.0
                    self._wander_t  = random.uniform(0.5, 1.0)

            if self._wander_dx != 0 or self._wander_dy != 0:
                me.ext_dx = self._wander_dx
                me.ext_dy = self._wander_dy
            else:
                loose = [b for b in balls
                         if b.state == LOOSE and b.z < 10 and not b.is_dangerous]
                if loose:
                    tgt = min(loose, key=lambda b: math.hypot(b.x-me.x, b.y-me.y))
                    dx  = tgt.x - me.x
                    dy  = tgt.y - me.y
                    n   = math.hypot(dx, dy)
                    if n > 1:
                        me.ext_dx = dx / n
                        me.ext_dy = dy / n
                    else:
                        me.ext_dx = 0.0;  me.ext_dy = 0.0
                else:
                    me.ext_dx = 0.0;  me.ext_dy = 0.0