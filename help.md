## Welcome to Ground Truth - PCB Analysis!

This help file can be displayed at any time by clicking the help button in the toolbar.

Note that the app is in early development and is thus not feature complete but rich in bugs. Feel free to report issues on Github.
Code contributions are welcome.

Enjoy using the app!

---
## Controls Summary

- `F` → enter annotation mode and cycle between tools
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

Note that some actions depend on the current mode (annotation vs selection mode). The active tool is displayed at the right end of the toolbar.

---
## Mouse interactions summary

### Line annotations
- While in line annotation mode, left or right click to start a segment; click again to end it and start the next segment
- The segment is placed in the left or right view according to the click (left or right mouse button) that starts the segment
- A second click ends a segment that was started. The next segment is then chained and immediately started.
- The next segment in a chain starts in the left or right view according to the click (left or right mouse button) that ended the previous segment.
- Double click to end the segment chain.
- Hold `Shift` while drawing to preview/place the segment on both views.

### Text annotations
- While in text annotation mode, left or right click to create a text annotation.
- The annotation is placed in the left or right view according to the click (left or right mouse button) that was clicked.
- Holding `Shift` while placing a text annotation will place it in both views.
- While in selection mode, double clicking on the selection point of a text annotation allows editing its text.

---
# Detailed controls documentation

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

#### Mouse interactions and annotation mode

Overview
- Enter annotation mode and choose the line tool to draw linear annotations.
- Click once in a view to start a new segment; move the mouse to preview the line; click again to finish that segment and (immediately) start the next segment whose start point is the finished end point.

Which view receives the annotation
- The view that receives a newly created annotation is determined by the click that *starts* the segment. If you start a segment by a left-click, the finished annotation will be placed in the left view (and likewise for right).
- When drawing a chain of segments, the click that *finishes* the previous segment is also the click that *starts* the next segment and thus also defines the start side of the next segment. 

Preview and `Shift` behavior
- While a segment is pending (after the first click), a preview shows the line from the start point to the current cursor.
- Hold `Shift` while drawing to preview that segment on both views simultaneously. Release `Shift` to preview only on the original start side.
- Ending a line segment while `Shift` is pressed will apply it to both sides, according to the preview. The start of the next segment still depends on the button clicked to finish the segment.

Selection and editing
- Switch to select mode to pick and move existing annotations or drag endpoints to resize.
- Deleting or moving segment is also possible while they are selected.

---

### Annotation Subtypes

| Key | Action |
|-----|--------|
| `C` | Cycle annotation subtype (context-dependent) |

Behavior:
- If in selection mode with selected annotations: cycles subtype of selected items
- If in annotation mode: cycles subtype for current tool

---

### Selection Mode

| Key | Action |
|-----|--------|
| `X` | Toggle selection mode |

Behavior:
- When activated, annotations can be selected by clicking on them
- Selected annotations can be edited in various ways
- Disables annotation mode
- Clears pending drawing state
- Toggles selection mode on/off

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
| `Enter`  | Edit the text of the selected text annotation |


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
- Any selected annotation will be unselected when changing layer
- Annotations can only be inserted/selected in the current layer

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