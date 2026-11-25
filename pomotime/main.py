#!/usr/bin/env python3
"""
PomoTime - Professional Pomodoro Timer Application
Built with Python 3 and PyQt6.

Features:
  * Focus / break timers with cycle tracking
  * Multi-block Session Queue planner
  * Productivity presets (Classic, Deep Work, Quick Sprint, Custom)
  * Mini-mode (always-on-top floating widget) and system tray
  * Bilingual English / Arabic UI with full RTL layout
  * Visual themes (default, forest, midnight, sunset)
  * Pure-Python synthesized notification sounds (no QtMultimedia)
  * Daily focus goal + session history + CSV export
  * --- Student-focused enhancements ---
      * Study subject planner (subjects + focus blocks needed per subject)
      * Strict Focus Mode (locks the app on the timer while studying)
      * Weekly study stats per subject, streak, and weekly goal
      * Unlockable achievements / badges
  * MIT License — free to use, modify, and distribute.
"""

import sys
import os
import csv
import subprocess
import platform
from datetime import datetime, date, timedelta

from PyQt6.QtCore import Qt, QTimer, QSettings, QDate
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStackedWidget, QComboBox, QFrame,
    QSystemTrayIcon, QMenu, QMessageBox, QSpinBox, QGridLayout,
    QTabWidget, QGraphicsDropShadowEffect, QFileDialog, QStyle,
    QLineEdit, QCheckBox, QListWidget, QListWidgetItem, QProgressBar,
)
from PyQt6.QtGui import QFont, QIcon, QPalette, QColor, QAction, QFontDatabase, QPixmap, QBrush, QPainter, QPen, QKeySequence

# Local package modules
from .i18n import (
    get_translation as t,
    SUPPORTED_LANGUAGES,
    DEFAULT_LANGUAGE,
    LANGUAGE_DIRECTIONS,
    LANGUAGE_NAMES,
)
from .audio import play_tone, SOUNDS
from .themes import THEMES, DEFAULT_THEME
from .storage import SettingsStore
from .queue import SessionQueue


