"""
Battle Ball — 1v1  |  game.py
게임 로직: PvP / vs 봇  +  폭탄 시스템
"""

import math
import random
import pygame
from settings import (
    WIDTH, HEIGHT, MID_X,
    CX1, CX2, CY1, CY2, CW, CH, N_BALLS,
    P_RADIUS, B_RADIUS, PICKUP_R, HIT_Z_MAX,
    GAME_SECS, P1_START, P2_START,
    C_P1, C_P1D, C_P2, C_P2D,
    C_SCORE1, C_SCORE2, C_TIMER, C_GOLD, C_WHITE,
    w2s, persp_z_scale,
)
from court   import Court
from player  import Player, ALIVE, KNOCKED, ROLLING
from ball    import Ball, Bomb, LOOSE, HELD, THROWN
from effects import Effects
from bot     import ScriptedBot

MENU = "menu"
PLAY = "play"
OVER = "over"

BOMB_RESPAWN = 10.0   # 폭탄 재등장 간격 (초)


class Game:
    def __init__(self, screen, mode: str = 'pvp'):
        self.screen = screen
        self.mode   = mode
        self.court  = Court()
        self.state  = MENU

        self.f_huge = pygame.font.Font(None, 140)
        self.f_big  = pygame.font.Font(None, 110)
        self.f_mid  = pygame.font.Font(None, 72)
        self.f_sm   = pygame.font.Font(None, 36)
        self.f_xs   = pygame.font.Font(None, 27)

        self.bot = None
        self._reset()

    # ── Reset ─────────────────────────────────────────────────────────────────

    def _reset(self):
        k1 = dict(u=pygame.K_w, d=pygame.K_s, l=pygame.K_a, r=pygame.K_d,
                  ls=pygame.K_q, rs=pygame.K_e)
        k2 = dict(u=pygame.K_i, d=pygame.K_k, l=pygame.K_j, r=pygame.K_l,
                  ls=pygame.K_u, rs=pygame.K_o)

        self.p1 = Player(1, *P1_START, k1, C_P1, C_P1D)
        self.p2 = Player(2, *P2_START, k2, C_P2, C_P2D)

        if self.mode == 'bot':
            self.p2.ext_control = True
            self.bot = ScriptedBot()

        self.balls = [
            Ball(CX1 + CW * 0.18, CY1 + (CY2-CY1) * 0.28, 0),
            Ball(CX1 + CW * 0.18, CY1 + (CY2-CY1) * 0.72, 1),
            Ball(CX1 + CW * 0.82, CY1 + (CY2-CY1) * 0.28, 2),
            Ball(CX1 + CW * 0.82, CY1 + (CY2-CY1) * 0.72, 3),
        ]
        self.timer  = float(GAME_SECS)
        self.winner = None
        self.fx     = Effects()

        self._next_bid       = 1000
        self._bomb_timer     = BOMB_RESPAWN   # 첫 폭탄 등장까지 대기

    # ── Events ────────────────────────────────────────────────────────────────

    def handle_event(self, ev):
        if ev.type != pygame.KEYDOWN:
            return
        k = ev.key
        if self.state == MENU:
            if k == pygame.K_SPACE: self.state = PLAY
        elif self.state == PLAY:
            if k == pygame.K_LSHIFT: self._action(self.p1)
            if k == pygame.K_SLASH and self.mode == 'pvp':
                self._action(self.p2)
            if k == pygame.K_TAB:  self.p1.try_roll()
            if k == pygame.K_p and self.mode == 'pvp':
                self.p2.try_roll()
            if k == pygame.K_ESCAPE: self.state = MENU
        elif self.state == OVER:
            if k == pygame.K_SPACE:
                self._reset(); self.state = PLAY
            if k == pygame.K_ESCAPE:
                self._reset(); self.state = MENU

    def _action(self, p: Player):
        if p.held: p.try_throw()
        else:      self._pickup(p)

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self, dt: float):
        if self.state != PLAY:
            return

        pr = pygame.key.get_pressed()
        self.p1.update(dt, pr)

        if self.mode == 'bot' and self.bot:
            self.bot.update(dt, self.p2, self.p1, self.balls)
            self.p2.update(dt, pr)
        else:
            self.p2.update(dt, pr)

        for b in self.balls: b.update(dt)

        # ── 폭탄 스폰 ──
        has_bomb = any(isinstance(b, Bomb) for b in self.balls)
        if not has_bomb:
            self._bomb_timer -= dt
            if self._bomb_timer <= 0:
                self._spawn_bomb()
                self._bomb_timer = BOMB_RESPAWN

        # ── 폭발 이펙트 생성 ──
        for b in self.balls:
            if isinstance(b, Bomb) and b.exploded and not b.explosion_spawned:
                sx, sy = w2s(b.x, b.y)
                self.fx.spawn_explosion(sx, sy)
                b.explosion_spawned = True

        self._check_hits()
        self._auto_pickup()

        # 폭발한 폭탄 제거
        self.balls = [b for b in self.balls
                      if not (isinstance(b, Bomb) and b.exploded)]

        self.fx.update(dt)
        self.timer = max(0.0, self.timer - dt)
        if self.timer == 0.0: self._end()

    # ── 게임 로직 ─────────────────────────────────────────────────────────────

    def _pickup(self, p: Player):
        if p.state in (KNOCKED, ROLLING): return
        best, bd = None, PICKUP_R ** 2
        for b in self.balls:
            if b.state == LOOSE and b.z < 8 and not b.is_dangerous:
                d = b.dist_sq(p.x, p.y)
                if d < bd: bd = d; best = b
        if best:
            best.state = HELD; best.owner = p; p.held = best

    def _auto_pickup(self):
        for p in (self.p1, self.p2):
            if p.held or p.state in (KNOCKED, ROLLING): continue
            for b in self.balls:
                if b.state != LOOSE or b.z >= 8: continue
                if b.is_dangerous: continue
                if b.dist_sq(p.x, p.y) < PICKUP_R ** 2:
                    b.state = HELD; b.owner = p; p.held = b; break

    def _check_hits(self):
        # ── 일반 공 직접 명중 ──
        for b in self.balls:
            if isinstance(b, Bomb): continue
            if not b.is_dangerous:  continue
            thrower = b.thrown_by
            target  = self.p2 if thrower is self.p1 else self.p1
            if target.state != ALIVE: continue
            if (math.hypot(b.x-target.x, b.y-target.y) < B_RADIUS + P_RADIUS
                    and b.z < HIT_Z_MAX):
                thrower.score += 1
                sx, sy = w2s(b.x, b.y)
                self.fx.spawn_hit(sx, sy - int(b.z * persp_z_scale(b.y)))
                target.get_hit()
                b.thrown_by = None;  b.state = LOOSE
                b.vx *= 0.25;  b.vy *= 0.25;  b.vz = 120.0

        # ── 폭탄 폭발 범위 피해 ──
        for b in self.balls:
            if not isinstance(b, Bomb): continue
            if not b.exploded:          continue
            for p in (self.p1, self.p2):
                if p.state != ALIVE: continue
                if math.hypot(p.x - b.x, p.y - b.y) < b.explosion_radius:
                    # 던진 사람과 무관하게 양쪽 모두 피해 가능
                    opponent = self.p2 if p is self.p1 else self.p1
                    opponent.score += 1
                    sx, sy = w2s(p.x, p.y)
                    self.fx.spawn_hit(sx, sy)
                    p.get_hit()

    def _end(self):
        self.state = OVER
        if   self.p1.score > self.p2.score: self.winner = 1
        elif self.p2.score > self.p1.score: self.winner = 2
        else:                               self.winner = 0

    def _spawn_bomb(self):
        """플레이어에게서 150px 이상 떨어진 랜덤 위치에 폭탄 소환."""
        for _ in range(50):
            x = random.uniform(CX1 + 80, CX2 - 80)
            y = random.uniform(CY1 + 80, CY2 - 80)
            if (math.hypot(x-self.p1.x, y-self.p1.y) > 150
                    and math.hypot(x-self.p2.x, y-self.p2.y) > 150):
                break
        self.balls.append(Bomb(x, y, self._next_bid))
        self._next_bid += 1

    # ── Draw ──────────────────────────────────────────────────────────────────

    def draw(self):
        if self.state == MENU: self._draw_menu(); return
        self._draw_game()
        if self.state == OVER: self._draw_over()

    def _draw_game(self):
        self.court.draw(self.screen)
        self.fx.draw_center(self.screen)

        loose = [b for b in self.balls if b.state != HELD]
        held  = [b for b in self.balls if b.state == HELD]
        ents  = sorted([self.p1, self.p2] + loose, key=lambda e: e.y)

        for e in ents:  e.draw_shadow(self.screen)
        for b in held:  b.draw_shadow(self.screen)
        for e in ents:  e.draw(self.screen)
        for b in held:  b.draw(self.screen)

        self.fx.draw(self.screen)
        self._hud()

    def _hud(self):
        s1 = self.f_big.render(str(self.p1.score), True, C_SCORE1)
        self.screen.blit(s1, (55, 8))
        s2 = self.f_big.render(str(self.p2.score), True, C_SCORE2)
        self.screen.blit(s2, s2.get_rect(right=WIDTH-55, top=8))

        m, s = divmod(int(self.timer), 60)
        tc = (255, 70, 70) if self.timer < 10 else C_TIMER
        ts = self.f_mid.render(f"{m}:{s:02d}", True, tc)
        self.screen.blit(ts, ts.get_rect(centerx=WIDTH//2, top=10))

        # 폭탄 소지 경고
        for p, x in [(self.p1, 55), (self.p2, WIDTH-110)]:
            if p.held and isinstance(p.held, Bomb):
                b = p.held
                if b.armed:
                    frac    = max(0, b.timer / b.explosion_radius * 10)
                    warn_c  = (255, 80, 80) if int(pygame.time.get_ticks()/150)%2 else (255,200,0)
                    txt = self.f_xs.render(
                        f"💣 {b.timer:.1f}s", True, warn_c)
                else:
                    txt = self.f_xs.render("💣 BOMB", True, (255, 200, 0))
                self.screen.blit(txt, (x, 90))

        if self.mode == 'bot':
            lbl = self.f_xs.render("BOT", True, C_SCORE2)
            self.screen.blit(lbl, lbl.get_rect(right=WIDTH-55, top=118))

        if self.mode == 'pvp':
            hint = "P1: WASD LShift 던지기 Tab 구르기 Q/E 스핀   P2: IJKL / 던지기 P 구르기 U/O 스핀   ESC 메뉴"
        else:
            hint = "P1: WASD LShift 던지기 Tab 구르기 Q/E 스핀     ESC 메뉴"
        h = self.f_xs.render(hint, True, (130, 130, 130))
        self.screen.blit(h, h.get_rect(centerx=WIDTH//2, bottom=HEIGHT-4))

    def _draw_menu(self):
        self.screen.fill((10, 22, 10))
        t = self.f_huge.render("BATTLE  BALL", True, C_GOLD)
        self.screen.blit(t, t.get_rect(centerx=WIDTH//2, centery=HEIGHT//2-100))
        sub = self.f_sm.render("1 v 1  피구 게임  +  💣 폭탄", True, C_WHITE)
        self.screen.blit(sub, sub.get_rect(centerx=WIDTH//2, centery=HEIGHT//2-15))

        if self.mode == 'bot':
            rows = [
                ("Player 1", "WASD 이동  LShift 던지기  Tab 구르기  Q/E 스핀", C_SCORE1),
                ("Player 2", "BOT (자동 조종)", C_SCORE2),
            ]
        else:
            rows = [
                ("Player 1", "WASD 이동  LShift 던지기  Tab 구르기  Q/E 스핀", C_SCORE1),
                ("Player 2", "IJKL 이동     / 던지기    P 구르기   U/O 스핀", C_SCORE2),
            ]
        for i, (label, ctrl, col) in enumerate(rows):
            lbl = self.f_xs.render(label, True, col)
            ctl = self.f_xs.render(ctrl,  True, C_WHITE)
            cy  = HEIGHT//2 + 48 + i*30
            self.screen.blit(lbl, lbl.get_rect(right=WIDTH//2-8,  centery=cy))
            self.screen.blit(ctl, ctl.get_rect(left=WIDTH //2+8,  centery=cy))

        bomb_hint = self.f_xs.render(
            "💣 폭탄: 착지 후 2.5초 뒤 폭발 — 범위 안에 있으면 사망  /  들고 있어도 폭발!",
            True, (200, 150, 50))
        self.screen.blit(bomb_hint, bomb_hint.get_rect(centerx=WIDTH//2, centery=HEIGHT//2+110))

        go = self.f_sm.render("SPACE  to start", True, C_GOLD)
        self.screen.blit(go, go.get_rect(centerx=WIDTH//2, centery=HEIGHT//2+148))

    def _draw_over(self):
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 168))
        self.screen.blit(ov, (0, 0))
        msgs = {0: ("DRAW!", C_WHITE),
                1: ("PLAYER 1  WINS!", C_SCORE1),
                2: ("PLAYER 2  WINS!", C_SCORE2)}
        msg, c = msgs[self.winner]
        wt = self.f_big.render(msg, True, c)
        self.screen.blit(wt, wt.get_rect(centerx=WIDTH//2, centery=HEIGHT//2-55))
        sc = self.f_sm.render(f"P1  {self.p1.score}  —  {self.p2.score}  P2", True, C_WHITE)
        self.screen.blit(sc, sc.get_rect(centerx=WIDTH//2, centery=HEIGHT//2+28))
        rs = self.f_xs.render("Space 재시작   ESC 메뉴", True, (195, 195, 195))
        self.screen.blit(rs, rs.get_rect(centerx=WIDTH//2, centery=HEIGHT//2+88))