"""
Battle Ball — 1v1  |  court.py
코트 렌더러 — 잔디, 나무 울타리, 배경 (정적 사전 렌더링)
"""

import random
import pygame
from settings import (
    WIDTH, HEIGHT,
    CX1, CX2, CY1, CY2, CW, CH, WALL_V,
    C_BG, C_GRASS, C_GRASS2,
    C_FENCE, C_FENCE_F, C_FENCE_T,
)


class Court:
    """
    __init__()에서 정적 배경을 한 번만 렌더링하고 Surface에 저장.
    draw()는 해당 Surface를 blit하기만 함 → 매 프레임 비용 최소화.
    """

    def __init__(self):
        self._surf = pygame.Surface((WIDTH, HEIGHT))
        self._build()

    # ── Pre-render ───────────────────────────────────────────────────────────

    def _build(self):
        s = self._surf
        s.fill(C_BG)
        self._draw_bg_trees(s)
        self._draw_grass(s)
        self._draw_fence(s)

    def _draw_bg_trees(self, s):
        """코트 바깥 영역에 나무 배치."""
        rng = random.Random(42)   # 고정 시드 → 항상 같은 배경
        for _ in range(38):
            tx = rng.randint(10, WIDTH - 10)
            ty = rng.randint(10, HEIGHT - 10)
            # 코트 안쪽은 건너뜀
            if CX1 - 55 < tx < CX2 + 55 and CY1 - 55 < ty < CY2 + 55:
                continue
            tr = rng.randint(13, 30)
            g  = rng.randint(42, 85)
            c_crown  = (10 + rng.randint(0, 12), g,      8  + rng.randint(0, 10))
            c_shade  = (8  + rng.randint(0, 8),  g - 22, 6  + rng.randint(0, 6))
            c_trunk  = (55 + rng.randint(0, 15), 32 + rng.randint(0, 10), 8)
            # 나무 줄기
            pygame.draw.rect(s, c_trunk,
                             (tx - 3, ty + tr // 3, 6, tr // 2))
            # 나무 그늘
            pygame.draw.circle(s, c_shade, (tx + 3, ty - tr // 3 + 5), tr + 5)
            # 나무 잎
            pygame.draw.circle(s, c_crown, (tx, ty - tr // 3),          tr)

    def _draw_grass(self, s):
        """교대 색상 세로 줄무늬 잔디 (영상의 잔디 텍스처 재현)."""
        stripe_w = 50
        for i, x in enumerate(range(CX1, CX2, stripe_w)):
            c = C_GRASS if i % 2 == 0 else C_GRASS2
            w = min(stripe_w, CX2 - x)
            pygame.draw.rect(s, c, (x, CY1, w, CH))

    def _draw_fence(self, s):
        """
        나무 울타리 — 상단보다 하단이 밝고 두드러짐
        (아래쪽이 '앞'에 있는 느낌 → Pseudo-3D 깊이감)
        """
        wt = WALL_V

        # ── 하단 벽 (앞쪽, 밝게) ──────────────────────
        # 위쪽 면 (보이는 상판)
        pygame.draw.rect(s, C_FENCE_T,
                         (CX1 - wt, CY2, CW + wt * 2, wt))
        # 앞면 (가장 밝음)
        pygame.draw.rect(s, C_FENCE_F,
                         (CX1 - wt, CY2 + wt, CW + wt * 2, wt // 2 + 4))
        # 경계선
        pygame.draw.rect(s, C_FENCE,
                         (CX1, CY2 - 3, CW, 5))

        # ── 상단 벽 (뒤쪽, 어둡게) ───────────────────
        pygame.draw.rect(s, C_FENCE,
                         (CX1 - wt, CY1 - wt, CW + wt * 2, wt))
        pygame.draw.rect(s, C_FENCE_T,
                         (CX1,      CY1 - 2,  CW, 4))

        # ── 좌측 벽 ──────────────────────────────────
        pygame.draw.rect(s, C_FENCE,
                         (CX1 - wt, CY1 - wt, wt, CH + wt * 2))
        pygame.draw.rect(s, C_FENCE_F,
                         (CX1 - 4,  CY1,      5,  CH))

        # ── 우측 벽 ──────────────────────────────────
        pygame.draw.rect(s, C_FENCE,
                         (CX2, CY1 - wt, wt, CH + wt * 2))
        pygame.draw.rect(s, C_FENCE_F,
                         (CX2,      CY1, 5, CH))

        # ── 울타리 기둥 ───────────────────────────────
        post_gap = 52
        post_w   = 9

        for px in range(CX1, CX2 + post_gap, post_gap):
            # 하단
            pygame.draw.rect(s, C_FENCE_F,
                             (px - post_w // 2, CY2, post_w, wt + 4))
            # 상단
            pygame.draw.rect(s, C_FENCE_T,
                             (px - post_w // 2, CY1 - wt, post_w, wt))

        for py in range(CY1, CY2 + post_gap, post_gap):
            # 좌측
            pygame.draw.rect(s, C_FENCE_T,
                             (CX1 - wt, py - post_w // 2, wt, post_w))
            # 우측
            pygame.draw.rect(s, C_FENCE_T,
                             (CX2, py - post_w // 2, wt, post_w))

        # ── 코너 강조 ─────────────────────────────────
        cs = wt + 6
        for cx, cy in [(CX1, CY1), (CX2, CY1), (CX1, CY2), (CX2, CY2)]:
            pygame.draw.rect(s, C_FENCE_T,
                             (cx - cs // 2, cy - cs // 2, cs, cs))

    # ── Draw ─────────────────────────────────────────────────────────────────

    def draw(self, screen):
        screen.blit(self._surf, (0, 0))