class CircularTimerWidget(QWidget):
    """A smooth circular progress widget for the timer display."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_app = parent
        self.time_left = 1500
        self.current_stage = "focus"
        self.progress = 1.0
        self.target_progress = 1.0
        self.animation_step = 0.02
        self.setFixedSize(300, 300)

        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self.animate)
        self.anim_timer.start(30)  # ~33 FPS

    def set_time(self, seconds, stage):
        self.time_left = seconds
        self.current_stage = stage
        self.progress = 1.0
        self.target_progress = 1.0
        self.update()

    def animate(self):
        if self.progress > self.target_progress:
            self.progress = max(self.target_progress, self.progress - self.animation_step)
        elif self.progress < self.target_progress:
            self.progress = min(self.target_progress, self.progress + self.animation_step)
        self.update()

    def paintEvent(self, a0):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        theme = self.parent_app.current_theme if self.parent_app else DEFAULT_THEME
        t_colors = THEMES.get(theme, THEMES[DEFAULT_THEME])

        width = self.width()
        height = self.height()
        center_x = width / 2
        center_y = height / 2
        radius = min(width, height) * 0.35

        painter.setPen(QPen(QColor(t_colors["border"]), 12))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(
            int(center_x - radius), int(center_y - radius),
            int(radius * 2), int(radius * 2),
        )

        painter.setPen(QPen(QColor(t_colors["accent"]), 10))
        span_angle = int(360 * self.progress * 16)
        painter.drawArc(
            int(center_x - radius), int(center_y - radius),
            int(radius * 2), int(radius * 2), 90 * 16, -span_angle,
        )
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

        self.container = QFrame()
        self.container.setObjectName("MiniContainer")
        self.container.setStyleSheet("""
            QFrame#MiniContainer {
                background-color: rgba(30, 41, 59, 210);
                border-radius: 12px;
                border: 1px solid rgba(255, 255, 255, 40);
            }
            QLabel { color: #FFFFFF; font-family: 'Segoe UI', Arial, sans-serif; }
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

        container_layout.addWidget(self.mini_stage_label)

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

        # ------------------------------------------------------------------
        # Core timer state
        # ------------------------------------------------------------------
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
        self.lang = DEFAULT_LANGUAGE
        self.is_mini_mode = False
        self.mini_widget = None
        self.current_theme = DEFAULT_THEME

        self.current_task = ""

        # Session queue
        self.session_queue = SessionQueue()
        self.queue_mode = False
        self.queue_index = 0
        self.preset_key = "classic"

        # Daily focus goal
        self.daily_goal_minutes = 120
        self.daily_focus_seconds = 0
        self.daily_focus_date = date.today().isoformat()

        # Automation
        self.auto_start_breaks = False
        self.auto_start_focus = False

        # ------------------------------------------------------------------
        # Student-focused state (phase 3)
        # ------------------------------------------------------------------
        # Subjects: list of {"name": str, "blocks_needed": int, "blocks_done": int}
        self.student_subjects = []
        self.focus_mode = False  # strict focus lock while studying

        # Weekly tracking: { "YYYY-MM-DD": {"subject": minutes, ...}, ... }
        self.weekly_focus_by_subject = {}
        self.weekly_goal_hours = 10
        self.streak_days = 0
        self._last_streak_date = None

        # Achievements: { badge_id: {"unlocked": bool, "progress": int, "need": int} }
        self.achievements = {
            "first": {"unlocked": False, "progress": 0, "need": 1},
            "streak3": {"unlocked": False, "progress": 0, "need": 3},
            "streak7": {"unlocked": False, "progress": 0, "need": 7},
            "hours5": {"unlocked": False, "progress": 0, "need": 300},  # minutes
            "hours10": {"unlocked": False, "progress": 0, "need": 600},  # minutes
        }

        # ------------------------------------------------------------------
        # Timers & audio
        # ------------------------------------------------------------------
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)

        self.alert_timer = QTimer(self)
        self.alert_timer.timeout.connect(self.repeat_alert_sound)
        self.alert_repeats_left = 0

        # Persistent storage
        self.store = SettingsStore()
        self.task_history = []

        self.init_ui()
        self.setup_tray()
        self.apply_theme()
        self.load_settings()

        self.setup_keyboard_shortcuts()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)

        # Top Bar
        top_bar_layout = QHBoxLayout()

        self.lang_combo = QComboBox()
        for code in SUPPORTED_LANGUAGES:
            self.lang_combo.addItem(LANGUAGE_NAMES[code], code)
        self.lang_combo.setCurrentIndex(
            SUPPORTED_LANGUAGES.index(self.lang) if self.lang in SUPPORTED_LANGUAGES else 0
        )
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

        # Current Task Input
        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText(self.t("current_task_placeholder"))
        self.task_input.setFixedWidth(360)
        self.task_input.textChanged.connect(self.update_current_task)
        timer_layout.addWidget(self.task_input, 0, Qt.AlignmentFlag.AlignCenter)

        # Focus Mode toggle (student feature)
        focus_mode_row = QHBoxLayout()
        focus_mode_row.setSpacing(8)
        self.focus_mode_label = QLabel(self.t("student_focus_mode"))
        self.focus_mode_label.setWordWrap(True)
        self.focus_mode_btn = QPushButton(self.t("student_focus_enable"))
        self.focus_mode_btn.setObjectName("SecondaryButton")
        self.focus_mode_btn.clicked.connect(self.toggle_focus_mode)
        focus_mode_row.addWidget(self.focus_mode_label)
        focus_mode_row.addStretch()
        focus_mode_row.addWidget(self.focus_mode_btn)
        timer_layout.addLayout(focus_mode_row)

        # Timer Display Card
        timer_card = QFrame()
        timer_card.setObjectName("TimerCard")
        timer_card.setFixedSize(380, 320)
        timer_card.setStyleSheet("")

        card_layout = QVBoxLayout(timer_card)
        card_layout.setContentsMargins(24, 20, 24, 20)
        card_layout.setSpacing(6)

        self.stage_label = QLabel(self.t("focus"))
        self.stage_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stage_label.setFont(QFont("Arial", 13, QFont.Weight.Bold))

        self.circular_timer = CircularTimerWidget(self)
        self.circular_timer.setFixedSize(230, 230)

        self.time_label = QLabel("25:00")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setFont(QFont("Arial", 40, QFont.Weight.Bold))
        self.time_label.setStyleSheet("")

        ring_container = QWidget()
        ring_container.setFixedSize(230, 230)
        self.circular_timer.setParent(ring_container)
        self.circular_timer.move(0, 0)
        self.time_label.setParent(ring_container)
        self.time_label.setGeometry(0, 0, 230, 230)

        self.cycles_label = QLabel(self.t("cycles", count=0, target=self.cycles_before_long_break))
        self.cycles_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cycles_label.setFont(QFont("Arial", 10))

        card_layout.addWidget(self.stage_label, 0, Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(ring_container, 0, Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(self.cycles_label, 0, Qt.AlignmentFlag.AlignCenter)

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

        # Live queue progress
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

        # Daily goal progress on Timer tab
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

        self.score_label = QLabel(self.t("productivity_score", score=0))
        self.score_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.score_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        stats_card_layout.addWidget(self.score_label)

        self.stats_daily_label = QLabel("")
        self.stats_daily_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stats_card_layout.addWidget(self.stats_daily_label)

        self.stats_daily_bar = QProgressBar()
        self.stats_daily_bar.setRange(0, 100)
        self.stats_daily_bar.setValue(0)
        self.stats_daily_bar.setTextVisible(False)
        self.stats_daily_bar.setFixedHeight(12)
        stats_card_layout.addWidget(self.stats_daily_bar)

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

        # Session Queue Tab
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

        # ---- NEW: Student Subjects Tab ----
        self.student_tab = QWidget()
        student_layout = QVBoxLayout(self.student_tab)
        student_layout.setSpacing(12)
        student_layout.setContentsMargins(16, 16, 16, 16)

        self.student_title = QLabel(self.t("student_title"))
        self.student_title.setFont(QFont("Arial", 15, QFont.Weight.Bold))
        self.student_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        student_layout.addWidget(self.student_title)

        self.student_description = QLabel(self.t("student_description"))
        self.student_description.setWordWrap(True)
        self.student_description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        student_layout.addWidget(self.student_description)

        add_subject_row = QHBoxLayout()
        add_subject_row.setSpacing(8)
        self.student_subject_edit = QLineEdit()
        self.student_subject_edit.setPlaceholderText(self.t("student_subject_placeholder"))
        self.student_blocks_spin = QSpinBox()
        self.student_blocks_spin.setRange(1, 50)
        self.student_blocks_spin.setValue(4)
        self.student_blocks_spin.setSuffix(" " + self.t("student_blocks"))
        self.student_add_btn = QPushButton(self.t("student_add_subject"))
        self.student_add_btn.clicked.connect(self.add_student_subject)
        add_subject_row.addWidget(self.student_subject_edit, 1)
        add_subject_row.addWidget(self.student_blocks_spin)
        add_subject_row.addWidget(self.student_add_btn)
        student_layout.addLayout(add_subject_row)

        self.student_subjects_label = QLabel(self.t("student_subjects"))
        self.student_subjects_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        student_layout.addWidget(self.student_subjects_label)

        self.student_list = QListWidget()
        self.student_list.setMinimumHeight(200)
        student_layout.addWidget(self.student_list, 1)

        student_btn_row = QHBoxLayout()
        student_btn_row.setSpacing(8)
        self.student_delete_btn = QPushButton(self.t("student_delete_subject"))
        self.student_delete_btn.setObjectName("SecondaryButton")
        self.student_delete_btn.clicked.connect(self.delete_student_subject)
        self.student_mark_done_btn = QPushButton(self.t("student_mark_done"))
        self.student_mark_done_btn.setObjectName("SecondaryButton")
        self.student_mark_done_btn.clicked.connect(self.mark_student_subject_done)
        self.student_mark_pending_btn = QPushButton(self.t("student_mark_pending"))
        self.student_mark_pending_btn.setObjectName("SecondaryButton")
        self.student_mark_pending_btn.clicked.connect(self.mark_student_subject_pending)
        student_btn_row.addWidget(self.student_delete_btn)
        student_btn_row.addWidget(self.student_mark_done_btn)
        student_btn_row.addWidget(self.student_mark_pending_btn)
        student_layout.addLayout(student_btn_row)

        self.tabs.addTab(self.student_tab, self.t("student_tab"))

        # ---- NEW: Weekly Stats Tab ----
        self.weekly_tab = QWidget()
        weekly_layout = QVBoxLayout(self.weekly_tab)
        weekly_layout.setSpacing(12)
        weekly_layout.setContentsMargins(16, 16, 16, 16)

        self.weekly_title = QLabel(self.t("student_weekly_title"))
        self.weekly_title.setFont(QFont("Arial", 15, QFont.Weight.Bold))
        self.weekly_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        weekly_layout.addWidget(self.weekly_title)

        self.weekly_description = QLabel(self.t("student_weekly_description"))
        self.weekly_description.setWordWrap(True)
        self.weekly_description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        weekly_layout.addWidget(self.weekly_description)

        weekly_goal_row = QHBoxLayout()
        weekly_goal_row.setSpacing(8)
        self.weekly_goal_label = QLabel(self.t("student_weekly_goal"))
        self.weekly_goal_spin = QSpinBox()
        self.weekly_goal_spin.setRange(1, 168)
        self.weekly_goal_spin.setValue(self.weekly_goal_hours)
        self.weekly_goal_spin.setSuffix(" " + self.t("student_blocks"))
        self.weekly_goal_spin.valueChanged.connect(self.set_weekly_goal)
        weekly_goal_row.addWidget(self.weekly_goal_label)
        weekly_goal_row.addStretch()
        weekly_goal_row.addWidget(self.weekly_goal_spin)
        weekly_layout.addLayout(weekly_goal_row)

        self.weekly_progress_label = QLabel("")
        self.weekly_progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.weekly_progress_label.setWordWrap(True)
        self.weekly_progress_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        weekly_layout.addWidget(self.weekly_progress_label)

        self.weekly_bar = QProgressBar()
        self.weekly_bar.setRange(0, 100)
        self.weekly_bar.setValue(0)
        self.weekly_bar.setTextVisible(False)
        self.weekly_bar.setFixedHeight(12)
        weekly_layout.addWidget(self.weekly_bar)

        self.streak_label = QLabel("")
        self.streak_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.streak_label.setFont(QFont("Arial", 11))
        weekly_layout.addWidget(self.streak_label)

        self.weekly_list = QListWidget()
        self.weekly_list.setMinimumHeight(180)
        weekly_layout.addWidget(self.weekly_list, 1)

        self.weekly_export_btn = QPushButton(self.t("student_export_csv"))
        self.weekly_export_btn.setObjectName("SecondaryButton")
        self.weekly_export_btn.clicked.connect(self.export_weekly_csv)
        weekly_layout.addWidget(self.weekly_export_btn)

        self.tabs.addTab(self.weekly_tab, self.t("student_weekly_tab"))

        # ---- NEW: Achievements Tab ----
        self.badges_tab = QWidget()
        badges_layout = QVBoxLayout(self.badges_tab)
        badges_layout.setSpacing(12)
        badges_layout.setContentsMargins(16, 16, 16, 16)

        self.badges_title = QLabel(self.t("student_badge_title"))
        self.badges_title.setFont(QFont("Arial", 15, QFont.Weight.Bold))
        self.badges_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badges_layout.addWidget(self.badges_title)

        self.badges_list = QListWidget()
        self.badges_list.setMinimumHeight(220)
        badges_layout.addWidget(self.badges_list, 1)

        self.tabs.addTab(self.badges_tab, self.t("student_badge_title"))

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
        return t(key, lang=self.lang, **kwargs)

    # ------------------------------------------------------------------
    # Translation / language
    # ------------------------------------------------------------------
    def setup_keyboard_shortcuts(self):
        self.shortcut_start_pause = QAction(self.t("start"), self)
        self.shortcut_start_pause.setShortcut(QKeySequence(Qt.Key.Key_Space))
        self.shortcut_start_pause.triggered.connect(self.toggle_start_pause)

        self.shortcut_reset = QAction(self.t("reset"), self)
        self.shortcut_reset.setShortcut(QKeySequence(Qt.Key.Key_R))
        self.shortcut_reset.triggered.connect(self.reset_timer)

        self.shortcut_skip = QAction(self.t("skip"), self)
        self.shortcut_skip.setShortcut(QKeySequence(Qt.Key.Key_S))
        self.shortcut_skip.triggered.connect(lambda: self.advance_stage(completed=False))

        self.shortcut_mini = QAction(self.t("mini_mode"), self)
        self.shortcut_mini.setShortcut(QKeySequence(Qt.Key.Key_M))
        self.shortcut_mini.triggered.connect(self.toggle_mini_mode)

    def change_language(self, index):
        self.lang = self.lang_combo.itemData(index)
        direction = (
            Qt.LayoutDirection.RightToLeft
            if self.lang == "ar"
            else Qt.LayoutDirection.LeftToRight
        )
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
        self.cycles_label.setText(
            self.t("cycles", count=self.completed_cycles, target=self.cycles_before_long_break)
        )

        start_button_text = self.t("pause") if self.is_running else self.t("start")
        self.start_btn.setText(start_button_text)
        if self.mini_widget:
            self.mini_widget.mini_play_btn.setText("⏸" if self.is_running else "▶")

        self.reset_btn.setText(self.t("reset"))
        self.skip_btn.setText(self.t("skip"))
        self.manage_queue_btn.setText(self.t("queue_manage"))
        self.focus_mode_btn.setText(
            self.t("student_focus_disable") if self.focus_mode else self.t("student_focus_enable")
        )

        self.tabs.setTabText(0, self.t("timer_tab"))
        self.tabs.setTabText(1, self.t("stats"))
        self.tabs.setTabText(2, self.t("queue_tab"))
        self.tabs.setTabText(3, self.t("student_tab"))
        self.tabs.setTabText(4, self.t("student_weekly_tab"))
        self.tabs.setTabText(5, self.t("student_badge_title"))
        self.tabs.setTabText(6, self.t("settings"))

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

        preset_keys = ["classic", "deep", "sprint", "custom"]
        for i in range(self.preset_combo.count()):
            key = preset_keys[i] if i < len(preset_keys) else ""
            if key:
                self.preset_combo.setItemText(i, self.t(f"preset_{key}"))

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
            self.queue_kind_combo.setItemText(i, self.t(kind))
        self.refresh_queue_ui()

        self.student_title.setText(self.t("student_title"))
        self.student_description.setText(self.t("student_description"))
        self.student_subject_edit.setPlaceholderText(self.t("student_subject_placeholder"))
        self.student_blocks_spin.setSuffix(" " + self.t("student_blocks"))
        self.student_add_btn.setText(self.t("student_add_subject"))
        self.student_subjects_label.setText(self.t("student_subjects"))
        self.student_delete_btn.setText(self.t("student_delete_subject"))
        self.student_mark_done_btn.setText(self.t("student_mark_done"))
        self.student_mark_pending_btn.setText(self.t("student_mark_pending"))
        self.focus_mode_label.setText(self.t("student_focus_mode"))
        self.refresh_student_ui()

        self.weekly_title.setText(self.t("student_weekly_title"))
        self.weekly_description.setText(self.t("student_weekly_description"))
        self.weekly_goal_label.setText(self.t("student_weekly_goal"))
        self.weekly_progress_label.setText(
            self.t("student_weekly_progress", done=self.weekly_done_hours(), target=self.weekly_goal_hours, percent=self.weekly_percent())
        )
        self.weekly_export_btn.setText(self.t("student_export_csv"))
        self.refresh_weekly_ui()

        self.badges_title.setText(self.t("student_badge_title"))
        self.refresh_badges_ui()

        self.recent_sessions_label.setText(self.t("recent_sessions"))
        self.export_csv_btn.setText(self.t("export_csv"))
        self.refresh_history_list()

        for i in range(self.theme_combo.count()):
            theme_key = f"theme_{self.theme_combo.itemData(i)}"
            self.theme_combo.setItemText(i, self.t(theme_key))

        self.update_statistics_display()

    # ------------------------------------------------------------------
    # Task / display helpers
    # ------------------------------------------------------------------
    def update_current_task(self):
        self.current_task = self.task_input.text().strip()
        self.update_task_display()

    def update_task_display(self):
        text = ""
        if self.queue_mode and 0 <= self.queue_index < len(self.session_queue):
            step = self.session_queue.current_block()
            if step:
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

    def update_stage_label_text(self):
        stage_text = self.t(self.current_stage)
        self.stage_label.setText(stage_text)
        if self.mini_widget:
            self.mini_widget.mini_stage_label.setText(stage_text)

    def load_current_stage_time(self):
        if self.queue_mode and self.session_queue.blocks:
            if self.queue_index < len(self.session_queue):
                step = self.session_queue.current_block()
                kind = str(step.get("kind", "focus"))
                if kind not in ("focus", "short_break", "long_break"):
                    kind = "focus"
                self.current_stage = kind
                self.time_left = int(step.get("minutes", self.focus_minutes) or self.focus_minutes) * 60
            else:
                self.time_left = 0
        elif self.current_stage == "focus":
            self.time_left = self.focus_minutes * 60
        elif self.current_stage == "short_break":
            self.time_left = self.short_break_minutes * 60
        else:
            self.time_left = self.long_break_minutes * 60

    def update_display(self):
        mins = self.time_left // 60
        secs = self.time_left % 60
        time_str = f"{mins:02d}:{secs:02d}"
        self.time_label.setText(time_str)

        if self.mini_widget:
            self.mini_widget.mini_time_label.setText(time_str)
            stage_text = (
                self.t("focus") if self.current_stage == "focus"
                else (self.t("short_break") if self.current_stage == "short_break" else self.t("long_break"))
            )
            self.mini_widget.mini_stage_label.setText(stage_text)
            self.mini_widget.mini_task_label.setText(self.task_display.text())

        if self.is_running:
            self.setWindowTitle(f"({time_str}) - " + self.t("app_title"))

    # ------------------------------------------------------------------
    # Timer engine
    # ------------------------------------------------------------------
    def toggle_start_pause(self):
        if self.is_running:
            self.timer.stop()
            self.is_running = False
            self.start_btn.setText(self.t("start"))
            if self.mini_widget:
                self.mini_widget.mini_play_btn.setText("▶")
            play_tone("click")
        else:
            if self.queue_mode and self.session_queue.blocks and self.session_queue.is_complete:
                self.session_queue.restart()
                self.queue_index = self.session_queue.index
                self.update_display()
            self.timer.start(1000)
            self.is_running = True
            self.start_btn.setText(self.t("pause"))
            if self.mini_widget:
                self.mini_widget.mini_play_btn.setText("⏸")
            play_tone("start_focus" if self.current_stage == "focus" else "start_break")

    def reset_timer(self):
        self.is_running = False
        self.timer.stop()
        if self.queue_mode and self.session_queue.blocks and self.session_queue.is_complete:
            self.session_queue.restart()
            self.queue_index = self.session_queue.index
            self.load_queue_step(self.queue_index)
        else:
            self.load_current_stage_time()
        self.update_display()
        self.start_btn.setText(self.t("start"))
        if self.mini_widget:
            self.mini_widget.mini_play_btn.setText("▶")

    def advance_stage(self, completed=True):
        if self.queue_mode and self.session_queue.blocks:
            self.advance_queue_stage(completed)
            return

        if self.current_stage == "focus":
            if completed:
                self.completed_cycles += 1
                self.cycles_label.setText(
                    self.t("cycles", count=self.completed_cycles, target=self.cycles_before_long_break)
                )

                self.task_history.append({
                    "task": self.current_task or self.t("history_untitled"),
                    "completed_at": datetime.now().isoformat(),
                    "duration": self.focus_minutes,
                })
                self._record_focus_minutes(self.focus_minutes)
                self.save_settings()
                self.refresh_history_list()
                self.update_daily_progress()

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
                if self.auto_start_breaks:
                    QTimer.singleShot(1000, self.toggle_start_pause)
        else:
            self.current_stage = "focus"
            self.time_left = self.focus_minutes * 60
            if completed:
                self.start_repeating_alert()
                self.show_notification(self.t("session_completed"), self.t("break_finished"))
                if self.auto_start_focus:
                    QTimer.singleShot(1000, self.toggle_start_pause)

        self.update_stage_label_text()
        self.update_task_display()
        self.update_display()
        self.update_statistics_display()

    def advance_queue_stage(self, completed=True):
        if self.session_queue.is_empty or self.session_queue.is_complete:
            return

        step = self.session_queue.current_block()
        stage = str(step.get("kind", "focus"))
        minutes = int(step.get("minutes", self.focus_minutes) or self.focus_minutes)

        if completed and stage == "focus":
            self.completed_cycles += 1
            self.cycles_label.setText(
                self.t("cycles", count=self.completed_cycles, target=self.cycles_before_long_break)
            )
            self.task_history.append({
                "task": str(step.get("task", "") or "") or self.current_task or self.t("history_untitled"),
                "completed_at": datetime.now().isoformat(),
                "duration": minutes,
            })
            self._record_focus_minutes(minutes)
        elif completed:
            self.total_breaks_taken += 1

        self.session_queue.advance()
        self.queue_index = self.session_queue.index

        if self.session_queue.is_complete:
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
            if self.time_left % 10 == 0:
                self.update_statistics_display()
        else:
            self.timer.stop()
            self.is_running = False
            self.start_btn.setText(self.t("start"))
            if self.mini_widget:
                self.mini_widget.mini_play_btn.setText("▶")
            self.advance_stage(completed=True)

    # ------------------------------------------------------------------
    # Presets
    # ------------------------------------------------------------------
    def on_preset_changed(self, index):
        key = self.preset_combo.itemData(index)
        if isinstance(key, str):
            self.apply_preset(key)

    def apply_preset(self, key):
        self.timer.stop()
        self.is_running = False
        self.start_btn.setText(self.t("start"))
        if self.mini_widget:
            self.mini_widget.mini_play_btn.setText("▶")

        if key == "custom":
            self.preset_key = "custom"
            if not self.session_queue.blocks:
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
        if not hasattr(self, "queue_list"):
            return
        self.queue_list.blockSignals(True)
        self.queue_list.clear()
        if self.session_queue.is_empty:
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
        self.queue_mode_check.setEnabled(not self.session_queue.is_empty)
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
        self.session_queue.add_block(kind, self.queue_minutes_spin.value(), self.queue_task_edit.text().strip())
        self.queue_task_edit.clear()
        self._finish_queue_edit(len(self.session_queue) - 1)

    def quick_add_cycle(self):
        self.session_queue.add_quick_cycle(self.focus_spin.value(), self.long_break_spin.value())
        self._finish_queue_edit(len(self.session_queue) - 1)

    def quick_add_extra_cycle(self):
        self.session_queue.add_extra_cycle(self.focus_spin.value(), self.break_spin.value())
        self._finish_queue_edit(len(self.session_queue) - 1)

    def _finish_queue_edit(self, select):
        if self.preset_key == "custom" and not self.queue_mode:
            self.queue_mode = True
            self.queue_index = 0
            self.load_queue_step(0)
        self.refresh_queue_ui(select=select)
        self.update_display()
        self.save_settings()

    def move_queue_up(self):
        row = self.queue_list.currentRow()
        if self.session_queue.move_up(row):
            self._after_queue_reorder(row - 1)

    def move_queue_down(self):
        row = self.queue_list.currentRow()
        if self.session_queue.move_down(row):
            self._after_queue_reorder(row + 1)

    def _after_queue_reorder(self, row):
        if self.queue_mode and not self.session_queue.is_empty:
            self.queue_index = min(self.queue_index, len(self.session_queue) - 1)
            self.load_queue_step(self.queue_index)
        self.refresh_queue_ui(select=row)
        self.update_display()
        self.save_settings()

    def delete_queue_block(self):
        row = self.queue_list.currentRow()
        if not self.session_queue.delete_block(row):
            return
        if self.session_queue.is_empty:
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
        self.session_queue.clear()
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
        requested = state == 2
        if requested and self.session_queue.is_empty:
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
        step = self.session_queue.load_step(index)
        if step is None:
            return
        kind = str(step.get("kind", "focus"))
        if kind not in ("focus", "short_break", "long_break"):
            kind = "focus"
        self.queue_index = self.session_queue.index
        self.current_stage = kind
        minutes = int(step.get("minutes", self.focus_minutes) or self.focus_minutes)
        self.time_left = minutes * 60
        self.update_stage_label_text()
        self.update_task_display()
        self.update_queue_progress()
        self.refresh_queue_ui()

    def update_queue_progress(self):
        if not hasattr(self, "queue_status_label"):
            return

        if self.session_queue.is_empty:
            self.queue_status_label.setVisible(False)
            self.queue_progress_label.setText(self.t("queue_empty"))
            return

        if not self.queue_mode:
            self.queue_status_label.setVisible(False)
            self.queue_progress_label.setText(self.t("queue_summary", count=len(self.session_queue)))
            return

        total = len(self.session_queue)
        if self.session_queue.is_complete:
            text = self.t("queue_complete")
        else:
            current = self.queue_index + 1
            if current < total:
                next_step = self.session_queue.next_block()
                next_stage = self.t(str(next_step.get("kind", "focus")))
                next_mins = int(next_step.get("minutes", self.focus_minutes) or self.focus_minutes)
                text = self.t(
                    "queue_progress",
                    current=current, total=total,
                    next_stage=next_stage, next_mins=next_mins,
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
        today = date.today().isoformat()
        if self.daily_focus_date != today:
            self.daily_focus_date = today
            self.daily_focus_seconds = 0
            self.store.daily_focus_date = today
            self.store.daily_focus_seconds = 0

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
    # ---- Student-focused features ----
    # ------------------------------------------------------------------
    def toggle_focus_mode(self):
        """Lock/unlock the app on the timer screen while studying."""
        self.focus_mode = not self.focus_mode
        self.focus_mode_btn.setText(
            self.t("student_focus_disable") if self.focus_mode else self.t("student_focus_enable")
        )
        self.save_settings()

        if self.focus_mode:
            self.tabs.setTabEnabled(0, True)
            for i in range(1, self.tabs.count()):
                self.tabs.setTabEnabled(i, False)
            self.tabs.setCurrentIndex(0)
            QMessageBox.information(
                self, self.t("student_focus_mode"),
                self.t("student_focus_mode_description"),
            )
        else:
            for i in range(1, self.tabs.count()):
                self.tabs.setTabEnabled(i, True)

    # ---- Student subjects ----
    def refresh_student_ui(self):
        if not hasattr(self, "student_list"):
            return
        self.student_list.blockSignals(True)
        self.student_list.clear()
        for subj in self.student_subjects:
            name = subj.get("name", "")
            needed = subj.get("blocks_needed", 0)
            done = subj.get("blocks_done", 0)
            status = self.t("student_completed") if done >= needed else self.t("student_pending")
            item_text = f"{name} — {done}/{needed} {self.t('student_blocks')} · {status}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, subj)
            self.student_list.addItem(item)
        self.student_list.blockSignals(False)

    def add_student_subject(self):
        name = self.student_subject_edit.text().strip()
        if not name:
            QMessageBox.information(self, self.t("student_title"), "Please enter a subject name.")
            return
        blocks = self.student_blocks_spin.value()
        self.student_subjects.append({
            "name": name,
            "blocks_needed": blocks,
            "blocks_done": 0,
        })
        self.student_subject_edit.clear()
        self.refresh_student_ui()
        self.save_settings()

    def delete_student_subject(self):
        row = self.student_list.currentRow()
        if row < 0 or row >= len(self.student_subjects):
            return
        del self.student_subjects[row]
        self.refresh_student_ui()
        self.save_settings()

    def _set_subject_done(self, row, done):
        if row < 0 or row >= len(self.student_subjects):
            return
        self.student_subjects[row]["blocks_done"] = done
        self.refresh_student_ui()
        self.save_settings()

    def mark_student_subject_done(self):
        row = self.student_list.currentRow()
        if row < 0:
            return
        self._set_subject_done(row, self.student_subjects[row]["blocks_needed"])

    def mark_student_subject_pending(self):
        row = self.student_list.currentRow()
        if row < 0:
            return
        self._set_subject_done(row, 0)

    def _record_focus_minutes(self, minutes):
        """Record focus minutes for weekly tracking + streak + achievements."""
        today = date.today().isoformat()
        # Weekly tracking (attribute to current global task or 'General')
        subject_name = self.current_task or "General"
        self.weekly_focus_by_subject.setdefault(today, {})
        self.weekly_focus_by_subject[today][subject_name] = (
            self.weekly_focus_by_subject[today].get(subject_name, 0) + minutes
        )

        # Streak logic: count consecutive days with any focus
        today_date = date.today()
        if self._last_streak_date is None:
            self.streak_days = 1
        else:
            delta = (today_date - self._last_streak_date).days
            if delta == 1:
                self.streak_days += 1
            elif delta > 1:
                self.streak_days = 1
        self._last_streak_date = today_date

        # Achievements
        self._check_achievements()

        self.save_settings()
        self.refresh_weekly_ui()
        self.refresh_badges_ui()

    def _check_achievements(self):
        total_focus_minutes = self.total_focus_seconds // 60
        weekly_minutes_this_week = self._weekly_total_minutes()

        checks = {
            "first": (self.completed_cycles >= 1, 1),
            "streak3": (self.streak_days >= 3, 3),
            "streak7": (self.streak_days >= 7, 7),
            "hours5": (total_focus_minutes >= 300, 300),
            "hours10": (weekly_minutes_this_week >= 600, 600),
        }
        for badge_id, (condition, need) in checks.items():
            ach = self.achievements[badge_id]
            if not ach["unlocked"] and condition:
                ach["unlocked"] = True
            ach["progress"] = min(need, {
                "first": self.completed_cycles,
                "streak3": self.streak_days,
                "streak7": self.streak_days,
                "hours5": total_focus_minutes,
                "hours10": weekly_minutes_this_week,
            }[badge_id])

    # ---- Weekly stats ----
    def _week_start(self, d: date) -> date:
        return d - timedelta(days=d.weekday())  # Monday

    def _weekly_total_minutes(self) -> int:
        start = self._week_start(date.today())
        total = 0
        for day_str, subjects in self.weekly_focus_by_subject.items():
            try:
                day = date.fromisoformat(day_str)
            except ValueError:
                continue
            if self._week_start(day) == start:
                total += sum(subjects.values())
        return total

    def weekly_done_hours(self) -> int:
        return self._weekly_total_minutes() // 60

    def weekly_percent(self) -> int:
        target = max(1, self.weekly_goal_hours * 60)
        return max(0, min(100, int(round(self._weekly_total_minutes() * 100 / target))))

    def set_weekly_goal(self, value):
        self.weekly_goal_hours = max(1, value)
        self.save_settings()
        self.refresh_weekly_ui()

    def refresh_weekly_ui(self):
        if not hasattr(self, "weekly_list"):
            return
        self.weekly_progress_label.setText(
            self.t("student_weekly_progress",
                   done=self.weekly_done_hours(), target=self.weekly_goal_hours, percent=self.weekly_percent())
        )
        self.weekly_bar.setValue(self.weekly_percent())
        self.streak_label.setText(self.t("student_streak", days=self.streak_days))

        self.weekly_list.blockSignals(True)
        self.weekly_list.clear()
        start = self._week_start(date.today())
        found = False
        for day_str in sorted(self.weekly_focus_by_subject.keys()):
            try:
                day = date.fromisoformat(day_str)
            except ValueError:
                continue
            if self._week_start(day) != start:
                continue
            found = True
            subjects = self.weekly_focus_by_subject[day_str]
            line = f"{day.strftime('%a %d/%m')}: "
            line += " • ".join(f"{subj} {mins//60}h{mins%60:02d}m" for subj, mins in subjects.items())
            self.weekly_list.addItem(line)
        if not found:
            self.weekly_list.addItem(self.t("student_no_weekly_data"))
        self.weekly_list.blockSignals(False)

    def export_weekly_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self, self.t("student_export_csv"), "pomotime_weekly.csv",
            self.t("csv_filter"),
        )
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(["Date", "Subject", "Minutes"])
                for day_str, subjects in sorted(self.weekly_focus_by_subject.items()):
                    for subj, mins in subjects.items():
                        writer.writerow([day_str, subj, mins])
            QMessageBox.information(self, self.t("student_export_csv"), self.t("student_csv_exported"))
        except OSError:
            QMessageBox.warning(self, self.t("student_export_csv"), self.t("csv_export_error"))

    # ---- Achievements ----
    def refresh_badges_ui(self):
        if not hasattr(self, "badges_list"):
            return
        self.badges_list.blockSignals(True)
        self.badges_list.clear()
        badge_defs = {
            "first": self.t("student_badge_first"),
            "streak3": self.t("student_badge_streak3"),
            "streak7": self.t("student_badge_streak7"),
            "hours5": self.t("student_badge_hours5"),
            "hours10": self.t("student_badge_hours10"),
        }
        for badge_id, label in badge_defs.items():
            ach = self.achievements.get(badge_id, {"unlocked": False, "progress": 0, "need": 1})
            status = self.t("student_badge_unlocked") if ach.get("unlocked") else self.t("student_badge_locked")
            item_text = f"{label} — {status} ({self.t('student_badge_progress', done=ach.get('progress', 0), need=ach.get('need', 1))})"
            item = QListWidgetItem(item_text)
            if ach["unlocked"]:
                item.setForeground(QColor("#059669"))
            else:
                item.setForeground(QColor("#94A3B8"))
            self.badges_list.addItem(item)
        self.badges_list.blockSignals(False)

    # ------------------------------------------------------------------
    # Statistics & CSV export
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
            self, self.t("csv_export_title"), "pomotime_sessions.csv",
            self.t("csv_filter"),
        )
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow([self.t("csv_task"), self.t("csv_duration"), self.t("csv_completed_at")])
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
            self.refresh_student_ui()
        elif index == 4:
            self.refresh_weekly_ui()
        elif index == 5:
            self.refresh_badges_ui()
        elif index == 6:
            self.update_daily_progress()

    def pause_text(self):
        return self.t("pause")

    # ------------------------------------------------------------------
    # Audio
    # ------------------------------------------------------------------
    def start_repeating_alert(self):
        self.alert_repeats_left = 3
        play_tone("alert")
        self.alert_timer.start(900)

    def repeat_alert_sound(self):
        if self.alert_repeats_left > 0:
            play_tone("alert")
            self.alert_repeats_left -= 1
        else:
            self.alert_timer.stop()

    # ------------------------------------------------------------------
    # Statistics display
    # ------------------------------------------------------------------
    def update_statistics_display(self):
        focus_mins_total = self.total_focus_seconds // 60
        self.stat_focus_label.setText(self.t("stats_total_focus", mins=focus_mins_total))
        self.stat_cycles_label.setText(self.t("stats_completed_cycles", count=self.completed_cycles))
        self.stat_breaks_label.setText(self.t("stats_breaks_taken", count=self.total_breaks_taken))
        self.update_score()
        self.update_daily_progress()

    def update_score(self):
        score = min(100, (self.completed_cycles * 25) + (self.total_focus_seconds // 60))
        self.score_label.setText(self.t("productivity_score", score=score))

    # ------------------------------------------------------------------
    # Tray
    # ------------------------------------------------------------------
    def setup_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        style = self.style()
        if style is not None:
            self.tray_icon.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_MessageBoxInformation))
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
            self.t("timer_running"), self.t("tray_running_message"),
            QSystemTrayIcon.MessageIcon.Information, 3000,
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

    # ------------------------------------------------------------------
    # Settings persistence
    # ------------------------------------------------------------------
    def save_settings(self, notify=False):
        old_focus = self.focus_minutes
        old_short_break = self.short_break_minutes
        old_long_break = self.long_break_minutes

        self.focus_minutes = self.focus_spin.value()
        self.short_break_minutes = self.break_spin.value()
        self.long_break_minutes = self.long_break_spin.value()
        self.cycles_before_long_break = self.cycles_spin.value()
        self.daily_goal_minutes = self.daily_goal_spin.value()

        self.check_daily_reset()

        self.store.focus_minutes = self.focus_minutes
        self.store.short_break_minutes = self.short_break_minutes
        self.store.long_break_minutes = self.long_break_minutes
        self.store.cycles_before_long_break = self.cycles_before_long_break
        self.store.daily_goal_minutes = self.daily_goal_minutes
        self.store.current_theme = self.current_theme
        self.store.language = self.lang
        self.store.auto_start_breaks = self.auto_start_breaks
        self.store.auto_start_focus = self.auto_start_focus
        self.store.current_task = self.current_task
        self.store.completed_cycles = self.completed_cycles
        self.store.total_focus_seconds = self.total_focus_seconds
        self.store.total_breaks_taken = self.total_breaks_taken
        self.store.daily_focus_seconds = self.daily_focus_seconds
        self.store.daily_focus_date = self.daily_focus_date
        self.store.preset_key = self.preset_key
        self.store.queue_mode = self.queue_mode
        self.store.queue_index = self.queue_index
        self.store.session_queue = [
            {"kind": b.get("kind"), "minutes": b.get("minutes"), "task": b.get("task", "")}
            for b in self.session_queue.blocks
        ]

        history = [
            {
                "task": task.get("task", ""),
                "completed_at": task.get("completed_at", ""),
                "duration": task.get("duration", 0),
            }
            for task in self.task_history
        ]
        self.store.task_history = history

        # Student-focused persistence
        self.store.student_subjects = self.student_subjects
        self.store.focus_mode = self.focus_mode
        self.store.weekly_focus_by_subject = self.weekly_focus_by_subject
        self.store.weekly_goal_hours = self.weekly_goal_hours
        self.store.streak_days = self.streak_days
        self.store._last_streak_date = self._last_streak_date.isoformat() if self._last_streak_date else None
        self.store.achievements = self.achievements

        self.store.sync()

        self.cycles_label.setText(
            self.t("cycles", count=self.completed_cycles, target=self.cycles_before_long_break)
        )
        if not self.is_running:
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
        self.refresh_student_ui()
        self.refresh_weekly_ui()
        self.refresh_badges_ui()

        if notify:
            QMessageBox.information(self, self.t("settings"), self.t("settings_saved"))

    def load_settings(self):
        # Apply core settings
        self.focus_minutes = self.store.focus_minutes
        self.short_break_minutes = self.store.short_break_minutes
        self.long_break_minutes = self.store.long_break_minutes
        self.cycles_before_long_break = self.store.cycles_before_long_break
        self.current_theme = self.store.current_theme
        self.auto_start_breaks = self.store.auto_start_breaks
        self.auto_start_focus = self.store.auto_start_focus
        self.current_task = self.store.current_task
        self.completed_cycles = self.store.completed_cycles
        self.total_focus_seconds = self.store.total_focus_seconds
        self.total_breaks_taken = self.store.total_breaks_taken
        self.daily_goal_minutes = self.store.daily_goal_minutes
        self.daily_focus_seconds = self.store.daily_focus_seconds
        self.daily_focus_date = self.store.daily_focus_date
        self.preset_key = self.store.preset_key
        self.queue_mode = self.store.queue_mode and bool(self.store.session_queue)
        self.queue_index = self.store.queue_index

        # Restore session queue
        self.session_queue.blocks = [
            {"kind": b.get("kind", "focus"), "minutes": b.get("minutes", self.focus_minutes), "task": b.get("task", "")}
            for b in self.store.session_queue
            if isinstance(b, dict)
        ]
        self.session_queue.index = self.queue_index
        self.session_queue.mode = self.queue_mode

        # Restore student-focused state
        self.student_subjects = self.store.student_subjects if isinstance(self.store.student_subjects, list) else []
        self.focus_mode = self.store.focus_mode
        self.weekly_focus_by_subject = self.store.weekly_focus_by_subject if isinstance(self.store.weekly_focus_by_subject, dict) else {}
        self.weekly_goal_hours = self.store.weekly_goal_hours
        self.streak_days = self.store.streak_days
        last = self.store._last_streak_date
        self._last_streak_date = date.fromisoformat(last) if last else None
        self.achievements = self.store.achievements if isinstance(self.store.achievements, dict) else self.achievements
        # Merge saved achievements with defaults so missing keys are filled in.
        if isinstance(self.store.achievements, dict):
            for key, default in self.achievements.items():
                if key not in self.store.achievements:
                    self.store.achievements[key] = dict(default)
                else:
                    saved = self.store.achievements[key]
                    if not isinstance(saved, dict):
                        self.store.achievements[key] = dict(default)
                    else:
                        for sub in ("unlocked", "progress", "need"):
                            if sub not in saved:
                                saved[sub] = default[sub]
            self.achievements = self.store.achievements

        # Restore task history
        self.task_history = []
        for task_entry in self.store.task_history:
            if isinstance(task_entry, dict):
                self.task_history.append({
                    "task": task_entry.get("task", ""),
                    "completed_at": task_entry.get("completed_at", ""),
                    "duration": task_entry.get("duration", 0),
                })

        # Synchronize widgets
        self.focus_spin.setValue(self.focus_minutes)
        self.break_spin.setValue(self.short_break_minutes)
        self.long_break_spin.setValue(self.long_break_minutes)
        self.cycles_spin.setValue(self.cycles_before_long_break)
        self.daily_goal_spin.setValue(self.daily_goal_minutes)
        self.weekly_goal_spin.setValue(self.weekly_goal_hours)

        self.lang = self.store.language
        lang_index = SUPPORTED_LANGUAGES.index(self.lang) if self.lang in SUPPORTED_LANGUAGES else 0
        self.lang_combo.blockSignals(True)
        self.lang_combo.setCurrentIndex(lang_index)
        self.lang_combo.blockSignals(False)

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
        self.auto_break_check.setChecked(self.auto_start_breaks)
        self.auto_focus_check.setChecked(self.auto_start_focus)
        self.focus_mode_btn.setText(
            self.t("student_focus_disable") if self.focus_mode else self.t("student_focus_enable")
        )
        for i in range(1, self.tabs.count()):
            self.tabs.setTabEnabled(i, not self.focus_mode)

        if self.queue_mode and self.session_queue.blocks:
            if self.queue_index >= len(self.session_queue.blocks):
                self.queue_index = len(self.session_queue.blocks)
                self.time_left = 0
                last_kind = str(self.session_queue.blocks[-1].get("kind", "focus"))
                if last_kind in ("focus", "short_break", "long_break"):
                    self.current_stage = last_kind
            else:
                self.queue_index = min(self.queue_index, len(self.session_queue.blocks) - 1)
                self.load_queue_step(self.queue_index)
        else:
            self.queue_index = 0
            self.current_stage = "focus"
            self.load_current_stage_time()

        self.queue_mode_check.blockSignals(True)
        self.queue_mode_check.setChecked(self.queue_mode)
        self.queue_mode_check.setEnabled(not self.session_queue.is_empty)
        self.queue_mode_check.blockSignals(False)

        self.refresh_queue_ui()
        self.refresh_student_ui()
        self.refresh_weekly_ui()
        self.refresh_badges_ui()
        self.update_task_display()
        self.update_display()
        self.refresh_history_list()
        self.update_statistics_display()

        self.apply_theme()

    def change_theme(self, index):
        self.current_theme = self.theme_combo.itemData(index)
        self.apply_theme()

    def apply_theme(self):
        t_colors = THEMES.get(self.current_theme, THEMES[DEFAULT_THEME])

        self.setStyleSheet(f"""
            QMainWindow {{ background-color: {t_colors['bg']}; }}
            QTabWidget::pane {{
                border: 1px solid {t_colors['border']};
                border-radius: 12px;
                background-color: {t_colors['card']};
                padding: 10px;
            }}
            QTabBar::tab {{
                background-color: {t_colors['tab_bg']};
                color: {t_colors['text']};
                padding: 10px 20px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: bold;
                font-size: 13px;
                margin-right: 4px;
            }}
            QTabBar::tab:selected {{
                background-color: {t_colors['accent']};
                color: #FFFFFF;
            }}
            QLabel {{ color: {t_colors['text']}; font-family: 'Segoe UI', -apple-system, Arial, sans-serif; }}
            QPushButton {{
                background-color: {t_colors['accent']};
                color: white;
                border-radius: 8px;
                font-weight: bold;
                font-size: 13px;
                padding: 8px 16px;
                border: none;
            }}
            QPushButton:hover {{ background-color: {t_colors['accent_hover']}; }}
            QPushButton:pressed {{ background-color: {t_colors['accent']}; }}
            QFrame#TimerCard, QFrame#StatsCard {{
                background-color: {t_colors['card']};
                border-radius: 16px;
                border: 1px solid {t_colors['border']};
            }}
            QComboBox, QSpinBox {{
                background-color: {t_colors['card']};
                color: {t_colors['text']};
                border: 1px solid {t_colors['border']};
                border-radius: 8px;
                padding: 6px 14px;
                font-size: 13px;
                min-height: 24px;
            }}
            QComboBox:hover, QSpinBox:hover {{ border: 1px solid {t_colors['accent']}; }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 24px;
                border-left-width: 0px;
                border-top-right-radius: 8px;
                border-bottom-right-radius: 8px;
            }}
            QComboBox::down-arrow {{ image: none; border: none; width: 0; height: 0; margin-right: 8px; }}
            QComboBox {{ padding-right: 28px; }}
            QComboBox QAbstractItemView {{
                background-color: {t_colors['card']};
                color: {t_colors['text']};
                border: 1px solid {t_colors['border']};
                outline: 0px;
            }}
            QComboBox QAbstractItemView::item {{
                padding: 8px 12px;
                color: {t_colors['text']};
                background-color: {t_colors['card']};
            }}
            QComboBox QAbstractItemView::item:selected,
            QComboBox QAbstractItemView::item:hover {{
                background-color: {t_colors['accent']};
                color: #FFFFFF;
            }}
            QLineEdit {{
                background-color: {t_colors['card']};
                color: {t_colors['text']};
                border: 1px solid {t_colors['border']};
                border-radius: 8px;
                padding: 8px 14px;
                font-size: 13px;
            }}
            QLineEdit:focus {{ border: 1px solid {t_colors['accent']}; }}
            QCheckBox {{
                color: {t_colors['text']};
                background: transparent;
                spacing: 8px;
                font-size: 13px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 2px solid {t_colors['border']};
                border-radius: 4px;
                background-color: {t_colors['card']};
            }}
            QCheckBox::indicator:checked {{
                background-color: {t_colors['accent']};
                border: 2px solid {t_colors['accent']};
                image: none;
            }}
            QProgressBar {{
                background-color: {t_colors['tab_bg']};
                border: 1px solid {t_colors['border']};
                border-radius: 6px;
                height: 12px;
                text-align: center;
                color: {t_colors['text']};
            }}
            QProgressBar::chunk {{
                background-color: {t_colors['accent']};
                border-radius: 6px;
            }}
            QListWidget {{
                background-color: {t_colors['card']};
                color: {t_colors['text']};
                border: 1px solid {t_colors['border']};
                border-radius: 8px;
                padding: 4px;
                font-size: 13px;
            }}
            QListWidget::item {{
                padding: 7px 8px;
                border-radius: 6px;
                color: {t_colors['text']};
            }}
            QListWidget::item:selected {{
                background-color: {t_colors['accent']};
                color: #FFFFFF;
            }}
            QListWidget::item:hover {{ background-color: {t_colors['tab_bg']}; }}
            QPushButton#SecondaryButton {{
                background-color: {t_colors['tab_bg']};
                color: {t_colors['text']};
                border: 1px solid {t_colors['border']};
                border-radius: 8px;
                font-weight: bold;
                font-size: 12px;
                padding: 7px 12px;
            }}
            QPushButton#SecondaryButton:hover {{
                border: 1px solid {t_colors['accent']};
                color: {t_colors['accent']};
            }}
        """)

        self.time_label.setStyleSheet(f"color: {t_colors['accent']}; font-size: 56px; font-weight: bold;")
        self.score_label.setStyleSheet(f"color: {t_colors['accent']}; font-weight: bold; font-size: 14px;")

    def toggle_auto_break(self, state):
        self.auto_start_breaks = state == 2
        self.save_settings()

    def toggle_auto_focus(self, state):
        self.auto_start_focus = state == 2
        self.save_settings()

    def toggle_mini_mode(self):
        if not self.is_mini_mode:
            self.is_mini_mode = True
            self.hide()
            if not self.mini_widget:
                self.mini_widget = FloatingMiniWidget(self)
            mins = self.time_left // 60
            secs = self.time_left % 60
            self.mini_widget.mini_time_label.setText(f"{mins:02d}:{secs:02d}")
            stage_text = (
                self.t("focus") if self.current_stage == "focus"
                else (self.t("short_break") if self.current_stage == "short_break" else self.t("long_break"))
            )
            self.mini_widget.mini_stage_label.setText(stage_text)
            self.mini_widget.mini_task_label.setText(self.task_display.text())
            self.mini_widget.mini_play_btn.setText("⏸" if self.is_running else "▶")
            self.mini_widget.show()
            self.mini_mode_btn.setText(self.t("normal_mode"))
        else:
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
        reply = QMessageBox.question(
            self,
            self.t("quit"),
            self.t("confirm_quit") if self.lang == "en" else self.t("confirm_quit_ar"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.timer.stop()
            self.save_settings()
            if a0 is not None:
                a0.accept()
        else:
            if a0 is not None:
                a0.ignore()
            self.hide_to_tray()


def main():
    app = QApplication(sys.argv)
    window = PomoTimeApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
