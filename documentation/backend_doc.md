# Battleship Backend Documentation (`backend.py`)

## Overview

This module implements the **game logic and networking layer** for a Battleship client.

It is responsible for:

- Maintaining board state
- Validating ship placement
- Handling bombing logic
- Tracking hits, misses, and sunk ships
- Synchronizing with the server
- Managing game state transitions

It acts as the bridge between:

- `board.py` (frontend)
- `server.py` (multiplayer relay server)

---

# Global Configuration

| Name | Type | Description |
|------|------|------------|
| `SERVER_IP` | `str` | Server address (`"127.0.0.1"`) |
| `PORT` | `int` | Server port (5000) |
| `BOARD_SIZE` | `int` | Board dimension (10x10 grid) |

---

# Networking State

| Name | Type | Description |
|------|------|------------|
| `sock` | `Optional[socket.socket]` | TCP connection to server |

---

# Game Board Memory

## Player Board

| Name | Type | Description |
|------|------|------------|
| `grid` | `List[List[str]]` | Player board (10x10) |

Cell Values:
- `"."` = empty
- `"S"` = ship
- `"X"` = hit
- `"O"` = miss
- `"D"` = sunk ship cell

---

## Target Board (Opponent View)

| Name | Type | Description |
|------|------|------------|
| `target_grid` | `List[List[str]]` | Tracks shots fired at opponent |

---

# Game State Variables

| Name | Type | Description |
|------|------|------------|
| `ship_count` | `int` | Number of ships selected |
| `ships` | `List[List[Tuple[int,int]]]` | Ship coordinate storage |
| `player_id` | `Optional[int]` | Player ID (1 or 2) |
| `your_turn` | `bool` | Whether player may fire |
| `winner` | `bool` | True if player won |
| `ships_locked` | `bool` | Whether local ships are locked |
| `all_ships_locked` | `bool` | Whether both players locked ships |
| `opponent_ships_sunk` | `int` | Count of enemy ships sunk |
| `GAME_STATE` | `str` | Current game state |

### Valid `GAME_STATE` Values

- `WAITING_FOR_PLAYERS_TO_CONNECT`
- `SELECT_SHIPS`
- `PLACE_SHIPS`
- `WAITING_FOR_OPPONENT`
- `RUNNING_GAME`
- `GAME_OVER`


---

# Shot Tracking

| Name | Type |
|------|------|
| `shots_received_hit` | `List[Tuple[int,int]]` |
| `shots_received_miss` | `List[Tuple[int,int]]` |
| `shots_sent_hit` | `List[Tuple[int,int]]` |
| `shots_sent_miss` | `List[Tuple[int,int]]` |

---

# Networking Functions

---

## `_send(msg: dict) -> None`

Sends a JSON message to the server with newline delimiter.

---

## `init_network() -> None`

Initializes networking:

1. Connects to server (or starts local server if needed)
2. Starts background listener thread

---

## `connect_to_server() -> socket.socket`

Attempts to connect to server.

If server not running:
- Starts local server
- Retries connection

---

## `start_local_server() -> None`

Imports and launches `server.main()` in a daemon thread.

---

## `listen_to_server() -> None`

Background loop:

- Receives newline-delimited JSON
- Parses messages
- Calls `handle_server_message()`

---

# Pre-Game Utility Functions

---

## `in_bounds(row: int, col: int) -> bool`

Returns True if coordinates are within board limits.

---

## `compute_ship_cells(row: int, col: int, size: int, orientation: str) -> List[Tuple[int,int]]`

Computes ship coordinate list from origin and orientation.

---

## `is_straight_and_contiguous(cells: List[Tuple[int,int]], size: int) -> bool`

Validates that cells form a straight contiguous line.

---

## `can_place_ship(cells: List[Tuple[int,int]]) -> bool`

Returns False if:
- Out of bounds
- Overlapping another ship

---

## `remove_ship_from_grid(cells: List[Tuple[int,int]]) -> None`

Clears `"S"` markers from grid.

---

## `update_game_state(new_state: str) -> None`

Updates `GAME_STATE` locally and notifies server.

---

## `update_ship_count(count: int) -> bool`

Validates ship count (1–5) and sends to server.

---

## `set_ship_count(count: int) -> None`

Sets local ship count (received from server).

---

# Ship Placement

---

## `place_ship(row: int, col: int, size: int, orientation: str) -> bool`

Places a ship locally if valid.

- Updates `grid`
- Appends to `ships`
- Returns True if successful

---

## `submit_placement() -> None`

Sends ship coordinates to server and locks ships.

---

# Bombing & Combat Logic

---

## `can_send_bomb(row: int, col: int) -> bool`

Prevents:
- Out-of-bounds shots
- Duplicate shots

---

## `send_bomb(row: int, col: int) -> None`

Sends bomb message if:

- `GAME_STATE == RUNNING_GAME`
- `your_turn == True`
- Shot is valid

---

## `receive_shot(row: int, col: int) -> None`

Handles opponent bomb:

- Updates grid
- Determines hit/miss
- Checks sunk condition
- Sends `hit_status` back

---

## `handle_hit_status(status: bool, row: int, col: int, sunk: bool, ship_coords: list, all_sunk: bool) -> None`

Handles result of shot fired by player:

- Updates `target_grid`
- Tracks hits/misses
- Handles sunk ships
- Sends `game_over` if needed

---

# Ship State Helpers

---

## `get_ship_index(row: int, col: int) -> int`

Returns index of ship occupying cell or -1.

---

## `get_ship_coords(ship_index: int) -> List[Tuple[int,int]]`

Returns ship coordinate list.

---

## `check_ship_sunk(ship_index: int) -> bool`

Returns True if all ship cells are `"X"`.

---

## `all_ships_sunk() -> bool`

Returns True if all player ships are destroyed.

---

## `sink_opp_ship(ship_coords: List[Tuple[int,int]]) -> None`

Marks opponent ship as sunk in `target_grid`.

---

## `sink_own_ship(ship_index: int) -> None`

Marks own ship as sunk in `grid`.

---

## `get_num_ships_sunk() -> int`

Returns number of player ships fully sunk.

---

## `ship_hit_counts() -> List[int]`

Returns number of hits per ship.

---

# Game Control

---

## `handle_game_over(winner_id: int) -> None`

Sets:

- `GAME_STATE = "GAME_OVER"`
- `winner = True/False`

---

## `reset_game() -> bool`

Resets:

- Grids
- Ships
- Shots
- State variables

Returns True after reset.

---

# Server Message Handling

---

## `handle_server_message(message: dict) -> None`

Dispatches messages received from server.

### Supported Message Types

| Type | Action |
|------|--------|
| `"player_id"` | Sets player ID |
| `"start_game"` | Moves to `SELECT_SHIPS` |
| `"set_ship_count"` | Sets local ship count |
| `"all_ships_locked"` | Enables match start |
| `"bomb"` | Calls `receive_shot()` |
| `"hit_status"` | Calls `handle_hit_status()` |
| `"change_turn"` | Toggles `your_turn` |
| `"game_over"` | Calls `handle_game_over()` |

---

# Architecture Summary

The backend:

- Owns all game logic
- Owns board memory
- Validates moves
- Tracks win/loss
- Synchronizes via JSON protocol
- Runs networking listener in background thread

It acts as the authoritative local game engine for each player.