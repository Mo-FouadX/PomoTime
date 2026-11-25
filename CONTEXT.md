# CONTEXT.md

## Project Overview
**PomoTime** is a professional, native Python desktop application designed for focus management using the Pomodoro technique. It combines a clean modern UI with multi-language support (English and Arabic), full Right-to-Left (RTL) layout switching, floating mini-mode ("always on top"), system tray background operation, cycle tracking, customizable session parameters, one-click productivity presets, a commercial-grade multi-block Session Queue, daily focus goals, visual themes, detailed statistics with CSV export, and a built-in sound system using Python's native libraries. **PomoTime is built and supported for Linux only** (`.AppImage`, `.deb`, and source compilation with Python 3.10+ & PyQt6).

## Student-focused enhancements (v1.1.0)
- **Study Subject Planner**: Add subjects with a target number of focus blocks per subject, mark them done/pending, and track progress per subject.
- **Strict Focus Mode**: Locks the app on the timer screen while studying so there are no distractions until the timer finishes.
- **Weekly Study Stats**: Focus minutes per subject for the current week, a weekly goal (hours), a study streak (consecutive days), and weekly CSV export.
- **Achievements / Badges**: First session, 3-day streak, 7-day streak, 5-hour day, 10-hour week — shown on a dedicated tab.

## Repository layout
```
PomoTime/
├── pomotime/                 # Python package
│   ├── __init__.py           # Public API + version
│   ├── main.py               # PomoTimeApp (Qt UI + timer engine + student features)
│   ├── i18n.py               # Bilingual translations (EN/AR) + RTL helpers
│   ├── audio.py              # Pure-Python chime synthesis + native playback
│   ├── themes.py             # 4 visual themes (default, forest, midnight, sunset)
│   ├── storage.py            # QSettings wrapper (settings, history, student state)
│   └── queue.py              # SessionQueue data model
├── tests/                    # Unit tests (unittest)
│   ├── __init__.py
│   └── test_basic.py
├── docs/                     # GitHub Pages site (landing page)
│   └── index.html
├── pomotime.py               # (removed in v1.1.0 — split into package above)
├── requirements.txt          # PyQt6>=6.5.0
├── CONTEXT.md                # This reference documentation
├── PLAYAPP.md                # User guide
├── README.md                 # General user documentation
├── LICENSE                   # MIT License
├── .gitignore
└── .github/
    └── workflows/
        └── build.yml         # CI/CD: tests, AppImage, .deb
```

## Architecture & Technology Stack
- **Language**: Python 3.10+
- **GUI Framework**: PyQt6 (native performance, QSystemTrayIcon, RTL via `setLayoutDirection`).
- **Packaging**: PyInstaller + linuxdeploy (AppImage) + dpkg-deb (.deb).
- **Sound & Alerts**: Chimes synthesized in pure Python (`math`, `wave`, `struct`) — no audio assets, no `QtMultimedia`. Native players: `paplay`/`aplay` on Linux (terminal bell fallback).
- **Persistence**: `QSettings("PomoTime", "Settings")` — durations, theme, language, queue, history, subjects, weekly stats, streak, achievements. `settings.sync()` on every save.
- **Testing**: `unittest`, run via CI (`python3 -m unittest discover -s tests -v`).

## Core Sound Architecture (`SOUNDS`)
The `SOUNDS` dictionary (`audio.py`) defines notification chimes as note sequences — `(frequency_hz, start_ms, duration_ms, gain)`:
- **click**: Soft 520 Hz tap (45 ms).
- **start_focus**: C5 (523.25 Hz) → G5 (783.99 Hz) ascending chime.
- **start_break**: G5 (783.99 Hz) → E5 (659.25 Hz) descending chime.
- **alert**: C5 → E5 → G5 → C6 arpeggio (~850 ms) for session completion.

## CI / Release pipeline (`.github/workflows/build.yml`)
Triggered on push to `main`/`master`, tags `v*`, pull requests, and manual dispatch.
1. **smoke-test**: Python 3.10, system Qt libs, `pip install -r requirements.txt`, byte-compiles all package modules, runs `unittest discover -s tests`, then a headless (`QT_QPA_PLATFORM=offscreen`) import smoke test that instantiates `PomoTimeApp`.
2. **build-linux-packages** (needs smoke-test): Builds a one-file PyInstaller executable (`--collect-all pomotime`, entry `pomotime/main.py`), generates a 256×256 PNG icon via Qt painter, assembles an AppImage via linuxdeploy, builds a `.deb` via `dpkg-deb`, verifies artifacts, and uploads them as workflow artifacts.

## Entry point
```bash
python3 -m pomotime.main
# or, from source checkout:
python3 pomotime/main.py
```

## Requirements
- Python 3.10+
- PyQt6 >= 6.5.0
- No multimedia packages required (pure Python audio, native system players only)
