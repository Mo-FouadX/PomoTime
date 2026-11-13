# PLAYAPP.md

## PomoTime - Professional Pomodoro Timer Application

Welcome to **PomoTime**, your native desktop productivity companion built in Python with PyQt6.

### Quick Start Guide

#### Prerequisites
Ensure you have Python 3.10 or newer and PyQt6 installed:
```bash
pip install PyQt6
```

#### Running the Application
Launch the application by running:
```bash
python3 pomotime.py
```

> Note: The app requires a display environment (X11, GTK/Qt). On headless servers it may need additional X server setup.

### Features & Usage

1. **Focus & Breaks**: Start a focus timer or take a short/long break. Completed cycles are tracked in real time, and a long break follows the configured number of focus cycles.
2. **One-Click Presets**: Use the preset bar above the timer to switch instantly between:
   - **Classic Pomodoro** — 25m focus / 5m break / 20m long break × 4
   - **Deep Work** — 50m focus / 10m break / 30m long break × 2
   - **Quick Sprint** — 15m focus / 3m break / 10m long break × 4
   - **Custom Queue** — runs your own multi-block session sequence
3. **Session Queue (Multi-Block Planner)**: Open the **Session Queue** tab to build a custom plan of focus blocks and breaks:
   - Add a block with a stage type, duration (1–180 minutes), and an optional task label.
   - Use **+ 2 Focus + Long Break** or **+ 1 Extra Cycle** for one-click patterns.
   - Reorder with **Move Up / Move Down**, or use **Delete Block** and **Clear Queue**.
   - The timer advances automatically through every step.
   - Live progress appears under the timer: `Queue Step 2 of 7 • Next: Long Break (15m)`.
   - The active queue-step task is shown in the main window and in Mini-Mode.
4. **Daily Focus Goal**: Set a **Daily Focus Target** in Settings. A themed progress bar on the Timer and Statistics tabs shows `Today: 50 / 120 mins • 42%`. The daily counter resets at midnight while all-time statistics and session history are preserved.
5. **Mini-Mode**: Click **Float Mini-Mode** to collapse into a sleek, floating window that stays on top of all applications. It shows the remaining time, stage, progress, and the active task or queue-step task.
6. **Bilingual & RTL Support**: Switch instantly between English (LTR) and Arabic (RTL) using the language selector. Labels, buttons, presets, queue items, dialogs, and layouts all update correctly.
7. **Notifications**: Receive native tray notifications and soft synthesized chimes when a focus session, break, or the full session queue finishes.
8. **Current Task / Focus Goal**: Enter a task above the timer card ("What are you focusing on?"). The field is wide enough to show the full placeholder in both languages.
9. **Statistics Tab**:
   - Total focus time, completed cycles, breaks taken, and Productivity Score (0–100).
   - Daily goal progress bar.
   - Scrollable **Recent Sessions** log with task name, duration, and timestamp.
   - **Export to CSV** button for the complete session history.
10. **Settings Tab**:
    - Focus, short break, long break, and cycles-before-long-break spinboxes.
    - Daily Focus Target (minutes).
    - Theme selector (Clean Default, Calm Forest, Midnight Focus, Warm Sunset).
    - Auto-start breaks / auto-start focus checkboxes.
    - Save Settings button (updates the Timer tab immediately).
11. **Keyboard Shortcuts**:
    - `Space` – Start/Pause
    - `R` – Reset
    - `S` – Skip
    - `M` – Toggle Mini-Mode
12. **Circular Progress Ring** around the countdown clock (smoothly depletes, color changes between Focus accent and Break green/teal).

### Architecture Highlights

- **Sound System**: Soft notification chimes synthesized in pure Python and played through native OS tools (`paplay`/`aplay` on Linux, `afplay` on macOS, `winsound` on Windows) — no `QtMultimedia` dependency.
- **Persistent Storage**: `QSettings("PomoTime", "Settings")` stores durations, cycle target, current task, theme, automation flags, statistics, daily goal state, task history, preset selection, and the JSON-serialized session queue. Settings are synced immediately on save.
- **Session Queue Engine**: Queue blocks are dictionaries (`kind`, `minutes`, `task`); the timer engine advances through them, logs completed focus blocks, and triggers the appropriate auto-start behavior.
- **Daily Focus Stats**: Today's focus time is tracked separately from all-time totals and resets at midnight; all-time totals and history are never reset.
- **Theme Styling**: `apply_theme()` controls all widgets, including progress bars, list widgets, queue controls, and secondary buttons across all four themes.
- **RTL Support**: Dynamic layout direction based on language selection; the floating Mini-Mode synchronizes direction, text, and active task.

### Keyboard Shortcuts

- **Space**: Start/Pause the timer
- **R**: Reset the current session or restart a completed queue
- **S**: Skip the current stage or queue block
- **M**: Toggle Mini-Mode (floating widget)

### Settings & Customization

- **Durations**: Adjust focus, short break, long break, and cycles before long break
- **Daily Goal**: Set a realistic daily focus target in minutes
- **Themes**: Four built-in themes (Clean Default, Calm Forest, Midnight Focus, Warm Sunset)
- **Presets**: Classic Pomodoro, Deep Work, Quick Sprint, or your own Custom Queue
- **Automation**: Auto-start breaks/focus options
- **Task Tracking**: Current task field plus the Recent Sessions history log and CSV export

### Tips

- The app remembers your settings, preset, and session queue across sessions
- Completed focus blocks are logged with task, duration, and timestamp
- The mini-mode widget can be dragged to any screen position
- Use keyboard shortcuts for quick control without touching the mouse
- Export your session history to CSV for spreadsheets or external reports
