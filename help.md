## Welcome to Ground Truth - PCB Analysis!

This help file can be displayed at any time by clicking the help button at the right of the tool bar.

Note that the app is in early development and is thus not feature complete but rich in bugs. Feel free to report issues on github
Code contributions are welcome.

Enjoy using the app!

---
## Controls Summary

- `F` → enter annotation mode and cycle tools
- `C` → cycle annotation subtype while in annotation mode
- `X` → toggle selection mode
- `+/-` → change annotation size
- `Delete` → remove selected annotations
- `Ctrl + Z` → undo
- `Ctrl + S` → save
- `WASD / arrows` → pan
- `Mouse Wheel` → zoom
- `Q` → reset view
- `Esc` → context-sensitive cancel/exit
- `0-9` → layer selection (10 first layers only)

Note that some actions depend on the current mode (annotation vs selection mode).

---
## Detailed controls documentation

___
### Annotation Mode

| Key | Action |
|-----|--------|
| `F` | Toggle annotation mode / cycle annotation tools |

Behavior:
- Enters annotation mode if not active
- Cycles through available annotation tools if already active
- Exits selection mode when activated
- Clears pending annotations and selection state

---

### Selection Mode

| Key | Action |
|-----|--------|
| `X` | Toggle selection mode |

Behavior:
- Disables annotation mode
- Clears pending drawing state
- Toggles selection mode on/off

---

### Annotation Subtypes

| Key | Action |
|-----|--------|
| `C` | Cycle annotation subtype (context-dependent) |

Behavior:
- If in selection mode with selected annotations: cycles subtype of selected items
- If in annotation mode: cycles subtype for current tool

---

### Annotation Styling

| Key | Action |
|-----|--------|
| `+` / `=` | Increase annotation size |
| `-` | Decrease annotation size |

Behavior:
- If in selection mode with selected annotations: changes size of selected items
- If in annotation mode: changes size for current tool

---

### Selection Editing

| Key | Action |
|-----|--------|
| `Delete` | Remove selected annotations |


---

### Navigation / View Control

| Key                          | Action                  |
|------------------------------|-------------------------|
| `Q`                          | Reset view (auto-range) |
| `A` / `Left Arrow`           | Pan left                |
| `D` / `Right Arrow`          | Pan right               |
| `W` / `Up Arrow`             | Pan up                  |
| `S` / `Down Arrow`           | Pan down                |
| `Mouse Wheel` | Zoom                    |

---

### Layer Selection

| Key | Action                 |
|-----|------------------------|
| `1`–`9` | Select layer index 1–9 |
| `0` | Select layer 10        |

Behavior:
- Only the first 10 layers are selectable with the number keys
- Any pending action will be canceled when changing layer

---

### Ctrl + Key Combinations

| Shortcut | Action |
|----------|--------|
| `Ctrl + Z` | Undo last action |
| `Ctrl + S` | Save current document |

---

### Escape Behavior

| State | Escape Action |
|-------|--------------|
| Annotation mode with active stroke | Cancel current stroke and reset series |
| Annotation mode idle | Exit annotation mode |
| Selection mode with selection | Clear selection |
| Selection mode without selection | Exit selection mode |

---