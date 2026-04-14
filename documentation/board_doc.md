# board.py Documentation

## Overview

`board.py` is the **frontend / presentation layer** of the Battleship game.  
It is responsible for everything the player **sees and interacts with**, including:

- Window creation and Pygame initialization
- Menus and screen navigation
- Ship placement UI
- Board rendering
- Player input (mouse + keyboard)
- Turn-based attack interaction
- Special ability interaction (Multi-Bomb / Radar)
- Animation handling
- Visual game feedback
- Coordination with `backend.py` game state

This file does **not** primarily contain the core rules of Battleship itself.  
Instead, it acts as the **visual and interactive wrapper** around the backend logic.

---

# Purpose of `board.py`

The main role of this file is to:

1. **Display the game**
2. **Collect user actions**
3. **Translate user actions into backend operations**
4. **Render backend state changes back to the screen**

A good mental model is:

- **`backend.py`** = game rules / state / logic
- **`board.py`** = interface / visuals / controls
- **`server.py`** = multiplayer communication relay

---

# High-Level Responsibilities

`board.py` is responsible for several major systems:

## 1. Window / Rendering Setup
Creates and manages the Pygame window, screen dimensions, fonts, colors, layout spacing, and asset loading.

## 2. UI State / Screen Flow
Controls what screen the player is currently on, such as:

- Main Menu
- Difficulty Selection
- Ship Count Selection
- Ship Placement
- Gameplay
- Waiting / Multiplayer Sync Screens
- Game Over Screen

## 3. Board Drawing
Renders:

- Player board
- Enemy board
- Hits / misses
- Ships
- Hover previews
- Selection overlays
- Labels / status text

## 4. Ship Placement
Handles the entire pre-game placement phase:

- Dragging ships
- Rotating ships
- Snapping to grid
- Placement validation
- Reset / lock-in behavior

## 5. Gameplay Input
Handles the player’s actions during the game:

- Clicking enemy cells to attack
- Activating Multi-Bomb
- Activating Radar
- Restricting invalid actions

## 6. Animation System
Displays game events with motion / effects, such as:

- Bomb drops
- Splashes
- Explosions
- Sunk ship effects
- Timeout effects

## 7. Turn / Status Display
Shows game state information like:

- Current turn
- Timer countdown
- Ability availability
- Win / loss state
- Waiting messages

## 8. Backend Synchronization
Reads from and writes to `backend.py` to keep the UI consistent with the real game state.

---

# File Architecture

The file is generally organized into the following conceptual areas:

## A. Configuration / Constants
Defines values such as:

- Grid size
- Cell size
- Window dimensions
- Margins / padding
- Fonts
- Colors
- Animation timing
- UI layout positions

These constants determine the visual scale and layout of the game.

### Why this matters
If another developer wants to:
- resize the game window
- enlarge the board
- improve UI spacing
- support different resolutions

this is one of the first places they should look.

---

## B. Asset Loading
The file likely loads assets such as:

- Bomb sprites
- Water splash frames
- Smoke / explosion animations
- Fonts
- Backgrounds or icons

These are used by the rendering and animation systems.

### Important note
If an image path or font path breaks, the game may crash at startup or fail to render properly.

### For future developers
If you want to:
- replace artwork
- improve visual polish
- add sound effects
- support theme changes

this section is where those integrations begin.

---

# Core Systems

# 1. Screen / Game State Management

`board.py` likely uses internal variables or flags to determine which screen is currently active.

Examples of common game states:

- `"main_menu"`
- `"difficulty_select"`
- `"ship_count_select"`
- `"placement"`
- `"gameplay"`
- `"game_over"`
- `"waiting_for_opponent"`

This state machine determines which draw and input logic should run.

## Why this matters
A lot of bugs in frontend game files happen when:

- input is still enabled on the wrong screen
- a screen transition occurs too early
- multiplayer readiness isn’t synchronized with UI state

## Developer note
If adding a new screen (for example, a **settings menu** or **tutorial screen**), you will likely need to update:

- event handling
- draw loop logic
- state transition logic

---

# 2. Main Menu System

The menu system is responsible for the player’s initial navigation through the game.

It likely includes options for:

- Single Player
- Multi-Player
- Quit / Exit

Depending on selection, the UI transitions to other setup screens.

## Responsibilities
- Draw menu buttons
- Detect mouse hover / click
- Transition to next state

