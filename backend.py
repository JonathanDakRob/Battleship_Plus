# This file will handle the backend of our battleship game
# backend.py

import socket
import json
import threading
import time
import random

SERVER_IP = "127.0.0.1"
PORT = 5000
BOARD_SIZE = 10

############################################################################# Memory #############################################################################
# Local Game State

# 10x10 grid representation
# "." = empty
# "S" = ship
# "X" = hit
# "O" = miss
# "D" = sunk
grid = [["." for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
target_grid = [["." for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

ship_count = 0
# Ships stored as arrays of coordinate tuples
# For example: [[(0,0)], [(2,3),(2,4)], [(5,1),(6,1),(7,1)]]
ships = []

# Identity and match state
player_id = None
your_turn = False
winner = False
ships_locked = False
all_ships_locked = False
opponent_ships_sunk = 0
multi_bomb_used = False # True after the player uses their one multibomb for this game
radar_used= False
radar_flash_data = None

# Game mode: Single or Multi-player
# Single Player: 1
# Multi-Playter: 2
GAME_MODE = 0

# Game state
# WAITING_FOR_PLAYERS_TO_CONNECT -> SELECT_SHIPS -> PLACE_SHIPS -> WAITING_FOR_OPPONENT -> RUNNING_GAME
GAME_STATE = "MAIN_MENU"

# Track shot outcomes (for UI & debugging)
shots_received_hit = []
shots_received_miss = []
shots_sent_hit = []
shots_sent_miss = []

####################################################################### Animation Logging #######################################################################################
# 1 = miss, 2 = hit, 3 = sunk, 4 = rising smoke
# loc = (x, y)
# board = 1 (top board), 2 (bottom board)
animations = []
wait_for_animation = False
def add_animation(num, loc, board, multi_bomb=False):
    # Adds a new animation integer value to the list
    animations.append({
        "type": num,
        "loc": loc,
        "board": board,
        "multi_bomb": multi_bomb
    })

def remove_animation():
    # Removes the next animation in the list and return the integer value
    if len(animations) > 0:
        next_animation = animations[0]
        animations.pop(0)
        return next_animation
    return 0

def set_wait_for_animation(wait):
    global wait_for_animation
    if wait in (True,False):
        if wait_for_animation != wait:
            wait_for_animation = wait
    else:
        print("BACKEND: Invalid Wait Value")
    
####################################################################### AI Components #######################################################################################
import random

# AI's own grid and ships (hidden from player)
ai_grid = [["." for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
ai_ships = []

# AI targeting state for medium difficulty
ai_mode = "hunt"        # "hunt" = random, "target" = follow up on a hit
ai_hits_pending = []    # Cells the AI has hit but not yet sunk
ai_tried = set()        # Every cell the AI has already shot

# Difficulty: "easy", "medium", "hard"
ai_difficulty = "medium"
ai_multi_bomb_used = False
AI_MULTI_BOMB_CHANCE = 0.1 # Chance to use multi-bomb on an AI turn

def ai_place_ships(count):
    """Randomly place AI ships on ai_grid."""
    global ai_ships, ai_grid
    ai_grid = [["." for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    ai_ships = []

    for size in range(1, count + 1):
        placed = False
        while not placed:
            orientation = random.choice(["H", "V"])
            row = random.randint(0, BOARD_SIZE - 1)
            col = random.randint(0, BOARD_SIZE - 1)
            cells = compute_ship_cells(row, col, size, orientation)
            # Check against ai_grid, not the player's grid
            valid = all(in_bounds(r, c) and ai_grid[r][c] == "." for r, c in cells)
            if valid:
                for r, c in cells:
                    ai_grid[r][c] = "S"
                ai_ships.append(cells)
                placed = True

def ai_pick_shot():
    """Pick a cell to shoot based on difficulty level."""
    global ai_mode, ai_hits_pending

    # Hard: cheat by reading the player's grid directly, never misses
    if ai_difficulty == "hard":
        candidates = [
            (r, c)
            for r in range(BOARD_SIZE)
            for c in range(BOARD_SIZE)
            if (r, c) not in ai_tried and grid[r][c] == "S"
        ]
        if candidates:
            return random.choice(candidates)

        # If no unseen ship cells remain, fall back to any legal untried cell so
        # hard mode never gets stuck in an infinite search loop late in the game.
        fallback = [
            (r, c)
            for r in range(BOARD_SIZE)
            for c in range(BOARD_SIZE)
            if (r, c) not in ai_tried
        ]
        if fallback:
            return random.choice(fallback)

        return None

    # Easy: purely random, no memory of hits
    elif ai_difficulty == "easy":
        while True:
            r = random.randint(0, BOARD_SIZE - 1)
            c = random.randint(0, BOARD_SIZE - 1)
            if (r, c) not in ai_tried:
                return r, c

    # Medium: hunt randomly, then target neighbors after a hit
    elif ai_difficulty == "medium":
        if ai_mode == "target" and ai_hits_pending:
            r, c = ai_hits_pending[-1]
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if in_bounds(nr, nc) and (nr, nc) not in ai_tried:
                    return nr, nc
            # No valid neighbors left for this hit, pop it and recurse
            ai_hits_pending.pop()
            return ai_pick_shot()

        # Hunt mode: random untried cell
        while True:
            r = random.randint(0, BOARD_SIZE - 1)
            c = random.randint(0, BOARD_SIZE - 1)
            if (r, c) not in ai_tried:
                return r, c

def ai_receive_result(row, col, hit, sunk):
    """Update AI targeting state after learning the result of its shot."""
    global ai_mode, ai_hits_pending
    ai_tried.add((row, col))
    if hit:
        if ai_difficulty == "medium":
            ai_hits_pending.append((row, col))
            ai_mode = "target"
    if sunk:
        if ai_difficulty == "medium":
            ai_hits_pending.clear()
            ai_mode = "hunt"

def ai_take_turn():
    """
    The AI shoots at the player's grid.
    Returns (row, col, hit, sunk, all_sunk) so board.py can update the display.
    """
    # Pick exactly one AI target per turn and use that same cell for hit detection,
    # board updates, targeting memory, and animation. This prevents the AI from
    # evaluating one square but marking a different one.
    shot = ai_pick_shot()
    if shot is None:
        return None, None, False, False, all_ships_sunk()

    row, col = shot
    ai_tried.add((row, col))

    hit = (grid[row][col] == "S")
    sunk = False
    all_sunk_result = False
    ship_idx = get_ship_index(row, col)
    anim_val = 0 # Value to queue animation

    if hit:
        grid[row][col] = "X"
        shots_received_hit.append((row, col))

        sunk = check_ship_sunk(ship_idx)
        if sunk:
            anim_val = 3
            sink_own_ship(ship_idx)
            all_sunk_result = all_ships_sunk()
        else:
            anim_val = 2
    else:
        grid[row][col] = "O"
        shots_received_miss.append((row, col))
        anim_val = 1

    ai_receive_result(row, col, hit, sunk)
    add_animation(anim_val, (row, col), 2)

    return row, col, hit, sunk, all_sunk_result

def ai_take_multi_bomb_turn():
    """
    AI uses a one-time 3x3 multi-bomb on the player's board.
    Returns (center_row, center_col, all_sunk_result).
    """
    global ai_multi_bomb_used

    # Pick the center of the multi-bomb using the existing AI targeting logic
    center_row, center_col = ai_pick_shot()
    cells = compute_multi_bomb_cells(center_row, center_col)

    anim_val = 0
    sunk_indexes = []
    hit_any = False

    for row, col in cells:
        # Skip cells the AI already attacked before
        if (row, col) in ai_tried:
            continue

        ai_tried.add((row, col))
        hit = (grid[row][col] == "S")
        ship_idx = get_ship_index(row, col)

        if hit:
            hit_any = True
            grid[row][col] = "X"
            shots_received_hit.append((row, col))

            sunk = check_ship_sunk(ship_idx)
            if sunk:
                if ship_idx not in sunk_indexes:
                    sunk_indexes.append(ship_idx)
                    sink_own_ship(ship_idx)
                anim_val = 3
            else:
                if anim_val < 2:
                    anim_val = 2
        else:
            grid[row][col] = "O"
            shots_received_miss.append((row, col))
            if anim_val < 1:
                anim_val = 1

    all_sunk_result = all_ships_sunk()

    # Queue one animation for the whole 3x3 attack
    add_animation(anim_val, (center_row,center_col), 2, multi_bomb=True)

    ai_multi_bomb_used = True
    print(f"AI used MULTI-BOMB at center ({center_row}, {center_col})")

    return center_row, center_col, hit_any, all_sunk_result

def player_shoot_ai(row, col):
    """
    Player shoots at the AI's grid.
    Returns (hit, sunk, all_sunk) so board.py can update target_grid and the display.
    """
    global opponent_ships_sunk

    hit = (ai_grid[row][col] == "S")
    sunk = False
    all_sunk_result = False
    anim_val = 0

    if hit:
        ai_grid[row][col] = "X"
        shots_sent_hit.append((row, col))
        # Check if that ship is fully sunk
        for ship in ai_ships:
            if (row, col) in ship:
                if all(ai_grid[r][c] == "X" for r, c in ship):
                    sunk = True
                    for r, c in ship:
                        ai_grid[r][c] = "D"
                        target_grid[r][c] = "D"
                    opponent_ships_sunk += 1
                break
        if not sunk:
            anim_val = 2
            target_grid[row][col] = "X"
        else:
            anim_val = 3
        # Check if ALL AI ships are sunk
        all_sunk_result = all(
            ai_grid[r][c] == "D"
            for ship in ai_ships
            for r, c in ship
        )
    else:
        anim_val = 1
        ai_grid[row][col] = "O"
        shots_sent_miss.append((row, col))
        target_grid[row][col] = "O"

    add_animation(anim_val, (row,col), 1)

    return hit, sunk, all_sunk_result

def player_multi_bomb_ai(center_row, center_col): ##
    """
    Player uses a one-time 3x3 multi-bomb against the AI board.
    Returns (used_successfully, all_sunk_result).
    """
    global opponent_ships_sunk, multi_bomb_used

    if multi_bomb_used:
        print("MULTI-BOMB FAILED: Already used this game.")
        return False, False

    cells = compute_multi_bomb_cells(center_row, center_col)

    if not can_send_multi_bomb(cells):
        print("MULTI-BOMB FAILED: Entire 3x3 area was already targeted.")
        return False, False

    sunk_ship_indexes = []
    anim_val = 0 # Used to queue animation

    for row, col in cells:
        # Ignore already-targeted cells, but continue processing the rest.
        if (row, col) in shots_sent_hit or (row, col) in shots_sent_miss:
            continue

        hit = (ai_grid[row][col] == "S")

        if hit:
            if anim_val < 2:
                anim_val = 2
            ai_grid[row][col] = "X"
            shots_sent_hit.append((row, col))
            target_grid[row][col] = "X"

            # Check whether this hit sunk an AI ship.
            for ship_index, ship in enumerate(ai_ships):
                if (row, col) in ship:
                    if all(ai_grid[r][c] in ("X", "D") for r, c in ship):
                        if ship_index not in sunk_ship_indexes:
                            sunk_ship_indexes.append(ship_index)
                            opponent_ships_sunk += 1
                            if anim_val < 3:
                                anim_val = 3

                            for r, c in ship:
                                ai_grid[r][c] = "D"
                                target_grid[r][c] = "D"
                    break
        else:
            ai_grid[row][col] = "O"
            shots_sent_miss.append((row, col))
            target_grid[row][col] = "O"
            if anim_val < 1:
                anim_val = 1

    all_sunk_result = all(
        ai_grid[r][c] == "D"
        for ship in ai_ships
        for r, c in ship
    )
    
    add_animation(anim_val, (center_row,center_col), 1, multi_bomb=True)
    multi_bomb_used = True
    print(f"MULTI-BOMB used in single player at center ({center_row}, {center_col})")
    return True, all_sunk_result

def player_radar_scan(center_row, center_col):
    """
    Reveals whether any AI ship exists in a 3x3 area.
    Returns (already_used, found) — does not shoot anything.
    """
    global radar_used
    if radar_used:
        print("RADAR FAILED: Already used.")
        return False, False

    cells = compute_multi_bomb_cells(center_row, center_col)
    found = any(ai_grid[r][c] == "S" for r, c in cells)
    radar_used = True
    print(f"RADAR SCAN at ({center_row},{center_col}): {'Ship found!' if found else 'Nothing found.'}")
    return True, found

def ai_should_use_multi_bomb():
    # AI can only use multi-bomb once per game.
    if ai_multi_bomb_used:
        return False

    if ai_difficulty == "easy":
        chance = 0.10
    elif ai_difficulty == "medium":
        chance = 0.20
    elif ai_difficulty == "hard":
        chance = 0.35
    else:
        chance = 0.20

    return random.random() < chance

def reset_ai():
    """Reset all AI state. Call this inside reset_game()."""
    global ai_grid, ai_ships, ai_mode, ai_hits_pending, ai_tried, ai_difficulty
    global ai_multi_bomb_used

    ai_grid = [["." for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    ai_ships = []
    ai_mode = "hunt"
    ai_hits_pending = []
    ai_tried = set()
    ai_difficulty = "medium"
    ai_multi_bomb_used = False

def get_ai_move_delay():
    """
    Returns a random delay range for the AI based on difficulty.
    This makes easier AI feel slower and harder AI feel faster.
    """
    if ai_difficulty == "easy":
        return random.uniform(1.0, 3.0)
    elif ai_difficulty == "medium":
        return random.uniform(0.75, 2.0)
    elif ai_difficulty == "hard":
        return random.uniform(0.1, 0.5)

    # Fallback
    return 1.0

############################################################################# Server Communication #############################################################################
sock = None

# Networking Helpers
def _send(msg):
    if GAME_MODE == 2 and sock is not None:
        sock.sendall((json.dumps(msg)+ "\n").encode())

############################################################################# Variable Updates #############################################################################
def update_game_mode(mode):
    global GAME_MODE
    if mode in range(1,3):
        GAME_MODE = mode
    else:
        print("INVALID GAME MODE")

def update_game_state(new_state):
    global GAME_STATE
    GAME_STATE = new_state

    # Only send state updates to the server in multiplayer mode
    if GAME_MODE == 2 and sock is not None:
        message = {
            "type": "game_state",
            "state": GAME_STATE,
            "sender": player_id # Sender
        }
        _send(message)

def send_turn_timeout():
    # Multiplayer only: tell the server this player's turn expired.
    if GAME_MODE == 2:
        msg = {
            "type": "turn_timeout",
            "player_id": player_id,
        }
        _send(msg)
    else:
        print("BACKEND: Invalid Game Mode for Turn Timeout message")

def handle_turn_timeout(p_id):
    # Move the game into the timeout screen and record the result.
    global your_turn, player_id

    your_turn = not your_turn

    # Multiplayer only: p_id represents which player timed outs
    if p_id in (1,2):
        add_animation(5, (-1,-1), p_id)
    else:
        print("BACKEND: Invalid Time Out Player ID")

############################################################################# Pre-game Functions #############################################################################
# Utility Functions
def in_bounds(row, col):
    return 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE

def compute_ship_cells(row, col, size, orientation):
    cells = []
    for i in range(size):
        if orientation == "H":
            r, c = row, col + i
        else:
            r, c = row + i, col
        cells.append((r, c))
    return cells

def compute_multi_bomb_cells(center_row, center_col):
    # Build the 3x3 area centered on the clicked grid cell.
    # Any cells that would go out of bounds are ignored.
    cells = []

    for r in range(center_row - 1, center_row + 2):
        for c in range(center_col - 1, center_col + 2):
            if in_bounds(r, c):
                cells.append((r, c))

    return cells

def is_straight_and_contiguous(cells, size):
    if size <= 1:
        return True

    rows = [r for (r, _) in cells]
    cols = [c for (_, c) in cells]

    same_row = all(r == rows[0] for r in rows)
    same_col = all(c == cols[0] for c in cols)

    if not (same_row or same_col):
        return False

    if same_row:
        sorted_cols = sorted(cols)
        return sorted_cols == list(range(sorted_cols[0], sorted_cols[0] + size))

    sorted_rows = sorted(rows)
    return sorted_rows == list(range(sorted_rows[0], sorted_rows[0] + size))

def can_place_ship(cells):
    for r, c in cells:
        if not in_bounds(r, c):
            return False
        if grid[r][c] == "S":
            return False
    return True

def remove_ship_from_grid(cells):
    # Clears old ship footprint when a ship is moved
    global grid
    for r, c in cells:
        if in_bounds(r, c) and grid[r][c] == "S":
            grid[r][c] = "."

def update_ship_count(count):
    # Player 1 selects ship count; server forwards to both clients.
    if not (1 <= count <= 5):
        print("ship count must be 1-5")
        return False
    
    message = {
        "type": "ship_count",
        "count": count
    }
    _send(message)
    return True

def set_ship_count(count):
    global ship_count
    ship_count = count

############################################################################# Ship Placement #############################################################################
def place_ship(row, col, size, orientation):
    # Place a ship locally and store coordinates in ships array.
    orientation = (orientation or "").strip().upper()

    if size > 1 and orientation not in ("H", "V"):
        print("Invalid orientation. Use 'H' or 'V'.")
        return False

    if size <= 1:
        orientation = "H"

    cells = compute_ship_cells(row, col, size, orientation)

    if not is_straight_and_contiguous(cells, size):
        print("Invalid ship placement (must be straight and contiguous).")
        return False

    if not can_place_ship(cells):
        print("Invalid ship placement.")
        return False

    for r, c in cells:
        grid[r][c] = "S" # Marks ship presence on the board

    ships.append(cells) # Saves ship cells for later hit/sunk logic
    print(f"Ship of size {size} placed at {cells}")
    return True

# Reconstruct the backend board and ships list from a validated placement
# layout sent by board.py. This gives gameplay logic one authoritative ship
# representation instead of relying on temporary drag-and-drop state.
def load_ships_from_layout(ship_layouts):
    """
    ship_layouts: list of dicts like
    [{"row": 0, "col": 0, "size": 3, "orientation": "H"}, ...]
    """
    global grid, ships

    grid = [["." for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    ships = []

    for ship in ship_layouts:
        ok = place_ship(
            ship["row"],
            ship["col"],
            ship["size"],
            ship["orientation"]
        )
        if not ok:
            raise ValueError(f"Invalid ship layout: {ship}")

def submit_placement():
    global ships_locked

    # Send ship coordinate arrays to server so opponent can start after both lock.
    payload = [{"cells": [[r, c] for (r, c) in ship]} for ship in ships]

    msg = {
        "type": "place_ships",
        "ships": payload
    }
    
    ships_locked = True
    print("Submitting ship placement to server")
    _send(msg)

############################################################################# In-game Functions #############################################################################
# Bombing Logic
def can_send_bomb(row, col):
    # Prevents repeats and out-of-bounds shots on opponent grid.
    if not in_bounds(row, col):
        return False
    if (row, col) in shots_sent_hit:
        return False
    if (row, col) in shots_sent_miss:
        return False
    return True

def can_send_multi_bomb(cells):
    # Allow the attack if at least one square in the 3x3 area
    # has not already been targeted before.
    for row, col in cells:
        if (row, col) not in shots_sent_hit and (row, col) not in shots_sent_miss:
            return True
    return False

def send_bomb(row, col):
    global your_turn, GAME_STATE

    # This is the main gate: only shoot during RUNNING_GAME.
    if GAME_STATE != "RUNNING_GAME":
        print("BOMB FAILED: Not in RUNNING_GAME.")
        return

    # Turn-based gating prevents both players shooting at once.
    if not your_turn:
        print("BOMB FAILED: Not your turn.")
        return

    if not can_send_bomb(row, col):
        print("BOMB FAILED: Invalid bomb (repeat or out of bounds).")
        return

    msg = {
        "type": "bomb",
        "row": row,
        "col": col
    }

    _send(msg)
    print(f"BOMB SENT: {row},{col}")

def send_radar_scan(row, col):
    global radar_used
    if radar_used:
        print("RADAR FAILED: Already used.")
        return
    msg = {
        "type": "radar_scan",
        "center_row": row,
        "center_col": col
    }
    _send(msg)
    radar_used = True
    print(f"RADAR SENT: center=({row},{col})")

def send_multi_bomb(row, col):
    global your_turn, GAME_STATE, multi_bomb_used

    # Only allow multi-bomb during the real gameplay phase.
    if GAME_STATE != "RUNNING_GAME":
        print("MULTI-BOMB FAILED: Not in RUNNING_GAME.")
        return

    # Only the current player can fire.
    if not your_turn:
        print("MULTI-BOMB FAILED: Not your turn.")
        return

    # Each player can only use multibomb once per game.
    if multi_bomb_used:
        print("MULTI-BOMB FAILED: Already used this game.")
        return

    # Convert one clicked square into a valid 3x3 attack area.
    cells = compute_multi_bomb_cells(row, col)

    # Block the attack if the whole area was already used before.
    if not can_send_multi_bomb(cells):
        print("MULTI-BOMB FAILED: Entire 3x3 area was already targeted.")
        return

    # Send both the center point and the full list of target cells.
    # The server forwards this to the defender.
    msg = {
        "type": "multi_bomb",
        "center_row": row,
        "center_col": col,
        "cells": [[r, c] for (r, c) in cells]
    }

    _send(msg)
    multi_bomb_used = True
    print(f"MULTI-BOMB SENT: center=({row}, {col}) cells={cells}")

def get_ship_index(row, col):
    # Returns the ship index containing (row, col), or -1 if no ship occupies it.
    target = (row, col)
    print(f"BACKEND: get_ship_index - {target}")
    for i in range(0,len(ships)):
        print(f"BACKEND: Checking index {i}, ship {ships[i]} for {target}")
        if target in ships[i]:
            print("FOUND!")
            return i
        else:
            print("NOT FOUND.")
    return -1

def get_ship_coords(ship_index):
    global ships

    ship = ships[ship_index]
    return ship

def check_ship_sunk(ship_index):
    # True if every cell in this ship has been hit ("X").
    print(f"BACKEND: Checking ship {ship_index} index")
    if ship_index < 0 or ship_index >= len(ships):
        return False
    ship = ships[ship_index]
    for r, c in ship:
        print(f"Ship {r}, {c} = {grid[r][c]}")
        if grid[r][c] != "X":
            return False
    return True

def all_ships_sunk():
    # True if all ships are sunk; used for loss condition.
    global ships
    for ship in ships:
        for r, c in ship:
            if not grid[r][c] == "D":
                return False
    return True

def sink_opp_ship(ship_coords):
    global target_grid, opponent_ships_sunk

    for r, c in ship_coords:
        target_grid[r][c] = "D"
        print(f"Grid ({r},{c}) = {target_grid[r][c]}")

    opponent_ships_sunk += 1

def sink_own_ship(ship_index):
    global ships, grid
    ship = ships[ship_index]

    for r, c in ship:
        grid[r][c] = "D"
        print(f"Grid ({r},{c}) = {grid[r][c]}")

def get_num_ships_sunk():
    global ships

    num_sunk = len(ships)
    for ship in ships:
        for r, c in ship:
            if grid[r][c] != "D":
                num_sunk = num_sunk - 1
                break
    
    return num_sunk

def receive_radar_scan(center_row, center_col):
    cells = compute_multi_bomb_cells(center_row, center_col)
    found = any(grid[r][c] == "S" for r, c in cells)
    msg = {
        "type": "radar_result",
        "center_row": center_row,
        "center_col": center_col,
        "found": found
    }
    _send(msg)
    print(f"RADAR RECEIVED at ({center_row},{center_col}): found={found}")

# Shot Handling (Local)
def receive_shot(row, col):
    # Applies opponent shot to our grid and sends hit_status back for their UI.
    global shots_received_hit, shots_received_miss, grid, animations

    # Always reply to duplicate attacks instead of silently ignoring them.
    # This prevents the attacker from hanging while waiting for a result.
    if (row, col) in shots_received_hit or (row, col) in shots_received_miss:
        print("Repeat shot received.")

        msg = {
            "type": "hit_status",
            "row": row,
            "col": col,
            "status": False,
            "sunk": False,
            "ship_coords": None,
            "all_sunk": all_ships_sunk()
        }
        _send(msg)
        return

    hit = (grid[row][col] == "S")
    print(f"Hit: {hit}")
    ship_index = get_ship_index(row, col)
    print(f"Ship Index: {ship_index}")
    sunk = False
    all_sunk = False
    ship_coords = None

    if hit:
        grid[row][col] = "X" # Mark damage on our ship
        shots_received_hit.append((row,col))
        print("Your ship was hit!")
        sunk = check_ship_sunk(ship_index) # True if this hit finished the ship
        print(f"Sunk: {sunk}")
        
        if sunk:
            add_animation(3, (row,col), 2) # Add sunk animation
            sink_own_ship(ship_index)
            print(f"Ship sunk {row}, {col}")
            ship_coords = get_ship_coords(ship_index)
            all_sunk = all_ships_sunk() # True if we have no ships left
            print("Your ship was sunk!")
        else:
            add_animation(2, (row,col), 2) # Add hit animation
            
    else:
        add_animation(1, (row,col), 2) # Add miss aniation
        grid[row][col] = "O" # Mark opponent miss on the board
        shots_received_miss.append((row,col))
        print("Opponent missed.")
    
    print(f"BACKEND: Receiving shot ({row},{col}) - Hit: {hit}, Index: {ship_index}, Sunk: {sunk}, All Sunk: {all_sunk}")

    msg = {
        "type": "hit_status",
        "row": row,
        "col": col,
        "status": hit, # Shooter expects boolean hit/miss
        "sunk": sunk,
        "ship_coords": ship_coords,
        "all_sunk": all_sunk
    }
    _send(msg)

def receive_multi_bomb(cells, center_row, center_col):
    # This function is called on the defending player's side.
    # It applies the full 3x3 attack to the local board and
    # sends one combined result message back to the attacker.
    global shots_received_hit, shots_received_miss, grid

    results = []
    sunk_ships = []
    sunk_indexes = []
    
    anim_play = 0 # Decides which animation to play after a multi-shot as to not play 9 animations

    for row, col in cells:
        # If a square was already attacked before, record it as a repeat
        # so the attacker still gets a full response for all 3x3 cells.
        if (row, col) in shots_received_hit or (row, col) in shots_received_miss:
            results.append({
                "row": row,
                "col": col,
                "status": "repeat"
            })
            continue

        hit = (grid[row][col] == "S")
        ship_index = get_ship_index(row, col)

        if hit:
            # Mark this board square as damaged.
            grid[row][col] = "X"
            shots_received_hit.append((row,col))

            # Check whether this hit completed an entire ship.
            sunk = check_ship_sunk(ship_index)

            if sunk:
                if anim_play < 3:
                    anim_play = 3
                # Convert that whole ship from X to D to show it is sunk.
                sink_own_ship(ship_index)

                # Avoid adding the same sunk ship multiple times
                # if several cells from that ship were hit in the 3x3 area.
                if ship_index not in sunk_indexes:
                    sunk_indexes.append(ship_index)
                    sunk_ships.append(get_ship_coords(ship_index))
            else:
                if anim_play < 2:
                    anim_play = 2

            results.append({
                "row": row,
                "col": col,
                "status": "hit"
            })

        else:
            if anim_play < 1:
                anim_play = 1
            # Mark misses on the defending board.
            grid[row][col] = "O"
            shots_received_miss.append((row,col))
            results.append({
                "row": row,
                "col": col,
                "status": "miss"
            })

    # Use the original clicked center for the 3x3 animation. Edge and corner
    # attacks can produce fewer than 9 valid cells, so indexing into cells[4]
    # is not safe. Edge and corner multi-bombs may have fewer than 5 valid cells.
    add_animation(anim_play, (center_row, center_col), 2, multi_bomb=True)

    # After all 3x3 cells are processed, check if the defender has lost.
    all_sunk = all_ships_sunk()

    # Send one combined result back to the attacker.
    msg = {
        "type": "multi_bomb_result",
        "results": results,
        "sunk_ships": sunk_ships,
        "all_sunk": all_sunk
    }
    _send(msg)

def handle_hit_status(status, row, col, sunk, ship_coords, all_sunk):
    global animations
    coord = (row,col)

    if status:
        shots_sent_hit.append(coord)
        if sunk:
            add_animation(3, (row,col), 1)# Ship sunk animation
            sink_opp_ship(ship_coords)
            print("You sunk a battleship!")
        else:
            add_animation(2, (row,col), 1) # Ship hit animation
            target_grid[row][col] = "X"
            print("Your shot hit!")
    else:
        add_animation(1, (row,col), 1) # Miss animation
        shots_sent_miss.append(coord)
        target_grid[row][col] = "O"
    
    if all_sunk:
        global player_id
        game_over_msg = {
            "type": "game_over",
            "winner": player_id
        }
        _send(game_over_msg)

def handle_multi_bomb_result(results, sunk_ships, all_sunk):
    # This function runs on the attacking player's side.
    # It updates the attacker's target grid using the combined 3x3 result.
    anim_play = 0

    for result in results:
        row = result["row"]
        col = result["col"]
        status = result["status"]

        if status == "hit":
            if anim_play < 2:
                anim_play = 2
            # Record this square as a successful hit on the opponent board.
            if (row, col) not in shots_sent_hit:
                shots_sent_hit.append((row,col))
            target_grid[row][col] = "X"

        elif status == "miss":
            if anim_play < 1:
                anim_play = 1
            # Record this square as a miss on the opponent board.
            if (row, col) not in shots_sent_miss:
                shots_sent_miss.append((row,col))
            target_grid[row][col] = "O"

    # If any full ships were sunk by the 3x3 attack,
    # mark all of those ship coordinates as D on the target grid.
    for ship_coords in sunk_ships:
        sink_opp_ship(ship_coords)
    
    if len(sunk_ships) > 0:
        anim_play = 3

    if results:
        center_idx = len(results) // 2
        center_result = results[center_idx]
        r = center_result["row"]
        c = center_result["col"]
        add_animation(anim_play,(r,c),1,multi_bomb=True)

# Helper: hit counts per ship
def ship_hit_counts():
    # Returns list like [hits_on_ship1, hits_on_ship2, ...]
    counts = []
    for ship in ships:
        hits = 0
        for r, c in ship:
            if grid[r][c] == "X":
                hits += 1
        counts.append(hits)
    return counts

def handle_game_over(winner_id):
    global winner, player_id, GAME_STATE
    GAME_STATE = "GAME_OVER"
    if winner_id == player_id:
        winner = True
        print("GAME OVER! YOU WIN!")
    else:
        winner = False
        print("GAME OVER! YOU LOSE.")

def reset_game():
    global grid, target_grid, ships, player_id, winner, opponent_ships_sunk, sock
    global shots_received_hit, shots_received_miss, shots_sent_hit, shots_sent_miss
    global ship_count, your_turn, GAME_STATE, GAME_MODE, multi_bomb_used
    global ships_locked, all_ships_locked
    global radar_used, radar_flash_data

    grid = [["." for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    target_grid = [["." for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

    ships = []
    shots_received_hit = []
    shots_received_miss = []
    shots_sent_hit = []
    shots_sent_miss = []
    player_id = None
    winner = False
    opponent_ships_sunk = 0

    reset_ai()

    ship_count = 0
    your_turn = False
    multi_bomb_used = False
    radar_used= False
    radar_flash_data = None

    GAME_MODE = 0
    GAME_STATE = "MAIN_MENU"
    ships_locked = False
    all_ships_locked = False

    print("Game has been reset.")
    return True

############################################################################# Message Handling #############################################################################

# handle_server_message --> This function handles JSON messages passed to it by the servergit
def handle_server_message(message):
    global player_id, GAME_STATE, ship_count, ships_locked, all_ships_locked, your_turn

    mtype = message["type"]

    if mtype == "player_id":
        player_id = message["player"]
        print(f"You are Player {player_id}")
    
    elif mtype == "start_game":
        GAME_STATE = "SELECT_SHIPS"

    elif mtype == "set_ship_count":
        set_ship_count(message["count"])

    elif mtype == "all_ships_locked":
        all_ships_locked = True

    elif mtype == "bomb":
        # When opponent fires a bomb at us, we respond with a hit_status message
        row = message["row"]
        col = message["col"]
        receive_shot(row, col)

    elif mtype == "hit_status":
        # This message is received after sending a bomb
        # "status": True/False if the bomb was a hit/miss
        status = message["status"]
        row = message["row"]
        col = message["col"]
        sunk = message["sunk"]
        ship_coords = message["ship_coords"]
        all_sunk = message["all_sunk"]

        handle_hit_status(status,row,col,sunk,ship_coords,all_sunk)

    elif mtype == "multi_bomb":
        # Defender receives the full 3x3 target area from the attacker.
        cells = []
        for pair in message["cells"]:
            cells.append((pair[0], pair[1]))

        # Fixed for multiplayer defender-side multi-bomb animation crash.
        receive_multi_bomb(cells, message["center_row"], message["center_col"])

    elif mtype == "multi_bomb_result":
        # Attacker receives the final combined outcome of the 3x3 attack.
        results = message["results"]
        sunk_ships = message["sunk_ships"]
        all_sunk = message["all_sunk"]

        handle_multi_bomb_result(results,sunk_ships,all_sunk)

        # If the defender has no ships left after the multi-bomb,
        # notify the server that this player won.
        if all_sunk:
            game_over_msg = {
                "type": "game_over",
                "winner": player_id,
            }
            _send(game_over_msg)

    elif mtype == "change_turn":
        if your_turn:
            print("BACKEND: Opponent's Turn Now")
            your_turn = False
        else:
            print("BACKEND: Your Turn Now")
            your_turn = True

    elif mtype == "game_over":
        winner_id = message["winner"]
        handle_game_over(winner_id)

    elif mtype == "turn_timeout":
        p_id = message["player_id"]
        handle_turn_timeout(p_id)

    # Return the client to a safe state if the other player drops so the UI
    # does not stay stuck in a multiplayer match with no opponent.
    elif mtype == "opponent_disconnected":
        print("BACKEND: Opponent disconnected.")
        GAME_STATE = "MAIN_MENU"
        your_turn = False

    elif mtype == "radar_scan":
        receive_radar_scan(message["center_row"], message["center_col"])

    elif mtype == "radar_result":
        global radar_flash_data
        radar_flash_data = {
            "center_row": message["center_row"],
            "center_col": message["center_col"],
            "found": message["found"]
        }
        print(f"RADAR RESULT: found={message['found']}")
    else:
        print(f"Unknown Message: {message}")

# Read newline-delimited JSON messages from the socket buffer.
# TCP can split or combine packets, so only parse complete lines.
def listen_to_server():
    global sock
    buffer = ""
    message = ""

    while True:
        try:
            data = sock.recv(4096).decode()
            if not data:
                print("BACKEND: Server connection closed.")
                break

            buffer += data

            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                if not line.strip():
                    continue
                message = json.loads(line)
                handle_server_message(message)

        except Exception as e:
            print("BACKEND listen_to_server error:", e)
            break

"""
The following functions work as follows:
    board.py runs init_network():
        Try to connect to server
            if the server is not started yet
                start the server
            else
                connect to the server

This allows board.py to be be the only file needing to be run
The first client that runs it hosts the server and is player 1
"""
def start_local_server():
    global server_host
    if server_host:
        return
    try:
        import server
        threading.Thread(target=server.main, daemon=True).start()
        server_host = True
    except OSError:
        print("BACKEND: Another server instance started")
        pass  # another instance started it first

server_started = False
server_host = False # True if this instance is hosting the server

def connect_to_server():
    global sock, server_started
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    while True:
        try:
            sock.connect((SERVER_IP, PORT))
            print("Connected to server.")
            return sock

        except ConnectionRefusedError:
            if not server_started:
                print("Server not running. Starting local server...")
                start_local_server()
                time.sleep(1) # Giving server time to bind
                server_started = True
            else:
                print("Waiting for server...")
                time.sleep(1)

def init_network():
    global sock
    sock = connect_to_server()
    threading.Thread(target=listen_to_server, daemon=True).start()
    print("Connected to server")

def disconnect_from_server():
    global sock, server_started, server_host
    if sock:
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except:
            pass
        sock.close()
        sock = None

    if server_host:
        import server
        server.running = False
        server_host = False
    server_started = False