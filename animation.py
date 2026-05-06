import time
import backend

from config import *
from audio import *
from display import screen
from drawing import draw_time_ran_out

animations = [] # Stores active animations
animation_playing = False

def draw_animation(screen):
    global time_out_start, BOMB_ANIM_DURATION, SMOKE_ANIM_DURATION, TIMEOUT_ANIM_DURATION
    global bomb_frame_count, hit_frame_count, miss_frame_count, sunk_frame_count
    fallingbomb_maxtime_ms = int(((bomb_frame_count / (bomb_frame_count+1)) * BOMB_ANIM_DURATION) * 1000)
    hitmiss_maxtime_ms = int((BOMB_ANIM_DURATION*1000) - fallingbomb_maxtime_ms)
    
    # Load the image
    image_path = None
    image = None

    # start_time = anim["start"]
    duration = 0.0  # seconds
    size = CELL_SIZE * 5

    for anim in animations[:]:
        anim_type = anim["type"]
        elapsed = time.monotonic() - anim["start"]

        if anim_type in (1,2,3):
            duration = BOMB_ANIM_DURATION
        elif anim_type == 4:
            duration = SMOKE_ANIM_DURATION
        elif anim_type == 5:
            duration = TIMEOUT_ANIM_DURATION
        
        # Stop after duration
        if elapsed > duration:
            backend.set_wait_for_animation(False)
            animations.remove(anim)
            continue

        if anim_type in (1,2,3):
            # Play Falling Bomb animation
            play_sound_effect("falling_bomb")
            backend.set_wait_for_animation(True) # Wait for animation to finish before next shot/turn
            
            # This un implemented code will be used to make the animations dynamic in terms of frame count
            # # bomb_frame = math.floor((elapsed / duration)*bomb_frame_count) + 1
            # # if not bomb_frame > bomb_frame_count:
            # #     image_path = "images\\bomb\\Battleship_Bomb" + str(bomb_frame) + ".png"
            if elapsed < (duration / 5):
                image_path = "images/bomb/Battleship_Bomb1.png"
            elif elapsed < (2* duration / 5):
                image_path = "images/bomb/Battleship_Bomb2.png"
            elif elapsed < (3* duration / 5):
                image_path = "images/bomb/Battleship_Bomb3.png"
            elif elapsed < (4* duration / 5):
                image_path = "images/bomb/Battleship_Bomb4.png"
            else:
                if anim_type == 1:
                    # Play Splash animation
                    play_sound_effect("splash", maxtime=hitmiss_maxtime_ms, fade_ms=hitmiss_maxtime_ms//2)
                    image_path = "images/miss/Battleship_Splash.png"
                else:
                    # Play Bang animation
                    play_sound_effect("bang", maxtime=hitmiss_maxtime_ms, fade_ms=hitmiss_maxtime_ms//2)
                    image_path = "images/hit/Battleship_Bang.png"

        if anim_type == 4:
            # Play RISING SMOKE aniation
            if elapsed < (duration/3):
                image_path = "images/sunk/Battleship_Smoke1.png"
            elif elapsed < (2* duration/3):
                image_path = "images/sunk/Battleship_Smoke2.png"
            else:
                image_path = "images/sunk/Battleship_Smoke3.png"
        
        if anim_type == 5:
            # Timed out animation: Board argument represents the player_id who timed out
            if anim["board"] == 0:
                draw_time_ran_out(True)
                time_out_start = anim["start"]
            elif anim["board"] in (1,2):
                draw_time_ran_out(anim["board"] == backend.player_id)
                time_out_start = anim["start"]
            else:
                print("ERROR: Animation 5 value error")
            break
        
        try:
            image = pygame.image.load(resource_path(image_path)).convert_alpha()
                
            # Get pixel location
            loc_x, loc_y = anim["loc"]
            x, y = get_cell_pixel(anim["board"], loc_x, loc_y)

            # Set animation location
            if anim_type in (1,2,3):
                # Splash animation
                scale = 1.0
                if anim["multi_bomb"]:
                    scale = 2.3
                if elapsed < (duration / 5):
                    scale = scale*0.9
                elif elapsed < (2* duration / 5):
                    scale = scale*0.8
                elif elapsed < (3* duration / 5):
                    scale = scale*0.7
                elif elapsed < (4* duration / 5):
                    scale = scale*0.6
                else:
                    if anim["multi_bomb"]:
                        scale = 2.3
                    else:
                        scale = 1.0

                image = pygame.transform.scale(image, (size*scale,size*scale))
                rect = image.get_rect()
                rect.center = (x+10, y+10) # Centering the image on the cell
            elif anim_type == 4:
                # Rising smoke animation
                image = pygame.transform.scale(image, (size//2.5, size//2.5))
                rect = image.get_rect()
                rect.bottomleft = (x+5, y+CELL_SIZE-5)
                
            # Draw image
            screen.blit(image, rect)
        except:
            print("ANIMATION IMAGE ERROR 1")
            pass

def animation_exists(anim_type, loc, board):
    for anim in animations:
        if (
            anim["type"] == anim_type and
            anim["loc"] == loc and
            anim["board"] == board
        ):
            return True
    return False

def get_cell_pixel(grid_id, row, col):
    if grid_id == 1:
        grid_x = GRID_PADDING
        grid_y = top_grid_y
    elif grid_id == 2:
        grid_x = GRID_PADDING
        grid_y = bottom_grid_y
    else:
        raise ValueError("Invalid grid_id")

    x = grid_x + col * CELL_SIZE
    y = grid_y + row * CELL_SIZE

    return x, y

def trigger_animation(num, loc, board, multi_bomb=False):
    animations.append({
        "type": num,
        "loc": loc,
        "board": board,
        "multi_bomb": multi_bomb,
        "start": time.monotonic()
    })