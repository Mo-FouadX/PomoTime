#!/usr/bin/env python3
"""
PomoTime - Professional Pomodoro Timer Application
Built with Python 3 and PyQt6.
Features: Focus/Break timers, Multi-Block Session Queue, Presets,
Mini-Mode (Always on Top), Tray Notifications, Full English/Arabic RTL
support, Themes, Daily Focus Goal, Session History and Statistics.
"""

import sys
import os
import platform
import csv
import json
import tempfile
import struct
import wave
import math
import random
import shutil
import subprocess
from datetime import datetime, date
from PyQt6.QtCore import Qt, QTimer, QLocale, QTime, QEvent, QSize, QSettings, QDate
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStackedWidget, QComboBox, QFrame,
    QSystemTrayIcon, QMenu, QMessageBox, QSpinBox, QGridLayout,
    QTabWidget, QGraphicsDropShadowEffect, QFileDialog,
    QLineEdit, QCheckBox, QListWidget, QListWidgetItem, QProgressBar, QStyle
)
from PyQt6.QtGui import QFont, QIcon, QPalette, QColor, QAction, QFontDatabase, QPixmap, QBrush, QPainter, QPen, QPolygon

# Sound System Configuration
# PomoTime intentionally relies on lightweight, native audio playback
# (paplay/aplay on Linux, afplay on macOS, winsound on Windows) so that
# PyQt6 alone is sufficient and no extra multimedia packages are required.

# Audio files cache
_audio_cache = {}

