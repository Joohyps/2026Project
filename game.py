"""
Battle Ball — 1v1  |  game.py
게임 로직: 상태머신, Y-sort 렌더링, 충돌 판정, HUD
"""

import math
import pygame
from settings import (
    WIDTH, HEIGHT, MID_X,
    CX1, CX2, CY1, CY2,
    P_RADIUS, B_RADIUS, PICKUP_R, HIT_Z_MAX,
    GAME_SECS,
    P1_START, P2_START, N_BALLS, CW, CH,
    C_P1, C_P1D, C_P2, C_P2D,
    C_SCORE1, C_SCORE2, C_TIMER, C_GOLD, C_WHITE,
)
from court   import Court
from player  import Player, ALIVE, KNOCKED, BLINK
from ball    import Ball, LOOSE, HELD, THROWN
from effects import Effects

# Game states
MENU = "menu"
PLAY = "play"
OVER = "over"


class Game:
    def __init__(self, screen):
        self.screen  = screen
        self.court   = Court()
        self.state   = MENU

        # Fonts
        self.f_huge  = pygame.font.Font(None, 140)
        self.f_big   = pygame.font.Font(None, 110)
        self.f_mid   = pygame.font.Font(None, 72)
        self.f_sm    = pygame.font.Font(None, 36)
        self.f_xs    = pygame.font.Font(None, 27)

        self._reset()

    # ── Initialise / Reset ───────────────────────────────────────────────────

    def _reset(self):
        # Player 1: WASD + Space
        k1 = dict(u=pygame.K_w, d=pygame.K_s,
                  l=pygame.K_a, r=pygame.K_d)
        # Player 2: IJKL + U
        k2 = dict(u=pygame.K_i, d=pygame.K_k,
                  l=pygame.K_j, r=pygame.K_l)

        self.p1 = Player(1, *P1_START, k1, C_P1, C_P1D)
        self.p2 = Player(2, *P2_START, k2, C_P2, C_P2D)

        # Balls — 2 on each half
        self.balls = []
        starts = [
            (CX1 + CW * 0.18, CY1 + CH * 0.28),
            (CX1 + CW * 0.18, CY1 + CH * 0.72),
            (CX1 + CW * 0.82, CY1 + CH * 0.28),
            (CX1 + CW * 0.82, CY1 + CH * 0.72),
        ]
        for i, (bx, by) in enumerate(starts[:N_BALLS]):
            self.balls.append(Ball(bx, by, i))

        self.timer  = float(GAME_SECS)
        self.winner = None
        self.fx     = Effects()

    # ── Event handling ───────────────────────────────────────────────────────

    def handle_event(self, ev):
        if ev.type != pygame.KEYDOWN:
            return
        k = ev.key

        if self.state == MENU:
            if k == pygame.K_SPACE:
                self.state = PLAY

        elif self.state == PLAY:
            if k == pygame.K_SPACE:
                self._action(self.p1)
            if k == pygame.K_u:
                self._action(self.p2)
            if k == pygame.K_ESCAPE:
                self.state = MENU

        elif self.state == OVER:
            if k == pygame.K_SPACE:
                self._reset()
                self.state = PLAY
            if k == pygame.K_ESCAPE:
                self._reset()
                self.state = MENU

    def _action(self, p: Player):
        """Space / U 키 — 공을 갖고 있으면 던지기, 없으면 줍기 시도."""
        if p.held:
            p.try_throw()
        else:
            self._try_pickup(p)

    # ── Update ───────────────────────────────────────────────────────────────

    def update(self, dt: float):
        if self.state != PLAY:
            return

        pressed = pygame.key.get_pressed()
        self.p1.update(dt, pressed)
        self.p2.update(dt, pressed)

        for b in self.balls:
            b.update(dt)

        self._auto_pickup()
        self._check_hits()
        self.fx.update(dt)

        self.timer = max(0.0, self.timer - dt)
        if self.timer == 0.0:
            self._end_match()

    # ── Pickup ───────────────────────────────────────────────────────────────

    def _try_pickup(self, p: Player):
        if p.state == KNOCKED:
            return
        best, best_d = None, PICKUP_R ** 2
        for b in self.balls:
            if b.state == LOOSE and b.z < 8:
                d = b.dist_sq(p.x, p.y)
                if d < best_d:
                    best_d = d
                    best   = b
        if best:
            best.state = HELD
            best.owner = p
            p.held     = best

    def _auto_pickup(self):
        """플레이어가 루즈 볼 위를 걸어가면 자동으로 줍기."""
        for p in [self.p1, self.p2]:
            if p.held or p.state == KNOCKED:
                continue
            for b in self.balls:
                if b.state != LOOSE or b.z >= 8:
                    continue
                if b.dist_sq(p.x, p.y) < PICKUP_R ** 2:
                    b.state = HELD
                    b.owner = p
                    p.held  = b
                    break

    # ── Hit detection ────────────────────────────────────────────────────────

    def _check_hits(self):
        for b in self.balls:
            if b.state != THROWN or b.thrown_by is None:
                continue
            thrower = b.thrown_by
            target  = self.p2 if thrower is self.p1 else self.p1

            if target.state != ALIVE:
                continue
            dist = math.hypot(b.x - target.x, b.y - target.y)
            if dist < B_RADIUS + P_RADIUS and b.z < HIT_Z_MAX:
                # ── 명중! ──
                thrower.score += 1
                # 파티클: 공의 화면 위치 (z 적용)
                self.fx.spawn_hit(b.x, b.y - b.z)
                target.get_hit()
                # 볼은 LOOSE로 전환
                b.state     = LOOSE
                b.thrown_by = None
                b.vx *= 0.25
                b.vy *= 0.25
                b.vz  = 120.0

    # ── Match end ────────────────────────────────────────────────────────────

    def _end_match(self):
        self.state = OVER
        if   self.p1.score > self.p2.score: self.winner = 1
        elif self.p2.score > self.p1.score: self.winner = 2
        else:                               self.winner = 0

    # ── Draw ─────────────────────────────────────────────────────────────────

    def draw(self):
        if self.state == MENU:
            self._draw_menu()
            return
        self._draw_game()
        if self.state == OVER:
            self._draw_over()

    def _draw_game(self):
        # 1. 코트 배경 (정적, pre-rendered)
        self.court.draw(self.screen)

        # 2. 중앙선
        self.fx.draw_center(self.screen)

        # 3. Y-sort: 모든 엔티티를 y 좌표 기준 정렬
        loose_balls  = [b for b in self.balls if b.state != HELD]
        held_balls   = [b for b in self.balls if b.state == HELD]
        entities     = [self.p1, self.p2] + loose_balls
        entities.sort(key=lambda e: e.y)

        # 4. 그림자 레이어 (엔티티 아래)
        for e in entities:
            if isinstance(e, Ball):
                e.draw_shadow(self.screen)
            else:
                e.draw_shadow(self.screen)
        for b in held_balls:
            b.draw_shadow(self.screen)

        # 5. 엔티티 레이어 (Y-sorted)
        for e in entities:
            e.draw(self.screen)
        for b in held_balls:
            b.draw(self.screen)

        # 6. 파티클 이펙트
        self.fx.draw(self.screen)

        # 7. HUD
        self._draw_hud()

    def _draw_hud(self):
        # ── 점수 ──
        s1 = self.f_big.render(str(self.p1.score), True, C_SCORE1)
        self.screen.blit(s1, (CX1 + 10, 4))

        s2 = self.f_big.render(str(self.p2.score), True, C_SCORE2)
        r2 = s2.get_rect(right=CX2 - 10, top=4)
        self.screen.blit(s2, r2)

        # ── 타이머 ──
        mins, secs = divmod(int(self.timer), 60)
        t_str = f"{mins}:{secs:02d}"
        # 10초 이하: 빨간색
        tc = (255, 80, 80) if self.timer < 10 else C_TIMER
        ts = self.f_mid.render(t_str, True, tc)
        self.screen.blit(ts, ts.get_rect(centerx=WIDTH // 2, top=8))

        # ── 조작 안내 (하단) ──
        hint = self.f_xs.render(
            "P1: WASD + Space (throw)     P2: IJKL + U (throw)     ESC: menu",
            True, (148, 148, 148))
        self.screen.blit(hint, hint.get_rect(centerx=WIDTH // 2, bottom=HEIGHT - 4))

    def _draw_menu(self):
        self.screen.fill((12, 26, 12))

        # 타이틀
        t = self.f_huge.render("BATTLE  BALL", True, C_GOLD)
        self.screen.blit(t, t.get_rect(centerx=WIDTH // 2, centery=HEIGHT // 2 - 100))

        sub = self.f_sm.render("1 v 1 피구 게임", True, C_WHITE)
        self.screen.blit(sub, sub.get_rect(centerx=WIDTH // 2, centery=HEIGHT // 2 - 18))

        # 조작 안내
        c1 = self.f_xs.render("Player 1   W A S D  to move    Space  to pick up / throw", True, C_SCORE1)
        self.screen.blit(c1, c1.get_rect(centerx=WIDTH // 2, centery=HEIGHT // 2 + 45))

        c2 = self.f_xs.render("Player 2   I J K L  to move       U   to pick up / throw", True, C_SCORE2)
        self.screen.blit(c2, c2.get_rect(centerx=WIDTH // 2, centery=HEIGHT // 2 + 75))

        go = self.f_sm.render("Press  SPACE  to start", True, C_GOLD)
        self.screen.blit(go, go.get_rect(centerx=WIDTH // 2, centery=HEIGHT // 2 + 135))

    def _draw_over(self):
        # 반투명 오버레이
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 168))
        self.screen.blit(ov, (0, 0))

        msg_map = {
            0: ("DRAW!",           C_WHITE),
            1: ("PLAYER 1  WINS!", C_SCORE1),
            2: ("PLAYER 2  WINS!", C_SCORE2),
        }
        msg, c = msg_map[self.winner]
        wt = self.f_big.render(msg, True, c)
        self.screen.blit(wt, wt.get_rect(centerx=WIDTH // 2, centery=HEIGHT // 2 - 55))

        sc = self.f_sm.render(
            f"  P1  {self.p1.score}   —   {self.p2.score}  P2  ", True, C_WHITE)
        self.screen.blit(sc, sc.get_rect(centerx=WIDTH // 2, centery=HEIGHT // 2 + 28))

        rs = self.f_xs.render("Space to restart   ESC for menu", True, (195, 195, 195))
        self.screen.blit(rs, rs.get_rect(centerx=WIDTH // 2, centery=HEIGHT // 2 + 88))
