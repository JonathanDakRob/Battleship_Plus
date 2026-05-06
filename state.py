from config import TURN_TIME_LIMIT

# This file contains game_state variables for the main loop
ships = []

# ------------------ TIMER STATE ------------------
current_turn_time_left = TURN_TIME_LIMIT
match_start_time = None
turn_start_time = None
last_turn_state = None
turn_timeout_sent = False

# Game state variables
# Please use these player_id variables when printing sending/printing things like: "Waiting For Player X"
player1_id = 1 
player2_id = 2
opponent_id = None
loading_angle = 0.0

running = True
ships_selected = False # Used to move on from ship selection stage
started_running_game = False # True if the game has fully started
multi_bomb_mode = False
radar_mode = False
radar_flash = None
game_mode = 0
ai_turn_due_time = None


