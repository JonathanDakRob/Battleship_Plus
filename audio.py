import pygame
from utils import *
from config import bar_rect

# Sound icon
volume = 0.5  # range: 0.0 to 1.0
dragging = False

# ------------------ PLAY AUDIO ------------------
def play_waves():
    global volume
    if not pygame.mixer.music.get_busy():
        pygame.mixer.music.load(resource_path("audio/waves.ogg"))
        pygame.mixer.music.set_volume(volume)
        pygame.mixer.music.play(-1)

def play_button_click(click, loops=0, maxtime=0, fade_ms=0):
    global volume
    path = "audio/click" + str(click) + ".ogg"
    click_sound = pygame.mixer.Sound(resource_path(path))
    click_sound.set_volume(volume)
    click_sound.play(loops, maxtime, fade_ms)

falling_bomb_channel = None
miss_hit_channel = None
def play_sound_effect(effect, loops=0, maxtime=0, fade_ms=0):
    #Plays any sound within the audio folder with the of "effect.ogg"
    global volume, falling_bomb_channel, miss_hit_channel
    try:
        path = "audio/" + effect + ".ogg"
        sound_effect = pygame.mixer.Sound(resource_path(path))
        sound_effect.set_volume(volume)
        
        if effect == "falling_bomb":
            if falling_bomb_channel is None:
                falling_bomb_channel = sound_effect.play(loops, maxtime, fade_ms)
            elif not falling_bomb_channel.get_busy():
                falling_bomb_channel = sound_effect.play(loops, maxtime, fade_ms)
        else:
            if miss_hit_channel is None:
                miss_hit_channel = sound_effect.play(loops, maxtime, fade_ms)
            elif not miss_hit_channel.get_busy():
                miss_hit_channel = sound_effect.play(loops, maxtime, fade_ms)
    except:
        print("SOUND EFFECT ERROR")

# ------------------ SOUND BAR FUNCTION ------------------
def handle_volume_input():
    global volume, dragging

    mouse_pos = pygame.mouse.get_pos()
    mouse_pressed = pygame.mouse.get_pressed()

    # Start dragging if clicking inside bar
    if mouse_pressed[0]:
        if bar_rect.collidepoint(mouse_pos) or dragging:
            dragging = True

            # Update volume based on mouse X position
            rel_x = mouse_pos[0] - bar_rect.x
            volume = max(0, min(1, rel_x / bar_rect.width))

            # OPTIONAL: actually apply volume to pygame mixer
            pygame.mixer.music.set_volume(volume)
    else:
        dragging = False