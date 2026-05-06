'''
PyGame Drawing Functions:
The following functions use PyGame to draw the frontend/UI of the game.
They are called during the main gameplay loop and draw things depending on the Game State.
'''

import pygame
import time
import math

from utils import *
from config import *
from display import screen
from audio import volume, dragging
from animation import *
from state import *
from entities import Cell

# BUTTON ANIMATION STATE
# Maps a pygame.Rect id -> timestamp of last click (for click-pulse effect)
button_click_times = {}

def draw_animated_button(surface, rect, base_color, text, font, mouse_pos, click_time=None):
    """Draw a menu button with hover-scale, click-pulse, and shimmer animation."""
    now = time.monotonic()
    hovered = rect.collidepoint(mouse_pos)

    scale = 1.0
    click_age = (now - click_time) if click_time is not None else 999
    if click_age < 0.25:
        t = click_age / 0.25
        scale = 1.0 - 0.07 * math.sin(math.pi * t)
    elif hovered:
        scale = 1.06

    sw = int(rect.width * scale)
    sh = int(rect.height * scale)
    scaled_rect = pygame.Rect(0, 0, sw, sh)
    scaled_rect.center = rect.center

    if click_age < 0.25:
        t = click_age / 0.25
        blend = max(0.0, 1.0 - t * 2)
        color = tuple(min(255, int(c + (255 - c) * blend * 0.45)) for c in base_color)
    elif hovered:
        color = tuple(min(255, c + 35) for c in base_color)
    else:
        color = base_color

    pygame.draw.rect(surface, color, scaled_rect, border_radius=8)

    if hovered and click_age >= 0.25:
        shimmer_speed = 1.2
        shimmer_width = int(sw * 0.25)
        progress = (now * shimmer_speed) % 1.0
        sx = scaled_rect.left + int(progress * (sw + shimmer_width)) - shimmer_width
        shimmer_surf = pygame.Surface((shimmer_width, sh), pygame.SRCALPHA)
        for px in range(shimmer_width):
            alpha = int(60 * math.sin(math.pi * px / shimmer_width))
            pygame.draw.line(shimmer_surf, (255, 255, 255, alpha), (px, 0), (px, sh))
        clip_rect = surface.get_clip()
        surface.set_clip(scaled_rect)
        surface.blit(shimmer_surf, (sx, scaled_rect.top))
        surface.set_clip(clip_rect)

    border_color = (255, 255, 255) if hovered else (200, 200, 200)
    border_w = 3 if hovered else 1
    pygame.draw.rect(surface, border_color, scaled_rect, border_w, border_radius=8)

    text_surf = font.render(text, True, (255, 255, 255))
    tx = scaled_rect.centerx - text_surf.get_width() // 2
    ty = scaled_rect.centery - text_surf.get_height() // 2
    surface.blit(text_surf, (tx, ty))

