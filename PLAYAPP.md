# PLAYAPP.md

## PomoTime - Professional Pomodoro Timer Application

Welcome to **PomoTime**, your ultimate native desktop productivity companion built in Python with PyQt6.

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

1. **Focus & Breaks**: Start the 25-minute focus timer or take a 5/15 minute break. Track completed cycles in real-time.
2. **Mini-Mode**: Click the **"Mini-Mode"** button to collapse into a sleek, floating window that stays on top of all your applications while you work.
3. **Bilingual & RTL Support**: Switch instantly between English (LTR) and Arabic (RTL) using the language selector. The entire interface, alignment, and typography adjust seamlessly.
4. **Notifications**: Receive native tray notifications and alerts when your focus or break session finishes.
5. **Background Soundscapes** (zero external assets):
   - Select from: *Gentle Rain*, *Quiet Cafe*, *Ocean Waves*, *Brown Noise*, *White Noise*.
   - Use the volume slider to control ambient audio; pauses during breaks or timer pause.
6. **Current Task / Focus Goal**: Enter a task above the timer card ("What are you focusing on?") — displayed inside Floating Mini-Mode.
7. **Statistics Tab**: Total focus time, completed cycles, breaks taken, daily streak, Productivity Score (0–100).
8. **Settings Tab**:
   - Duration spinboxes (focus, short break, long break, cycles before long break)
   - Theme combo (Clean Default, Calm Forest, Midnight Focus, Warm Sunset)
   - Music combo (none, rain, cafe, waves, brown, white noise)
   - Ambient volume slider
   - Auto-start breaks / auto-start focus checkboxes
   - Current task field
9. **Keyboard Shortcuts**:
   - `Space` – Start/Pause
   - `R` – Reset
   - `S` – Skip
   - `M` – Toggle Mini-Mode
10. **Circular Progress Ring** around the countdown clock (smoothly depletes, color changes between Focus accent and Break green/teal).

### Architecture Highlights

- **Sound System**: Cross-platform programmatic WAV generation + playback via `QSoundEffect` (PyQt6.QtMultimedia), fallback to `aplay`/`afplay` (Linux/macOS) and `winsound` (Windows).
- **Persistent Storage**: `QSettings("PomoTime", "Settings")` for widget values, cycle counts, task history, ambient volume; stats saved at exit/session end.
- **Daily Focus Stats**: Resets today's total at midnight; keeps all-time totals.
- **Theme Styling**: Hardcoded inline colors removed; `apply_theme()` controls all widgets cleanly.
- **RTL Support**: Dynamic layout direction based on language selection; `FloatingMiniWidget` syncs theme dynamically.

### Keyboard Shortcuts

- **Space**: Start/Pause the timer
- **R**: Reset the current session
- **S**: Skip the current stage
- **M**: Toggle Mini-Mode (floating widget)

### Settings & Customization

- **Durations**: Adjust focus, short break, long break, and cycles before long break
- **Themes**: Four built-in themes (Clean Default, Calm Forest, Midnight Focus, Warm Sunset)
- **Ambient Sounds**: Six options (None, Rain, Cafe, Waves, Brown Noise, White Noise)
- **Automation**: Auto-start breaks/focus options
- **Task Tracking**: Current task field with history log

### Tips

- The app remembers your settings across sessions
- Completed tasks are logged with timestamps
- The mini-mode widget can be dragged to any screen position
- Use keyboard shortcuts for quick control without touching the mouse