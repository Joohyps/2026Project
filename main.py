"""
Battle Ball — 1v1
엔트리 포인트: python main.py
"""

import sys
import pygame
from settings import WIDTH, HEIGHT, FPS
from game import Game


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Battle Ball — 1v1")
    clock  = pygame.time.Clock()
    game   = Game(screen)

    while True:
        # dt: 최대 0.05s 클램프 → 프레임 드랍 시 물리 폭발 방지
        dt = min(clock.tick(FPS) / 1000.0, 0.05)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            game.handle_event(event)

        game.update(dt)
        game.draw()
        pygame.display.flip()


if __name__ == "__main__":
    main()