def draw_main_menu(mouse_pos):
    font = pygame.font.Font(resource_path("fonts/PressStart2P-Regular.ttf"), LARGE_FONT_SIZE)
    button_font = pygame.font.Font(resource_path("fonts/PressStart2P-Regular.ttf"), SMALL_FONT_SIZE)

    # single_rect = pygame.Rect(WINDOW_WIDTH//2 - 150, WINDOW_HEIGHT//2 - 80, 300, 60)
    # multi_rect = pygame.Rect(WINDOW_WIDTH//2 - 150, WINDOW_HEIGHT//2 + 20, 300, 60)

    sp_color = (70,130,180)
    mp_color = (70,130,180)

    #if SINGLE_PLAYER_RECT.collidepoint(mouse_pos):
        #sp_color = (100,160,210)
        #pygame.draw.rect(screen, (255, 255, 255), SINGLE_PLAYER_RECT.inflate(-6, -6), 2)

    #if MULTI_PLAYER_RECT.collidepoint(mouse_pos):
        #mp_color = (100,160,210)
        #pygame.draw.rect(screen, (255, 255, 255), MULTI_PLAYER_RECT.inflate(-6, -6), 2)

    title = font.render("Battleship", True, (255,255,255))
    draw_text_with_outline(screen,
                    "Battleship",
                    font,
                    (255, 255, 255),
                    (0, 0, 0),
                    (WINDOW_WIDTH//2 - title.get_width()//2, WINDOW_HEIGHT//4),
                    shadow_x = -5,
                    shadow_y = 5)
    draw_animated_button(screen, SINGLE_PLAYER_RECT, (70, 130, 180), "Single Player", button_font,
                     mouse_pos, button_click_times.get(id(SINGLE_PLAYER_RECT)))
    draw_animated_button(screen, MULTI_PLAYER_RECT, (70, 130, 180), "Multi-Player", button_font,
                         mouse_pos, button_click_times.get(id(MULTI_PLAYER_RECT)))
      
       
    # screen.blit(title, (WINDOW_WIDTH//2 - title.get_width()//2, WINDOW_HEIGHT//4))

    #pygame.draw.rect(screen, sp_color, SINGLE_PLAYER_RECT)
    #pygame.draw.rect(screen, mp_color, MULTI_PLAYER_RECT)

    #single_text = button_font.render("Single Player", True, (255,255,255))
    #multi_text = button_font.render("Multi-Player", True, (255,255,255))

    #screen.blit(single_text, (SINGLE_PLAYER_RECT.centerx - single_text.get_width()//2,
                                #SINGLE_PLAYER_RECT.centery - single_text.get_height()//2))

    #screen.blit(multi_text, (MULTI_PLAYER_RECT.centerx - multi_text.get_width()//2,
                                #MULTI_PLAYER_RECT.centery - multi_text.get_height()//2))
    
    return SINGLE_PLAYER_RECT, MULTI_PLAYER_RECT

def draw_difficulty_selection(mouse_pos):
    font = pygame.font.Font(resource_path("fonts/PressStart2P-Regular.ttf"), int(LARGE_FONT_SIZE * 0.9))
    btn_font = pygame.font.Font(resource_path("fonts/PressStart2P-Regular.ttf"), SMALL_FONT_SIZE)
    title = font.render("Select Difficulty", True, (255, 255, 255))
    screen.blit(title, (WINDOW_WIDTH//2 - title.get_width()//2, WINDOW_HEIGHT//4))

    for rect, label, base_color in [
        (EASY_RECT,   "Easy",   (60, 160, 60)),
        (MEDIUM_RECT, "Medium", (70, 130, 180)),
        (HARD_RECT,   "Hard",   (180, 50, 50)),
    ]:
        draw_animated_button(screen, rect, base_color, label, btn_font,
                             mouse_pos, button_click_times.get(id(rect)))
    """
        color = tuple(min(c + 30, 255) for c in base_color) if rect.collidepoint(mouse_pos) else base_color
        pygame.draw.rect(screen, color, rect)
        text = btn_font.render(label, True, (255, 255, 255))
        screen.blit(text, (rect.centerx - text.get_width()//2, rect.centery - text.get_height()//2))
"""

def draw_message(message):
    font = pygame.font.Font(resource_path("fonts/PressStart2P-Regular.ttf"), LARGE_FONT_SIZE)
    title = font.render(message,True,(255,255,255))

    screen.blit(
        title,
        (WINDOW_WIDTH // 2 - title.get_width() // 2,
         WINDOW_HEIGHT // 2 - title.get_height())
    )

def draw_button(mouse_pos, text="BACK", color=(180, 50, 50), border_rad=0):
    font = pygame.font.SysFont(None, 20)

    # Draw button
    if BUTTON_RECT.collidepoint(mouse_pos):
        color = (230,100,100)
        pygame.draw.rect(screen, (255, 255, 255), BUTTON_RECT.inflate(4, 4), 2, border_radius=border_rad)
    else:
        pygame.draw.rect(screen, color, BUTTON_RECT, border_radius=border_rad)

    # Draw text
    text = font.render(text, True, (255, 255, 255))
    screen.blit(text, (BUTTON_RECT.centerx - text.get_width()//2, BUTTON_RECT.centery - text.get_height()//2))

def draw_waiting_for_player(message, number=0):
    font = pygame.font.Font(resource_path("fonts/PressStart2P-Regular.ttf"), SMALL_FONT_SIZE)
    small_font = pygame.font.Font(resource_path("fonts/PressStart2P-Regular.ttf"), SMALL_FONT_SIZE // 2)
    
    if number == 0:
        title = font.render(f"Waiting for Other Player...", True, (255, 255, 255))
    else:
        title = font.render(f"Waiting for Player {number}...", True, (255, 255, 255))
    subtitle = small_font.render(message, True, (180, 180, 180))

    screen.blit(
        title,
        (WINDOW_WIDTH // 2 - title.get_width() // 2,
         WINDOW_HEIGHT // 2 - title.get_height())
    )

    screen.blit(
        subtitle,
        (WINDOW_WIDTH // 2 - subtitle.get_width() // 2,
         WINDOW_HEIGHT // 2 + 10)
    )

def draw_ship_selection():
    font = pygame.font.Font(resource_path("fonts/PressStart2P-Regular.ttf"), int(SMALL_FONT_SIZE * 0.8))
    small_font = pygame.font.Font(resource_path("fonts/PressStart2P-Regular.ttf"), int(SMALL_FONT_SIZE * 0.45))

    title_text = font.render("Select Number of Ships (1 - 5)", True, (255, 255, 255))
    instruction_text = small_font.render("Press a number key 1, 2, 3, 4, or 5", True, (200, 200, 200))

    screen.blit(title_text, (WINDOW_WIDTH // 2 - title_text.get_width() // 2, (WINDOW_HEIGHT // 2) - (3 * instruction_text.get_height())))
    screen.blit(instruction_text, (WINDOW_WIDTH // 2 - instruction_text.get_width() // 2, WINDOW_HEIGHT // 2))


    pygame.display.flip()

def draw_game_over(winner):
    font = pygame.font.Font(resource_path("fonts/PressStart2P-Regular.ttf"), int(LARGE_FONT_SIZE))
    small_font = pygame.font.Font(resource_path("fonts/PressStart2P-Regular.ttf"), int(SMALL_FONT_SIZE * 1.2))

    title = title = font.render(f"GAME OVER", True, (255, 255, 255))
    subtitle = ""

    if winner:
        subtitle = small_font.render("Victory!!!", True, (0, 139, 0))
    else:
        subtitle = small_font.render("Defeat...", True, (139, 0, 0))

    screen.blit(
        title,
        (WINDOW_WIDTH // 2 - title.get_width() // 2,
         WINDOW_HEIGHT // 2 - title.get_height())
    )

    screen.blit(
        subtitle,
        (WINDOW_WIDTH // 2 - subtitle.get_width() // 2,
         WINDOW_HEIGHT // 2 + 10)
    )

def draw_loading_circle(angle):
    """
    surface: pygame surface to draw on
    center: (x, y)
    radius: circle radius
    angle: current rotation angle
    """
    # screen.fill(BG_COLOR)

    center = (WINDOW_WIDTH//2, WINDOW_HEIGHT//2)
    radius = 15
    rect = pygame.Rect(0, 0, radius * 2, radius * 2)
    rect.center = center

    start_angle = angle
    end_angle = angle + math.pi / 2   # length of arc

    pygame.draw.arc(screen, (255, 255, 255), rect, start_angle, end_angle, 4)

def draw_ship_placement():
    draw_coordinates(GRID_PADDING, GRID_PADDING)

    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            rect = pygame.Rect(
                GRID_PADDING + col * CELL_SIZE,
                GRID_PADDING + row * CELL_SIZE,
                CELL_SIZE,
                CELL_SIZE
            )
            pygame.draw.rect(screen, WATER_COLOR, rect)      # fill blue
            pygame.draw.rect(screen, GRID_COLOR, rect, 2)
   
    active_ship = None
    for ship in ships:
        if ship.dragging:
            active_ship = ship
        else:
            ship.draw(screen)
    
    if active_ship:
        active_ship.draw(screen)

    #pygame.display.flip()

def draw_volume_bar():
    # Draw sound icon (placeholder square)
    icon = pygame.image.load(resource_path("images/audio/audio_icon.png")).convert_alpha()
    icon = pygame.transform.scale(icon, (icon_rect.width, icon_rect.height))

    mouse_pos = pygame.mouse.get_pos()

    # Show bar only when hovering icon or interacting with bar
    if icon_rect.collidepoint(mouse_pos) or bar_rect.collidepoint(mouse_pos) or dragging:
        # Background bar
        pygame.draw.rect(screen, DARK_GRAY, bar_rect)

        # Filled portion
        fill_width = int(bar_rect.width * volume)
        fill_rect = pygame.Rect(bar_rect.x, bar_rect.y, fill_width, bar_rect.height)
        pygame.draw.rect(screen, GREEN, fill_rect)

    screen.blit(icon, icon_rect.topleft)


# ------------------ COORDINATE DRAWING ------------------
def draw_coordinates(start_x, start_y):
    font = pygame.font.SysFont("monospace", int(CELL_SIZE//1.5), bold=True)
    letters = "ABCDEFGHIJ"
    
    for i in range(GRID_SIZE):
        # --- Draw Numbers (Horizontal: 1-10) ---
        # Centered above each column
        num_text = font.render(str(i + 1), True, (255, 255, 255))
        num_x = start_x + (i * CELL_SIZE) + (CELL_SIZE // 2 - num_text.get_width() // 2)
        num_y = start_y - LABEL_MARGIN
        screen.blit(num_text, (num_x, num_y))
        
        # --- Draw Letters (Vertical: A-J) ---
        # Centered to the left of each row
        let_text = font.render(letters[i], True, (255, 255, 255))
        let_x = start_x - LABEL_MARGIN
        let_y = start_y + (i * CELL_SIZE) + (CELL_SIZE // 2 - let_text.get_height() // 2)
        screen.blit(let_text, (let_x, let_y))

# ------------------ DRAW LOCK AND RESET BUTTON ------------------
def draw_control_buttons(mouse_pos):
    lock_color = (50, 200, 50)
    reset_color = (200, 50, 50)

    # Lock Button
    if LOCK_BUTTON_RECT.collidepoint(mouse_pos):
        lock_color = (70, 230, 70)  
        pygame.draw.rect(screen, (255, 255, 255), LOCK_BUTTON_RECT.inflate(4, 4), 2)
    else:
        pygame.draw.rect(screen, lock_color, LOCK_BUTTON_RECT)

    # Reset Button
    if RESET_BUTTON_RECT.collidepoint(mouse_pos):
        reset_color = (220, 80, 70)
        pygame.draw.rect(screen, (255, 255, 255), RESET_BUTTON_RECT.inflate(4, 4), 2)
    else:
        pygame.draw.rect(screen, reset_color, RESET_BUTTON_RECT)
 
    
    font = pygame.font.SysFont(None, 18)
    lock_text = font.render("LOCK", True, (255, 255, 255))
    reset_text = font.render("RESET", True, (255, 255, 255))
    
    screen.blit(lock_text, (LOCK_BUTTON_RECT.centerx - lock_text.get_width() // 2, LOCK_BUTTON_RECT.centery - lock_text.get_height() // 2))
    screen.blit(reset_text, (RESET_BUTTON_RECT.centerx - reset_text.get_width() // 2, RESET_BUTTON_RECT.centery - reset_text.get_height() // 2))
    
    return LOCK_BUTTON_RECT, RESET_BUTTON_RECT

# ------------------ RUNNING_GAME DRAW HELPERS ------------------
def draw_backend_ships():
    # Draw ships stored in backend.ships onto the bottom grid.
    # Assumes backend.ships is a list of lists of (row, col) tuples.
    # Meant for the RUNNING_GAME state
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            if backend.grid[row][col] == "S":
                x = GRID_PADDING + col * CELL_SIZE
                y = bottom_grid_y + row * CELL_SIZE
                rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(screen, (0, 200, 0), rect)
                pygame.draw.rect(screen, (50, 50, 50), rect, 2)

def draw_mark_cell(cell_value, origin_y, row, col, board):
    # Only draw for hit/miss cells.
    if cell_value not in ("X", "O", "D"):
        return

    x = GRID_PADDING + col * CELL_SIZE
    y = origin_y + row * CELL_SIZE
    rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)

    # Red = hit, Blue = miss, Dark red = sunk
    color = None
    if cell_value == "X":
        color = (220, 80, 80)
    elif cell_value == "O":
        color = (225, 225, 220)
    elif cell_value == "D":
        if not animation_exists(4, (row,col), board):
            trigger_animation(4, (row,col), board)
        color = (125, 40, 40)
    pygame.draw.rect(screen, color, rect)
    pygame.draw.rect(screen, (50, 50, 50), rect, 2)

def draw_marks():
    # Draw opponent board marks (top) and your board marks (bottom) in one pass.
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            draw_mark_cell(backend.target_grid[r][c], top_grid_y, r, c, 1)  # Your shots
            draw_mark_cell(backend.grid[r][c], bottom_grid_y, r, c, 2)  # Opponent shots


# ------------------ GRID CREATION ------------------
def create_grid(grid_id, start_x, start_y):
    cells = []
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            rect = pygame.Rect(
                start_x + col * CELL_SIZE,
                start_y + row * CELL_SIZE,
                CELL_SIZE,
                CELL_SIZE
            )
            cells.append(Cell(rect, grid_id, row, col))
    return cells

####
top_grid = create_grid(0, GRID_PADDING, top_grid_y)
bottom_grid = create_grid(1, GRID_PADDING, bottom_grid_y)

all_cells = top_grid + bottom_grid

# ---------------- POWER UPS -------------------
def draw_multi_bomb_preview(mouse_pos):
    # When multi-bomb mode is armed, show the player
    # which 3x3 area will be attacked before they click.
    if not multi_bomb_mode:
        return

    for cell in top_grid:
        if cell.rect.collidepoint(mouse_pos):
            center_row, center_col = cell.get_coords()
            cells = backend.compute_multi_bomb_cells(center_row, center_col)

            # Highlight every valid cell in the 3x3 area.
            for r, c in cells:
                x = GRID_PADDING + c * CELL_SIZE
                y = top_grid_y + r * CELL_SIZE
                rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(screen, (240, 220, 80), rect, 3)

def draw_radar_preview(mouse_pos):
    if not radar_mode:
        return
    for cell in top_grid:
        if cell.rect.collidepoint(mouse_pos):
            center_row, center_col = cell.get_coords()
            cells = backend.compute_multi_bomb_cells(center_row, center_col)
            for r, c in cells:
                x = GRID_PADDING + c * CELL_SIZE
                y = top_grid_y + r * CELL_SIZE
                rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(screen, (80, 200, 255), rect, 3)

def draw_radar_flash():
    if not radar_flash:
        return
    elapsed = time.monotonic() - radar_flash["start"]
    if elapsed > 1.5:
        return
    color = (0, 255, 100) if radar_flash["result"] else (255, 80, 80)
    for r, c in radar_flash["cells"]:
        x = GRID_PADDING + c * CELL_SIZE
        y = top_grid_y + r * CELL_SIZE
        rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
        pygame.draw.rect(screen, color, rect, 3)


# ----------------------- STATUS PANEL -----------------------
def draw_status_panel():
    # Simple UI panel to explain state during demo
    panel_x = GRID_PADDING + GRID_SIZE * CELL_SIZE + 15
    panel_y = 30

    player_panel_x = panel_x
    player_panel_y = panel_y + (GRID_PADDING + GRID_SIZE * CELL_SIZE)

    power_panel_x = END_OF_GRID_X + ((WINDOW_WIDTH - END_OF_GRID_X) // 2)
    power_panel_y = END_OF_GRID_Y - (END_OF_GRID_Y // 4)

    if backend.multi_bomb_used:
        multi_bomb_status = "USED"
    elif multi_bomb_mode:
        multi_bomb_status = "ARMED"
    else:
        multi_bomb_status = "READY"

    if backend.GAME_MODE == 2:
        player_label = f"Player {str(backend.player_id)}"
    else:
        player_label = "Single Player"

    # Build these labels separately to keep the status panel readable and avoid
    # fragile inline f-string expressions for turn/radar state text.
    turn_text = "Your Turn" if backend.your_turn else "Opponent's Turn"
    radar_text = "USED" if backend.radar_used else ("ARMED" if radar_mode else "READY")

    lines = [
        player_label,
        turn_text,
        "",
        f"Enemy ships sunk: {backend.opponent_ships_sunk}/{len(backend.ships)}",
        f"Shots hit: {len(backend.shots_sent_hit)}",
        f"Shots missed: {len(backend.shots_sent_miss)}",
        "",
        f"Big-bomb (M): {multi_bomb_status}",
        f"Radar (R): {radar_text}"
    ]

    opp_lines = [
        f"Ships sunk: {backend.get_num_ships_sunk()}/{len(backend.ships)}",
        f"Hits recv: {len(backend.shots_received_hit)}",
        f"Miss recv: {len(backend.shots_received_miss)}",
    ]

    power_lines = [
        
    ]

    # Timer at the bottom of the screen
    timer_font = pygame.font.Font(resource_path("fonts/PressStart2P-Regular.ttf"), MEDIUM_FONT_SIZE)
    timer_surf = timer_font.render(format_seconds(current_turn_time_left), True, (255,255,255))
    screen.blit(timer_surf, BUTTON_RECT.inflate(12,12))

    panel_font = pygame.font.Font(resource_path("fonts/PressStart2P-Regular.ttf"), SMALL_FONT_SIZE//2)
    panel_color = (0, 0, 200)

    for i, text in enumerate(lines):
        surf = panel_font.render(text, True, panel_color)
        screen.blit(surf, (panel_x, panel_y + i * 22))

    for i, text in enumerate(opp_lines):
        surf = panel_font.render(text, True, panel_color)
        screen.blit(surf, (player_panel_x, player_panel_y + i*22))

    for i, text in enumerate(power_lines):
        power_surf = panel_font.render(text, True, panel_color)
        power_rect = power_surf.get_rect(center=(power_panel_x, power_panel_y + i*22))
        screen.blit(power_surf, power_rect)

def draw_lock_button(mouse_pos):
    # Place button at the bottom center
    button_rect = pygame.Rect(WINDOW_WIDTH // 2 - 70, WINDOW_HEIGHT - 50, 140, 35)
    if button_rect.collidepoint(mouse_pos):
        color = (70, 230, 70)  
        pygame.draw.rect(screen, (255, 255, 255), button_rect.inflate(4, 4), 2)
    else:
        color = (50, 200, 50)  
    pygame.draw.rect(screen, color, button_rect)
    
    font = pygame.font.SysFont(None, 24)
    text = font.render("LOCK SHIPS", True, (255, 255, 255))
    screen.blit(text, (button_rect.centerx - text.get_width() // 2, button_rect.centery - text.get_height() // 2))
    return button_rect

def format_seconds(seconds):
    seconds = max(0, int(seconds))
    mins = seconds // 60
    secs = seconds % 60
    return f"{mins:02d}:{secs:02d}"

def draw_time_ran_out(lost_turn):
    # Player ran out of time, other player's turn
    global time_out_start
    duration = 1.8 # display message for this many seconds
    font = pygame.font.Font(resource_path("font/PressStart2P-Regular.ttf"), int(LARGE_FONT_SIZE * 1.2))
    font.set_bold(True)
    small_font = pygame.font.Font(resource_path("fonts/PressStart2P-Regular.ttf"), MEDIUM_FONT_SIZE)

    title = font.render("TIME RAN OUT", True, (139, 0, 0))
    subtitle = None

    elapsed = time.monotonic() - time_out_start

    if (elapsed <= duration):

        if lost_turn:
            subtitle = "Lost your turn"
            subtitle_render = small_font.render(subtitle, True, (180, 180, 180))
            
        else:
            subtitle = "Your turn now"
            subtitle_render = small_font.render(subtitle, True, (180, 180, 180))
            
        draw_text_with_outline(screen,
                               "TIME RAN OUT", # Text
                               font, # Font
                               (255, 102, 102), # Text Color
                               (0, 0, 0), # Outline Color
                               (WINDOW_WIDTH // 2 - title.get_width() // 2, WINDOW_HEIGHT // 2 - title.get_height()) # Position
        )

        draw_text_with_outline(screen,
                               subtitle, # Text
                               small_font, # Font
                               (255, 255, 255), # Text Color
                               (0, 0, 0), # Outline Color
                               (WINDOW_WIDTH // 2 - subtitle_render.get_width() // 2, WINDOW_HEIGHT // 2 + 12) # Position
        ) 

    else:
        time_out_start = -1.0 # No 'time ran out' to display

def draw_text_with_outline(screen, text, font, text_color, outline_color, pos, shadow_x=0, shadow_y=0):
    x, y = pos

    # Draw outline
    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1),
                   (-1, -1), (-1, 1), (1, -1), (1, 1)]:
        outline_surface = font.render(text, True, outline_color)
        screen.blit(outline_surface, (x + dx + shadow_x, y + dy + shadow_y))

    # Draw main text
    text_surface = font.render(text, True, text_color)
    screen.blit(text_surface, (x, y))

# Used to control wave frames
last_wave_timer = time.monotonic()
wave_frame = 1
total_frames = 3


# ========================== DRAW BACKGROUND ANIMATIONS ==========================
def draw_background(game_state):
    global last_wave_timer, wave_frame, total_frames
    
    
    if time.monotonic() - last_wave_timer > 1:
        wave_frame = ((wave_frame + 1) % total_frames) +1
        last_wave_timer = time.monotonic()

    path = "images/backgrounds/Battleship_BG_Waves" + str(wave_frame) + ".png"
    background = pygame.image.load(resource_path(path))

    background = pygame.transform.scale(background, (WINDOW_WIDTH, WINDOW_HEIGHT))
    screen.blit(background, (0,0))
    
    background2 = None
    if game_state == "MAIN_MENU":
        background2 = pygame.image.load(resource_path("images/backgrounds/Battleship_MainMenuBGShips.png"))
        background2 = pygame.transform.scale(background2, (WINDOW_WIDTH, WINDOW_HEIGHT))      
    else:
        pass
    
    if background2 != None:
        screen.blit(background2, (0,0))