# server.py Documentation

## Overview

`server.py` is the **multiplayer relay server** for the Battleship game.

It is responsible for connecting exactly **two players** and forwarding gameplay messages between them.

Unlike `backend.py`, which manages the local game state for one player, `server.py` acts as the **communication hub** that allows two clients to stay synchronized during a multiplayer match.

This file handles:

- Accepting incoming player connections
- Assigning player IDs
- Managing a 2-player session
- Relaying JSON messages between players
- Coordinating turn / state synchronization
- Broadcasting game events

---

# Purpose of `server.py`

The main job of the server is **not** to run the whole game logic itself.

Instead, its role is to:

1. Accept client connections
2. Identify who each player is
3. Receive structured game messages
4. Forward those messages to the other player
5. Keep the multiplayer session alive and synchronized

A useful mental model is:

- `board.py` = UI / rendering
- `backend.py` = local game logic + client networking
- `server.py` = multiplayer message relay

---

# High-Level Responsibilities

## 1. Host a Socket Server
Listens for incoming player connections.

## 2. Accept Exactly Two Players
This game is built around a **2-player multiplayer session**.

## 3. Assign Player Roles / IDs
Determines which connected client is Player 1 vs Player 2.

## 4. Relay Messages
Receives messages from one player and sends them to the other.

## 5. Keep Session State Organized
Tracks connected clients and session status.

---

# Core Architecture

The server is likely built around Python sockets and threading.

This usually means:

- a main listening socket
- one thread per connected client
- a shared structure storing active players
- JSON-based message passing

## Why this matters
This is a relatively lightweight architecture that works well for a small 2-player project, but it also means concurrency and disconnect handling matter.

---

# Core Systems

# 1. Server Initialization

At startup, the server likely:

- creates a socket
- binds to a host / port
- starts listening for incoming connections

Typical config includes:

- host IP
- port number (commonly `5000`)

## Developer note
If another programmer wants to:
- change the port
- support public hosting
- make the server configurable

this is one of the first places to modify.

---

# 2. Client Connection Handling

When a client connects, the server likely:

1. accepts the socket
2. stores the connection
3. assigns the player a role / ID
4. starts a dedicated client-handling thread

## Important constraint
This project appears to be designed for **exactly 2 players**.

That means the server likely assumes:
- Player 1 connects
- Player 2 connects
- game session begins

## Developer warning
If someone later wants to support:
- lobbies
- multiple rooms
- multiple matches simultaneously

this architecture will need major expansion.

---

# 3. Player Tracking

The server likely stores:

- client sockets
- player IDs
- connection status
- maybe readiness / game state metadata

This tracking is essential for routing messages correctly.

## Common issue
If the server loses track of which socket belongs to which player, gameplay synchronization will break quickly.

---

# 4. Message Relay System

This is the most important part of `server.py`.

The server receives a message from one client and forwards it to the other.

Typical relayed events include:

- player ready
- placement complete
- attack
- radar use
- multi-bomb use
- timeout
- game over

## Important note
The server is likely **not deeply interpreting the full game rules**.

Instead, it mostly acts as a relay / coordinator.

That means the server should ideally stay relatively “thin.”

---

# 5. JSON Message Handling

The project appears to use structured message passing, likely through JSON.

Typical messages probably include fields such as:

- message type
- player ID
- coordinates
- turn info
- ability usage
- game status

## Why this matters
A programmer editing this file needs to keep message structure consistent with `backend.py`.

If the server expects one JSON format and the client sends another, multiplayer will fail.

## Developer warning
Message schema mismatches are one of the most common multiplayer bugs.

---

# 6. Threading Model

The server likely uses threads so that each connected client can be handled independently.

Typical design:
- main thread accepts new clients
- client threads receive and forward messages

## Why this matters
Threading introduces concurrency risks, especially when shared structures are modified.

## Potential risk areas
- player list mutation
- disconnect handling
- session cleanup
- race conditions on send / receive

For a 2-player project, this is manageable, but it still requires care.

---

# 7. Disconnect Handling

A good multiplayer server must handle cases where a player disconnects unexpectedly.

This may include:

- broken socket connection
- player closing the game
- network interruption
- timeout / crash

## Server responsibilities
The server should ideally:

- detect disconnect
- clean up the client socket
- notify the remaining player
- prevent hanging threads / stale state

## Developer warning
Disconnect handling is one of the easiest places for multiplayer code to become unstable.

---

# 8. Session Coordination

The server may also help coordinate high-level session flow, such as:

- both players connected
- both players ready
- game start
- turn timeout relay
- game over broadcast

This is where the server helps keep both clients synchronized.

## Important distinction
The server should not become the “true game engine” unless intentionally redesigned.

Right now, it likely acts more as a **traffic controller** than a rules engine.

---

# Integration with `backend.py`

This is the most important relationship for this file.

`backend.py` likely acts as the multiplayer **client**, while `server.py` acts as the multiplayer **relay server**.

## `backend.py` responsibilities
- send local player actions
- receive opponent actions
- apply state locally

## `server.py` responsibilities
- route those messages correctly
- keep clients connected
- coordinate session messaging

## Important design rule
The server and client must agree on:

- message formats
- message timing
- expected event flow
- player identity handling

If any of those differ, multiplayer will become inconsistent.

---

# Important Developer Workflows

---

## If you want to add a new multiplayer feature
You will likely need to update:

- `backend.py` message sending
- `server.py` message relay / recognition
- `backend.py` message receiving
- `board.py` frontend behavior

---

## If you want to debug multiplayer desync
Check:

- message structure
- message ordering
- player ID assignment
- disconnect handling
- turn synchronization

---

## If you want to support more than 2 players or rooms
This file will require major redesign.

The current architecture is likely built specifically for a **single 2-player session**.

---

# Common Maintenance Risks

The most likely fragile areas in `server.py` are:

- socket disconnects
- malformed JSON
- thread cleanup
- player list consistency
- forwarding to wrong client
- game stuck waiting for a message

---

# Recommended Testing Checklist

Any developer modifying `server.py` should test:

## Connection Flow
- first player joins
- second player joins
- game starts correctly

## Relay Flow
- attack message relays
- radar relays
- multi-bomb relays
- timeout relays
- game-over relays

## Failure Cases
- one player disconnects before game starts
- one player disconnects mid-game
- malformed message received
- server restart behavior

---

# Suggested Refactoring Opportunities

If multiplayer is expanded, `server.py` could eventually be split into:

- `session_manager.py`
- `client_handler.py`
- `message_router.py`
- `protocol.py`

That would make the networking layer easier to maintain.

---

# Summary

`server.py` is the **multiplayer communication backbone** of the Battleship project.

It is responsible for:

- accepting 2-player connections
- assigning player identities
- relaying game messages
- keeping multiplayer sessions synchronized

It is intentionally lightweight, but it is still a critical part of the game’s architecture.

For any programmer working on it, the key principle is:

> Keep the server predictable, consistent, and synchronized with the message format expected by `backend.py`.