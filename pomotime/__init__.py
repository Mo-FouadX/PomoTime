"""
PomoTime - Professional Pomodoro Timer Application.

A polished, bilingual (English/Arabic) desktop timer built with Python 3 and
PyQt6 that helps students and professionals manage focus sessions using the
Pomodoro technique.

Public API:
    main - Application entry point and PomoTimeApp class.
"""

from .main import PomoTimeApp, main

__all__ = ["PomoTimeApp", "main"]
__version__ = "1.1.0"
