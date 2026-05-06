# BATTLESHIP CONIGURATION
import pygame
import os

os.environ['SDL_VIDEO_CENTERED'] = '1' 

GRID_SIZE = 10 # Number of rows and columns on the board
CELL_SIZE = 25 # Shrinks the squares so the window isn't too tall
SHIP_BLOCK_SIZE = CELL_SIZE
LABEL_MARGIN = 20
GRID_PADDING = 40
WINDOW_WIDTH = int(((GRID_SIZE * CELL_SIZE) + (2 * GRID_PADDING)) * 1.67)
WINDOW_HEIGHT = int(WINDOW_WIDTH * 1.3)
END_OF_GRID_X = GRID_PADDING + GRID_SIZE * CELL_SIZE
END_OF_GRID_Y = 2 * END_OF_GRID_X


# Font size for START2P font based on window width for consistency
LARGE_FONT_SIZE = WINDOW_WIDTH // 15
MEDIUM_FONT_SIZE = WINDOW_WIDTH // 20
SMALL_FONT_SIZE = WINDOW_WIDTH // 25

top_grid_y = GRID_PADDING + 10
bottom_grid_y = top_grid_y + (GRID_SIZE * CELL_SIZE) + 30


# Colors
BG_COLOR = (30, 30, 30)
GRID_COLOR = (0, 0, 128)
HOVER_COLOR = (100, 180, 255)
WATER_COLOR =  (35,137,218)
WATER_HOVER_COLOR = (15,94,156)

SHIP_COLOR = (180, 180, 180)
SHIP_PADDING = 20

WHITE = (255, 255, 255)
GRAY = (120, 120, 120)
DARK_GRAY = (70, 70, 70)
GREEN = (100, 200, 100)


# UI Rects
LOCK_BUTTON_RECT = pygame.Rect(WINDOW_WIDTH // 2 - 90, WINDOW_HEIGHT - 50, 80, 30)
RESET_BUTTON_RECT = pygame.Rect(WINDOW_WIDTH // 2 + 10, WINDOW_HEIGHT - 50, 80, 30)

SINGLE_PLAYER_RECT = pygame.Rect(WINDOW_WIDTH//2 - 150, WINDOW_HEIGHT//2 - 80, 300, 60)
MULTI_PLAYER_RECT = pygame.Rect(WINDOW_WIDTH//2 - 150, WINDOW_HEIGHT//2 + 20, 300, 60)

button_rect_width = 80
button_rect_height = 30
BUTTON_RECT = pygame.Rect(WINDOW_WIDTH//2 - button_rect_width//2,
                          WINDOW_HEIGHT - (button_rect_height + 20),
                          button_rect_width,
                          button_rect_height)

EASY_RECT   = pygame.Rect(WINDOW_WIDTH//2 - 100, WINDOW_HEIGHT//2 - 90, 200, 50)
MEDIUM_RECT = pygame.Rect(WINDOW_WIDTH//2 - 100, WINDOW_HEIGHT//2 - 20, 200, 50)
HARD_RECT   = pygame.Rect(WINDOW_WIDTH//2 - 100, WINDOW_HEIGHT//2 + 50, 200, 50)


# Timer related
TURN_TIME_LIMIT = 30 # Seconds per turn
match_timer_rect_width = 80
match_timer_rect_height = 30
MATCH_TIMER_RECT = pygame.Rect(WINDOW_WIDTH//2 - match_timer_rect_width//2,
                          WINDOW_HEIGHT - (match_timer_rect_height + 20),
                          match_timer_rect_width,
                          match_timer_rect_height)


# ANIMATIONS
BOMB_ANIM_DURATION = 2.0 # Seconds
SMOKE_ANIM_DURATION = 1.2  # Seconds
TIMEOUT_ANIM_DURATION = 1.8 # Seconds

# bomb_frame_count = len(os.listdir("images\\bomb"))
# hit_frame_count = len(os.listdir("images\\hit"))
# miss_frame_count = len(os.listdir("images\\miss"))
# sunk_frame_count = len(os.listdir("images\\sunk"))

bomb_frame_count = 4
hit_frame_count = 1
miss_frame_count = 1
sunk_frame_count = 3

# Volume bar settings
BAR_WIDTH = 80
BAR_HEIGHT = 10
ICON_SIZE = 30
icon_rect = pygame.Rect(10, WINDOW_HEIGHT - ICON_SIZE - 10, ICON_SIZE, ICON_SIZE)
bar_rect = pygame.Rect(
    icon_rect.right + 10,
    icon_rect.centery - BAR_HEIGHT // 2,
    BAR_WIDTH,
    BAR_HEIGHT
)