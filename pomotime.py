#!/usr/bin/env python3
"""
PomoTime - Professional Pomodoro Timer Application
Built with Python 3 and PyQt6.
Features: Focus/Break timers, Mini-Mode (Always on Top), Tray Notifications, 
Full English/Arabic RTL support, Background Music, Themes, and Statistics.
"""

import sys
import os
import platform
import json
import tempfile
import struct
import wave
import math
import random
from datetime import datetime, date
from PyQt6.QtCore import Qt, QTimer, QLocale, QTime, QEvent, QSize, QSettings, QDate
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStackedWidget, QComboBox, QFrame,
    QSystemTrayIcon, QMenu, QMessageBox, QSpinBox, QGridLayout,
    QTabWidget, QGraphicsDropShadowEffect, QSlider, QFileDialog,
    QLineEdit, QCheckBox, QListWidget
)
from PyQt6.QtGui import QFont, QIcon, QPalette, QColor, QAction, QFontDatabase, QPixmap, QBrush, QPainter, QPen, QPolygon

# Sound System Configuration
try:
    from PyQt6.QtMultimedia import QSoundEffect
    SOUND_SYSTEM = "qsoundeffect"
except ImportError:
    SOUND_SYSTEM = "none"

# Audio files cache
_audio_cache = {}

