# CONTEXT.md

## Project Overview
**PomoTime** is a professional, native Python desktop application designed for focus management using the Pomodoro technique. It combines a clean modern UI with multi-language support (English and Arabic), full Right-to-Left (RTL) layout switching, floating mini-mode ("always on top"), system tray background operation, cycle tracking, customizable session parameters, one-click productivity presets, a commercial-grade multi-block Session Queue, daily focus goals, visual themes, detailed statistics with CSV export, and a built-in sound system using Python's native libraries. **PomoTime is built and supported for Linux only** (`.AppImage`, `.deb`, and source compilation with Python 3.10+ & PyQt6). Windows and macOS support is planned for future releases.

## Architecture & Technology Stack
- **Language**: Python 3.10+
- **GUI Framework**: PyQt6 (Chosen for robust native performance, native styling, powerful layout management, QSystemTrayIcon integration, and robust Right-to-Left layout support via `setLayoutDirection`).
- **Sound & Alert System**:
  - Soft, musical notification chimes synthesized in pure Python (`math`, `wave`, `struct`) — no audio assets and no `QtMultimedia` dependency.
  - Each chime mixes bell harmonics with a short fade-in, exponential decay, and fade-out to eliminate clicks and pops.
  - Native players: `paplay`/`aplay` on Linux (terminal bell as final fallback).
  - **Platform scope**: Linux only — Windows/macOS playback paths are not required at this stage.

## Core Sound Architecture (`SOUNDS`)
The `SOUNDS` dictionary at the top of `pomotime.py` defines notification chimes as note sequences — `(frequency_hz, start_ms, duration_ms, gain)`:
- **`click`**: Soft 520 Hz tap (45 ms) for buttons and controls.
- **`start_focus`**: C5 (523.25 Hz) → G5 (783.99 Hz) ascending chime.
- **`start_break`**: G5 (783.99 Hz) → E5 (659.25 Hz) descending chime.
- **`alert`**: C5 → E5 → G5 → C6 arpeggio (~850 ms) for session completion.

## Core Features Implemented

### 1. Focus & Break Timers
- **Focus Session**: Default 25 minutes (customizable).
- **Short Break**: Default 5 minutes (customizable).
- **Long Break**: Default 20 minutes (customizable).
- **Cycle Logic**: Automatically switches between focus and breaks. A long break occurs after a configurable number of cycles (default: 4). Pattern example: `25m Focus -> 5m Break -> 25m Focus -> 5m Break -> ... -> 20m Long Break`.

### 2. Alerts & Notifications
- **Visual**: Desktop tray notifications on session completion.
- **Audio**: Soft synthesized notification chimes with distinct start/click sounds and a pleasant repeating alert when a session expires.

### 3. Mini-Mode View (Floating Widget)
- **Behavior**: Clicking "Float Mini-Mode" hides the main window and shows a lightweight, semi-transparent, frameless widget.
- **Features**:
  - Stays on top of all other applications (`WindowStaysOnTopHint`).
  - Displays remaining time, current stage, and progress bar.
  - Includes Play/Pause and Close controls.
  - **Boundary Detection**: Prevents the widget from being dragged off-screen; snaps to screen edges.

### 4. Background Operation
- **Hide to Tray**: Allows hiding the main interface completely while the timer continues running in the background.
- **Tray Menu**: Provides options to restore the window or quit the application.
- **Tooltip**: Shows live status in the system tray.

### 5. Cycle & Stage Tracking
- Tracks focus vs. break stages.
- Counts completed focus cycles against a configurable target (e.g., 4/4).
- Schedules a long break whenever the completed-cycle count reaches a multiple of the target.

### 6. Internationalization & RTL
- **Languages**: Full bilingual support (English 🇬🇧/🇺🇸 and Arabic 🇸🇦).
- **Layout**: Dynamic switching between Left-to-Right (LTR) and Right-to-Left (RTL) layouts based on language selection.
- **RTL Alignment**: `QComboBox`, `QSpinBox`, and `QTabWidget` align properly in RTL mode.

