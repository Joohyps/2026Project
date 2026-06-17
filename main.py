"""
Battle Ball — 1v1  |  main.py
모드 선택: PvP / 사람 vs 봇
"""

import sys
import pygame
from settings import WIDTH, HEIGHT, FPS, C_GOLD, C_WHITE, C_SCORE1, C_SCORE2
from game import Game


def run_menu(screen, clock):
    f_title = pygame.font.Font(None, 110)
    f_mode  = pygame.font.Font(None, 48)
    f_desc  = pygame.font.Font(None, 27)
    f_hint  = pygame.font.Font(None, 24)

    modes = [
        ('1  vs  1   PvP',
         'WASD + LShift   vs   IJKL + /   두 사람이 직접 조종',
         C_SCORE1),
        ('사람  vs  봇',
         'WASD + LShift 로 플레이   오른쪽은 자동 봇',
         C_SCORE2),
    ]
    selected = 0

    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return 'quit'
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_UP, pygame.K_w):
                    selected = (selected - 1) % 2
                if ev.key in (pygame.K_DOWN, pygame.K_s):
                    selected = (selected + 1) % 2
                if ev.key == pygame.K_1: return 'pvp'
                if ev.key == pygame.K_2: return 'bot'
                if ev.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return ['pvp', 'bot'][selected]
                if ev.key == pygame.K_ESCAPE:
                    return 'quit'
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                mx, my = ev.pos
                for i in range(2):
                    ry = 300 + i * 140
                    if WIDTH//2 - 370 < mx < WIDTH//2 + 370 and ry < my < ry + 100:
                        return ['pvp', 'bot'][i]
            if ev.type == pygame.MOUSEMOTION:
                mx, my = ev.pos
                for i in range(2):
                    ry = 300 + i * 140
                    if WIDTH//2 - 370 < mx < WIDTH//2 + 370 and ry < my < ry + 100:
                        selected = i

        screen.fill((8, 18, 8))

        t = f_title.render("BATTLE  BALL", True, C_GOLD)
        screen.blit(t, t.get_rect(centerx=WIDTH // 2, centery=130))
        sub = f_desc.render("1 v 1  피구 게임", True, (130, 130, 130))
        screen.blit(sub, sub.get_rect(centerx=WIDTH // 2, centery=195))

        card_w, card_h = 740, 100
        for i, (title, desc, col) in enumerate(modes):
            ry  = 300 + i * 140
            cx  = WIDTH // 2
            sel = selected == i
            bg  = (16, 35, 16) if sel else (10, 22, 10)
            bc  = col if sel else (45, 65, 45)
            rect = pygame.Rect(cx - card_w//2, ry, card_w, card_h)
            pygame.draw.rect(screen, bg,  rect, border_radius=10)
            pygame.draw.rect(screen, bc,  rect, 2, border_radius=10)
            num = f_mode.render(str(i + 1), True, col)
            screen.blit(num, (cx - card_w//2 + 20, ry + 14))
            tc = C_WHITE if sel else (170, 170, 170)
            screen.blit(f_mode.render(title, True, tc), (cx - card_w//2 + 65, ry + 12))
            dc = (175, 175, 175) if sel else (95, 95, 95)
            screen.blit(f_desc.render(desc, True, dc), (cx - card_w//2 + 65, ry + 62))

        hint = f_hint.render(
            "↑ ↓  또는  1 / 2  선택     Enter  확인     ESC  종료",
            True, (70, 70, 70))
        screen.blit(hint, hint.get_rect(centerx=WIDTH // 2, bottom=HEIGHT - 14))

        clock.tick(60)
        pygame.display.flip()


def run_game(screen, clock, mode: str) -> str:
    game = Game(screen, mode=mode)
    while True:
        dt = min(clock.tick(FPS) / 1000.0, 0.05)
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return 'quit'
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                if game.state in ('play', 'over'):
                    game.state = 'menu'
                else:
                    return 'menu'
            game.handle_event(ev)
        game.update(dt)
        game.draw()
        pygame.display.flip()


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Battle Ball — 1v1")
    clock = pygame.time.Clock()

    while True:
        result = run_menu(screen, clock)
        if result == 'quit': break
        r = run_game(screen, clock, mode=result)
        if r == 'quit': break

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()