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
from PyQt6.QtCore import Qt, QTimer, QLocale, QTime, QEvent, QSize
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStackedWidget, QComboBox, QFrame,
    QSystemTrayIcon, QMenu, QMessageBox, QSpinBox, QGridLayout,
    QTabWidget, QGraphicsDropShadowEffect, QSlider, QFileDialog
)
from PyQt6.QtGui import QFont, QIcon, QPalette, QColor, QAction, QFontDatabase, QPixmap, QBrush

# Sound System Configuration
try:
    if platform.system() == "Windows":
        import winsound
        SOUND_SYSTEM = "winsound"
    else:
        # Fallback for Linux/Mac using system bell or simple beep if possible
        # For a more robust cross-platform solution without external files, 
        # we might use a simple beep via shell or just silent if not supported.
        SOUND_SYSTEM = "none" 
except ImportError:
    SOUND_SYSTEM = "none"

# Sound Definitions (Frequency in Hz, Duration in ms)
SOUNDS = {
    "click": {"freq": 800, "dur": 100},   # Button click
    "start_focus": {"freq": 1200, "dur": 400}, # High pitch for focus start
    "start_break": {"freq": 600, "dur": 400},  # Lower pitch for break start
    "alert": {"freq": 1500, "dur": 200},       # Alert when timer ends
}

# Translations Dictionary
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
        "theme_sunset": "Warm Sunset"
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
        "theme_sunset": "غروب دافئ"
    }
}

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
        
        container_layout.addWidget(self.mini_stage_label)
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
        
        # Audio setup
        self.alert_timer = QTimer(self)
        self.alert_timer.timeout.connect(self.repeat_alert_sound)
        self.alert_repeats_left = 0

        self.init_ui()
        self.setup_tray()
        self.apply_theme()

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
        
        # Timer Display Card
        timer_card = QFrame()
        timer_card.setObjectName("TimerCard")
        timer_card.setFixedSize(350, 250)
        timer_card.setStyleSheet("""
            QFrame#TimerCard {
                background-color: #FFFFFF;
                border-radius: 20px;
                border: 1px solid #E2E8F0;
            }
        """)
        card_layout = QVBoxLayout(timer_card)
        card_layout.setContentsMargins(30, 30, 30, 30)
        card_layout.setSpacing(15)
        
        self.stage_label = QLabel(self.t("focus"))
        self.stage_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stage_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        
        self.time_label = QLabel("25:00")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setFont(QFont("Arial", 48, QFont.Weight.Bold))
        self.time_label.setStyleSheet("color: #3B82F6;")
        
        self.cycles_label = QLabel(self.t("cycles", count=0, target=self.cycles_before_long_break))
        self.cycles_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        card_layout.addWidget(self.stage_label)
        card_layout.addWidget(self.time_label)
        card_layout.addWidget(self.cycles_label)
        
        timer_layout.addWidget(timer_card, 0, Qt.AlignmentFlag.AlignCenter)
        
        # Controls
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(15)
        
        self.start_btn = QPushButton(self.t("start"))
        self.start_btn.setFixedSize(100, 40)
        self.start_btn.clicked.connect(self.toggle_start_pause)
        
        self.reset_btn = QPushButton(self.t("reset"))
        self.reset_btn.setFixedSize(100, 40)
        self.reset_btn.clicked.connect(self.reset_timer)
        
        self.skip_btn = QPushButton(self.t("skip"))
        self.skip_btn.setFixedSize(100, 40)
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
        stats_card.setFixedSize(380, 280)
        stats_card.setStyleSheet("""
            QFrame#StatsCard {
                background-color: #FFFFFF;
                border-radius: 16px;
                border: 1px solid #E2E8F0;
            }
            QLabel {
                font-size: 15px;
                color: #334155;
            }
        """)
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
        self.score_label = QLabel("Productivity Score: 0/100")
        self.score_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.score_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.score_label.setStyleSheet("color: #10B981;")
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
        self.music_combo.currentIndexChanged.connect(self.change_music)
        music_layout.addWidget(QLabel(self.t("bg_music")))
        music_layout.addWidget(self.music_combo)
        settings_layout.addLayout(music_layout)
        
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
        """Play sound using winsound on Windows or terminal bell on Linux/Mac."""
        sound = SOUNDS.get(sound_key)
        if not sound:
            return
        
        freq = sound["freq"]
        dur = sound["dur"]
        
        try:
            if SOUND_SYSTEM == "winsound":
                winsound.Beep(freq, dur)
            else:
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
            self.play_tone("click")
        else:
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.update_timer)
            self.timer.start(1000)
            self.is_running = True
            self.start_btn.setText(self.t("pause"))
            if self.mini_widget:
                self.mini_widget.mini_play_btn.setText("⏸")
            self.play_tone("start_focus" if self.current_stage == "focus" else "start_break")

    def reset_timer(self):
        self.is_running = False
        if hasattr(self, 'timer'):
            self.timer.stop()
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
        else:
            # Break finished -> back to focus
            self.current_stage = "focus"
            self.time_left = self.focus_minutes * 60
            if completed:
                self.start_repeating_alert()
                self.show_notification(self.t("session_completed"), self.t("break_finished"))
        
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
        restore_action = QAction("Show PomoTime", self)
        restore_action.triggered.connect(self.show_from_tray)
        quit_action = QAction(self.t("quit"), self)
        quit_action.triggered.connect(QApplication.quit)
        
        tray_menu.addAction(restore_action)
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
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid {t['subtext']};
                margin-right: 8px;
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
        """)
        
        self.time_label.setStyleSheet(f"color: {t['accent']}; font-size: 56px; font-weight: bold;")
        self.score_label.setStyleSheet(f"color: {t['accent']}; font-weight: bold; font-size: 14px;")

    def change_music(self, index):
        self.bg_music_type = self.music_combo.itemData(index)
        # In a full implementation, this would start/stop an audio player
        print(f"Background music changed to: {self.bg_music_type}")

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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PomoTimeApp()
    window.show()
    sys.exit(app.exec())
