"""
Battle Ball — 1v1  |  ball.py
공 클래스 — z축 포물선 물리, 그림자 분리 렌더링
"""

import math
import pygame
from settings import (
    CX1, CX2, CY1, CY2, B_RADIUS,
    GRAVITY, THROW_SPD, THROW_VZ, BOUNCE_K, ROLL_DAMP,
    C_BALL, C_BALLD, C_SHADOW,
)

# Ball states
LOOSE  = "loose"
HELD   = "held"
THROWN = "thrown"


class Ball:
    """
    x, y  : 2-D game-world position (used for collision detection)
    z     : height above ground (purely visual)

    렌더링:  screen_y = y - z   (공이 높을수록 화면 위로 올라감)
    그림자:  항상 (x, y) 고정   (공과 그림자가 멀어질수록 높이 느낌)
    """

    def __init__(self, x: float, y: float, bid: int):
        self.bid = bid
        self.x   = float(x)
        self.y   = float(y)
        self.z   = 0.0

        self.vx  = 0.0
        self.vy  = 0.0
        self.vz  = 0.0        # upward velocity

        self.state     = LOOSE
        self.owner     = None  # Player reference when HELD
        self.thrown_by = None  # Player reference for hit detection

    # ── Throw ────────────────────────────────────────────────────────────────

    def throw(self, dx: float, dy: float):
        """
        dx, dy : unit direction vector (already normalised by caller)
        포물선 발사: vz = THROW_VZ, 수평 속도 = THROW_SPD
        """
        self.state     = THROWN
        self.vx        = dx * THROW_SPD
        self.vy        = dy * THROW_SPD * 0.38   # y방향은 약간 줄임
        self.vz        = THROW_VZ
        self.owner     = None

    # ── Update ───────────────────────────────────────────────────────────────

    def update(self, dt: float):
        if self.state == HELD:
            return  # 위치는 Player.update()에서 제어

        # 수직 (z축) — 중력 적용
        self.vz -= GRAVITY * dt
        self.z  += self.vz  * dt

        # 수평 이동
        self.x += self.vx * dt
        self.y += self.vy * dt

        # 벽 반사
        if self.x < CX1 + B_RADIUS:
            self.x  = CX1 + B_RADIUS
            self.vx = abs(self.vx) * 0.55
        if self.x > CX2 - B_RADIUS:
            self.x  = CX2 - B_RADIUS
            self.vx = -abs(self.vx) * 0.55
        if self.y < CY1 + B_RADIUS:
            self.y  = CY1 + B_RADIUS
            self.vy = abs(self.vy) * 0.55
        if self.y > CY2 - B_RADIUS:
            self.y  = CY2 - B_RADIUS
            self.vy = -abs(self.vy) * 0.55

        # 착지 처리
        if self.z <= 0.0:
            self.z = 0.0
            if self.state == THROWN:
                # 던진 공은 착지 즉시 LOOSE (명중 판정 기회 끝)
                self.state     = LOOSE
                self.thrown_by = None
                if abs(self.vz) > 90:
                    self.vz = -self.vz * BOUNCE_K
                else:
                    self.vz = 0.0
            elif self.state == LOOSE:
                if abs(self.vz) > 50:
                    self.vz = -self.vz * BOUNCE_K
                else:
                    self.vz = 0.0
                    # 굴림 감쇠
                    spd = math.hypot(self.vx, self.vy)
                    if spd > 3:
                        f = max(0.0, 1.0 - ROLL_DAMP * dt)
                        self.vx *= f
                        self.vy *= f
                    else:
                        self.vx = 0.0
                        self.vy = 0.0

    # ── Draw ─────────────────────────────────────────────────────────────────

    def draw_shadow(self, screen):
        """그라운드 그림자 — 게임 좌표 (x, y) 위치에 고정."""
        sx = int(self.x)
        sy = int(self.y)
        # 공이 높이 뜰수록 그림자 작아짐
        sr = max(3, int(B_RADIUS * max(0.25, 1.0 - self.z * 0.007)))
        pygame.draw.ellipse(screen, C_SHADOW,
                            (sx - sr, sy - sr // 2 + 2, sr * 2, sr))

    def draw(self, screen):
        """공 본체 — screen_y = y - z 로 높이 표현."""
        sx  = int(self.x)
        sy  = int(self.y)
        bsy = sy - int(self.z)   # 핵심: z만큼 위로 올라감

        # 공과 그림자 사이 점선 (고도 시각화)
        if self.z > 15:
            step = max(8, int(self.z / 4))
            for h in range(step, int(self.z), step):
                pygame.draw.circle(screen, (50, 82, 50), (sx, sy - h), 1)

        # 공 본체 (높을수록 약간 크게 → 더욱 입체감)
        scale = 1.0 + self.z * 0.0007
        r = max(5, int(B_RADIUS * scale))

        pygame.draw.circle(screen, C_BALLD, (sx, bsy + 2), r)   # 아랫면 그림자
        pygame.draw.circle(screen, C_BALL,  (sx, bsy),     r)   # 메인 색상
        # 스펙큘러 하이라이트
        hl_r = max(2, r // 3)
        pygame.draw.circle(screen, (255, 130, 130),
                           (sx - r // 3, bsy - r // 3), hl_r)

    # ── Utility ──────────────────────────────────────────────────────────────

    def dist_sq(self, px: float, py: float) -> float:
        """2D 거리의 제곱 (충돌 판정에 사용)."""
        return (self.x - px) ** 2 + (self.y - py) ** 2
