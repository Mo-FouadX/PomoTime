# PomoTime

Welcome to **PomoTime**, your ultimate native desktop productivity companion built in Python with PyQt6.

## Quick Start Guide

### Prerequisites
Ensure you have Python 3.10 or newer and PyQt6 installed:
```bash
pip install PyQt6
```

### Running the Application
Launch the application by running:
```bash
python3 pomotime.py
```

> Note: The app requires a display environment (X11, GTK/Qt). On headless servers it may need additional X server setup.

## Features & Usage

1. **Focus & Breaks**: Start the 25-minute focus timer or take a 5/15 minute break. Track completed cycles in real-time.
2. **One-Click Presets**: Switch between Classic Pomodoro (25/5/20 ×4), Deep Work (50/10/30 ×2), Quick Sprint (15/3/10 ×4), or your own Custom Queue.
3. **Session Queue**: Build a multi-block plan of focus sessions and breaks with optional task labels, quick-add patterns, and move/delete/clear controls. The timer advances automatically and shows live progress such as `Queue Step 2 of 7 • Next: Long Break (15m)`.
4. **Mini-Mode**: Click **Float Mini-Mode** to collapse into a sleek, floating window that stays on top of all your applications. It shows the active task or queue-step task.
5. **Bilingual & RTL Support**: Switch instantly between English (LTR) and Arabic (RTL) using the language selector. The entire interface, alignment, and typography adjust seamlessly.
6. **Notifications**: Receive native tray notifications and soft, synthesized completion chimes when your focus, break, or queue finishes.
7. **Current Task / Focus Goal**: Enter a task above the timer card ("What are you focusing on?") — displayed inside Floating Mini-Mode.
8. **Daily Focus Goal**: Set a target in Settings and track `Today: 50 / 120 mins • 42%` on the Timer and Statistics tabs. The daily counter resets at midnight while all-time history is preserved.
9. **Statistics Tab**: Total focus time, completed cycles, breaks taken, Productivity Score (0–100), Daily Goal progress, a scrollable Recent Sessions log, and **Export to CSV**.
10. **Settings Tab**:
    - Duration spinboxes (focus, short break, long break, cycles before long break)
    - Daily Focus Target (minutes)
    - Theme combo (Clean Default, Calm Forest, Midnight Focus, Warm Sunset)
    - Auto-start breaks / auto-start focus checkboxes
11. **Keyboard Shortcuts**:
    - `Space` – Start/Pause
    - `R` – Reset
    - `S` – Skip
    - `M` – Toggle Mini-Mode
12. **Circular Progress Ring** around the countdown clock (smoothly depletes, color changes between Focus accent and Break green/teal).

## Architecture Highlights

- **Sound System**: Cross-platform synthesized notification chimes + native playback via `paplay`/`aplay` (Linux), `afplay` (macOS), and `winsound` (Windows) — no `QtMultimedia` dependency.
- **Persistent Storage**: `QSettings("PomoTime", "Settings")` for widget values, cycle counts, theme, daily goal state, task history, preset selection, and the JSON-serialized session queue.
- **Session Queue Engine**: Blocks store `kind`, `minutes`, and `task`; the timer engine advances through them, logs completed focus sessions, and handles auto-start behavior.
- **Daily Focus Stats**: Resets today's total at midnight; keeps all-time totals and history.
- **Theme Styling**: Hardcoded inline colors removed; `apply_theme()` themes progress bars, list widgets, queue controls, and secondary buttons across all four themes.
- **RTL Support**: Dynamic layout direction based on language selection; `FloatingMiniWidget` syncs direction, text, and the active task.

## File Structure
- `pomotime.py`: Main application logic, UI, sound system.
- `.github/workflows/build.yml`: CI/CD pipeline.
- `requirements.txt`: Dependencies (`PyQt6>=6.5.0`).
- `CONTEXT.md`: Reference documentation.
- `PLAYAPP.md`: User-facing quick start guide.
- `README.md`: This file.
