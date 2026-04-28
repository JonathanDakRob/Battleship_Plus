#This file handles the server for Battleship
#server.py

import socket
import json
import threading
import time

HOST = "0.0.0.0"
PORT = 5000

clients = []

# Game related memory
player1_locked = False
player2_locked = False
player_turn = 1

GAME_OVER = False
winner = None

def send(conn, msg):
    conn.sendall((json.dumps(msg) + "\n").encode())

def handle_message(conn, player_index, message):
    global player1_locked, player2_locked, GAME_OVER, winner

    # Validate message shape before dispatching. The server is mostly a relay,
    # but one malformed payload should not break the whole match thread.
    if not isinstance(message, dict) or "type" not in message:
        print(f"SERVER: Ignoring malformed message: {message}")
        return

    # Do not try to relay gameplay messages unless both player sockets still
    # exist. This avoids index errors and bad relays after a disconnect.
    if len(clients) < 2:
        print("SERVER: Cannot relay message; opponent is not connected.")
        return

    opponent = clients[1 - player_index]

    if message["type"] == "game_state":
        state = message["state"]
        sender = message["sender"]
        print(f"SERVER: Player {sender} reached state: {state}")

    elif message["type"] == "ship_count":
        new_message = {
            "type": "set_ship_count",
            "count": message["count"]
        }
        send(conn,new_message)
        send(opponent,new_message)

    elif message["type"] == "place_ships":
        print("SERVER: Ships Placed and Locked")
        if player_index == 0:
            player1_locked = True
        else:
            player2_locked = True

        if player1_locked and player2_locked:
            all_locked_msg = {
                "type": "all_ships_locked"
            }
            send(conn,all_locked_msg)
            send(opponent,all_locked_msg)

    elif message["type"] == "bomb":
        row = message["row"]
        col = message["col"]
        coord = (row,col)
        print(f"SERVER: Player {player_index} shoots opponent at {coord}")
        send(opponent,message)

    elif message["type"] == "hit_status":
        if message["all_sunk"] == True:
            GAME_OVER = True
        if message["status"] == False:
            changeTurn_msg = {
                "type": "change_turn"
            }
            send(opponent,changeTurn_msg)
            send(conn,changeTurn_msg)
        send(opponent,message)

    elif message["type"] == "multi_bomb":
        # The attacker already computed the 3x3 target area in backend.py.
        # The server's job is just to forward that attack request to the opponent.
        print(f"SERVER: Player {player_index + 1} used multi_bomb")
        send(opponent,message)

    elif message["type"] == "multi_bomb_result":
        # The defender sends back one combined result for the whole 3x3 attack.
        # If all ships are sunk after this attack, the game is now over.
        if message["all_sunk"] == True:
            GAME_OVER = True

        # Send the full multi-bomb result back to the attacking player
        # so their board can update all hit/miss cells at once.
        send(opponent,message)

        # Multi-bomb always consumes the turn, so after it finishes,
        # both clients receive a change_turn message.
        changeTurn_msg = {
            "type": "change_turn"
        }
        send(opponent, changeTurn_msg)
        send(conn, changeTurn_msg)

    elif message["type"] == "radar_scan":
        print(f"SERVER: Player {player_index + 1} used radar scan")
        send(opponent, message)

    elif message["type"] == "radar_result":
        send(opponent, message)

    # Broadcast the timeout event to both clients so they can stay synchronized
    # on whose turn was forfeited.
    elif message["type"] == "turn_timeout":
        # This player's turn expired, so switch turns for both clients.
        print(f"SERVER: Player {message['player_id']} turn timed out")
        
        send(opponent, message)
        send(conn, message)

    elif message["type"] == "time_ran_out":
        # Player's turn timed out

        send(opponent, message)
        send(conn, message)

    elif message["type"] == "game_over":
        GAME_OVER = True
        winner = message["winner"]

        send(opponent,message)
        send(conn,message)

    else:
        print(f'SERVER: Player {player_index} sending {message["type"]} message to opponent')
        send(opponent,message)

running = False

def handle_client(player_index):
    global clients, running
    buffer = ""
    message = ""

    conn = clients[player_index]

    global p2_game_state, player1_locked, player2_locked
    global GAME_OVER, p2_game_state, player1_locked, player2_locked

    while running:
        try:
            data = conn.recv(4096).decode()
            if not data:
                print("SERVER ERROR: Did not receive data")
                break

            buffer += data

            # Messages are newline-delimited JSON. Buffer partial socket reads until a
            # complete message arrives, then process one message at a time.
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                if not line.strip():
                    continue
                message = json.loads(line)
                print(f"SERVER: Received from Player {player_index + 1}: {message}")
                handle_message(conn, player_index, message)

        except Exception as e:
            print("SERVER: Client disconnected:", e)
            break

    # Clean up
    try:
        conn.close()
    except:
        pass

    if conn in clients:
        clients.remove(conn)

    # Notify the remaining client that the session is no longer valid so the
    # frontend can leave the multiplayer match cleanly.
    for other in clients[:]:
        try:
            send(other, {"type": "opponent_disconnected"})
        except:
            pass

    running = False

def main():
    global clients, player1_locked, player2_locked, running
    global GAME_OVER, winner

    clients = []
    player1_locked = False
    player2_locked = False
    GAME_OVER = False
    winner = None

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(2)

    print("SERVER: Waiting for players...")

    # Accept two players
    for i in range(2):
        player_id = i+1
        conn, addr = server.accept()
        print(f"SERVER: Player {player_id} connected from {addr}")
        clients.append(conn)

        # Send player ID to client
        msg = {
            "type": "player_id",
            "player": player_id
        }
        send(conn,msg)

    running = True
    # Start a thread for each player
    threading.Thread(target=handle_client, args=(0,), daemon=True).start()
    threading.Thread(target=handle_client, args=(1,), daemon=True).start()

    start_msg = {
        "type": "start_game"
    }

    for conn in clients:
        send(conn,start_msg)

    print("SERVER: Both players connected. Game starting.")

    # Keep server alive
    while True:
        if len(clients) < 2:
            running = False
            server.close()
            print("SERVER: Shutting down...")
            time.sleep(1) # Give server time to shut down
            break
        time.sleep(0.1)