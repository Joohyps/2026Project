"""
Battle Ball — 1v1  |  court.py
원근 투영 코트 렌더러
"""

import random
import pygame
from settings import (
    WIDTH, HEIGHT,
    CX1, CX2, CY1, CY2, CW, CH, MID_X, FENCE_D,
    C_BG, C_GRASS, C_GRASS2,
    C_FENCE, C_FENCE_F, C_FENCE_T,
    w2s,
)


class Court:
    """
        원근 투영 기반 경기장 렌더

        - 생성 시 배경을 한 번만 그려 Surface에 저장
        - draw() 호출 시 저장된 Surface만 출력하여 렌더링 비용 최소화
        - settings.py의 w2s() 원근 투영 함수를 사용하여 사다리꼴 경기장을 표현

        속성:
        - _surf : 미리 렌더링된 코트 배경 Surface

        메서드:
        - draw(screen)      : 코트를 화면에 렌더링
        - _build()          : 코트 전체 배경 생성
        - _draw_bg(s)       : 배경 장식(나무) 생성
        - _draw_grass(s)    : 경기장 잔디 및 줄무늬 생성
        - _draw_fence(s)    : 경기장 울타리 및 경계선 생성
        """
    def __init__(self):
        self._surf = pygame.Surface((WIDTH, HEIGHT))
        self._build()

    def _build(self):
        s = self._surf
        s.fill(C_BG)
        self._draw_bg(s)
        self._draw_grass(s)
        self._draw_fence(s)

    def _draw_bg(self, s):
        rng = random.Random(42)
        for _ in range(45):
            tx = rng.randint(5, WIDTH - 5)
            ty = rng.randint(5, HEIGHT - 5)
            if (CX1 - 70 < tx < CX2 + 70) and (CY1 - 70 < ty < CY2 + 70):
                continue
            tr    = rng.randint(12, 28)
            gv    = rng.randint(40, 80)
            crown = (8 + rng.randint(0, 12), gv,      6 + rng.randint(0, 10))
            shade = (6 + rng.randint(0, 8),  gv - 20, 4)
            trunk = (52 + rng.randint(0, 14), 30 + rng.randint(0, 8), 7)
            pygame.draw.rect(s, trunk, (tx - 3, ty + tr // 3, 6, tr // 2))
            pygame.draw.circle(s, shade, (tx + 3, ty - tr // 3 + 6), tr + 5)
            pygame.draw.circle(s, crown, (tx,     ty - tr // 3),     tr)

    def _draw_grass(self, s):
        field = [w2s(CX1, CY1), w2s(CX2, CY1),
                 w2s(CX2, CY2), w2s(CX1, CY2)]
        pygame.draw.polygon(s, C_GRASS, field)

        sw = 50
        for i, gx in enumerate(range(CX1, CX2, sw)):
            c  = C_GRASS if i % 2 == 0 else C_GRASS2
            x2 = min(gx + sw, CX2)
            pts = [w2s(gx, CY1), w2s(x2, CY1),
                   w2s(x2, CY2), w2s(gx, CY2)]
            pygame.draw.polygon(s, c, pts)

        for i in range(8):
            gy = CY1 + (i + 0.5) * CH / 8
            p1 = w2s(CX1, gy)
            p2 = w2s(CX2, gy)
            pygame.draw.line(s, (38, 84, 36), p1, p2, 1)

    def _draw_fence(self, s):
        fd = FENCE_D

        # 하단 (가장 잘 보임)
        pygame.draw.polygon(s, C_FENCE_F, [
            w2s(CX1,      CY2),
            w2s(CX2,      CY2),
            w2s(CX2 + fd, CY2 + fd),
            w2s(CX1 - fd, CY2 + fd),
        ])
        pygame.draw.polygon(s, C_FENCE_T, [
            w2s(CX1 - fd, CY2 + fd),
            w2s(CX2 + fd, CY2 + fd),
            w2s(CX2 + fd, CY2 + fd + 6),
            w2s(CX1 - fd, CY2 + fd + 6),
        ])

        # 상단 (어두움)
        pygame.draw.polygon(s, C_FENCE_T, [
            w2s(CX1 - fd, CY1 - fd),
            w2s(CX2 + fd, CY1 - fd),
            w2s(CX2,      CY1),
            w2s(CX1,      CY1),
        ])

        # 좌측
        pygame.draw.polygon(s, C_FENCE, [
            w2s(CX1 - fd, CY1 - fd),
            w2s(CX1,      CY1),
            w2s(CX1,      CY2),
            w2s(CX1 - fd, CY2 + fd),
        ])

        # 우측
        pygame.draw.polygon(s, C_FENCE, [
            w2s(CX2,      CY1),
            w2s(CX2 + fd, CY1 - fd),
            w2s(CX2 + fd, CY2 + fd),
            w2s(CX2,      CY2),
        ])

        # 코트 내부 테두리
        pygame.draw.polygon(s, C_FENCE_T,
            [w2s(CX1, CY1), w2s(CX2, CY1),
             w2s(CX2, CY2), w2s(CX1, CY2)], 2)

        # 하단 기둥
        for gx in range(CX1, CX2 + 52, 52):
            pygame.draw.line(s, C_FENCE_T, w2s(gx, CY2), w2s(gx, CY2 + fd), 4)

        # 좌우 기둥
        for gy in range(CY1, CY2 + 52, 52):
            pygame.draw.line(s, C_FENCE_T, w2s(CX1, gy),      w2s(CX1 - fd, gy), 3)
            pygame.draw.line(s, C_FENCE_T, w2s(CX2, gy),      w2s(CX2 + fd, gy), 3)

    def draw(self, screen):
        screen.blit(self._surf, (0, 0))