# server.py  –  WebSocket relay server for Battleship
#
# Replaces the old raw-TCP server. Run this on a public host (VPS, Railway,
# Render, etc.). Players connect via WebSocket; one creates a room and gets a
# 4-letter code, the other joins with that code.
#
# Requirements:
#   pip install websockets
#
# Run:
#   python server.py
#
# Environment variables (optional overrides):
#   PORT  – listening port (default 5000)
#   HOST  – bind address  (default 0.0.0.0)

import asyncio
import json
import os
import random
import string
import time

import websockets

HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", 5000))

# rooms[code] = {"players": [ws1, ws2 | None], "locked": [False, False]}
rooms: dict[str, dict] = {}


# ── helpers ──────────────────────────────────────────────────────────────────

def make_code(length: int = 4) -> str:
    """Return a unique uppercase room code."""
    chars = string.ascii_uppercase + string.digits
    while True:
        code = "".join(random.choices(chars, k=length))
        if code not in rooms:
            return code


async def send_json(ws, obj: dict) -> None:
    try:
        await ws.send(json.dumps(obj))
    except Exception:
        pass


async def relay(sender_ws, room: dict, msg: dict) -> None:
    """Forward msg to the other player in the room."""
    players = room["players"]
    for ws in players:
        if ws is not None and ws is not sender_ws:
            await send_json(ws, msg)


# ── per-connection handler ────────────────────────────────────────────────────

async def handle(ws):
    """Manage one WebSocket connection for its entire lifetime."""
    player_index: int | None = None
    room_code: str | None = None
    room: dict | None = None

    print(f"SERVER: New connection from {ws.remote_address}")

    try:
        async for raw in ws:
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                print("SERVER: Ignoring non-JSON message")
                continue

            if not isinstance(msg, dict) or "type" not in msg:
                print(f"SERVER: Ignoring malformed message: {msg}")
                continue

            mtype = msg["type"]
            print(f"SERVER: [{room_code or '?'}] P{(player_index or -1) + 1} → {mtype}")

            # ── lobby messages ────────────────────────────────────────────

            if mtype == "create_room":
                # Player 1 creates a new room and receives the code.
                room_code = make_code()
                room = {
                    "players": [ws, None],
                    "locked": [False, False],
                    "game_over": False,
                }
                rooms[room_code] = room
                player_index = 0
                await send_json(ws, {"type": "room_created", "code": room_code, "player": 1})
                print(f"SERVER: Room {room_code} created")

            elif mtype == "join_room":
                code = str(msg.get("code", "")).upper().strip()
                if code not in rooms:
                    await send_json(ws, {"type": "error", "message": "Room not found."})
                    continue
                target = rooms[code]
                if target["players"][1] is not None:
                    await send_json(ws, {"type": "error", "message": "Room is full."})
                    continue

                target["players"][1] = ws
                room_code = code
                room = target
                player_index = 1

                # Tell the joining player their ID.
                await send_json(ws, {"type": "player_id", "player": 2})
                # Tell the host their ID and that the opponent joined.
                host_ws = room["players"][0]
                await send_json(host_ws, {"type": "player_id", "player": 1})
                await send_json(host_ws, {"type": "opponent_joined"})

                # Start the game for both players.
                for p_ws in room["players"]:
                    await send_json(p_ws, {"type": "start_game"})

                print(f"SERVER: Room {room_code} is full – game starting")

            # ── in-game relay messages ────────────────────────────────────

            elif room is None:
                # Any game message before the player is in a room is invalid.
                print("SERVER: Game message received before joining a room – ignoring")

            elif mtype == "ship_count":
                new_msg = {"type": "set_ship_count", "count": msg["count"]}
                await send_json(ws, new_msg)
                await relay(ws, room, new_msg)

            elif mtype == "place_ships":
                print(f"SERVER: Player {player_index + 1} locked ships")
                room["locked"][player_index] = True
                if all(room["locked"]):
                    for p_ws in room["players"]:
                        await send_json(p_ws, {"type": "all_ships_locked"})

            elif mtype == "bomb":
                row, col = msg.get("row"), msg.get("col")
                print(f"SERVER: Player {player_index + 1} bombs ({row},{col})")
                await relay(ws, room, msg)

            elif mtype == "hit_status":
                if msg.get("all_sunk"):
                    room["game_over"] = True
                if not msg.get("status"):
                    change = {"type": "change_turn"}
                    await send_json(ws, change)
                    await relay(ws, room, change)
                await relay(ws, room, msg)

            elif mtype == "multi_bomb":
                print(f"SERVER: Player {player_index + 1} used multi_bomb")
                await relay(ws, room, msg)

            elif mtype == "multi_bomb_result":
                if msg.get("all_sunk"):
                    room["game_over"] = True
                await relay(ws, room, msg)
                change = {"type": "change_turn"}
                await send_json(ws, change)
                await relay(ws, room, change)

            elif mtype == "radar_scan":
                print(f"SERVER: Player {player_index + 1} used radar scan")
                await relay(ws, room, msg)

            elif mtype == "radar_result":
                await relay(ws, room, msg)

            elif mtype == "turn_timeout":
                print(f"SERVER: Player {msg.get('player_id')} turn timed out")
                await send_json(ws, msg)
                await relay(ws, room, msg)

            elif mtype == "time_ran_out":
                await send_json(ws, msg)
                await relay(ws, room, msg)

            elif mtype == "game_state":
                print(f"SERVER: Player {msg.get('sender')} state → {msg.get('state')}")

            elif mtype == "game_over":
                room["game_over"] = True
                await send_json(ws, msg)
                await relay(ws, room, msg)

            else:
                # Generic relay fallback – forward unknown message types so new
                # features added to the game clients work without server changes.
                print(f"SERVER: Relaying unknown type '{mtype}'")
                await relay(ws, room, msg)

    except websockets.exceptions.ConnectionClosedOK:
        print(f"SERVER: Player {(player_index or -1) + 1} disconnected cleanly")
    except websockets.exceptions.ConnectionClosedError as exc:
        print(f"SERVER: Player {(player_index or -1) + 1} connection error: {exc}")
    except Exception as exc:
        print(f"SERVER: Unexpected error: {exc}")
    finally:
        # Notify the opponent and clean up the room.
        if room is not None and player_index is not None:
            room["players"][player_index] = None
            opponent = room["players"][1 - player_index]
            if opponent is not None:
                await send_json(opponent, {"type": "opponent_disconnected"})
            # Remove room if both slots are empty.
            if all(p is None for p in room["players"]):
                rooms.pop(room_code, None)
                print(f"SERVER: Room {room_code} removed")


# ── entry point ───────────────────────────────────────────────────────────────

async def main():
    print(f"SERVER: Listening on ws://{HOST}:{PORT}")
    async with websockets.serve(handle, HOST, PORT):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())