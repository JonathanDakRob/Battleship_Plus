#This file will handle the frontend/main loop of our battleship game

import pygame
import asyncio

import sys
import os
import math
import time

import backend
from config import *
from entities import * # Import Cells and Ships classes
from utils import *
from audio import *
from animation import *
from display import *
from drawing import *
from state import *

# ------------------ CONFIG ------------------

# To trigger the time out screen, set this value to the current time (time.monotonic())
time_out_start = -1.0


# ------------------ SHIP CREATION ------------------
def create_ships(num_ships):
    global ships
    ships.clear()

    ships_start_x = GRID_PADDING + GRID_SIZE * CELL_SIZE + 20
    ships_start_y = top_grid_y

    for ship_length in range(1, num_ships + 1):
        ship = Ship(ship_length, ships_start_x, ships_start_y)
        ships.append(ship)

        ships_start_y += (ship_length * CELL_SIZE) + 10

# Rebuild the authoritative backend ship layout from the draggable UI ships
# right before LOCK SHIPS. This prevents the frontend placement state and
# backend hit/sunk logic from drifting out of sync.
def sync_backend_placement_from_ui():
    layout = []

    for ship in ships:
        if not ship.placed or ship.grid_row is None or ship.grid_col is None:
            return False

        layout.append({
            "row": ship.grid_row,
            "col": ship.grid_col,
            "size": ship.length,
            "orientation": ship.orientation
        })

    try:
        backend.load_ships_from_layout(layout)
        return True
    except ValueError as e:
        print("PLACEMENT SYNC ERROR:", e)
        return False

# Reset transient frontend-only state so a new game does not inherit
# leftover radar previews, timers, or pending AI turn delays.
def reset_local_ui_state():
    global ships_selected, started_running_game, multi_bomb_mode, ships, game_mode
    global match_start_time, turn_start_time, current_turn_time_left
    global turn_timeout_sent, last_turn_state, ai_turn_due_time
    global radar_mode, radar_flash

    ships_selected = False
    started_running_game = False
    multi_bomb_mode = False
    radar_mode = False
    radar_flash = None
    game_mode = 0
    ships.clear()

    match_start_time = None
    turn_start_time = None
    current_turn_time_left = TURN_TIME_LIMIT
    turn_timeout_sent = False
    last_turn_state = None
    ai_turn_due_time = None

def start_game_timers():
    global match_start_time, turn_start_time
    global current_turn_time_left
    global turn_timeout_sent, last_turn_state

    now = time.monotonic()
    match_start_time = now
    turn_start_time = now
    turn_timeout_sent = False
    last_turn_state = backend.your_turn

def reset_turn_timer():
    global turn_start_time, current_turn_time_left
    global turn_timeout_sent, last_turn_state

    turn_start_time = time.monotonic()
    current_turn_time_left = TURN_TIME_LIMIT
    turn_timeout_sent = False
    last_turn_state = backend.your_turn

def update_running_game_timers():
    global  current_turn_time_left, time_out_start
    global turn_timeout_sent, last_turn_state, multi_bomb_mode

    if match_start_time is None:
        return

    now = time.monotonic()

    # Reset the turn timer whenever the turn changes
    if last_turn_state is None or backend.your_turn != last_turn_state:
        reset_turn_timer()

    # Per-turn timer
    if turn_start_time is not None:
        current_turn_time_left = max(
            0,
            TURN_TIME_LIMIT - int(now - turn_start_time)
        )

    # Turn timed out
    if current_turn_time_left <= 0:
        multi_bomb_mode = False

        # Single-player: just lose the turn
        if backend.GAME_MODE == 1:
            if backend.your_turn:
                backend.your_turn = False
                trigger_animation(5, (-1,-1), 0)
                reset_turn_timer()

        # Multiplayer: notify server
        elif backend.GAME_MODE == 2:
            if backend.your_turn and not turn_timeout_sent:
                backend.send_turn_timeout()
                turn_timeout_sent = True

def draw_clear_screen(screen):
    screen.fill(BG_COLOR)

# ------------------ START SERVER FUNCTION ------------------
import threading
def start_network():
    backend.init_network()
    backend.update_game_state("WAITING_FOR_PLAYERS_TO_CONNECT")

