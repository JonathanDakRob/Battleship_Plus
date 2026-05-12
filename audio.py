import pygame
from utils import *
from config import bar_rect

# Sound icon
volume = 0.5  # range: 0.0 to 1.0
dragging = False


# ------------------ AUDIO CACHE -----------------
button_sounds = {
    1: pygame.mixer.Sound(resource_path("audio/click1.ogg")),
    2: pygame.mixer.Sound(resource_path("audio/click2.ogg"))
}


# ------------------ AUDIO QUEUE -----------------
audio_queue = []
current_audio = None

def add_audio(type):
    audio_queue.append(type)

# ------------------ QUEUE HANDLER -------------------
def handle_audio_queue():
    """
    Plays one queued audio at a time.
    Removes the audio from the queue after starting playback.
    Prevents the same queue entry from replaying repeatedly.
    """

    # If audio is still playing, wait
    if pygame.mixer.get_busy():
        return

    # Nothing to play
    if not audio_queue:
        return

    # Get first queued sound
    audio_type = audio_queue.pop(0)

    # Play it once
    play_audio(audio_type)

# ------------------ PLAY AUDIO ------------------
def play_audio(audio_type):
    """
    Plays audio/{audio_type}.ogg
    """
    global current_audio

    path = resource_path(f"audio/{audio_type}.ogg")

    current_audio = pygame.mixer.Sound(path)
    current_audio.play()

def play_waves():
    global volume
    if not pygame.mixer.music.get_busy():
        print("TEST 1: WAVES PLAYING")
        pygame.mixer.music.load(resource_path("audio/waves.ogg"))
        pygame.mixer.music.set_volume(volume)
        pygame.mixer.music.play(-1)

def play_button_click(click, loops=0, maxtime=0, fade_ms=0):
    global volume
    click_sound = button_sounds[click]
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
        
        sound_effect.play(loops, maxtime, fade_ms)
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