### 7. Visual Themes
- Four built-in themes: *Clean Default*, *Calm Forest*, *Midnight Focus*, and *Warm Sunset*.

### 8. Statistics & Productivity
- Metrics tracked: Total focus time, completed cycles, breaks taken, and a calculated Productivity Score (0–100).
- Daily Focus Goal progress bar (`Today: 50 / 120 mins • 42%`) on both the Timer and Statistics tabs. The daily counter resets at midnight while all-time totals and history remain intact.
- **Recent Sessions Log**: Scrollable list of completed focus blocks with task name, duration, and timestamp.
- **Export to CSV**: Writes the full session history (task, duration, completion time) using `QFileDialog` and Python's `csv` module.

### 9. Current Task / Focus Goal
- **Input**: Text field above the timer card ("What are you focusing on?"), fixed at 360 px so the full placeholder stays visible in both languages.
- **Mini-Mode**: Displays the active task or current queue-step task in the Floating Mini-Widget.
- **Queue Integration**: When a queue block defines a task label, it is shown automatically in the main window and mini-mode.

### 10. Smart Automation & Controls
- **Auto-start Breaks**: After a focus session completes.
- **Auto-start Focus**: After a break finishes.
- **Keyboard Shortcuts**: `Space` (Start/Pause), `R` (Reset), `S` (Skip), `M` (Toggle Mini-Mode).

### 11. Circular Progress Ring
- Smooth progress ring painted via `QPainter` in `CircularTimerWidget`.
- Visually depletes as time passes; color changes smoothly between Focus (accent) and Break (green/teal).

### 12. Productivity Presets
- **Classic Pomodoro**: 25m focus / 5m break / 20m long break × 4.
- **Deep Work**: 50m focus / 10m break / 30m long break × 2.
- **Quick Sprint**: 15m focus / 3m break / 10m long break × 4.
- **Custom Queue**: Activates the user-defined multi-block sequence.
- Applying a preset updates the duration spin boxes, cycle target, timer stage, and persistent settings immediately.

### 13. Multi-Block Session Queue
- Dedicated **Session Queue** tab for building a custom sequence of focus, short-break, and long-break blocks with optional task labels.
- **Block editor**: Choose stage type, minutes (1–180), and an optional task label; add blocks individually.
- **Quick-add**: `+ 2 Focus + Long Break` and `+ 1 Extra Cycle` buttons build common patterns in one click.
- **Reordering**: Move Up, Move Down, Delete Block, and Clear Queue.
- **Automatic progression**: The timer advances through every queue step in order. Completion of the final block shows a queue-complete notification and stays at `00:00` until reset or restart.
- **Live progress**: `Queue Step 2 of 7 • Next: Long Break (15m)` appears directly under the timer controls and in the queue tab.
- **Persistence**: The queue is serialized as JSON inside `QSettings`, together with queue mode and the current index.

### 14. Persistent Storage
- `QSettings("PomoTime", "Settings")` stores durations, cycle target, theme, automation flags, current task, completed cycles, all-time focus/break totals, daily goal, daily focus seconds and date, task history, preset key, and the serialized session queue.
- `settings.sync()` is called on every save so values survive immediately, even without a clean exit.
- Legacy background-sound keys (`bg_music_type`, `ambient_volume`) are purged during startup.

## File Structure
- `pomotime.py`: Main application logic, UI, built-in sound system, circular timer widget, presets, session queue, daily goal, task/history tracking, keyboard shortcuts, close handling, and persistent storage.
- `requirements.txt`: Dependency specification (`PyQt6>=6.5.0`). No multimedia package is required.
- `.github/workflows/build.yml`: CI/CD pipeline with smoke tests, icon generation, AppImage and `.deb` builds.
- `CONTEXT.md`: This reference documentation.
- `README.md`: General user documentation.