# ------------------------------------ GAMEPLAY LOOP ------------------------------------
async def main():
    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        game_state = backend.GAME_STATE
        
        if backend.player_id != None:
            opponent_id = (backend.player_id % 2) + 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            game_state = backend.GAME_STATE
            
            # ------------------ MAIN MENU STATE ------------------
            if game_state == "MAIN_MENU":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    # Single player button sets game mode to 1 and moved to the select difficulty stage
                    if SINGLE_PLAYER_RECT.collidepoint(event.pos):
                        play_button_click(1)
                        button_click_times[id(SINGLE_PLAYER_RECT)] = time.monotonic()
                        reset_local_ui_state()
                        backend.update_game_mode(1)
                        backend.update_game_state("SELECT_DIFFICULTY")

                    # Multi-player button setes game mode to 2 and waiting for another player to connect
                    if MULTI_PLAYER_RECT.collidepoint(event.pos):
                        play_button_click(1)
                        button_click_times[id(MULTI_PLAYER_RECT)] = time.monotonic()
                        backend.update_game_state("LOADING")
                        backend.update_game_mode(2)

                        threading.Thread(target=start_network, daemon=True).start()

            # ------------------ LOADING STATE ------------------
            elif game_state == "LOADING":
                pass

            # ------------------ WAITING FOR PLAYERS TO CONNECT STATE ------------------
            elif game_state == "WAITING_FOR_PLAYERS_TO_CONNECT":
                pass

            # ------------------ SHIP SELECTION STATE ------------------
            elif game_state == "SELECT_SHIPS":
                # Single player
                if backend.GAME_MODE == 1:
                    if event.type == pygame.KEYDOWN:
                        if event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5]:
                            ship_count = int(event.unicode)
                            backend.set_ship_count(ship_count)
                            create_ships(ship_count)
                            backend.update_game_state("PLACE_SHIPS")
                
                # Multi-player
                elif backend.GAME_MODE == 2:
                    if backend.player_id == player1_id:
                        if event.type == pygame.KEYDOWN:
                            if event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5]:
                                ship_count = int(event.unicode)
                                print(f"Selected {ship_count} ships")

                                create_ships(ship_count)
                                backend.update_ship_count(ship_count)
                                backend.update_game_state("PLACE_SHIPS")

                    if backend.player_id == player2_id:
                        ship_count = backend.ship_count
                        if ship_count > 0 and ships_selected == False:
                            ships_selected = True
                            print(f"Player {player1_id} selected {ship_count} ships")
                            print(f"SHIP COUNT: {ship_count}")
                            create_ships(ship_count)

                            backend.update_game_state("PLACE_SHIPS")

            # ------------------ SHIP PLACING STATE ------------------
            elif game_state == "PLACE_SHIPS":
                # Single player
                if backend.GAME_MODE == 1:
                    for ship in ships:
                        ship.handle_event(event)

                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        if RESET_BUTTON_RECT.collidepoint(event.pos):
                            play_button_click(2)
                            backend.grid = [["." for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
                            create_ships(len(ships))

                        # Only start the match after every visual ship has been converted into
                        # canonical backend state. This keeps ship placement validation and
                        # gameplay damage logic using the same source of truth.
                        elif LOCK_BUTTON_RECT.collidepoint(event.pos):
                            all_valid = all(s.placed for s in ships)
                            if all_valid and sync_backend_placement_from_ui():
                                play_button_click(2)
                                backend.ai_place_ships(len(ships))
                                backend.your_turn = True
                                backend.update_game_state("RUNNING_GAME")

                # Multi-player    
                elif backend.GAME_MODE == 2:
                    for ship in ships:
                        ship.handle_event(event)    

                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        if RESET_BUTTON_RECT.collidepoint(event.pos):
                            print("Resetting Ships...")

                            # Recreate the draggable ship set once after clearing the placement board.
                            # Rebuilding it inside a loop is redundant and can cause confusing reset behavior.
                            backend.grid = [["." for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
                            create_ships(len(ships))

                        # Only start the match after every visual ship has been converted into
                        # canonical backend state. This keeps ship placement validation and
                        # gameplay damage logic using the same source of truth.
                        elif LOCK_BUTTON_RECT.collidepoint(event.pos):
                            all_valid = all(s.placed for s in ships)
                            if all_valid and sync_backend_placement_from_ui():
                                backend.submit_placement()
                                backend.update_game_state("WAITING_FOR_OPPONENT")

            # ------------------ WAITING FOR OTHER PLAYER STATE ------------------
            elif game_state == "WAITING_FOR_OPPONENT":
                # Multi-player only
                if backend.all_ships_locked:
                    backend.update_game_state("RUNNING_GAME")

            # ------------------ RUNNING GAME STATE ------------------
            elif game_state == "RUNNING_GAME":
                # Start match / turn timers once when gameplay begins.
                if not started_running_game:
                    started_running_game = True

                    if backend.GAME_MODE == 2:
                        # Player 1 starts in multiplayer
                        backend.your_turn = (backend.player_id == player1_id)

                    start_game_timers()

                # Single player
                if backend.GAME_MODE == 1:
                    if backend.your_turn:
                        # If it is the player's turn again, clear any pending AI move
                        ai_turn_due_time = None

                        if event.type == pygame.KEYDOWN:
                            if event.key == pygame.K_m:
                                # Only allow multi-bomb mode if it has not already been used.
                                if backend.multi_bomb_used:
                                    print("MULTI-BOMB already used this game.")
                                    multi_bomb_mode = False
                                else:
                                    multi_bomb_mode = not multi_bomb_mode
                                    print(f"MULTI-BOMB MODE: {multi_bomb_mode}")

                            elif event.key == pygame.K_r:
                                if backend.radar_used:
                                    print("RADAR already used.")
                                    radar_mode = False
                                else:
                                    radar_mode = not radar_mode
                                    print(f"RADAR MODE: {radar_mode}")

                        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                            if backend.your_turn and not backend.wait_for_animation:
                                for cell in top_grid:
                                    if cell.rect.collidepoint(mouse_pos):
                                        r, c = cell.get_coords()

                                        if radar_mode:
                                            used, found = backend.player_radar_scan(r, c)
                                            if used:
                                                radar_mode = False
                                                cells = backend.compute_multi_bomb_cells(r, c)
                                                radar_flash = {
                                                    "cells": cells,
                                                    "result": found,
                                                    "start": time.monotonic()
                                                }
                                            break
                                        
                                        elif multi_bomb_mode:
                                            print(f"FRONTEND: Sending SINGLE-PLAYER MULTI-BOMB to {(r, c)}")
                                            used_successfully, all_sunk = backend.player_multi_bomb_ai(r, c)

                                            # Only disable the mode after a successful use.
                                            if used_successfully:
                                                multi_bomb_mode = False

                                                if all_sunk:
                                                    backend.winner = True
                                                    backend.update_game_state("GAME_OVER")
                                                else:
                                                    # Multi-bomb always ends the player's turn in single-player.
                                                    backend.your_turn = False
                                            break ###

                                        else:
                                            if (r, c) not in backend.shots_sent_hit and (r, c) not in backend.shots_sent_miss:
                                                hit, sunk, all_sunk = backend.player_shoot_ai(r, c)
                                                if all_sunk:
                                                    backend.winner = True
                                                    backend.update_game_state("GAME_OVER")
                                                else:
                                                    if not hit:
                                                        backend.your_turn = False
                                            break
                    else:
                        # Start a random AI delay so the AI does not always move instantly
                        if ai_turn_due_time is None:
                            ai_delay = backend.get_ai_move_delay()
                            ai_turn_due_time = time.monotonic() + ai_delay

                        elif time.monotonic() >= ai_turn_due_time and not backend.wait_for_animation:
                            # Give the AI a random chance to use this one-time multi-bomb
                            if backend.ai_should_use_multi_bomb():
                                center_row, center_col, hit, all_sunk = backend.ai_take_multi_bomb_turn()
                                print(f"AI multi-bombed around ({center_row}, {center_col})")
                            else:
                                row, col, hit, sunk, all_sunk = backend.ai_take_turn()

                            if all_sunk:
                                backend.winner = False
                                backend.update_game_state("GAME_OVER")
                            else:
                                backend.your_turn = True
                                reset_turn_timer()

                            ai_turn_due_time = None

                # Multi-player
                elif backend.GAME_MODE == 2:
                    # Initialize turn rule once when the match begins
                    # if not started_running_game:
                        # started_running_game = True

                        # This gives Player 1 the first move without needing server logic yet.
                        # backend.your_turn = (backend.player_id == player1_id)

                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_m:
                            # Only allow multibomb mode if it has not already been used.
                            if backend.multi_bomb_used:
                                print("MULTI-BOMB already used this game.")
                                multi_bomb_mode = False
                            else:
                                # Press M to toggle multi-bomb mode on or off.
                                multi_bomb_mode = not multi_bomb_mode
                                print(f"MULTI-BOMB MODE: {multi_bomb_mode}")

                        elif event.key == pygame.K_r:
                            if backend.radar_used:
                                print("RADAR already used.")
                                radar_mode = False
                            else:
                                radar_mode = not radar_mode
                                print(f"RADAR MODE: {radar_mode}")

                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        # Gate input so only the active player can fire
                        # if backend.your_turn:
                            # Only allow shots on the opponent grid (top grid)

                        for cell in top_grid:
                            if cell.rect.collidepoint(mouse_pos):
                                cell.handle_click()
                                click_row, click_col = cell.get_coords()

                                # Can only send bomb if it is your turn
                                if backend.your_turn:
                                    if radar_mode:
                                        backend.send_radar_scan(click_row, click_col)
                                        radar_mode = False
                                        break
                                    elif multi_bomb_mode:
                                        print(f"FRONTEND: Sending MULTI-BOMB to {click_row, click_col}")
                                        backend.send_multi_bomb(click_row, click_col)
                                        multi_bomb_mode = False
                                    else:
                                        print(f"FRONTEND: Sending Bomb to {click_row, click_col}")
                                        backend.send_bomb(click_row, click_col)
                                
                                break

            # ------------------ TIME RAN OUT STATE ---------------
            elif game_state == "TIME_RAN_OUT":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if BUTTON_RECT.collidepoint(mouse_pos):
                        backend.disconnect_from_server()
                        backend.reset_game()
                        reset_local_ui_state()

            # ------------------ GAME OVER STATE ------------------
            elif game_state == "GAME_OVER":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if BUTTON_RECT.collidepoint(mouse_pos):
                        backend.disconnect_from_server()
                        backend.reset_game()
                        reset_local_ui_state()

            # ------------------ SELECT DIFFICULTY STATE ------------------
            # Single player only
            elif game_state == "SELECT_DIFFICULTY":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if EASY_RECT.collidepoint(event.pos):
                        play_button_click(1)
                        button_click_times[id(EASY_RECT)] = time.monotonic()
                        backend.ai_difficulty = "easy"
                        backend.update_game_state("SELECT_SHIPS")
            
                    elif MEDIUM_RECT.collidepoint(event.pos):
                        play_button_click(1)
                        button_click_times[id(MEDIUM_RECT)] = time.monotonic()
                        backend.ai_difficulty = "medium"
                        backend.update_game_state("SELECT_SHIPS")
            
                    elif HARD_RECT.collidepoint(event.pos):
                        play_button_click(1)
                        button_click_times[id(HARD_RECT)] = time.monotonic()
                        backend.ai_difficulty = "hard"
                        backend.update_game_state("SELECT_SHIPS")
                    
                    elif BUTTON_RECT.collidepoint(event.pos):
                        play_button_click(1)
                        backend.update_game_state("MAIN_MENU")
                        backend.reset_game()
                        reset_local_ui_state()

        #  ------------------ TIMER UPDATES ------------------
        # Keep the turn timer running once per main loop while gameplay is active.
        # This makes timeout behavior consistent across single-player and multiplayer.
        if backend.GAME_STATE == "RUNNING_GAME":
            update_running_game_timers()
            game_state = backend.GAME_STATE

        # ------------------ SINGLE PLAYER AI AUTO-TURN ------------------
        if backend.GAME_STATE == "RUNNING_GAME" and backend.GAME_MODE == 1:
            if not backend.your_turn and not backend.wait_for_animation:
                # Start a random AI delay so the AI does not always move instantly
                if ai_turn_due_time is None:
                    ai_delay = backend.get_ai_move_delay()
                    ai_turn_due_time = time.monotonic() + ai_delay

                elif time.monotonic() >= ai_turn_due_time:
                    ai_hit = False
                    all_sunk = False
                    ai_used_multi_bomb = False

                    # Give the AI a random chance to use this one-time multi-bomb
                    if backend.ai_should_use_multi_bomb():
                        ai_used_multi_bomb = True
                        center_row, center_col, ai_hit, all_sunk = backend.ai_take_multi_bomb_turn()
                        print(f"AI multi-bombed around ({center_row}, {center_col})")
                    else:
                        row, col, hit, sunk, all_sunk = backend.ai_take_turn()
                        ai_hit = hit

                    if all_sunk:
                        backend.winner = False
                        backend.update_game_state("GAME_OVER")
                    else:
                        # Standard single-player turn rule:
                        # normal shot hit = AI keeps turn, normal shot miss = player gets turn.
                        # Multi-bomb always consumes the turn for balance.
                        if ai_hit and not ai_used_multi_bomb:
                            backend.your_turn = False
                        else:
                            backend.your_turn = True
                            reset_turn_timer()

                    # Clear the pending AI move time so the next AI move
                    # can be scheduled again if it keeps the turn.
                    ai_turn_due_time = None
            else:
                # If it is the player's turn again, clear any pending AI move
                ai_turn_due_time = None

        # ------------------ DRAWING ------------------
        draw_background(game_state)
        draw_volume_bar()
        handle_volume_input()

        play_waves()

        if game_state == "MAIN_MENU":
            draw_main_menu(mouse_pos)

        elif game_state == "WAITING_FOR_PLAYERS_TO_CONNECT":
            draw_waiting_for_player(f"Waiting for opponent to connect...", opponent_id)
            
        elif game_state == "LOADING":
            draw_loading_circle(loading_angle)
            loading_angle += 0.1
        
        elif game_state == "SELECT_SHIPS":
            # Single player
            if backend.GAME_MODE == 1:
                draw_ship_selection()
            # Multi-player
            if backend.GAME_MODE == 2:
                if backend.player_id == player1_id:
                    draw_ship_selection()
                if backend.player_id == player2_id:
                    draw_waiting_for_player(f"Player {player1_id} will select 1-5 ships", player1_id)
        
        elif game_state == "PLACE_SHIPS":
            # Single player
            if backend.GAME_MODE == 1:
                draw_ship_placement()
                draw_coordinates(GRID_PADDING, GRID_PADDING)
                draw_control_buttons(mouse_pos)
            # Multi-player
            if backend.GAME_MODE == 2:
                draw_ship_placement()
                draw_coordinates(GRID_PADDING, GRID_PADDING)
                draw_control_buttons(mouse_pos)
        
        elif game_state == "WAITING_FOR_OPPONENT":
            # Only for multi-player
            draw_waiting_for_player(f"Player {opponent_id} is still placing their ships", opponent_id)

        elif game_state == "RUNNING_GAME":
            # Update turn timers once per main loop before drawing. Keeping timeout logic
            # in one place avoids duplicate turn-loss checks in the same frame.
            draw_coordinates(GRID_PADDING, top_grid_y)
            draw_coordinates(GRID_PADDING, bottom_grid_y)
            for cell in all_cells:
                cell.draw(screen, mouse_pos)
            
            if multi_bomb_mode:
                draw_multi_bomb_preview(mouse_pos)

            if radar_mode:
                draw_radar_preview(mouse_pos)

            if backend.radar_flash_data is not None:
                cells = backend.compute_multi_bomb_cells(
                    backend.radar_flash_data["center_row"],
                    backend.radar_flash_data["center_col"]
                )
                radar_flash = {
                    "cells": cells,
                    "result": backend.radar_flash_data["found"],
                    "start": time.monotonic()
                }
                backend.radar_flash_data = None

            draw_radar_flash()

            draw_backend_ships()
            draw_status_panel()
            draw_marks() 

            # Draw animation if there are any queued
            if len(backend.animations) > 0:
                new_animation = backend.remove_animation()
                print(f"Triggering Animation: {new_animation}")
                trigger_animation(new_animation["type"], new_animation["loc"], new_animation["board"], new_animation["multi_bomb"])
            if len(animations) > 0:
                draw_animation(screen)

        elif game_state == "GAME_OVER":
            draw_game_over(backend.winner)
            draw_button(mouse_pos, color=(0,255,0), text="Main Menu")

        elif game_state == "SINGLE_PLAYER":
            draw_message("Single player construction in progress")
            draw_button(mouse_pos)

        elif game_state == "SELECT_DIFFICULTY":
            draw_difficulty_selection(mouse_pos)   
            draw_button(mouse_pos)     

        pygame.display.flip()
        clock.tick(60)

        await asyncio.sleep(0)
    
    pygame.quit()
    sys.exit()

asyncio.run(main())