def generate_wav_file(freq, duration, filename):
    """Generate a WAV file with specified frequency and duration."""
    sample_rate = 44100
    samples = int(sample_rate * duration / 1000)
    
    # Generate sine wave
    wave_data = []
    for i in range(samples):
        t = float(i) / sample_rate
        value = int(32767 * math.sin(2 * math.pi * freq * t))
        wave_data.append(struct.pack('<h', value))
    
    # Write WAV file
    with wave.open(filename, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(b''.join(wave_data))

def get_audio_file(sound_key):
    """Get or generate audio file for a sound."""
    if sound_key not in _audio_cache:
        sound = SOUNDS.get(sound_key)
        if sound:
            # Create temp file
            temp_dir = tempfile.gettempdir()
            filename = os.path.join(temp_dir, f"pomotime_{sound_key}.wav")
            
            # Generate WAV file if it doesn't exist
            if not os.path.exists(filename):
                generate_wav_file(sound["freq"], sound["dur"], filename)
            
            _audio_cache[sound_key] = filename
    
    return _audio_cache.get(sound_key)

# Sound Definitions (Frequency in Hz, Duration in ms)
SOUNDS = {
    "click": {"freq": 800, "dur": 100},   # Button click
    "start_focus": {"freq": 1200, "dur": 400}, # High pitch for focus start
    "start_break": {"freq": 600, "dur": 400},  # Lower pitch for break start
    "alert": {"freq": 1500, "dur": 200},       # Alert when timer ends
    "rain": {"freq": 200, "dur": 100},         # Ambient rain
    "cafe": {"freq": 400, "dur": 100},        # Ambient cafe
    "waves": {"freq": 100, "dur": 100},       # Ocean waves
    "brown": {"freq": 50, "dur": 100},        # Brown noise
    "white": {"freq": 1000, "dur": 100},      # White noise
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
        "bg_music": "Background Sound:",
        "music_none": "None (Silent)",
        "music_rain": "Gentle Rain",
        "music_cafe": "Quiet Cafe",
        "music_waves": "Ocean Waves",
        "sound_alerts": "Sound Alerts:",
        "theme_default": "Clean Default",
        "theme_forest": "Calm Forest",
        "theme_midnight": "Midnight Focus",
        "theme_sunset": "Warm Sunset",
        "current_task_placeholder": "What are you focusing on?",
        "volume": "Volume:",
        "auto_start_breaks": "Auto-start Breaks",
        "auto_start_focus": "Auto-start Focus",
        "theme": "Theme:",
        "bg_music": "Background Sound:",
        "show_to_tray": "Show PomoTime",
        "hide_to_tray": "Hide to Tray",
        "confirm_quit": "Are you sure you want to quit PomoTime?",
        "confirm_quit_ar": "هل تريد حقاً مغادرة بوموتايم؟",
        "timer_running": "PomoTime Running",
        "break_started": "Break started!",
        "focus_started": "Focus session started!",
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
        "bg_music": "الصوت المحيط:",
        "music_none": "بدون (صامت)",
        "music_rain": "مطر لطيف",
        "music_cafe": "مقهى هادئ",
        "music_waves": "أمواج المحيط",
        "sound_alerts": "التنبيهات الصوتية:",
        "theme_default": "افتراضي نظيف",
        "theme_forest": "غابة هادئة",
        "theme_midnight": "تركيز منتصف الليل",
        "theme_sunset": "غروب دافئ",
        "current_task_placeholder": "ما الذي تركز عليه الآن؟",
        "volume": "مستوى الصوت:",
        "auto_start_breaks": "بدء الاستراحة تلقائياً",
        "auto_start_focus": "بدء التركيز تلقائياً",
        "theme": "السمة:",
        "bg_music": "الصوت المحيط:",
        "show_to_tray": "عرض بوموتايم",
        "hide_to_tray": "إخفاء إلى صينية النظام",
        "confirm_quit": "هل تريد حقاً إغلاق التطبيقات؟",
        "confirm_quit_ar": "هل تريد حقاً مغادرة بوموتايم؟",
        "timer_running": "بوموتايم - يعمل في الخلفية",
        "break_started": "بدأ وقت الاستاحة!",
        "focus_started": "بدأت جلسة التركيز!",
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

    def paintEvent(self, event):
        """Paint the circular timer with progress."""
        from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont
        from PyQt6.QtCore import Qt, QRectF
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Get theme colors
        if self.parent_app:
            theme = self.parent_app.current_theme
            themes = {
                "default": {"bg": "#F1F5F9", "card": "#FFFFFF", "text": "#0F172A", "accent": "#2563EB", "border": "#CBD5E1"},
                "forest": {"bg": "#F0FDF4", "card": "#FFFFFF", "text": "#064E3B", "accent": "#059669", "border": "#A7F3D0"},
                "midnight": {"bg": "#090D16", "card": "#131C2E", "text": "#F8FAFC", "accent": "#6366F1", "border": "#1E293B"},
                "sunset": {"bg": "#FFFBEB", "card": "#FFFFFF", "text": "#7C2D12", "accent": "#EA580C", "border": "#FED7AA"}
            }
        else:
            themes = {"default": {"bg": "#F1F5F9", "card": "#FFFFFF", "text": "#0F172A", "accent": "#2563EB", "border": "#CBD5E1"}}
        t = themes.get(theme, themes["default"]) if theme else themes["default"]
        
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
        self.resize(220, 110)
        
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
        container_layout.addLayout(btn_layout)

        layout.addWidget(self.container)

        self._old_pos = None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self._old_pos is not None:
            delta = event.globalPosition().toPoint() - self._old_pos
            new_pos = self.pos() + delta
            
            # Keep within screen boundaries
            screen_geo = self.screen().geometry()
            if new_pos.x() < screen_geo.left():
                new_pos.setX(screen_geo.left())
            if new_pos.y() < screen_geo.top():
                new_pos.setY(screen_geo.top())
            if new_pos.x() + self.width() > screen_geo.right():
                new_pos.setX(screen_geo.right() - self.width())
            if new_pos.y() + self.height() > screen_geo.bottom():
                new_pos.setY(screen_geo.bottom() - self.height())
                
            self.move(new_pos)
            self._old_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._old_pos = None


class PomoTimeApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PomoTime")
        self.setGeometry(100, 100, 550, 700)

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
        self.bg_music_type = "none"
        
        # Task tracking
        self.current_task = ""
        
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
        
        # Ambient audio
        self.ambient_sound = None
        self.ambient_volume = 0.5
        
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
        
        # Current Task Input (above the timer card, full width)
        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText(self.t("current_task_placeholder"))
        self.task_input.setMaximumWidth(380)
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
        
        stats_title = QLabel(self.t("stats"))
        stats_title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        stats_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stats_card_layout.addWidget(stats_title)
        
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
        
        stats_layout.addWidget(stats_card, 0, Qt.AlignmentFlag.AlignCenter)
        self.tabs.addTab(self.stats_tab, self.t("stats"))
        
        # Settings Tab
        self.settings_tab = QWidget()
        settings_layout = QVBoxLayout(self.settings_tab)
        settings_layout.setSpacing(15)
        
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
        
        settings_layout.addLayout(grid)
        
        # Theme & Music
        theme_layout = QHBoxLayout()
        self.theme_combo = QComboBox()
        self.theme_combo.addItem(self.t("theme_default"), "default")
        self.theme_combo.addItem(self.t("theme_forest"), "forest")
        self.theme_combo.addItem(self.t("theme_midnight"), "midnight")
        self.theme_combo.addItem(self.t("theme_sunset"), "sunset")
        self.theme_combo.currentIndexChanged.connect(self.change_theme)
        theme_layout.addWidget(QLabel(self.t("theme_label")))
        theme_layout.addWidget(self.theme_combo)
        settings_layout.addLayout(theme_layout)

        music_layout = QHBoxLayout()
        self.music_combo = QComboBox()
        self.music_combo.addItem(self.t("music_none"), "none")
        self.music_combo.addItem(self.t("music_rain"), "rain")
        self.music_combo.addItem(self.t("music_cafe"), "cafe")
        self.music_combo.addItem(self.t("music_waves"), "waves")
        self.music_combo.addItem(self.t("music_brown"), "brown")
        self.music_combo.addItem(self.t("music_white"), "white")
        self.music_combo.currentIndexChanged.connect(self.change_music)
        music_layout.addWidget(QLabel(self.t("bg_music")))
        music_layout.addWidget(self.music_combo)
        settings_layout.addLayout(music_layout)
        
        # Volume control for ambient sounds
        volume_layout = QHBoxLayout()
        volume_layout.addWidget(QLabel(self.t("volume")))
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(int(self.ambient_volume * 100))
        self.volume_slider.valueChanged.connect(self.change_volume)
        volume_layout.addWidget(self.volume_slider)
        settings_layout.addLayout(volume_layout)
        
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
        self.save_settings_btn.clicked.connect(self.save_settings)
        settings_layout.addWidget(self.save_settings_btn)
        
        self.tabs.addTab(self.settings_tab, self.t("settings"))
        
        self.main_layout.addWidget(self.tabs)

    def t(self, key, **kwargs):
        text = TRANSLATIONS[self.lang].get(key, key)
        if kwargs:
            try:
                return text.format(**kwargs)
            except KeyError:
                return text
        return text
    
    def update_current_task(self):
        """Update the current task from the input field."""
        text = self.task_input.text().strip()
        if text:
            self.current_task = text
            # Update display
            self.task_display.setText(self.current_task)
        else:
            self.task_display.setText("")
    
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
        
        self.tabs.setTabText(0, self.t("timer_tab"))
        self.tabs.setTabText(1, self.t("stats"))
        self.tabs.setTabText(2, self.t("settings"))
        
        self.focus_label_set.setText(self.t("focus_duration"))
        self.break_label_set.setText(self.t("break_duration"))
        self.long_break_label_set.setText(self.t("long_break_duration"))
        self.cycles_label_set.setText(self.t("cycles_target"))
        self.save_settings_btn.setText(self.t("save_settings"))
        self.tray_icon.setToolTip(self.t("tray_tooltip"))
        self.task_input.setPlaceholderText(self.t("current_task_placeholder"))
        self.auto_break_check.setText(self.t("auto_start_breaks"))
        self.auto_focus_check.setText(self.t("auto_start_focus"))
        self.save_settings_btn.setText(self.t("save_settings"))
        # Update theme and music combo labels
        if self.theme_combo.count() > 0:
            for i in range(self.theme_combo.count()):
                self.theme_combo.setItemText(i, self.t(self.theme_combo.itemData(i)))
        if self.music_combo.count() > 0:
            for i in range(self.music_combo.count()):
                self.music_combo.setItemText(i, self.t(self.music_combo.itemData(i)))
        
        # Update stats text
        focus_mins_total = self.total_focus_seconds // 60
        self.stat_focus_label.setText(self.t("stats_total_focus", mins=focus_mins_total))
        self.stat_cycles_label.setText(self.t("stats_completed_cycles", count=self.completed_cycles))
        self.stat_breaks_label.setText(self.t("stats_breaks_taken", count=self.total_breaks_taken))
        
        # Update score
        self.update_score()

    def update_score(self):
        # Simple productivity score calculation
        score = min(100, (self.completed_cycles * 25) + (self.total_focus_seconds // 60))
        self.score_label.setText(f"Productivity Score: {score}/100")

    def pause_text(self):
        return self.t("pause")

    def play_tone(self, sound_key):
        """Play sound using QSoundEffect or system bell."""
        sound = SOUNDS.get(sound_key)
        if not sound:
            return

        try:
            if SOUND_SYSTEM == "qsoundeffect":
                # Use QSoundEffect for better cross-platform support
                audio_file = get_audio_file(sound_key)
                if audio_file and os.path.exists(audio_file):
                    from PyQt6.QtMultimedia import QSoundEffect
                    effect = QSoundEffect(self)
                    effect.setSource(audio_file)
                    effect.setVolume(1.0)
                    effect.play()
                    return
            
            # Fallback for different platforms
            if platform.system() == "Windows":
                import winsound
                winsound.Beep(sound["freq"], sound["dur"])
            else:
                # Try system audio players on Linux/Mac
                audio_file = get_audio_file(sound_key)
                if audio_file and os.path.exists(audio_file):
                    import subprocess
                    try:
                        if platform.system() == "Linux":
                            subprocess.run(["aplay", audio_file], check=True, timeout=1)
                        elif platform.system() == "Darwin":  # macOS
                            subprocess.run(["afplay", audio_file], check=True, timeout=1)
                    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
                        # Final fallback to terminal bell
                        print("\a", end="", flush=True)
        except Exception:
            pass

    def start_repeating_alert(self):
        """Trigger a repeating alert when timer expires."""
        self.alert_repeats_left = 3
        self.play_tone("alert")
        self.alert_timer.start(600)

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
            # Stop ambient sound during pause
            if self.ambient_sound:
                self.ambient_sound.stop()
            self.play_tone("click")
        else:
            self.timer.start(1000)
            self.is_running = True
            self.start_btn.setText(self.t("pause"))
            if self.mini_widget:
                self.mini_widget.mini_play_btn.setText("⏸")
            # Start ambient sound if enabled
            if self.bg_music_type != "none":
                self.start_ambient_sound()
            self.play_tone("start_focus" if self.current_stage == "focus" else "start_break")

    def reset_timer(self):
        self.is_running = False
        self.timer.stop()
        # Stop ambient sound
        if self.ambient_sound:
            self.ambient_sound.stop()
        self.load_current_stage_time()
        self.update_display()
        self.start_btn.setText(self.t("start"))
        if self.mini_widget:
            self.mini_widget.mini_play_btn.setText("▶")

    def load_current_stage_time(self):
        if self.current_stage == "focus":
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
        if self.current_stage == "focus":
            if completed:
                self.completed_cycles += 1
                self.cycles_label.setText(self.t("cycles", count=self.completed_cycles, target=self.cycles_before_long_break))
                
                # Save completed task to history
                if self.current_task:
                    self.task_history.append({
                        "task": self.current_task,
                        "completed_at": datetime.now().isoformat(),
                        "duration": self.focus_minutes
                    })
                    self.save_settings()

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
        self.update_display()
        self.update_statistics_display()

    def update_timer(self):
        if self.time_left > 0:
            if self.current_stage == "focus":
                self.total_focus_seconds += 1
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
        
        # Also update window title with time if running
        if self.is_running:
            self.setWindowTitle(f"({time_str}) - " + self.t("app_title"))

    def setup_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_MessageBoxInformation))
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
            "PomoTime Running",
            "PomoTime is running in the background. Click tray icon to restore.",
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

    def save_settings(self):
        # Save widget settings to QSettings
        self.settings.setValue("focus_minutes", self.focus_spin.value())
        self.settings.setValue("short_break_minutes", self.break_spin.value())
        self.settings.setValue("long_break_minutes", self.long_break_spin.value())
        self.settings.setValue("cycles_before_long_break", self.cycles_spin.value())
        self.settings.setValue("current_theme", self.current_theme)
        self.settings.setValue("bg_music_type", self.bg_music_type)
        self.settings.setValue("auto_start_breaks", self.auto_start_breaks)
        self.settings.setValue("auto_start_focus", self.auto_start_focus)
        self.settings.setValue("current_task", self.current_task)
        self.settings.setValue("completed_cycles", self.completed_cycles)
        self.settings.setValue("total_focus_seconds", self.total_focus_seconds)
        self.settings.setValue("total_breaks_taken", self.total_breaks_taken)
        
        # Save task history
        history = []
        for task in self.task_history:
            history.append({
                "task": task["task"],
                "completed_at": task["completed_at"],
                "duration": task["duration"]
            })
        self.settings.setValue("task_history", history)
        
        # Save ambient volume
        self.settings.setValue("ambient_volume", self.ambient_volume)
        
        # Update state variables from UI
        self.focus_minutes = self.focus_spin.value()
        self.short_break_minutes = self.break_spin.value()
        self.long_break_minutes = self.long_break_spin.value()
        self.cycles_before_long_break = self.cycles_spin.value()
        
        if not self.is_running:
            self.load_current_stage_time()
            self.update_display()
        
        QMessageBox.information(self, self.t("settings"), "Settings saved successfully!" if self.lang == "en" else "تم حفظ الإعدادات بنجاح!")
    def load_settings(self):
        # Load settings from QSettings
        focus = self.settings.value("focus_minutes", 25, type=int)
        break_time = self.settings.value("short_break_minutes", 5, type=int)
        long_break = self.settings.value("long_break_minutes", 20, type=int)
        cycles = self.settings.value("cycles_before_long_break", 4, type=int)
        theme = self.settings.value("current_theme", "default", type=str)
        music = self.settings.value("bg_music_type", "none", type=str)
        auto_breaks = self.settings.value("auto_start_breaks", False, type=bool)
        auto_focus = self.settings.value("auto_start_focus", False, type=bool)
        task = self.settings.value("current_task", "", type=str)
        completed = self.settings.value("completed_cycles", 0, type=int)
        total_focus = self.settings.value("total_focus_seconds", 0, type=int)
        total_breaks = self.settings.value("total_breaks_taken", 0, type=int)
        volume = self.settings.value("ambient_volume", 0.5, type=float)
        
        # Apply settings
        self.focus_minutes = focus
        self.short_break_minutes = break_time
        self.long_break_minutes = long_break
        self.cycles_before_long_break = cycles
        self.current_theme = theme
        self.bg_music_type = music
        self.auto_start_breaks = auto_breaks if auto_breaks is not None else False
        self.auto_start_focus = auto_focus if auto_focus is not None else False
        self.current_task = task if task else ""
        self.completed_cycles = completed
        self.total_focus_seconds = total_focus
        self.total_breaks_taken = total_breaks
        self.ambient_volume = volume if volume is not None else 0.5
        
        # Load task history
        saved_history = self.settings.value("task_history", [], type=list)
        self.task_history = []
        if saved_history:
            for task in saved_history:
                if isinstance(task, dict):
                    self.task_history.append({
                        "task": task.get("task", ""),
                        "completed_at": task.get("completed_at", ""),
                        "duration": task.get("duration", 0)
                    })
        
        # Apply theme
        self.apply_theme()
        
    def set_volume(self, volume):
        """Set the ambient sound volume."""
        self.ambient_volume = volume
        
    def set_volume(self, volume):
        """Set the ambient sound volume."""
        self.ambient_volume = volume
        # Apply volume to any active ambient sound
        if self.ambient_sound:
            # QAudioSink or similar would go here
            pass

        # Save widget settings to QSettings
        self.settings.setValue("focus_minutes", self.focus_spin.value())
        self.settings.setValue("short_break_minutes", self.break_spin.value())
        self.settings.setValue("long_break_minutes", self.long_break_spin.value())
        self.settings.setValue("cycles_before_long_break", self.cycles_spin.value())
        self.settings.setValue("current_theme", self.current_theme)
        self.settings.setValue("bg_music_type", self.bg_music_type)
        self.settings.setValue("auto_start_breaks", self.auto_start_breaks)
        self.settings.setValue("auto_start_focus", self.auto_start_focus)
        self.settings.setValue("current_task", self.current_task)
        self.settings.setValue("completed_cycles", self.completed_cycles)
        self.settings.setValue("total_focus_seconds", self.total_focus_seconds)
        self.settings.setValue("total_breaks_taken", self.total_breaks_taken)

        # Save task history
        history = []
        for task in self.task_history:
            history.append({
                "task": task["task"],
                "completed_at": task["completed_at"],
                "duration": task["duration"]
            })
        self.settings.setValue("task_history", history)

        # Save ambient volume
        self.settings.setValue("ambient_volume", self.ambient_volume)

        # Update state variables from UI
        self.focus_minutes = self.focus_spin.value()
        self.short_break_minutes = self.break_spin.value()
        self.long_break_minutes = self.long_break_spin.value()
        self.cycles_before_long_break = self.cycles_spin.value()

        if not self.is_running:
            self.load_current_stage_time()
            self.update_display()

        QMessageBox.information(self, self.t("settings"), "Settings saved successfully!" if self.lang == "en" else "تم حفظ الإعدادات بنجاح!")

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
                selection-background-color: {t['accent']};
                selection-color: #FFFFFF;
                padding: 4px;
                border-radius: 6px;
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
            QSlider::groove:horizontal {{
                height: 6px;
                background: {t['border']};
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {t['accent']};
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }}
        """)
        
        self.time_label.setStyleSheet(f"color: {t['accent']}; font-size: 56px; font-weight: bold;")
        self.score_label.setStyleSheet(f"color: {t['accent']}; font-weight: bold; font-size: 14px;")

    def change_music(self, index):
        self.bg_music_type = self.music_combo.itemData(index)
        # In a full implementation, this would start/stop an audio player
        print(f"Background music changed to: {self.bg_music_type}")


    def change_volume(self, value):
        """Set the ambient sound volume (0-100)."""
        self.ambient_volume = value / 100.0
        if self.ambient_sound:
            # QSoundEffect doesn't have volume property directly
            pass
    
    def toggle_auto_break(self, state):
        """Enable/disable auto-start breaks after focus session."""
        self.auto_start_breaks = state == 2  # Qt.Checked == 2
        self.save_settings()
    
    def toggle_auto_focus(self, state):
        """Enable/disable auto-start focus after break."""
        self.auto_start_focus = state == 2  # Qt.Checked == 2
        self.save_settings()
    
    def start_ambient_sound(self):
        """Start playing the selected ambient sound."""
        if self.bg_music_type == "none" or not self.is_running:
            return
        # Stop any existing ambient sound
        if self.ambient_sound:
            self.ambient_sound.stop()
        
        # Generate and play ambient sound using QSoundEffect
        try:
            from PyQt6.QtMultimedia import QSoundEffect
            audio_file = get_audio_file(self.bg_music_type)
            if audio_file and os.path.exists(audio_file):
                self.ambient_sound = QSoundEffect(self)
                self.ambient_sound.setSource(audio_file)
                self.ambient_sound.setVolume(self.ambient_volume)
                self.ambient_sound.setLoopCount(QSoundEffect.LoopCount.Infinite)
                self.ambient_sound.play()
        except Exception as e:
            print(f"Could not start ambient sound: {e}")
    
    def stop_ambient_sound(self):
        """Stop the ambient sound."""
        if self.ambient_sound:
            self.ambient_sound.stop()
            self.ambient_sound = None
    
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

    def closeEvent(self, event):
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
            if self.ambient_sound:
                self.ambient_sound.stop()
            # Save stats before quitting
            self.save_settings()
            event.accept()
        else:
            # Minimize to tray instead
            event.ignore()
            self.hide_to_tray()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PomoTimeApp()
    window.show()
    sys.exit(app.exec())
