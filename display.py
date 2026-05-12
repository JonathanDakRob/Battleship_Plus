import pygame
from config import WINDOW_HEIGHT, WINDOW_WIDTH

# ------------------ INIT ------------------
pygame.mixer.pre_init(
    frequency=44100,
    size=-16,
    channels=2,
    buffer=4096
)
pygame.init() # Initialize pygame
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Battleship Game")
clock = pygame.time.Clock()