def generate_chime(notes, filename, volume=1.0, sample_rate=44100):
    """Synthesize a soft, bell-like chime from a musical note sequence.

    Each note is ``(frequency_hz, start_ms, duration_ms, gain)``. Notes are
    mixed together and shaped with a short fade-in, exponential decay and a
    short fade-out, producing a warm marimba/bell tone without clicks or pops.
    """
    if not notes:
        return

    # Total length of the mixed clip.
    total_ms = max(start_ms + dur_ms for _, start_ms, dur_ms, _ in notes)
    total_samples = max(1, int(sample_rate * total_ms / 1000.0))
    buffer = [0.0] * total_samples

    for freq, start_ms, dur_ms, gain in notes:
        start_sample = int(sample_rate * start_ms / 1000.0)
        note_samples = max(1, int(sample_rate * dur_ms / 1000.0))
        attack = max(1, int(0.006 * sample_rate))          # 6 ms fade-in
        release = max(1, min(int(0.020 * sample_rate), note_samples // 3))

        for i in range(note_samples):
            index = start_sample + i
            if index >= total_samples:
                break

            t = i / sample_rate
            position = i / note_samples

            # Smooth envelope: attack, exponential decay, then release.
            envelope = math.exp(-4.5 * position)
            if i < attack:
                envelope *= i / attack
            remaining = note_samples - i
            if remaining < release:
                envelope *= remaining / release

            # Bell/marimba voicing: fundamental plus soft harmonics.
            waveform = (
                0.65 * math.sin(2 * math.pi * freq * t)
                + 0.25 * math.sin(2 * math.pi * 2.0 * freq * t)
                + 0.10 * math.sin(2 * math.pi * 3.0 * freq * t)
            )
            buffer[index] += gain * envelope * waveform

    # Only normalize when the mix would clip. This preserves the intended
    # loudness difference between a subtle click and a full alert chime.
    peak = max((abs(sample) for sample in buffer), default=0.0)
    scale = (0.95 / peak) if peak > 0.95 else 1.0
    amplitude = max(0.0, min(1.0, volume)) * scale

    frames = []
    for sample in buffer:
        value = int(32767 * max(-1.0, min(1.0, sample * amplitude)))
        frames.append(struct.pack('<h', value))

    with wave.open(filename, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(b''.join(frames))

def get_audio_file(sound_key):
    """Get or generate the notification chime file for a sound."""
    cache_key = f"v2_{sound_key}"

    if cache_key not in _audio_cache:
        sound = SOUNDS.get(sound_key)
        if sound and "notes" in sound:
            # Create temp file
            temp_dir = tempfile.gettempdir()
            filename = os.path.join(temp_dir, f"pomotime_{cache_key}.wav")

            # Generate WAV file if it doesn't exist
            if not os.path.exists(filename):
                generate_chime(sound["notes"], filename)

            _audio_cache[cache_key] = filename

    return _audio_cache.get(cache_key)

def get_player_command(audio_file):
    """Return the native command used to play a WAV file, or None if unavailable."""
    system = platform.system()
    if system == "Linux":
        if shutil.which("paplay"):
            return ["paplay", audio_file]
        if shutil.which("aplay"):
            return ["aplay", "-q", audio_file]
    elif system == "Darwin":
        if shutil.which("afplay"):
            return ["afplay", audio_file]
    return None

# Sound Definitions
# Notification sounds are musical note sequences:
#   (frequency_hz, start_ms, duration_ms, gain)
SOUNDS = {
    # Very soft wood/pop tap for buttons and controls.
    "click": {
        "notes": [(520.0, 0.0, 45.0, 0.20)],
        "dur": 45,
    },
    # Uplifting C5 -> G5 ascending chime.
    "start_focus": {
        "notes": [
            (523.25, 0.0, 260.0, 0.55),
            (783.99, 135.0, 260.0, 0.50),
        ],
        "dur": 400,
    },
    # Warm G5 -> E5 descending chime.
    "start_break": {
        "notes": [
            (783.99, 0.0, 260.0, 0.50),
            (659.25, 135.0, 260.0, 0.55),
        ],
        "dur": 400,
    },
    # Gentle C5 -> E5 -> G5 -> C6 arpeggio, like a modern OS notification.
    "alert": {
        "notes": [
            (523.25, 0.0, 420.0, 0.45),
            (659.25, 110.0, 420.0, 0.42),
            (783.99, 220.0, 420.0, 0.40),
            (1046.50, 330.0, 480.0, 0.35),
        ],
        "dur": 850,
    },
}

TRANSLATIONS = {
    "en": {
        "app_title": "PomoTime - Professional Pomodoro Timer",
        "focus": "Focus Session",
        "short_break": "Short Break",
        "long_break": "Long Break",
        "start": "Start",
        "pause": "Pause",
        "reset": "Reset",
        "skip": "Skip",
        "mini_mode": "Float Mini-Mode",
        "normal_mode": "Normal Mode",
        "cycles": "Completed Cycles: {count} / {target}",
        "settings": "Settings",
        "stats": "Statistics",
        "timer_tab": "Timer",
        "focus_duration": "Focus Duration (min):",
        "break_duration": "Break Duration (min):",
        "long_break_duration": "Long Break Duration (min):",
        "cycles_target": "Cycles Before Long Break:",
        "save_settings": "Save Settings",
        "session_completed": "Session Completed!",
        "focus_finished": "Great job! Time for a break.",
        "break_finished": "Break ended! Let's get back to focus.",
        "language": "Language / اللغة",
        "ready": "Ready to focus",
        "stats_total_focus": "Total Focus Time: {mins} minutes",
        "stats_completed_cycles": "Completed Focus Cycles: {count}",
        "stats_breaks_taken": "Total Breaks Taken: {count}",
        "tray_tooltip": "PomoTime - Active",
        "hide_to_tray": "Hide to Tray",
        "quit": "Quit PomoTime",
        "theme_label": "Theme:",
        "sound_alerts": "Sound Alerts:",
        "theme_default": "Clean Default",
        "theme_forest": "Calm Forest",
        "theme_midnight": "Midnight Focus",
        "theme_sunset": "Warm Sunset",
        "current_task_placeholder": "What are you focusing on?",
        "auto_start_breaks": "Auto-start Breaks",
        "auto_start_focus": "Auto-start Focus",
        "theme": "Theme:",
        "show_to_tray": "Show PomoTime",
        "hide_to_tray": "Hide to Tray",
        "confirm_quit": "Are you sure you want to quit PomoTime?",
        "confirm_quit_ar": "هل تريد حقاً مغادرة بوموتايم؟",
        "timer_running": "PomoTime Running",
        "tray_running_message": "PomoTime is running in the background. Click the tray icon to restore.",
        "settings_saved": "Settings saved successfully!",
        "productivity_score": "Productivity Score: {score}/100",
        "break_started": "Break started!",
        "focus_started": "Focus session started!",
        "preset_label": "Preset:",
        "preset_classic": "Classic Pomodoro (25/5/20 ×4)",
        "preset_deep": "Deep Work (50/10/30 ×2)",
        "preset_sprint": "Quick Sprint (15/3/10 ×4)",
        "preset_custom": "Custom Queue",
        "queue_tab": "Session Queue",
        "queue_title": "Multi-Block Session Planner",
        "queue_description": "Build your own sequence of focus blocks and breaks. The timer advances through every step automatically.",
        "queue_mode": "Use Session Queue",
        "queue_empty": "Your queue is empty. Add blocks below or use a quick-add button.",
        "queue_summary": "{count} blocks ready",
        "queue_item_format": "{index}. {stage} · {mins}m — {task}",
        "queue_item_no_task": "{index}. {stage} · {mins}m",
        "queue_progress": "Queue Step {current} of {total} • Next: {next_stage} ({next_mins}m)",
        "queue_progress_last": "Queue Step {current} of {total} • Last step",
        "queue_complete": "Queue complete! Great work.",
        "queue_complete_notification_title": "Queue Complete!",
        "queue_complete_notification_message": "You finished every block in your session queue.",
        "queue_new_block": "New Block:",
        "queue_add": "Add Block",
        "queue_task_placeholder": "Optional task label",
        "queue_move_up": "Move Up",
        "queue_move_down": "Move Down",
        "queue_delete": "Delete Block",
        "queue_clear": "Clear Queue",
        "queue_quick_cycle": "+ 2 Focus + Long Break",
        "queue_quick_extra": "+ 1 Extra Cycle",
        "queue_manage": "Manage Queue",
        "daily_goal_target": "Daily Focus Target (min):",
        "daily_progress": "Today: {done} / {target} mins • {percent}%",
        "recent_sessions": "Recent Sessions",
        "export_csv": "Export to CSV",
        "csv_export_title": "Export Sessions to CSV",
        "csv_filter": "CSV Files (*.csv)",
        "csv_exported": "Sessions exported successfully.",
        "csv_export_error": "Could not export sessions.",
        "csv_task": "Task",
        "csv_duration": "Duration (min)",
        "csv_completed_at": "Completed At",
        "no_sessions": "No sessions logged yet.",
        "history_entry": "{task} · {mins}m · {when}",
        "history_untitled": "Focus Session",
        "min_suffix": " min",
    },
    "ar": {
        "app_title": "بوموتايم - مؤقت بومودورو الاحترافي",
        "focus": "جلسة تركيز",
        "short_break": "استراحة قصيرة",
        "long_break": "استراحة طويلة",
        "start": "بدء",
        "pause": "إيقاف مؤقت",
        "reset": "إعادة ضبط",
        "skip": "تخطي",
        "mini_mode": "وضع العائم المصغر",
        "normal_mode": "الوضع العادي",
        "cycles": "الدورات المكتملة: {count} / {target}",
        "settings": "الإعدادات",
        "stats": "الإحصائيات",
        "timer_tab": "المؤقت",
        "focus_duration": "مدة التركيز (دقيقة):",
        "break_duration": "مدة الاستراحة (دقيقة):",
        "long_break_duration": "مدة الاستراحة الطويلة (دقيقة):",
        "cycles_target": "عدد الدورات قبل الاستراحة الطويلة:",
        "save_settings": "حفظ الإعدادات",
        "session_completed": "انتهت الجلسة!",
        "focus_finished": "عمل رائع! وقت الاستراحة.",
        "break_finished": "انتهت الاستراحة! لنرجع إلى التركيز.",
        "language": "اللغة / Language",
        "ready": "مستعد للتركيز",
        "stats_total_focus": "إجمالي وقت التركيز: {mins} دقيقة",
        "stats_completed_cycles": "دورات التركيز المكتملة: {count}",
        "stats_breaks_taken": "إجمالي الاستراحات: {count}",
        "tray_tooltip": "بوموتايم - يعمل في الخلفية",
        "hide_to_tray": "إخفاء إلى صينية النظام",
        "quit": "إغلاق التطبيق",
        "theme_label": "السمة:",
        "sound_alerts": "التنبيهات الصوتية:",
        "theme_default": "افتراضي نظيف",
        "theme_forest": "غابة هادئة",
        "theme_midnight": "تركيز منتصف الليل",
        "theme_sunset": "غروب دافئ",
        "current_task_placeholder": "ما الذي تركز عليه الآن؟",
        "auto_start_breaks": "بدء الاستراحة تلقائياً",
        "auto_start_focus": "بدء التركيز تلقائياً",
        "theme": "السمة:",
        "show_to_tray": "عرض بوموتايم",
        "hide_to_tray": "إخفاء إلى صينية النظام",
        "confirm_quit": "هل تريد حقاً إغلاق بوموتايم؟",
        "confirm_quit_ar": "هل تريد حقاً مغادرة بوموتايم؟",
        "timer_running": "بوموتايم - يعمل في الخلفية",
        "tray_running_message": "بوموتايم يعمل في الخلفية. انقر على أيقونة صينية النظام للاستعادة.",
        "settings_saved": "تم حفظ الإعدادات بنجاح!",
        "productivity_score": "درجة الإنتاجية: {score}/100",
        "break_started": "بدأ وقت الاستراحة!",
        "focus_started": "بدأت جلسة التركيز!",
        "preset_label": "النمط الجاهز:",
        "preset_classic": "بومودورو كلاسيكي (25/5/20 ×4)",
        "preset_deep": "عمل عميق (50/10/30 ×2)",
        "preset_sprint": "سباق سريع (15/3/10 ×4)",
        "preset_custom": "جدول مخصص",
        "queue_tab": "جدول الجلسات",
        "queue_title": "مخطط الجلسات متعدد المراحل",
        "queue_description": "ابنِ تسلسلك الخاص من جلسات التركيز والاستراحات، وسيتقدم المؤقت تلقائياً خلال كل خطوة.",
        "queue_mode": "تفعيل وضع الجدول",
        "queue_empty": "جدولك فارغ. أضف مراحل أدناه أو استخدم أزرار الإضافة السريعة.",
        "queue_summary": "{count} مراحل جاهزة",
        "queue_item_format": "{index}. {stage} · {mins} دقيقة — {task}",
        "queue_item_no_task": "{index}. {stage} · {mins} دقيقة",
        "queue_progress": "الخطوة {current} من {total} • التالي: {next_stage} ({next_mins} دقيقة)",
        "queue_progress_last": "الخطوة {current} من {total} • الخطوة الأخيرة",
        "queue_complete": "اكتمل الجدول! عمل رائع.",
        "queue_complete_notification_title": "اكتمل جدول الجلسات!",
        "queue_complete_notification_message": "أتممت كل مراحل جدول جلستك.",
        "queue_new_block": "مرحلة جديدة:",
        "queue_add": "إضافة مرحلة",
        "queue_task_placeholder": "اسم المهمة (اختياري)",
        "queue_move_up": "تحريك لأعلى",
        "queue_move_down": "تحريك لأسفل",
        "queue_delete": "حذف المرحلة",
        "queue_clear": "مسح الجدول",
        "queue_quick_cycle": "+ دورتا تركيز + استراحة طويلة",
        "queue_quick_extra": "+ دورة إضافية",
        "queue_manage": "إدارة الجدول",
        "daily_goal_target": "هدف التركيز اليومي (دقيقة):",
        "daily_progress": "اليوم: {done} / {target} دقيقة • {percent}%",
        "recent_sessions": "الجلسات الأخيرة",
        "export_csv": "تصدير إلى CSV",
        "csv_export_title": "تصدير الجلسات إلى CSV",
        "csv_filter": "ملفات CSV (*.csv)",
        "csv_exported": "تم تصدير الجلسات بنجاح.",
        "csv_export_error": "تعذر تصدير الجلسات.",
        "csv_task": "المهمة",
        "csv_duration": "المدة (دقيقة)",
        "csv_completed_at": "وقت الإكمال",
        "no_sessions": "لا توجد جلسات مسجلة بعد.",
        "history_entry": "{task} · {mins} دقيقة · {when}",
        "history_untitled": "جلسة تركيز",
        "min_suffix": " دقيقة",
    }
}


class CircularTimerWidget(QWidget):
    """A smooth circular progress widget for the timer display."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_app = parent
        self.time_left = 1500 if parent is None else parent.focus_minutes * 60
        self.current_stage = "focus"
        self.progress = 0.0
        self.target_progress = 1.0
        self.animation_step = 0.02
        self.setFixedSize(300, 300)
        
        # Animation timer
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self.animate)
        self.anim_timer.start(30)  # ~33 FPS

    def set_time(self, seconds, stage):
        """Set the time and stage."""
        self.time_left = seconds
        self.current_stage = stage
        self.progress = 1.0
        self.target_progress = 1.0
        self.update()

    def animate(self):
        """Smooth animation progress."""
        if self.progress > self.target_progress:
            self.progress = max(self.target_progress, self.progress - self.animation_step)
        elif self.progress < self.target_progress:
            self.progress = min(self.target_progress, self.progress + self.animation_step)
        self.update()

    def paintEvent(self, a0):
        """Paint the circular timer with progress."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Always initialize the theme with a safe default before branching.
        theme = self.parent_app.current_theme if self.parent_app else "default"
        themes = {
            "default": {"bg": "#F1F5F9", "card": "#FFFFFF", "text": "#0F172A", "accent": "#2563EB", "border": "#CBD5E1"},
            "forest": {"bg": "#F0FDF4", "card": "#FFFFFF", "text": "#064E3B", "accent": "#059669", "border": "#A7F3D0"},
            "midnight": {"bg": "#090D16", "card": "#131C2E", "text": "#F8FAFC", "accent": "#6366F1", "border": "#1E293B"},
            "sunset": {"bg": "#FFFBEB", "card": "#FFFFFF", "text": "#7C2D12", "accent": "#EA580C", "border": "#FED7AA"}
        }
        t = themes.get(theme, themes["default"])
        
        width = self.width()
        height = self.height()
        center_x = width / 2
        center_y = height / 2
        radius = min(width, height) * 0.35
        
        # Draw outer circle background
        painter.setPen(QPen(QColor(t["border"]), 12))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(int(center_x - radius), int(center_y - radius), int(radius * 2), int(radius * 2))
        
        # Draw progress arc
        painter.setPen(QPen(QColor(t["accent"]), 10))
        span_angle = int(360 * self.progress * 16)  # 16 = 1 degree in Qt
        painter.drawArc(int(center_x - radius), int(center_y - radius), int(radius * 2), int(radius * 2), 90 * 16, -span_angle)
        
        # Note: CircularTimerWidget now draws ONLY the progress ring.
        # Time, stage, and cycles labels are drawn via QLabels by PomoTimeApp.
        
        painter.end()


class FloatingMiniWidget(QWidget):
    """A sleek, semi-transparent floating widget for Mini-Mode."""
    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.FramelessWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.resize(240, 140)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Container frame with glassmorphism/translucent effect
        self.container = QFrame()
        self.container.setObjectName("MiniContainer")
        self.container.setStyleSheet("""
            QFrame#MiniContainer {
                background-color: rgba(30, 41, 59, 210);
                border-radius: 12px;
                border: 1px solid rgba(255, 255, 255, 40);
            }
            QLabel {
                color: #FFFFFF;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton {
                background-color: #3B82F6;
                color: white;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
                border: none;
            }
            QPushButton:hover { background-color: #2563EB; }
        """)
        
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(15, 15, 15, 15)
        
        self.mini_stage_label = QLabel("Focus")
        self.mini_stage_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mini_stage_label.setFont(QFont("Arial", 10))
        
        self.mini_time_label = QLabel("25:00")
        self.mini_time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mini_time_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))

        # Current task / active queue step shown directly in mini mode.
        self.mini_task_label = QLabel("")
        self.mini_task_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mini_task_label.setFont(QFont("Arial", 9))
        self.mini_task_label.setWordWrap(True)
        self.mini_task_label.setStyleSheet("color: rgba(255, 255, 255, 190);")
        
        btn_layout = QHBoxLayout()
        self.mini_play_btn = QPushButton("▶")
        self.mini_play_btn.setFixedSize(30, 30)
        self.mini_play_btn.clicked.connect(lambda: self.main_app.toggle_start_pause())
        
        self.mini_close_btn = QPushButton("🗖")
        self.mini_close_btn.setFixedSize(30, 30)
        self.mini_close_btn.clicked.connect(lambda: self.main_app.toggle_mini_mode())
        
        btn_layout.addWidget(self.mini_play_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.mini_close_btn)
        
        # Mini stage label
        container_layout.addWidget(self.mini_stage_label)
        
        # Mini progress bar
        self.mini_progress_bar = QFrame()
        self.mini_progress_bar.setFixedHeight(8)
        self.mini_progress_bar.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 40);
                border-radius: 4px;
                margin: 5px 0;
            }
        """)
        mini_progress_layout = QHBoxLayout(self.mini_progress_bar)
        self.mini_progress_fill = QFrame()
        self.mini_progress_fill.setFixedWidth(0)
        self.mini_progress_fill.setStyleSheet("""
            QFrame {
                background-color: #6366F1;
                border-radius: 4px;
            }
        """)
        mini_progress_layout.addWidget(self.mini_progress_fill)
        mini_progress_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addWidget(self.mini_progress_bar)
        
        container_layout.addWidget(self.mini_time_label)
        container_layout.addWidget(self.mini_task_label)
        container_layout.addLayout(btn_layout)

        layout.addWidget(self.container)

        self._old_pos = None

    def mousePressEvent(self, a0):
        if a0 is not None and a0.button() == Qt.MouseButton.LeftButton:
            self._old_pos = a0.globalPosition().toPoint()

    def mouseMoveEvent(self, a0):
        if a0 is not None and self._old_pos is not None:
            delta = a0.globalPosition().toPoint() - self._old_pos
            new_pos = self.pos() + delta

            # Keep within screen boundaries
            screen = self.screen() or QApplication.primaryScreen()
            if screen:
                screen_geo = screen.geometry()
                if new_pos.x() < screen_geo.left():
                    new_pos.setX(screen_geo.left())
                if new_pos.y() < screen_geo.top():
                    new_pos.setY(screen_geo.top())
                if new_pos.x() + self.width() > screen_geo.right():
                    new_pos.setX(screen_geo.right() - self.width())
                if new_pos.y() + self.height() > screen_geo.bottom():
                    new_pos.setY(screen_geo.bottom() - self.height())

            self.move(new_pos)
            self._old_pos = a0.globalPosition().toPoint()

    def mouseReleaseEvent(self, a0):
        if a0 is not None and a0.button() == Qt.MouseButton.LeftButton:
            self._old_pos = None


class PomoTimeApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PomoTime")
        self.setGeometry(100, 100, 640, 860)

        # State variables
        self.focus_minutes = 25
        self.short_break_minutes = 5
        self.long_break_minutes = 20
        self.cycles_before_long_break = 4

        self.current_stage = "focus"
        self.time_left = self.focus_minutes * 60
        self.is_running = False
        self.completed_cycles = 0
        self.total_focus_seconds = 0
        self.total_breaks_taken = 0
        self.lang = "en"
        self.is_mini_mode = False
        self.mini_widget = None
        self.current_theme = "default"
        
        # Task tracking
        self.current_task = ""
        
        # Session queue (list of {"kind", "minutes", "task"}) and preset state
        self.session_queue = []
        self.queue_index = 0
        self.queue_mode = False
        self.preset_key = "classic"

        # Daily focus goal tracking
        self.daily_goal_minutes = 120
        self.daily_focus_seconds = 0
        self.daily_focus_date = date.today().isoformat()

        # Automation settings
        self.auto_start_breaks = False
        self.auto_start_focus = False
        
        # Timer setup - initialize once
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)
        
        # Audio setup
        self.alert_timer = QTimer(self)
        self.alert_timer.timeout.connect(self.repeat_alert_sound)
        self.alert_repeats_left = 0
        
        # Load saved settings
        self.settings = QSettings("PomoTime", "Settings")
        
        # Task history
        self.task_history = []

        self.init_ui()
        self.setup_tray()
        self.apply_theme()
        self.load_settings()
        
        # Keyboard shortcuts
        self.setup_keyboard_shortcuts()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)
        
        # Top Bar
        top_bar_layout = QHBoxLayout()

        self.lang_combo = QComboBox()
        self.lang_combo.addItem("English", "en")
        self.lang_combo.addItem("العربية", "ar")
        self.lang_combo.currentIndexChanged.connect(self.change_language)
        top_bar_layout.addWidget(self.lang_combo)

        top_bar_layout.addStretch()

        # Task input

        self.mini_mode_btn = QPushButton(self.t("mini_mode"))
        self.mini_mode_btn.clicked.connect(self.toggle_mini_mode)
        top_bar_layout.addWidget(self.mini_mode_btn)

        self.hide_tray_btn = QPushButton(self.t("hide_to_tray"))
        self.hide_tray_btn.clicked.connect(self.hide_to_tray)
        top_bar_layout.addWidget(self.hide_tray_btn)

        self.main_layout.addLayout(top_bar_layout)
        
        # Tabs
        self.tabs = QTabWidget()
        self.timer_tab = QWidget()
        timer_layout = QVBoxLayout(self.timer_tab)
        timer_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        timer_layout.setSpacing(20)

        # Preset selector bar
        preset_layout = QHBoxLayout()
        preset_layout.setSpacing(10)
        self.preset_label_widget = QLabel(self.t("preset_label"))
        self.preset_combo = QComboBox()
        self.preset_combo.addItem(self.t("preset_classic"), "classic")
        self.preset_combo.addItem(self.t("preset_deep"), "deep")
        self.preset_combo.addItem(self.t("preset_sprint"), "sprint")
        self.preset_combo.addItem(self.t("preset_custom"), "custom")
        self.preset_combo.currentIndexChanged.connect(self.on_preset_changed)
        preset_layout.addWidget(self.preset_label_widget)
        preset_layout.addWidget(self.preset_combo)
        timer_layout.addLayout(preset_layout)

        # Current Task Input (above the timer card, fixed width for full placeholder)
        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText(self.t("current_task_placeholder"))
        self.task_input.setFixedWidth(360)
        self.task_input.textChanged.connect(self.update_current_task)
        timer_layout.addWidget(self.task_input, 0, Qt.AlignmentFlag.AlignCenter)

        # Timer Display Card with circular progress ring
        timer_card = QFrame()
        timer_card.setObjectName("TimerCard")
        timer_card.setFixedSize(380, 320)
        timer_card.setStyleSheet("")  # Themed via apply_theme()

        card_layout = QVBoxLayout(timer_card)
        card_layout.setContentsMargins(24, 20, 24, 20)
        card_layout.setSpacing(6)

        # Stage label (Focus Session / Short Break / Long Break)
        self.stage_label = QLabel(self.t("focus"))
        self.stage_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stage_label.setFont(QFont("Arial", 13, QFont.Weight.Bold))

        # Circular progress ring (draws ONLY the ring - no text inside)
        self.circular_timer = CircularTimerWidget(self)
        self.circular_timer.setFixedSize(230, 230)

        # Live countdown text - centered inside the ring via layout stacking
        self.time_label = QLabel("25:00")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setFont(QFont("Arial", 40, QFont.Weight.Bold))
        self.time_label.setStyleSheet("")

        # Center the time_label on top of the circular ring
        ring_container = QWidget()
        ring_container.setFixedSize(230, 230)
        self.circular_timer.setParent(ring_container)
        self.circular_timer.move(0, 0)
        self.time_label.setParent(ring_container)
        self.time_label.setGeometry(0, 0, 230, 230)

        # Cycles label below the ring
        self.cycles_label = QLabel(self.t("cycles", count=0, target=self.cycles_before_long_break))
        self.cycles_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cycles_label.setFont(QFont("Arial", 10))

        card_layout.addWidget(self.stage_label, 0, Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(ring_container, 0, Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(self.cycles_label, 0, Qt.AlignmentFlag.AlignCenter)

        # Task display (shows the active task name under the timer)
        self.task_display = QLabel("")
        self.task_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.task_display.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.task_display.setWordWrap(True)
        card_layout.addWidget(self.task_display, 0, Qt.AlignmentFlag.AlignCenter)

        timer_layout.addWidget(timer_card, 0, Qt.AlignmentFlag.AlignCenter)

                
        # Controls
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(15)
        
        self.start_btn = QPushButton(self.t("start"))
        self.start_btn.setMinimumWidth(125)
        self.start_btn.setFixedHeight(42)
        self.start_btn.clicked.connect(self.toggle_start_pause)
        
        self.reset_btn = QPushButton(self.t("reset"))
        self.reset_btn.setMinimumWidth(125)
        self.reset_btn.setFixedHeight(42)
        self.reset_btn.clicked.connect(self.reset_timer)
        
        self.skip_btn = QPushButton(self.t("skip"))
        self.skip_btn.setMinimumWidth(125)
        self.skip_btn.setFixedHeight(42)
        self.skip_btn.clicked.connect(lambda: self.advance_stage(completed=False))
        
        controls_layout.addWidget(self.start_btn)
        controls_layout.addWidget(self.reset_btn)
        controls_layout.addWidget(self.skip_btn)
        
        timer_layout.addLayout(controls_layout)

        # Live queue progress (visible while queue mode is active)
        self.queue_status_label = QLabel("")
        self.queue_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.queue_status_label.setWordWrap(True)
        self.queue_status_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.queue_status_label.setVisible(False)
        timer_layout.addWidget(self.queue_status_label)

        self.manage_queue_btn = QPushButton(self.t("queue_manage"))
        self.manage_queue_btn.setObjectName("SecondaryButton")
        self.manage_queue_btn.clicked.connect(self.open_queue_tab)
        timer_layout.addWidget(self.manage_queue_btn, 0, Qt.AlignmentFlag.AlignCenter)

        # Daily goal progress on the Timer tab
        self.timer_daily_label = QLabel("")
        self.timer_daily_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        timer_layout.addWidget(self.timer_daily_label)

        self.timer_daily_bar = QProgressBar()
        self.timer_daily_bar.setRange(0, 100)
        self.timer_daily_bar.setValue(0)
        self.timer_daily_bar.setTextVisible(False)
        self.timer_daily_bar.setFixedHeight(12)
        self.timer_daily_bar.setFixedWidth(360)
        timer_layout.addWidget(self.timer_daily_bar, 0, Qt.AlignmentFlag.AlignCenter)

        self.tabs.addTab(self.timer_tab, self.t("timer_tab"))
        
        # Statistics Tab
        self.stats_tab = QWidget()
        stats_layout = QVBoxLayout(self.stats_tab)
        stats_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stats_layout.setSpacing(20)
        
        stats_card = QFrame()
        stats_card.setObjectName("StatsCard")
        stats_card.setStyleSheet("")  # Remove hardcoded background
        stats_card_layout = QVBoxLayout(stats_card)
        stats_card_layout.setContentsMargins(25, 25, 25, 25)
        stats_card_layout.setSpacing(15)
        
        self.stats_title = QLabel(self.t("stats"))
        self.stats_title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.stats_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stats_card_layout.addWidget(self.stats_title)
        
        self.stat_focus_label = QLabel(self.t("stats_total_focus", mins=0))
        stats_card_layout.addWidget(self.stat_focus_label)
        
        self.stat_cycles_label = QLabel(self.t("stats_completed_cycles", count=0))
        stats_card_layout.addWidget(self.stat_cycles_label)
        
        self.stat_breaks_label = QLabel(self.t("stats_breaks_taken", count=0))
        stats_card_layout.addWidget(self.stat_breaks_label)
        
        # Productivity Score
        self.score_label = QLabel(self.t("productivity_score", score=0))
        self.score_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.score_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        stats_card_layout.addWidget(self.score_label)

        # Daily goal progress on the Statistics tab
        self.stats_daily_label = QLabel("")
        self.stats_daily_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stats_card_layout.addWidget(self.stats_daily_label)

        self.stats_daily_bar = QProgressBar()
        self.stats_daily_bar.setRange(0, 100)
        self.stats_daily_bar.setValue(0)
        self.stats_daily_bar.setTextVisible(False)
        self.stats_daily_bar.setFixedHeight(12)
        stats_card_layout.addWidget(self.stats_daily_bar)

        # Recent sessions log
        self.recent_sessions_label = QLabel(self.t("recent_sessions"))
        self.recent_sessions_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        stats_card_layout.addWidget(self.recent_sessions_label)

        self.history_list = QListWidget()
        self.history_list.setMinimumHeight(170)
        self.history_list.setMinimumWidth(420)
        stats_card_layout.addWidget(self.history_list)

        self.export_csv_btn = QPushButton(self.t("export_csv"))
        self.export_csv_btn.setObjectName("SecondaryButton")
        self.export_csv_btn.clicked.connect(self.export_sessions_csv)
        stats_card_layout.addWidget(self.export_csv_btn)

        stats_card.setMinimumWidth(460)
        stats_layout.addWidget(stats_card, 0, Qt.AlignmentFlag.AlignCenter)
        self.tabs.addTab(self.stats_tab, self.t("stats"))

        # Session Queue Tab (multi-block planner)
        self.queue_tab = QWidget()
        queue_layout = QVBoxLayout(self.queue_tab)
        queue_layout.setSpacing(12)
        queue_layout.setContentsMargins(16, 16, 16, 16)

        self.queue_title = QLabel(self.t("queue_title"))
        self.queue_title.setFont(QFont("Arial", 15, QFont.Weight.Bold))
        self.queue_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        queue_layout.addWidget(self.queue_title)

        self.queue_description = QLabel(self.t("queue_description"))
        self.queue_description.setWordWrap(True)
        self.queue_description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        queue_layout.addWidget(self.queue_description)

        self.queue_mode_check = QCheckBox(self.t("queue_mode"))
        self.queue_mode_check.stateChanged.connect(self.toggle_queue_mode)
        queue_layout.addWidget(self.queue_mode_check)

        self.queue_list = QListWidget()
        self.queue_list.setMinimumHeight(150)
        queue_layout.addWidget(self.queue_list, 1)

        self.queue_progress_label = QLabel(self.t("queue_empty"))
        self.queue_progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.queue_progress_label.setWordWrap(True)
        self.queue_progress_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        queue_layout.addWidget(self.queue_progress_label)

        # Add custom block row
        self.queue_new_block_label = QLabel(self.t("queue_new_block"))
        queue_layout.addWidget(self.queue_new_block_label)

        add_row = QHBoxLayout()
        add_row.setSpacing(8)
        self.queue_kind_combo = QComboBox()
        self.queue_kind_combo.addItem(self.t("focus"), "focus")
        self.queue_kind_combo.addItem(self.t("short_break"), "short_break")
        self.queue_kind_combo.addItem(self.t("long_break"), "long_break")
        self.queue_kind_combo.currentIndexChanged.connect(self.on_queue_kind_changed)
        self.queue_minutes_spin = QSpinBox()
        self.queue_minutes_spin.setRange(1, 180)
        self.queue_minutes_spin.setValue(self.focus_minutes)
        self.queue_minutes_spin.setSuffix(self.t("min_suffix"))
        self.queue_task_edit = QLineEdit()
        self.queue_task_edit.setPlaceholderText(self.t("queue_task_placeholder"))
        self.queue_add_btn = QPushButton("+ " + self.t("queue_add"))
        self.queue_add_btn.clicked.connect(self.add_queue_block)
        add_row.addWidget(self.queue_kind_combo)
        add_row.addWidget(self.queue_minutes_spin)
        add_row.addWidget(self.queue_task_edit, 1)
        add_row.addWidget(self.queue_add_btn)
        queue_layout.addLayout(add_row)

        # Quick-add buttons
        quick_row = QHBoxLayout()
        quick_row.setSpacing(8)
        self.queue_quick_cycle_btn = QPushButton(self.t("queue_quick_cycle"))
        self.queue_quick_cycle_btn.setObjectName("SecondaryButton")
        self.queue_quick_cycle_btn.clicked.connect(self.quick_add_cycle)
        self.queue_quick_extra_btn = QPushButton(self.t("queue_quick_extra"))
        self.queue_quick_extra_btn.setObjectName("SecondaryButton")
        self.queue_quick_extra_btn.clicked.connect(self.quick_add_extra_cycle)
        quick_row.addWidget(self.queue_quick_cycle_btn)
        quick_row.addWidget(self.queue_quick_extra_btn)
        queue_layout.addLayout(quick_row)

        # Reorder / delete controls
        manage_row = QHBoxLayout()
        manage_row.setSpacing(8)
        self.queue_up_btn = QPushButton(self.t("queue_move_up"))
        self.queue_up_btn.setObjectName("SecondaryButton")
        self.queue_up_btn.clicked.connect(self.move_queue_up)
        self.queue_down_btn = QPushButton(self.t("queue_move_down"))
        self.queue_down_btn.setObjectName("SecondaryButton")
        self.queue_down_btn.clicked.connect(self.move_queue_down)
        self.queue_delete_btn = QPushButton(self.t("queue_delete"))
        self.queue_delete_btn.setObjectName("SecondaryButton")
        self.queue_delete_btn.clicked.connect(self.delete_queue_block)
        self.queue_clear_btn = QPushButton(self.t("queue_clear"))
        self.queue_clear_btn.setObjectName("SecondaryButton")
        self.queue_clear_btn.clicked.connect(self.clear_queue)
        manage_row.addWidget(self.queue_up_btn)
        manage_row.addWidget(self.queue_down_btn)
        manage_row.addWidget(self.queue_delete_btn)
        manage_row.addWidget(self.queue_clear_btn)
        queue_layout.addLayout(manage_row)

        self.tabs.addTab(self.queue_tab, self.t("queue_tab"))

        # Settings Tab
        self.settings_tab = QWidget()
        settings_layout = QVBoxLayout(self.settings_tab)
        settings_layout.setSpacing(15)
        settings_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        grid = QGridLayout()
        grid.setSpacing(10)
        
        self.focus_spin = QSpinBox()
        self.focus_spin.setValue(self.focus_minutes)
        self.focus_label_set = QLabel(self.t("focus_duration"))
        grid.addWidget(self.focus_label_set, 0, 0)
        grid.addWidget(self.focus_spin, 0, 1)
        
        self.break_spin = QSpinBox()
        self.break_spin.setValue(self.short_break_minutes)
        self.break_label_set = QLabel(self.t("break_duration"))
        grid.addWidget(self.break_label_set, 1, 0)
        grid.addWidget(self.break_spin, 1, 1)
        
        self.long_break_spin = QSpinBox()
        self.long_break_spin.setValue(self.long_break_minutes)
        self.long_break_label_set = QLabel(self.t("long_break_duration"))
        grid.addWidget(self.long_break_label_set, 2, 0)
        grid.addWidget(self.long_break_spin, 2, 1)
        
        self.cycles_spin = QSpinBox()
        self.cycles_spin.setValue(self.cycles_before_long_break)
        self.cycles_spin.setMinimum(1)
        self.cycles_label_set = QLabel(self.t("cycles_target"))
        grid.addWidget(self.cycles_label_set, 3, 0)
        grid.addWidget(self.cycles_spin, 3, 1)

        self.daily_goal_spin = QSpinBox()
        self.daily_goal_spin.setRange(5, 1440)
        self.daily_goal_spin.setValue(self.daily_goal_minutes)
        self.daily_goal_spin.setSuffix(self.t("min_suffix"))
        self.daily_goal_label_set = QLabel(self.t("daily_goal_target"))
        grid.addWidget(self.daily_goal_label_set, 4, 0)
        grid.addWidget(self.daily_goal_spin, 4, 1)
        
        settings_layout.addLayout(grid)
        
        # Theme & Music
        theme_layout = QHBoxLayout()
        self.theme_combo = QComboBox()
        self.theme_combo.addItem(self.t("theme_default"), "default")
        self.theme_combo.addItem(self.t("theme_forest"), "forest")
        self.theme_combo.addItem(self.t("theme_midnight"), "midnight")
        self.theme_combo.addItem(self.t("theme_sunset"), "sunset")
        self.theme_combo.currentIndexChanged.connect(self.change_theme)
        self.theme_label_widget = QLabel(self.t("theme_label"))
        theme_layout.addWidget(self.theme_label_widget)
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        settings_layout.addLayout(theme_layout)
        
        # Automation options
        auto_layout = QVBoxLayout()
        self.auto_break_check = QCheckBox(self.t("auto_start_breaks"))
        self.auto_break_check.setChecked(self.auto_start_breaks)
        self.auto_break_check.stateChanged.connect(self.toggle_auto_break)
        auto_layout.addWidget(self.auto_break_check)
        
        self.auto_focus_check = QCheckBox(self.t("auto_start_focus"))
        self.auto_focus_check.setChecked(self.auto_start_focus)
        self.auto_focus_check.stateChanged.connect(self.toggle_auto_focus)
        auto_layout.addWidget(self.auto_focus_check)
        
        settings_layout.addLayout(auto_layout)
        
        self.save_settings_btn = QPushButton(self.t("save_settings"))
        self.save_settings_btn.clicked.connect(lambda: self.save_settings(notify=True))
        settings_layout.addWidget(self.save_settings_btn)
        settings_layout.addStretch()
        
        self.tabs.addTab(self.settings_tab, self.t("settings"))
        self.tabs.currentChanged.connect(self.on_tab_changed)
        
        self.main_layout.addWidget(self.tabs)

    def t(self, key, **kwargs):
        text = TRANSLATIONS[self.lang].get(key)
        if not isinstance(text, str):
            text = key
        if kwargs:
            try:
                return text.format(**kwargs)
            except (KeyError, IndexError):
                return text
        return text
    
    def update_current_task(self):
        """Update the current task from the input field."""
        self.current_task = self.task_input.text().strip()
        self.update_task_display()
    
    def setup_keyboard_shortcuts(self):
        """Setup global keyboard shortcuts using QAction."""
        from PyQt6.QtGui import QKeySequence
        
        # Space - Start/Pause
        self.shortcut_start_pause = QAction(self.t("start"), self)
        self.shortcut_start_pause.setShortcut(QKeySequence(Qt.Key.Key_Space))
        self.shortcut_start_pause.triggered.connect(self.toggle_start_pause)

        # R - Reset
        self.shortcut_reset = QAction(self.t("reset"), self)
        self.shortcut_reset.setShortcut(QKeySequence(Qt.Key.Key_R))
        self.shortcut_reset.triggered.connect(self.reset_timer)

        # S - Skip
        self.shortcut_skip = QAction(self.t("skip"), self)
        self.shortcut_skip.setShortcut(QKeySequence(Qt.Key.Key_S))
        self.shortcut_skip.triggered.connect(lambda: self.advance_stage(completed=False))

        # M - Toggle Mini-Mode
        self.shortcut_mini = QAction(self.t("mini_mode"), self)
        self.shortcut_mini.setShortcut(QKeySequence(Qt.Key.Key_M))
        self.shortcut_mini.triggered.connect(self.toggle_mini_mode)

    def change_language(self, index):
        self.lang = self.lang_combo.itemData(index)
        direction = Qt.LayoutDirection.RightToLeft if self.lang == "ar" else Qt.LayoutDirection.LeftToRight
        self.setLayoutDirection(direction)
        if self.mini_widget:
            self.mini_widget.setLayoutDirection(direction)
        self.retranslate_ui()
        self.apply_theme()

    def retranslate_ui(self):
        self.setWindowTitle(self.t("app_title"))
        self.mini_mode_btn.setText(self.t("mini_mode") if not self.is_mini_mode else self.t("normal_mode"))
        self.hide_tray_btn.setText(self.t("hide_to_tray"))
        self.update_stage_label_text()
        self.cycles_label.setText(self.t("cycles", count=self.completed_cycles, target=self.cycles_before_long_break))
        
        start_button_text = self.pause_text() if self.is_running else self.t("start")
        self.start_btn.setText(start_button_text)
        if self.mini_widget:
            self.mini_widget.mini_play_btn.setText("⏸" if self.is_running else "▶")
            
        self.reset_btn.setText(self.t("reset"))
        self.skip_btn.setText(self.t("skip"))
        self.manage_queue_btn.setText(self.t("queue_manage"))
        
        self.tabs.setTabText(0, self.t("timer_tab"))
        self.tabs.setTabText(1, self.t("stats"))
        self.tabs.setTabText(2, self.t("queue_tab"))
        self.tabs.setTabText(3, self.t("settings"))
        
        self.focus_label_set.setText(self.t("focus_duration"))
        self.break_label_set.setText(self.t("break_duration"))
        self.long_break_label_set.setText(self.t("long_break_duration"))
        self.cycles_label_set.setText(self.t("cycles_target"))
        self.daily_goal_label_set.setText(self.t("daily_goal_target"))
        self.queue_minutes_spin.setSuffix(self.t("min_suffix"))
        self.daily_goal_spin.setSuffix(self.t("min_suffix"))
        self.save_settings_btn.setText(self.t("save_settings"))
        self.tray_icon.setToolTip(self.t("tray_tooltip"))
        self.task_input.setPlaceholderText(self.t("current_task_placeholder"))
        self.auto_break_check.setText(self.t("auto_start_breaks"))
        self.auto_focus_check.setText(self.t("auto_start_focus"))
        self.theme_label_widget.setText(self.t("theme_label"))
        self.stats_title.setText(self.t("stats"))
        self.preset_label_widget.setText(self.t("preset_label"))

        # Update preset combo display names
        preset_keys = ["classic", "deep", "sprint", "custom"]
        for i in range(self.preset_combo.count()):
            key = preset_keys[i] if i < len(preset_keys) else ""
            if key:
                self.preset_combo.setItemText(i, self.t(f"preset_{key}"))

        # Update queue tab text
        self.queue_title.setText(self.t("queue_title"))
        self.queue_description.setText(self.t("queue_description"))
        self.queue_mode_check.setText(self.t("queue_mode"))
        self.queue_new_block_label.setText(self.t("queue_new_block"))
        self.queue_task_edit.setPlaceholderText(self.t("queue_task_placeholder"))
        self.queue_add_btn.setText("+ " + self.t("queue_add"))
        self.queue_quick_cycle_btn.setText(self.t("queue_quick_cycle"))
        self.queue_quick_extra_btn.setText(self.t("queue_quick_extra"))
        self.queue_up_btn.setText(self.t("queue_move_up"))
        self.queue_down_btn.setText(self.t("queue_move_down"))
        self.queue_delete_btn.setText(self.t("queue_delete"))
        self.queue_clear_btn.setText(self.t("queue_clear"))
        for i in range(self.queue_kind_combo.count()):
            kind = self.queue_kind_combo.itemData(i)
            kind_key = f"{kind}"
            self.queue_kind_combo.setItemText(i, self.t(kind_key))
        self.refresh_queue_ui()

        self.recent_sessions_label.setText(self.t("recent_sessions"))
        self.export_csv_btn.setText(self.t("export_csv"))
        self.refresh_history_list()

        # Update theme combo display names
        for i in range(self.theme_combo.count()):
            theme_key = f"theme_{self.theme_combo.itemData(i)}"
            self.theme_combo.setItemText(i, self.t(theme_key))
        
        # Update stats text
        focus_mins_total = self.total_focus_seconds // 60
        self.stat_focus_label.setText(self.t("stats_total_focus", mins=focus_mins_total))
        self.stat_cycles_label.setText(self.t("stats_completed_cycles", count=self.completed_cycles))
        self.stat_breaks_label.setText(self.t("stats_breaks_taken", count=self.total_breaks_taken))
        
        # Update score and daily progress
        self.update_score()
        self.update_daily_progress()

    def update_score(self):
        # Simple productivity score calculation
        score = min(100, (self.completed_cycles * 25) + (self.total_focus_seconds // 60))
        self.score_label.setText(self.t("productivity_score", score=score))

    # ------------------------------------------------------------------
    # Presets
    # ------------------------------------------------------------------
    def on_preset_changed(self, index):
        key = self.preset_combo.itemData(index)
        if isinstance(key, str):
            self.apply_preset(key)

    def apply_preset(self, key):
        """Apply a built-in productivity preset or activate the custom queue."""
        # Applying any preset starts from a clean, paused state.
        self.timer.stop()
        self.is_running = False
        self.start_btn.setText(self.t("start"))
        if self.mini_widget:
            self.mini_widget.mini_play_btn.setText("▶")

        if key == "custom":
            self.preset_key = "custom"
            if not self.session_queue:
                self.queue_mode = False
                self.queue_mode_check.blockSignals(True)
                self.queue_mode_check.setChecked(False)
                self.queue_mode_check.blockSignals(False)
                self.queue_status_label.setVisible(False)
                self.open_queue_tab()
            else:
                self.queue_mode = True
                self.queue_index = 0
                self.queue_mode_check.blockSignals(True)
                self.queue_mode_check.setChecked(True)
                self.queue_mode_check.blockSignals(False)
                self.load_queue_step(0)
                self.refresh_queue_ui()
                self.update_display()
            self.save_settings()
            return

        presets = {
            "classic": (25, 5, 20, 4),
            "deep": (50, 10, 30, 2),
            "sprint": (15, 3, 10, 4),
        }
        if key not in presets:
            return

        focus, short_break, long_break, cycles = presets[key]
        self.preset_key = key

        self.focus_spin.setValue(focus)
        self.break_spin.setValue(short_break)
        self.long_break_spin.setValue(long_break)
        self.cycles_spin.setValue(cycles)

        self.queue_mode = False
        self.queue_mode_check.blockSignals(True)
        self.queue_mode_check.setChecked(False)
        self.queue_mode_check.blockSignals(False)
        self.current_stage = "focus"
        self.time_left = focus * 60
        self.update_stage_label_text()
        self.update_task_display()
        self.refresh_queue_ui()
        self.save_settings()

    # ------------------------------------------------------------------
    # Task display helpers
    # ------------------------------------------------------------------
    def update_task_display(self):
        """Show the active queue step task or the global current task."""
        text = ""
        if self.queue_mode and 0 <= self.queue_index < len(self.session_queue):
            step = self.session_queue[self.queue_index]
            step_task = str(step.get("task", "") or "")
            if step_task:
                text = step_task
            elif step.get("kind", "focus") == "focus":
                text = self.current_task
        else:
            text = self.current_task

        self.task_display.setText(text)
        if self.mini_widget:
            self.mini_widget.mini_task_label.setText(text)

    # ------------------------------------------------------------------
    # Session Queue management
    # ------------------------------------------------------------------
    def open_queue_tab(self):
        self.tabs.setCurrentIndex(2)

    def queue_step_text(self, index, step):
        stage = self.t(str(step.get("kind", "focus")))
        minutes = int(step.get("minutes", self.focus_minutes) or self.focus_minutes)
        task = str(step.get("task", "") or "")
        if task:
            return self.t("queue_item_format", index=index + 1, stage=stage, mins=minutes, task=task)
        return self.t("queue_item_no_task", index=index + 1, stage=stage, mins=minutes)

    def refresh_queue_ui(self, select=None):
        """Rebuild the queue list and synchronize controls with state."""
        if not hasattr(self, "queue_list"):
            return

        self.queue_list.blockSignals(True)
        self.queue_list.clear()
        if not self.session_queue:
            empty_item = QListWidgetItem(self.t("queue_empty"))
            empty_item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.queue_list.addItem(empty_item)
        else:
            for i, step in enumerate(self.session_queue):
                self.queue_list.addItem(self.queue_step_text(i, step))

            if self.queue_mode and self.queue_index < len(self.session_queue):
                self.queue_list.setCurrentRow(self.queue_index)
            elif select is not None and 0 <= select < len(self.session_queue):
                self.queue_list.setCurrentRow(select)
        self.queue_list.blockSignals(False)

        self.queue_mode_check.blockSignals(True)
        self.queue_mode_check.setChecked(self.queue_mode)
        self.queue_mode_check.setEnabled(bool(self.session_queue))
        self.queue_mode_check.blockSignals(False)

        self.update_queue_progress()

    def on_queue_kind_changed(self, index):
        kind = self.queue_kind_combo.itemData(index)
        if kind == "focus":
            self.queue_minutes_spin.setValue(self.focus_spin.value())
        elif kind == "short_break":
            self.queue_minutes_spin.setValue(self.break_spin.value())
        elif kind == "long_break":
            self.queue_minutes_spin.setValue(self.long_break_spin.value())

    def add_queue_block(self):
        kind = self.queue_kind_combo.currentData()
        if not isinstance(kind, str):
            kind = "focus"
        self.session_queue.append({
            "kind": kind,
            "minutes": self.queue_minutes_spin.value(),
            "task": self.queue_task_edit.text().strip(),
        })
        self.queue_task_edit.clear()
        self._finish_queue_edit(len(self.session_queue) - 1)

    def quick_add_cycle(self):
        """Append 2 focus blocks followed by a long break."""
        for _ in range(2):
            self.session_queue.append({
                "kind": "focus",
                "minutes": self.focus_spin.value(),
                "task": "",
            })
        self.session_queue.append({
            "kind": "long_break",
            "minutes": self.long_break_spin.value(),
            "task": "",
        })
        self._finish_queue_edit(len(self.session_queue) - 1)

    def quick_add_extra_cycle(self):
        """Append one focus block followed by a short break."""
        self.session_queue.append({
            "kind": "focus",
            "minutes": self.focus_spin.value(),
            "task": "",
        })
        self.session_queue.append({
            "kind": "short_break",
            "minutes": self.break_spin.value(),
            "task": "",
        })
        self._finish_queue_edit(len(self.session_queue) - 1)

    def _finish_queue_edit(self, select):
        # Adding a block while the Custom Queue preset is selected activates it.
        if self.preset_key == "custom" and not self.queue_mode:
            self.queue_mode = True
            self.queue_index = 0
            self.load_queue_step(0)
        self.refresh_queue_ui(select=select)
        self.update_display()
        self.save_settings()

    def move_queue_up(self):
        row = self.queue_list.currentRow()
        if row <= 0 or row >= len(self.session_queue):
            return
        self.session_queue[row - 1], self.session_queue[row] = self.session_queue[row], self.session_queue[row - 1]
        self._after_queue_reorder(row - 1)

    def move_queue_down(self):
        row = self.queue_list.currentRow()
        if row < 0 or row >= len(self.session_queue) - 1:
            return
        self.session_queue[row + 1], self.session_queue[row] = self.session_queue[row], self.session_queue[row + 1]
        self._after_queue_reorder(row + 1)

    def _after_queue_reorder(self, row):
        if self.queue_mode and self.session_queue:
            self.queue_index = min(self.queue_index, len(self.session_queue) - 1)
            self.load_queue_step(self.queue_index)
        self.refresh_queue_ui(select=row)
        self.update_display()
        self.save_settings()

    def delete_queue_block(self):
        row = self.queue_list.currentRow()
        if row < 0 or row >= len(self.session_queue):
            return
        del self.session_queue[row]

        if not self.session_queue:
            self.queue_mode = False
            self.queue_index = 0
            self.current_stage = "focus"
            self.load_current_stage_time()
            self.update_stage_label_text()
        elif self.queue_mode:
            if row < self.queue_index:
                self.queue_index -= 1
            self.queue_index = max(0, min(self.queue_index, len(self.session_queue) - 1))
            self.load_queue_step(self.queue_index)

        self.refresh_queue_ui()
        self.update_task_display()
        self.update_display()
        self.save_settings()

    def clear_queue(self):
        self.session_queue = []
        self.queue_index = 0
        self.queue_mode = False
        self.current_stage = "focus"
        self.load_current_stage_time()
        self.update_stage_label_text()
        self.update_task_display()
        self.refresh_queue_ui()
        self.update_display()
        self.save_settings()

    def toggle_queue_mode(self, state):
        requested = state == 2  # Qt.Checked == 2
        if requested and not self.session_queue:
            self.queue_mode = False
            self.queue_mode_check.blockSignals(True)
            self.queue_mode_check.setChecked(False)
            self.queue_mode_check.blockSignals(False)
            self.queue_status_label.setVisible(False)
            self.queue_progress_label.setText(self.t("queue_empty"))
            self.open_queue_tab()
            return

        self.timer.stop()
        self.is_running = False
        self.start_btn.setText(self.t("start"))
        if self.mini_widget:
            self.mini_widget.mini_play_btn.setText("▶")

        self.queue_mode = requested
        if requested:
            self.preset_key = "custom"
            self.preset_combo.blockSignals(True)
            custom_index = self.preset_combo.findData("custom")
            if custom_index >= 0:
                self.preset_combo.setCurrentIndex(custom_index)
            self.preset_combo.blockSignals(False)
            self.queue_index = 0
            self.load_queue_step(0)
        else:
            self.current_stage = "focus"
            self.load_current_stage_time()
            self.update_stage_label_text()
            self.update_task_display()

        self.refresh_queue_ui()
        self.update_display()
        self.save_settings()

    def load_queue_step(self, index):
        """Load a queue step into the timer engine."""
        if not self.session_queue:
            return
        index = max(0, min(index, len(self.session_queue) - 1))
        step = self.session_queue[index]
        kind = str(step.get("kind", "focus"))
        if kind not in ("focus", "short_break", "long_break"):
            kind = "focus"

        self.queue_index = index
        self.current_stage = kind
        minutes = int(step.get("minutes", self.focus_minutes) or self.focus_minutes)
        self.time_left = minutes * 60

        self.update_stage_label_text()
        self.update_task_display()
        self.update_queue_progress()
        self.refresh_queue_ui()

    def update_queue_progress(self):
        """Refresh the live queue progress labels on the Timer and Queue tabs."""
        if not hasattr(self, "queue_status_label"):
            return

        if not self.session_queue:
            self.queue_status_label.setVisible(False)
            self.queue_progress_label.setText(self.t("queue_empty"))
            return

        if not self.queue_mode:
            self.queue_status_label.setVisible(False)
            self.queue_progress_label.setText(self.t("queue_summary", count=len(self.session_queue)))
            return

        total = len(self.session_queue)
        if self.queue_index >= total:
            text = self.t("queue_complete")
        else:
            current = self.queue_index + 1
            if self.queue_index + 1 < total:
                next_step = self.session_queue[self.queue_index + 1]
                next_stage = self.t(str(next_step.get("kind", "focus")))
                next_mins = int(next_step.get("minutes", self.focus_minutes) or self.focus_minutes)
                text = self.t(
                    "queue_progress",
                    current=current,
                    total=total,
                    next_stage=next_stage,
                    next_mins=next_mins,
                )
            else:
                text = self.t("queue_progress_last", current=current, total=total)

        self.queue_status_label.setText(text)
        self.queue_status_label.setVisible(True)
        self.queue_progress_label.setText(text)

    # ------------------------------------------------------------------
    # Daily focus goal
    # ------------------------------------------------------------------
    def check_daily_reset(self):
        """Reset the daily counter when the calendar day changes."""
        today = date.today().isoformat()
        if self.daily_focus_date != today:
            self.daily_focus_date = today
            self.daily_focus_seconds = 0
            self.settings.setValue("daily_focus_date", today)
            self.settings.setValue("daily_focus_seconds", 0)

    def update_daily_progress(self):
        self.check_daily_reset()
        done = self.daily_focus_seconds // 60
        target = max(1, self.daily_goal_minutes)
        percent = max(0, min(100, int(round(done * 100 / target))))
        text = self.t("daily_progress", done=done, target=target, percent=percent)

        if hasattr(self, "timer_daily_label"):
            self.timer_daily_label.setText(text)
            self.stats_daily_label.setText(text)
            self.timer_daily_bar.setValue(percent)
            self.stats_daily_bar.setValue(percent)

    # ------------------------------------------------------------------
    # Session history & CSV export
    # ------------------------------------------------------------------
    def refresh_history_list(self):
        if not hasattr(self, "history_list"):
            return

        self.history_list.clear()
        if not self.task_history:
            self.history_list.addItem(self.t("no_sessions"))
            return

        for entry in reversed(self.task_history[-200:]):
            task = str(entry.get("task", "") or self.t("history_untitled"))
            duration = entry.get("duration", 0)
            raw_when = str(entry.get("completed_at", "") or "")
            try:
                when = datetime.fromisoformat(raw_when).strftime("%Y-%m-%d %H:%M")
            except (ValueError, TypeError):
                when = raw_when
            self.history_list.addItem(
                self.t("history_entry", task=task, mins=duration, when=when)
            )

    def export_sessions_csv(self):
        if not self.task_history:
            QMessageBox.information(self, self.t("export_csv"), self.t("no_sessions"))
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            self.t("csv_export_title"),
            "pomotime_sessions.csv",
            self.t("csv_filter"),
        )
        if not path:
            return

        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow([
                    self.t("csv_task"),
                    self.t("csv_duration"),
                    self.t("csv_completed_at"),
                ])
                for entry in self.task_history:
                    writer.writerow([
                        entry.get("task", "") or self.t("history_untitled"),
                        entry.get("duration", 0),
                        entry.get("completed_at", ""),
                    ])
            QMessageBox.information(self, self.t("export_csv"), self.t("csv_exported"))
        except OSError:
            QMessageBox.warning(self, self.t("export_csv"), self.t("csv_export_error"))

    def on_tab_changed(self, index):
        if index == 1:
            self.update_statistics_display()
            self.refresh_history_list()
        elif index == 2:
            self.refresh_queue_ui()
        elif index == 3:
            self.update_daily_progress()

    def pause_text(self):
        return self.t("pause")

    def play_tone(self, sound_key):
        """Play a soft notification chime using native OS audio playback."""
        sound = SOUNDS.get(sound_key)
        if not sound:
            return

        audio_file = get_audio_file(sound_key)
        if audio_file and os.path.exists(audio_file):
            try:
                if platform.system() == "Windows":
                    import winsound
                    flags = winsound.SND_FILENAME | winsound.SND_ASYNC  # type: ignore[attr-defined]
                    winsound.PlaySound(audio_file, flags)  # type: ignore[attr-defined]
                    return

                # Native system audio players on Linux/macOS.
                player = get_player_command(audio_file)
                if player:
                    subprocess.Popen(
                        player,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    return
            except Exception:
                pass

        # Fallback: a short system beep if WAV playback is unavailable.
        try:
            if platform.system() == "Windows":
                import winsound
                notes = sound.get("notes") or []
                freq = notes[0][0] if notes else sound.get("freq", 800)
                winsound.Beep(int(freq), int(sound.get("dur", 100)))  # type: ignore[attr-defined]
                return
        except Exception:
            pass

        # Final fallback to the terminal bell.
        print("\a", end="", flush=True)

    def start_repeating_alert(self):
        """Trigger a repeating alert when timer expires."""
        self.alert_repeats_left = 3
        self.play_tone("alert")
        self.alert_timer.start(900)

    def repeat_alert_sound(self):
        if self.alert_repeats_left > 0:
            self.play_tone("alert")
            self.alert_repeats_left -= 1
        else:
            self.alert_timer.stop()

    def toggle_start_pause(self):
        if self.is_running:
            self.timer.stop()
            self.is_running = False
            self.start_btn.setText(self.t("start"))
            if self.mini_widget:
                self.mini_widget.mini_play_btn.setText("▶")
            self.play_tone("click")
        else:
            # Restart a finished queue from the first block before starting.
            if self.queue_mode and self.session_queue and self.queue_index >= len(self.session_queue):
                self.queue_index = 0
                self.load_queue_step(0)
                self.update_display()
            self.timer.start(1000)
            self.is_running = True
            self.start_btn.setText(self.t("pause"))
            if self.mini_widget:
                self.mini_widget.mini_play_btn.setText("⏸")
            self.play_tone("start_focus" if self.current_stage == "focus" else "start_break")

    def reset_timer(self):
        self.is_running = False
        self.timer.stop()
        if self.queue_mode and self.session_queue and self.queue_index >= len(self.session_queue):
            # Restart a completed queue from its first block.
            self.queue_index = 0
            self.load_queue_step(0)
        else:
            self.load_current_stage_time()
        self.update_display()
        self.start_btn.setText(self.t("start"))
        if self.mini_widget:
            self.mini_widget.mini_play_btn.setText("▶")

    def load_current_stage_time(self):
        if self.queue_mode and self.session_queue:
            if self.queue_index < len(self.session_queue):
                step = self.session_queue[self.queue_index]
                kind = str(step.get("kind", "focus"))
                if kind not in ("focus", "short_break", "long_break"):
                    kind = "focus"
                self.current_stage = kind
                self.time_left = int(step.get("minutes", self.focus_minutes) or self.focus_minutes) * 60
            else:
                # A completed queue stays at 00:00 until restarted.
                self.time_left = 0
        elif self.current_stage == "focus":
            self.time_left = self.focus_minutes * 60
        elif self.current_stage == "short_break":
            self.time_left = self.short_break_minutes * 60
        else:
            self.time_left = self.long_break_minutes * 60

    def update_stage_label_text(self):
        stage_text = self.t(self.current_stage.replace("_", "_"))
        self.stage_label.setText(stage_text)
        if self.mini_widget:
            self.mini_widget.mini_stage_label.setText(stage_text)

    def advance_stage(self, completed=True):
        if self.queue_mode and self.session_queue:
            self.advance_queue_stage(completed)
            return

        if self.current_stage == "focus":
            if completed:
                self.completed_cycles += 1
                self.cycles_label.setText(self.t("cycles", count=self.completed_cycles, target=self.cycles_before_long_break))
                
                # Save completed task to history (always log the focus block).
                self.task_history.append({
                    "task": self.current_task or self.t("history_untitled"),
                    "completed_at": datetime.now().isoformat(),
                    "duration": self.focus_minutes
                })
                self.save_settings()
                self.refresh_history_list()
                self.update_daily_progress()

            # Decide on short or long break
            if self.completed_cycles > 0 and self.completed_cycles % self.cycles_before_long_break == 0:
                self.current_stage = "long_break"
                self.time_left = self.long_break_minutes * 60
            else:
                self.current_stage = "short_break"
                self.time_left = self.short_break_minutes * 60

            if completed:
                self.total_breaks_taken += 1
                self.start_repeating_alert()
                self.show_notification(self.t("session_completed"), self.t("focus_finished"))
                
                # Auto-start breaks if enabled
                if self.auto_start_breaks:
                    QTimer.singleShot(1000, self.toggle_start_pause)
        else:
            # Break finished -> back to focus
            self.current_stage = "focus"
            self.time_left = self.focus_minutes * 60
            if completed:
                self.start_repeating_alert()
                self.show_notification(self.t("session_completed"), self.t("break_finished"))
                
                # Auto-start focus if enabled
                if self.auto_start_focus:
                    QTimer.singleShot(1000, self.toggle_start_pause)

        self.update_stage_label_text()
        self.update_task_display()
        self.update_display()
        self.update_statistics_display()

    def advance_queue_stage(self, completed=True):
        """Advance to the next block in the custom session queue."""
        total = len(self.session_queue)
        if self.queue_index >= total:
            return

        step = self.session_queue[self.queue_index]
        stage = str(step.get("kind", "focus"))
        minutes = int(step.get("minutes", self.focus_minutes) or self.focus_minutes)

        if completed and stage == "focus":
            self.completed_cycles += 1
            self.cycles_label.setText(self.t("cycles", count=self.completed_cycles, target=self.cycles_before_long_break))
            self.task_history.append({
                "task": str(step.get("task", "") or "") or self.current_task or self.t("history_untitled"),
                "completed_at": datetime.now().isoformat(),
                "duration": minutes,
            })
            self.refresh_history_list()
        elif completed:
            self.total_breaks_taken += 1

        self.queue_index += 1

        if self.queue_index >= total:
            # Queue finished: keep the final step visible and announce completion.
            self.update_queue_progress()
            self.update_display()
            self.update_statistics_display()
            self.save_settings()
            if completed:
                self.start_repeating_alert()
                self.show_notification(
                    self.t("queue_complete_notification_title"),
                    self.t("queue_complete_notification_message"),
                )
            self.refresh_history_list()
            self.update_daily_progress()
            return

        self.load_queue_step(self.queue_index)
        self.update_statistics_display()

        if completed:
            self.start_repeating_alert()
            if stage == "focus":
                self.show_notification(self.t("session_completed"), self.t("focus_finished"))
            else:
                self.show_notification(self.t("session_completed"), self.t("break_finished"))

            # Auto-start policy follows the *next* block type.
            if self.current_stage == "focus":
                if self.auto_start_focus:
                    QTimer.singleShot(1000, self.toggle_start_pause)
            else:
                if self.auto_start_breaks:
                    QTimer.singleShot(1000, self.toggle_start_pause)

        self.refresh_history_list()
        self.update_daily_progress()
        self.save_settings()

    def update_timer(self):
        if self.time_left > 0:
            if self.current_stage == "focus":
                self.check_daily_reset()
                self.total_focus_seconds += 1
                self.daily_focus_seconds += 1
            self.time_left -= 1
            self.update_display()
            # Periodically update stats in background
            if self.time_left % 10 == 0:
                self.update_statistics_display()
        else:
            self.timer.stop()
            self.is_running = False
            self.start_btn.setText(self.t("start"))
            if self.mini_widget:
                self.mini_widget.mini_play_btn.setText("▶")
            self.advance_stage(completed=True)

    def update_statistics_display(self):
        focus_mins_total = self.total_focus_seconds // 60
        self.stat_focus_label.setText(self.t("stats_total_focus", mins=focus_mins_total))
        self.stat_cycles_label.setText(self.t("stats_completed_cycles", count=self.completed_cycles))
        self.stat_breaks_label.setText(self.t("stats_breaks_taken", count=self.total_breaks_taken))
        self.update_score()
        self.update_daily_progress()

    def update_display(self):
        mins = self.time_left // 60
        secs = self.time_left % 60
        time_str = f"{mins:02d}:{secs:02d}"
        self.time_label.setText(time_str)
        
        # Update mini widget if active
        if self.mini_widget:
            self.mini_widget.mini_time_label.setText(time_str)
            stage_text = self.t("focus") if self.current_stage == "focus" else (self.t("short_break") if self.current_stage == "short_break" else self.t("long_break"))
            self.mini_widget.mini_stage_label.setText(stage_text)
            self.mini_widget.mini_task_label.setText(self.task_display.text())
        
        # Also update window title with time if running
        if self.is_running:
            self.setWindowTitle(f"({time_str}) - " + self.t("app_title"))

    def setup_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        style = self.style()
        if style is not None:
            self.tray_icon.setIcon(
                style.standardIcon(QStyle.StandardPixmap.SP_MessageBoxInformation)
            )
        self.tray_icon.setToolTip(self.t("tray_tooltip"))
        
        tray_menu = QMenu()
        show_action = QAction(self.t("show_to_tray"), self)
        show_action.triggered.connect(self.show_from_tray)
        quit_action = QAction(self.t("quit"), self)
        quit_action.triggered.connect(QApplication.quit)

        tray_menu.addAction(show_action)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_icon_activated)
        self.tray_icon.show()

    def hide_to_tray(self):
        self.hide()
        self.tray_icon.showMessage(
            self.t("timer_running"),
            self.t("tray_running_message"),
            QSystemTrayIcon.MessageIcon.Information,
            3000
        )

    def show_from_tray(self):
        self.show()
        self.activateWindow()

    def tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.isVisible():
                self.hide()
            else:
                self.show_from_tray()

    def save_settings(self, notify=False):
        """Persist every setting immediately and refresh the affected UI."""
        old_focus = self.focus_minutes
        old_short_break = self.short_break_minutes
        old_long_break = self.long_break_minutes

        # Pull widget values into state *before* writing, so the saved snapshot
        # and the live labels always agree (fixes the stale cycles label).
        self.focus_minutes = self.focus_spin.value()
        self.short_break_minutes = self.break_spin.value()
        self.long_break_minutes = self.long_break_spin.value()
        self.cycles_before_long_break = self.cycles_spin.value()
        self.daily_goal_minutes = self.daily_goal_spin.value()

        # Roll the daily counter over before persisting it.
        self.check_daily_reset()

        self.settings.setValue("focus_minutes", self.focus_minutes)
        self.settings.setValue("short_break_minutes", self.short_break_minutes)
        self.settings.setValue("long_break_minutes", self.long_break_minutes)
        self.settings.setValue("cycles_before_long_break", self.cycles_before_long_break)
        self.settings.setValue("daily_goal_minutes", self.daily_goal_minutes)
        self.settings.setValue("current_theme", self.current_theme)
        self.settings.setValue("language", self.lang)
        self.settings.setValue("auto_start_breaks", self.auto_start_breaks)
        self.settings.setValue("auto_start_focus", self.auto_start_focus)
        self.settings.setValue("current_task", self.current_task)
        self.settings.setValue("completed_cycles", self.completed_cycles)
        self.settings.setValue("total_focus_seconds", self.total_focus_seconds)
        self.settings.setValue("total_breaks_taken", self.total_breaks_taken)
        self.settings.setValue("daily_focus_seconds", self.daily_focus_seconds)
        self.settings.setValue("daily_focus_date", self.daily_focus_date)
        self.settings.setValue("preset_key", self.preset_key)
        self.settings.setValue("queue_mode", self.queue_mode)
        self.settings.setValue("queue_index", self.queue_index)
        self.settings.setValue("session_queue", json.dumps(self.session_queue, ensure_ascii=False))
        
        # Save task history
        history = []
        for task in self.task_history:
            history.append({
                "task": task.get("task", ""),
                "completed_at": task.get("completed_at", ""),
                "duration": task.get("duration", 0),
            })
        self.settings.setValue("task_history", history)
        self.settings.sync()

        # Immediate UI refresh: the completed-cycles target must update as soon
        # as "Cycles Before Long Break" changes.
        self.cycles_label.setText(
            self.t("cycles", count=self.completed_cycles, target=self.cycles_before_long_break)
        )
        if not self.is_running:
            # Only reset the paused countdown when the active stage duration
            # actually changed (or the clock is already empty).
            if not self.queue_mode:
                if self.current_stage == "focus":
                    duration_changed = self.focus_minutes != old_focus
                elif self.current_stage == "short_break":
                    duration_changed = self.short_break_minutes != old_short_break
                else:
                    duration_changed = self.long_break_minutes != old_long_break
                if duration_changed or self.time_left <= 0:
                    self.load_current_stage_time()
            self.update_display()
        self.update_statistics_display()
        self.refresh_history_list()
        self.update_daily_progress()
        self.update_queue_progress()

        if notify:
            QMessageBox.information(self, self.t("settings"), self.t("settings_saved"))

    def load_settings(self):
        # Purge legacy background-sound preferences from older versions.
        self.settings.remove("bg_music_type")
        self.settings.remove("ambient_volume")
        # Load settings from QSettings
        focus = self.settings.value("focus_minutes", 25, type=int)
        break_time = self.settings.value("short_break_minutes", 5, type=int)
        long_break = self.settings.value("long_break_minutes", 20, type=int)
        cycles = self.settings.value("cycles_before_long_break", 4, type=int)
        theme = self.settings.value("current_theme", "default", type=str)
        auto_breaks = self.settings.value("auto_start_breaks", False, type=bool)
        auto_focus = self.settings.value("auto_start_focus", False, type=bool)
        task = self.settings.value("current_task", "", type=str)
        completed = self.settings.value("completed_cycles", 0, type=int)
        total_focus = self.settings.value("total_focus_seconds", 0, type=int)
        total_breaks = self.settings.value("total_breaks_taken", 0, type=int)
        daily_goal = self.settings.value("daily_goal_minutes", 120, type=int)
        daily_seconds = self.settings.value("daily_focus_seconds", 0, type=int)
        daily_date = self.settings.value("daily_focus_date", date.today().isoformat(), type=str)
        preset_key = self.settings.value("preset_key", "classic", type=str)
        queue_mode = self.settings.value("queue_mode", False, type=bool)
        queue_index = self.settings.value("queue_index", 0, type=int)
        raw_queue = self.settings.value("session_queue", "", type=str)
        
        # Apply settings
        self.focus_minutes = focus if focus else 25
        self.short_break_minutes = break_time if break_time else 5
        self.long_break_minutes = long_break if long_break else 20
        self.cycles_before_long_break = cycles if cycles else 4
        self.current_theme = theme if theme else "default"
        self.auto_start_breaks = auto_breaks if auto_breaks is not None else False
        self.auto_start_focus = auto_focus if auto_focus is not None else False
        self.current_task = task if task else ""
        self.completed_cycles = completed if completed else 0
        self.total_focus_seconds = total_focus if total_focus else 0
        self.total_breaks_taken = total_breaks if total_breaks else 0
        self.daily_goal_minutes = max(5, daily_goal if daily_goal else 120)
        self.daily_focus_seconds = daily_seconds if daily_seconds else 0
        self.daily_focus_date = daily_date if daily_date else date.today().isoformat()
        self.preset_key = preset_key if preset_key else "classic"

        # Restore the custom session queue from JSON.
        self.session_queue = []
        if raw_queue:
            try:
                parsed_queue = json.loads(raw_queue)
            except (ValueError, TypeError):
                parsed_queue = []
            if isinstance(parsed_queue, list):
                for item in parsed_queue:
                    if not isinstance(item, dict):
                        continue
                    kind = str(item.get("kind", "focus"))
                    if kind not in ("focus", "short_break", "long_break"):
                        kind = "focus"
                    try:
                        minutes = int(item.get("minutes", self.focus_minutes))
                    except (TypeError, ValueError):
                        minutes = self.focus_minutes
                    minutes = max(1, min(180, minutes))
                    self.session_queue.append({
                        "kind": kind,
                        "minutes": minutes,
                        "task": str(item.get("task", "") or ""),
                    })

        self.queue_index = max(0, queue_index if queue_index else 0)
        self.queue_mode = bool(queue_mode) and bool(self.session_queue)
        if self.queue_mode:
            # A restored queue is always represented by the Custom Queue preset.
            self.preset_key = "custom"
        
        # Load task history
        saved_history = self.settings.value("task_history", [], type=list)
        self.task_history = []
        if saved_history:
            for task_entry in saved_history:
                if isinstance(task_entry, dict):
                    self.task_history.append({
                        "task": task_entry.get("task", ""),
                        "completed_at": task_entry.get("completed_at", ""),
                        "duration": task_entry.get("duration", 0),
                    })

        # Synchronize widgets with restored state without firing user handlers.
        self.focus_spin.setValue(self.focus_minutes)
        self.break_spin.setValue(self.short_break_minutes)
        self.long_break_spin.setValue(self.long_break_minutes)
        self.cycles_spin.setValue(self.cycles_before_long_break)
        self.daily_goal_spin.setValue(self.daily_goal_minutes)

        self.theme_combo.blockSignals(True)
        theme_index = self.theme_combo.findData(self.current_theme)
        if theme_index >= 0:
            self.theme_combo.setCurrentIndex(theme_index)
        self.theme_combo.blockSignals(False)

        self.preset_combo.blockSignals(True)
        preset_index = self.preset_combo.findData(self.preset_key)
        if preset_index >= 0:
            self.preset_combo.setCurrentIndex(preset_index)
        self.preset_combo.blockSignals(False)

        self.task_input.setText(self.current_task)

        if self.queue_mode and self.session_queue:
            if self.queue_index >= len(self.session_queue):
                # The queue was completed before exit: keep it at 00:00.
                self.queue_index = len(self.session_queue)
                self.time_left = 0
                last_kind = str(self.session_queue[-1].get("kind", "focus"))
                if last_kind in ("focus", "short_break", "long_break"):
                    self.current_stage = last_kind
            else:
                self.queue_index = min(self.queue_index, len(self.session_queue) - 1)
                self.load_queue_step(self.queue_index)
        else:
            self.queue_index = 0
            self.current_stage = "focus"
            self.load_current_stage_time()

        self.queue_mode_check.blockSignals(True)
        self.queue_mode_check.setChecked(self.queue_mode)
        self.queue_mode_check.setEnabled(bool(self.session_queue))
        self.queue_mode_check.blockSignals(False)

        self.refresh_queue_ui()
        self.update_task_display()
        self.update_display()
        self.refresh_history_list()
        self.update_statistics_display()

        # Apply theme
        self.apply_theme()

    def change_theme(self, index):
        self.current_theme = self.theme_combo.itemData(index)
        self.apply_theme()

    def apply_theme(self):
        themes = {
            "default": {
                "bg": "#F1F5F9",
                "card": "#FFFFFF",
                "text": "#0F172A",
                "subtext": "#64748B",
                "accent": "#2563EB",
                "accent_hover": "#1D4ED8",
                "border": "#CBD5E1",
                "tab_bg": "#E2E8F0"
            },
            "forest": {
                "bg": "#F0FDF4",
                "card": "#FFFFFF",
                "text": "#064E3B",
                "subtext": "#047857",
                "accent": "#059669",
                "accent_hover": "#047857",
                "border": "#A7F3D0",
                "tab_bg": "#D1FAE5"
            },
            "midnight": {
                "bg": "#090D16",
                "card": "#131C2E",
                "text": "#F8FAFC",
                "subtext": "#94A3B8",
                "accent": "#6366F1",
                "accent_hover": "#4F46E5",
                "border": "#1E293B",
                "tab_bg": "#1E293B"
            },
            "sunset": {
                "bg": "#FFFBEB",
                "card": "#FFFFFF",
                "text": "#7C2D12",
                "subtext": "#9A3412",
                "accent": "#EA580C",
                "accent_hover": "#C2410C",
                "border": "#FED7AA",
                "tab_bg": "#FEF3C7"
            }
        }
        
        t = themes.get(self.current_theme, themes["default"])
        
        # Professional modern styling with clean spacing, polished shadows, and smooth controls
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {t['bg']};
            }}
            QTabWidget::pane {{
                border: 1px solid {t['border']};
                border-radius: 12px;
                background-color: {t['card']};
                padding: 10px;
            }}
            QTabBar::tab {{
                background-color: {t['tab_bg']};
                color: {t['text']};
                padding: 10px 20px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: bold;
                font-size: 13px;
                margin-right: 4px;
            }}
            QTabBar::tab:selected {{
                background-color: {t['accent']};
                color: #FFFFFF;
            }}
            QLabel {{
                color: {t['text']};
                font-family: 'Segoe UI', -apple-system, Arial, sans-serif;
            }}
            QPushButton {{
                background-color: {t['accent']};
                color: white;
                border-radius: 8px;
                font-weight: bold;
                font-size: 13px;
                padding: 8px 16px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {t['accent_hover']};
            }}
            QPushButton:pressed {{
                background-color: {t['accent']};
            }}
            QFrame#TimerCard, QFrame#StatsCard {{
                background-color: {t['card']};
                border-radius: 16px;
                border: 1px solid {t['border']};
            }}
            QComboBox, QSpinBox {{
                background-color: {t['card']};
                color: {t['text']};
                border: 1px solid {t['border']};
                border-radius: 8px;
                padding: 6px 14px;
                font-size: 13px;
                min-height: 24px;
            }}
            QComboBox:hover, QSpinBox:hover {{
                border: 1px solid {t['accent']};
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 24px;
                border-left-width: 0px;
                border-top-right-radius: 8px;
                border-bottom-right-radius: 8px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border: none;
                width: 0;
                height: 0;
                margin-right: 8px;
            }}
            /* Let Qt render native arrow via padding and style */
            QComboBox {{
                padding-right: 28px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {t['card']};
                color: {t['text']};
                border: 1px solid {t['border']};
                outline: 0px;
            }}
            QComboBox QAbstractItemView::item {{
                padding: 8px 12px;
                color: {t['text']};
                background-color: {t['card']};
            }}
            QComboBox QAbstractItemView::item:selected,
            QComboBox QAbstractItemView::item:hover {{
                background-color: {t['accent']};
                color: #FFFFFF;
            }}
            QLineEdit {{
                background-color: {t['card']};
                color: {t['text']};
                border: 1px solid {t['border']};
                border-radius: 8px;
                padding: 8px 14px;
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border: 1px solid {t['accent']};
            }}
            QCheckBox {{
                color: {t['text']};
                background: transparent;
                spacing: 8px;
                font-size: 13px;
            }}
            QCheckBox:hover {{
                color: {t['text']};
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 2px solid {t['border']};
                border-radius: 4px;
                background-color: {t['card']};
            }}
            QCheckBox::indicator:hover {{
                border: 2px solid {t['accent']};
            }}
            QCheckBox::indicator:checked {{
                background-color: {t['accent']};
                border: 2px solid {t['accent']};
                image: none;
            }}
            QProgressBar {{
                background-color: {t['tab_bg']};
                border: 1px solid {t['border']};
                border-radius: 6px;
                height: 12px;
                text-align: center;
                color: {t['text']};
            }}
            QProgressBar::chunk {{
                background-color: {t['accent']};
                border-radius: 6px;
            }}
            QListWidget {{
                background-color: {t['card']};
                color: {t['text']};
                border: 1px solid {t['border']};
                border-radius: 8px;
                padding: 4px;
                font-size: 13px;
            }}
            QListWidget::item {{
                padding: 7px 8px;
                border-radius: 6px;
                color: {t['text']};
            }}
            QListWidget::item:selected {{
                background-color: {t['accent']};
                color: #FFFFFF;
            }}
            QListWidget::item:hover {{
                background-color: {t['tab_bg']};
            }}
            QPushButton#SecondaryButton {{
                background-color: {t['tab_bg']};
                color: {t['text']};
                border: 1px solid {t['border']};
                border-radius: 8px;
                font-weight: bold;
                font-size: 12px;
                padding: 7px 12px;
            }}
            QPushButton#SecondaryButton:hover {{
                border: 1px solid {t['accent']};
                color: {t['accent']};
            }}
        """)
        
        self.time_label.setStyleSheet(f"color: {t['accent']}; font-size: 56px; font-weight: bold;")
        self.score_label.setStyleSheet(f"color: {t['accent']}; font-weight: bold; font-size: 14px;")

    def toggle_auto_break(self, state):
        """Enable/disable auto-start breaks after focus session."""
        self.auto_start_breaks = state == 2  # Qt.Checked == 2
        self.save_settings()
    
    def toggle_auto_focus(self, state):
        """Enable/disable auto-start focus after break."""
        self.auto_start_focus = state == 2  # Qt.Checked == 2
        self.save_settings()
    
    def toggle_mini_mode(self):
        if not self.is_mini_mode:
            # Enter mini mode: hide main window, show floating mini widget
            self.is_mini_mode = True
            self.hide()
            
            if not self.mini_widget:
                self.mini_widget = FloatingMiniWidget(self)
            
            # Sync display
            mins = self.time_left // 60
            secs = self.time_left % 60
            self.mini_widget.mini_time_label.setText(f"{mins:02d}:{secs:02d}")
            stage_text = self.t("focus") if self.current_stage == "focus" else (self.t("short_break") if self.current_stage == "short_break" else self.t("long_break"))
            self.mini_widget.mini_stage_label.setText(stage_text)
            self.mini_widget.mini_task_label.setText(self.task_display.text())
            self.mini_widget.mini_play_btn.setText("⏸" if self.is_running else "▶")
            
            self.mini_widget.show()
            self.mini_mode_btn.setText(self.t("normal_mode"))
        else:
            # Return to normal mode: close mini widget, restore main window
            self.is_mini_mode = False
            if self.mini_widget:
                self.mini_widget.hide()
                self.mini_widget = None
            
            self.show()
            self.activateWindow()
            self.mini_mode_btn.setText(self.t("mini_mode"))

    def show_notification(self, title, message):
        self.tray_icon.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, 5000)

    def closeEvent(self, a0):
        # Handle window close event - optionally minimize to tray.

        reply = QMessageBox.question(
            self,
            self.t("quit"),
            self.t("confirm_quit") if self.lang == "en" else self.t("confirm_quit_ar"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        if reply == QMessageBox.StandardButton.Yes:
            # Stop timers
            self.timer.stop()
            # Save stats before quitting
            self.save_settings()
            if a0 is not None:
                a0.accept()
        else:
            # Minimize to tray instead
            if a0 is not None:
                a0.ignore()
            self.hide_to_tray()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PomoTimeApp()
    window.show()
    sys.exit(app.exec())