## Developer note
If you want to:
- redesign the UI
- add settings
- add credits
- add a tutorial button

the main menu drawing and click handling are where those changes should happen.

---

# 3. Single Player Setup Flow

For single-player mode, the player likely goes through setup steps such as:

1. Select difficulty
2. Select number of ships
3. Place ships
4. Start game

## Difficulty Modes
The frontend likely only handles **selection and display** of difficulty.

The actual AI behavior should be implemented in `backend.py`.

### Important separation
- `board.py` = lets the user choose difficulty
- `backend.py` = determines what difficulty actually does

This separation is important if another developer wants to modify AI behavior without touching the UI.

---

# 4. Multiplayer Setup Flow

For multiplayer mode, `board.py` is responsible for guiding the user through the multiplayer session setup.

This may include:

- waiting for second player
- displaying connection status
- synchronizing game readiness
- placement readiness / lock-in
- waiting for opponent to finish setup

## Important dependency
Multiplayer flow depends heavily on communication with `backend.py` and `server.py`.

That means UI issues in multiplayer are often **not purely UI bugs** — they may actually be backend synchronization issues.

## Developer warning
If a screen gets “stuck” in multiplayer, possible causes include:

- missing network message
- stale readiness flag
- frontend waiting for a backend state that never updates

---

# 5. Board Rendering System

This is one of the most important parts of `board.py`.

It is responsible for drawing the two grids:

## Player Board
Displays:
- player ships
- hits taken
- misses received
- sunk ship visuals

## Enemy Board
Displays:
- attacks made
- hits confirmed
- misses confirmed
- target previews / hover state

### Typical rendering layers
Board drawing usually happens in layers like:

1. Grid background
2. Cell outlines
3. Ships (player board only)
4. Hits / misses
5. Overlays
6. Animation effects
7. Text labels

## Why this matters
If rendering order is wrong, visual bugs can happen such as:

- ships appearing above explosions incorrectly
- hits being hidden
- hover effects not showing
- animations covering UI text

## Developer note
If modifying visuals, preserve the **draw order** carefully.

---

# 6. Ship Placement System

The ship placement system is one of the most interactive parts of the file.

This system likely handles:

- draggable ships
- hover previews
- rotation
- snapping ships to grid
- validating placement
- preventing overlap
- resetting placement
- locking final placement

## Typical placement workflow

1. Player selects / drags a ship
2. Ship follows cursor
3. Optional rotation occurs
4. Ship is dropped
5. Position is snapped to nearest valid cells
6. Placement is validated
7. If valid, ship is placed
8. If invalid, it returns or rejects placement

## Important developer concept
There are usually **two representations** of ships during placement:

### A. Visual / draggable representation
Used for:
- on-screen dragging
- preview position
- cursor interaction

### B. Backend board representation
Used for:
- actual logical placement
- collision checking
- gameplay damage tracking

These two representations must stay synchronized.

## Common bug sources
This is a high-risk area for bugs such as:

- ship appears placed but backend didn’t register it
- rotation preview doesn’t match actual placement
- drag origin offsets are wrong
- ships clip off-grid
- reset clears visuals but not backend state

## For developers
If changing placement behavior, test:

- horizontal placement
- vertical placement
- edge-of-board placement
- overlap rejection
- reset after partial placement
- lock after all ships placed

---

# 7. Rotation Handling

The file likely supports rotating ships during placement (commonly with `R`).

## Responsibilities
- toggle orientation
- redraw ship dimensions
- update collision preview
- preserve drag interaction

## Developer note
Rotation logic is usually tightly coupled with placement validation.

If rotation behaves strangely, check both:

- visual size / rectangle update
- backend placement bounds check

---

# 8. Input Handling

`board.py` likely has a central event loop using `pygame.event.get()`.

It should process events such as:

## Mouse Input
- click buttons
- drag ships
- drop ships
- select attack cell

## Keyboard Input
- rotate ship
- toggle Multi-Bomb
- toggle Radar
- maybe reset / debug shortcuts

## Why this matters
A lot of UI behavior depends on **which game state is active** when input is received.

For example:
- `R` during placement = rotate ship
- `R` during gameplay = activate radar

That means keybindings may be **context-sensitive**.

## Developer warning
Be careful when reusing keys across screens.

