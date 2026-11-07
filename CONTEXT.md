# CONTEXT.md

## Project Overview
**PomoTime** is a professional, native Python desktop application designed for focus management using the Pomodoro technique. It combines a clean modern UI with multi-language support (English and Arabic), full Right-to-Left (RTL) layout switching, floating mini-mode ("always on top"), system tray background operation, cycle tracking, customizable session parameters, visual themes, detailed statistics, and a built-in sound system using Python's native libraries.

## Architecture & Technology Stack
- **Language**: Python 3.10+
- **GUI Framework**: PyQt6 (Chosen for robust native performance, native styling, powerful layout management, QSystemTrayIcon integration, and robust Right-to-Left layout support via `setLayoutDirection`).
- **Sound & Alert System**: 
  - Uses Python's built-in `winsound` module on Windows for zero-dependency native audio beeps.
  - Features configurable frequency (Hz) and duration (ms) for easy tone modification.
  - Cross-platform fallback support.

## Core Sound Architecture (`SOUNDS`)
The application defines a centralized `SOUNDS` dictionary at the top of `pomotime.py`, allowing users or developers to easily modify frequencies and durations:
- **`click`**: Freq: 800 Hz, Dur: 100 ms — Played on clicking Start, Stop, or Reset.
- **`start_focus`**: Freq: 1200 Hz, Dur: 400 ms — Distinct higher pitch tone when beginning a Focus session.
- **`start_break`**: Freq: 600 Hz, Dur: 400 ms — Distinct lower pitch tone when beginning a Break period.
- **`alert`**: Freq: 1500 Hz, Dur: 200 ms — Repeating alert tone triggered when any session timer expires.

## Core Features Implemented

### 1. Focus & Break Timers
- **Focus Session**: Default 25 minutes (customizable).
- **Short Break**: Default 5 minutes (customizable).
- **Long Break**: Default 20 minutes (customizable).
- **Cycle Logic**: Automatically switches between focus and breaks. A long break occurs after a configurable number of cycles (default: 4). Pattern example: `25m Focus -> 5m Break -> 25m Focus -> 5m Break -> ... -> 20m Long Break`.

### 2. Alerts & Notifications
- **Visual**: Desktop tray notifications on session completion.
- **Audio**: Built-in programmatic audio alerts (`winsound.Beep`) with repeating alarms upon session expiration and distinct start/click sounds.

### 3. Mini-Mode View (Floating Widget)
- **Behavior**: Clicking "Float Mini-Mode" hides the main window and shows a lightweight, semi-transparent, frameless widget.
- **Features**: 
  - Stays on top of all other applications (`WindowStaysOnTopHint`).
  - Displays remaining time and current stage.
  - Includes Play/Pause and Close controls.
  - **Boundary Detection**: Prevents the widget from being dragged off-screen; snaps to screen edges.

### 4. Background Operation
- **Hide to Tray**: Allows hiding the main interface completely while the timer continues running in the background.
- **Tray Menu**: Provides options to restore the window or quit the application.
- **Tooltip**: Shows live status in the system tray.

### 5. Cycle & Stage Tracking
- Tracks focus vs. break stages.
- Counts completed touchscreen/focus cycles against a target (e.g., 4/4).
- Resets cycle count after a long break.

### 6. Internationalization & RTL
- **Languages**: Full bilingual support (English 🇬🇧/🇺🇸 and Arabic 🇸🇦).
- **Layout**: Dynamic switching between Left-to-Right (LTR) and Right-to-Left (RTL) layouts based on language selection.

### 7. Visual Themes
- Four built-in themes: *Clean Default*, *Calm Forest*, *Midnight Focus*, and *Warm Sunset*.

### 8. Statistics & Productivity
- Metrics tracked: Total focus time, completed cycles, breaks taken, and a calculated Productivity Score (0–100).

## File Structure
- `pomotime.py`: Main application logic, UI, and built-in sound system.
- `CONTEXT.md`: This reference documentation.
- `PLAYAPP.md`: User-facing quick start guide.
