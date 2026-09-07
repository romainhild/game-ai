"""Entry point: window, clock, and (later) the scene stack."""

from __future__ import annotations

import pygame

WINDOW_SIZE = (800, 600)
BG_COLOR = (24, 24, 28)
FPS = 60


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode(WINDOW_SIZE)
    pygame.display.set_caption("AI RPG")
    clock = pygame.time.Clock()

    running = True
    while running:
        for event in pygame.event.get():
            if (
                event.type == pygame.QUIT
                or event.type == pygame.KEYDOWN
                and event.key == pygame.K_ESCAPE
            ):
                running = False

        screen.fill(BG_COLOR)
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