A single key may need different behavior depending on whether the user is:
- in menu
- placing ships
- attacking
- game over

---

# 9. Gameplay Interaction System

Once the match starts, `board.py` switches from placement logic to turn-based combat interaction.

This system is responsible for:

- determining if the player is allowed to act
- translating clicks on the enemy board into attacks
- showing previews / hover cells
- handling special ability targeting
- blocking illegal actions

## Important frontend rule
The frontend should not allow attacks if:

- it is not the player’s turn
- the game is over
- the cell has already been targeted
- the user is waiting on animation / sync state

## Why this matters
Even if the backend validates these too, the frontend should still try to prevent bad input for better UX.

---

# 10. Special Ability System

One of the custom mechanics in this project is the inclusion of special abilities.

These likely include:

## Multi-Bomb
A one-time 3x3 attack.

### UI responsibilities
- indicate whether it is available
- allow toggling it on/off
- show target area preview
- send correct attack intent to backend
- visually distinguish it from normal attack mode

## Radar Scan
A one-time 3x3 scan that reveals whether at least one ship is in the area.

### UI responsibilities
- indicate whether it is available
- allow toggling it on/off
- show scan area preview
- trigger non-damaging backend scan action
- display result to player

## Developer warning
These systems are more complex than normal attacks because they involve:

- alternate targeting modes
- temporary input state changes
- different result handling
- one-time-use tracking

## Common bug sources
- ability mode remains active after use
- preview area doesn’t match backend target area
- wrong board receives the action
- ability can be reused incorrectly

---

# 11. Hover / Target Preview System

The game likely includes hover previews for actions like:

- normal attack target
- multi-bomb 3x3 preview
- radar 3x3 preview
- placement preview

This is a **purely visual helper system**, but it is important for usability.

## Developer note
This system often needs to:

- convert mouse position → grid coordinates
- clamp values to board boundaries
- generate affected cells
- draw highlights without committing the action

This is a good place to improve polish if another developer wants to enhance UX.

---

# 12. Animation System

`board.py` appears to use an animation queue or animation management system to show game events visually.

This is a major polish feature and one of the more advanced frontend systems in the project.

## Likely animation types
- bomb falling
- splash / miss
- explosion / hit
- smoke for sunk ships
- timeout visual effect

## Common structure
Animations are often stored in a list or queue of objects / dictionaries containing fields like:

- animation type
- board target
- cell / pixel position
- start time
- current frame
- duration

## Why this matters
Animations often need to exist **independently of game logic**.

For example:
- the backend may already know the shot result
- but the UI still needs time to visually show it

This means the file likely has logic for:
- queuing animations
- updating active animations
- removing finished animations
- delaying follow-up actions until animation completes

## Developer warning
Animation timing bugs can cause:
- double attacks
- skipped effects
- turn changes too early
- desync in multiplayer visuals

## Best practice
If adding new effects, keep animation logic **data-driven** where possible instead of hardcoding each one separately.

---

# 13. Turn Timer Display

The game includes a timed turn mechanic, and `board.py` is responsible for displaying that to the user.

This likely includes:

- showing countdown value
- warning when time is low
- showing timeout messages
- reflecting when a turn has ended due to time expiration

## Important note
The frontend display may not be the true authority for timeout logic.

Usually:
- `backend.py` or multiplayer state determines timeout validity
- `board.py` just reflects it visually

This distinction matters when debugging multiplayer timer issues.

---

# 14. Status / HUD Display

The HUD (heads-up display) likely shows important game information such as:

- current player turn
- ability availability
- timer
- mode (normal / multi-bomb / radar)
- hit / miss feedback
- multiplayer waiting messages

## Developer note
If another programmer wants to improve readability or UX, this is one of the highest-value areas to refine.

Good improvements could include:
- clearer ability indicators
- better turn messaging
- better low-time warnings
- more distinct multiplayer sync messages

---

# 15. Endgame / Game Over Handling

At the end of the match, `board.py` likely transitions to a game-over state.

This system may include:

- win / loss message
- final board display
- replay / quit options
- multiplayer end sync behavior

## Developer note
A common edge case here is making sure the frontend doesn’t continue accepting attacks after the backend has already declared the winner.

---

# Integration with `backend.py`

This is one of the most important sections for developers.

`board.py` is tightly coupled to `backend.py`, but they should still remain conceptually separate.

## `board.py` should generally:
- ask backend for game state
- ask backend if an action is valid
- send player actions to backend
- render backend results

## `backend.py` should generally:
- own the actual board state
- own hit / miss logic
- own AI decisions
- own multiplayer state changes
- own win / loss detection

## Healthy dependency pattern
Good frontend code should **not reimplement game logic unnecessarily**.

For example:
- `board.py` should not decide whether a shot is a hit by itself if `backend.py` already knows
- `board.py` should not decide if all ships are sunk independently if backend already tracks it

## Why this matters
Duplicating game logic in both files creates desync bugs and makes maintenance harder.

---

# Multiplayer-Specific Frontend Concerns

When multiplayer is active, `board.py` likely behaves differently in several ways:

- waits for server/backend confirmation
- shows “waiting for opponent”
- disables local input while remote turn resolves
- reflects network-driven events

## Developer warning
Multiplayer UI bugs are often caused by one of three things:

1. frontend waiting on a backend flag
2. backend waiting on a network message
3. animation delay blocking state progression

If something “hangs,” check all three layers.

---

# Main Loop Responsibilities

The main game loop in `board.py` likely follows the standard Pygame pattern:

1. process events
2. update game state / UI state
3. update animations
4. draw everything
5. refresh display
6. cap framerate

## Why this matters
This loop is effectively the “heartbeat” of the entire frontend.

If performance drops or visual bugs occur, this is often the first place to inspect.

---

# Important Developer Workflows

This section explains where a future developer should go depending on what they want to modify.

---

## If you want to change visuals
Look in:
- constants / dimensions
- color definitions
- draw functions
- asset loading
- animation rendering

---

## If you want to change ship placement behavior
Look in:
- drag / drop logic
- rotation handling
- placement validation calls
- reset / lock-in handling

---

## If you want to change attack behavior
Look in:
- enemy board click handling
- hover target logic
- special ability targeting
- backend action calls

---

## If you want to change special abilities
Look in:
- ability toggle input
- preview drawing
- ability availability display
- action dispatch to backend

---

## If you want to improve multiplayer UX
Look in:
- waiting screens
- turn state display
- lock / ready synchronization
- timeout feedback
- backend state polling / update handling

---

## If you want to improve polish
Look in:
- animation queue
- hit / miss feedback
- screen transitions
- HUD readability
- menu visuals

---

# Common Maintenance Risks

This file is likely one of the more fragile files in the project because it combines:

- rendering
- input
- state transitions
- timing
- animation
- backend integration

That means bugs can cascade across multiple systems.

## High-risk areas
The most likely places for regressions are:

- ship placement
- animation timing
- multiplayer turn flow
- special ability targeting
- screen transitions

## Recommendation for future developers
When making changes, test these flows every time:

### Placement
- place all ships
- rotate ships
- reset ships
- lock placement

### Gameplay
- normal attack
- repeat attack rejection
- turn switching
- timer expiration

### Special Abilities
- use radar once
- use multi-bomb once
- verify they cannot be reused

### Multiplayer
- both players connect
- both place ships
- attacks sync properly
- timeout sync works
- game over sync works

---

# Suggested Refactoring Opportunities

If another developer plans to expand this project, `board.py` would likely benefit from modularization.

## Recommended future refactors

### 1. Separate UI Screens into Classes or Modules
Instead of keeping all screens in one file, split into:

- `menu_screen.py`
- `placement_screen.py`
- `gameplay_screen.py`
- `gameover_screen.py`

### 2. Extract Animation System
Move animation handling into something like:

- `animations.py`

### 3. Extract UI Components
Buttons, labels, and overlays could become reusable components.

### 4. Create a Dedicated Input Layer
This helps avoid giant event loops.

### 5. Separate Rendering from State Logic
A clearer split between:
- “what should happen”
- “how it should look”

would improve maintainability.

---

# Summary

`board.py` is the **interactive heart of the game’s user experience**.

It is responsible for turning the raw Battleship logic into a playable and visually understandable experience through:

- menus
- board rendering
- ship placement
- attacks
- special abilities
- multiplayer flow
- animations
- status feedback

For a future developer, the most important thing to understand is:

> `board.py` should primarily control **presentation and interaction**, while `backend.py` should remain the source of truth for **game logic and state**.

Maintaining that separation will make the codebase easier to debug, expand, and improve over time.