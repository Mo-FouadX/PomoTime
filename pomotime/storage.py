"""
Persistent storage for PomoTime.

Handles reading/writing application settings and task history via QSettings,
with daily-goal rollover and legacy key cleanup.
"""

import json
from datetime import date

from PyQt6.QtCore import QSettings

from .i18n import DEFAULT_LANGUAGE
from .themes import DEFAULT_THEME

SETTINGS_ORG = "PomoTime"
SETTINGS_APP = "Settings"


class SettingsStore:
    """Thin wrapper around QSettings with sensible defaults and migration."""

    def __init__(self, config_dir=None):
        if config_dir is not None:
            QSettings.setPath(QSettings.Format.NativeFormat, QSettings.Scope.UserScope, config_dir)
        self.settings = QSettings(SETTINGS_ORG, SETTINGS_APP)
        self._purge_legacy_keys()

    def _purge_legacy_keys(self):
        """Remove legacy background-sound preferences from older versions."""
        self.settings.remove("bg_music_type")
        self.settings.remove("ambient_volume")

    # ---- getters ----

    def get_int(self, key, default=0):
        return int(self.settings.value(key, default, type=int))

    def get_str(self, key, default=""):
        return str(self.settings.value(key, default, type=str))

    def get_bool(self, key, default=False):
        value = self.settings.value(key, default, type=bool)
        return bool(value) if value is not None else default

    def get_list(self, key, default=None):
        if default is None:
            default = []
        return self.settings.value(key, default, type=list)

    def get_dict(self, key, default=None):
        if default is None:
            default = {}
        raw = self.settings.value(key, "", type=str)
        if not raw:
            return default
        try:
            parsed = json.loads(raw)
        except (ValueError, TypeError):
            return default
        return parsed if isinstance(parsed, dict) else default

    def set_dict(self, key, value):
        self.set(key, json.dumps(value, ensure_ascii=False))

    # ---- setters ----

    def set(self, key, value):
        self.settings.setValue(key, value)

    def sync(self):
        self.settings.sync()

    # ---- high-level persisted state ----

    @property
    def focus_minutes(self):
        return self.get_int("focus_minutes", 25)

    @focus_minutes.setter
    def focus_minutes(self, value):
        self.set("focus_minutes", value)

    @property
    def short_break_minutes(self):
        return self.get_int("short_break_minutes", 5)

    @short_break_minutes.setter
    def short_break_minutes(self, value):
        self.set("short_break_minutes", value)

    @property
    def long_break_minutes(self):
        return self.get_int("long_break_minutes", 20)

    @long_break_minutes.setter
    def long_break_minutes(self, value):
        self.set("long_break_minutes", value)

    @property
    def cycles_before_long_break(self):
        return self.get_int("cycles_before_long_break", 4)

    @cycles_before_long_break.setter
    def cycles_before_long_break(self, value):
        self.set("cycles_before_long_break", value)

    @property
    def current_theme(self):
        return self.get_str("current_theme", DEFAULT_THEME)

    @current_theme.setter
    def current_theme(self, value):
        self.set("current_theme", value)

    @property
    def language(self):
        return self.get_str("language", DEFAULT_LANGUAGE)

    @language.setter
    def language(self, value):
        self.set("language", value)

    @property
    def auto_start_breaks(self):
        return self.get_bool("auto_start_breaks", False)

    @auto_start_breaks.setter
    def auto_start_breaks(self, value):
        self.set("auto_start_breaks", value)

    @property
    def auto_start_focus(self):
        return self.get_bool("auto_start_focus", False)

    @auto_start_focus.setter
    def auto_start_focus(self, value):
        self.set("auto_start_focus", value)

    @property
    def current_task(self):
        return self.get_str("current_task", "")

    @current_task.setter
    def current_task(self, value):
        self.set("current_task", value)

    @property
    def completed_cycles(self):
        return self.get_int("completed_cycles", 0)

    @completed_cycles.setter
    def completed_cycles(self, value):
        self.set("completed_cycles", value)

    @property
    def total_focus_seconds(self):
        return self.get_int("total_focus_seconds", 0)

    @total_focus_seconds.setter
    def total_focus_seconds(self, value):
        self.set("total_focus_seconds", value)

    @property
    def total_breaks_taken(self):
        return self.get_int("total_breaks_taken", 0)

    @total_breaks_taken.setter
    def total_breaks_taken(self, value):
        self.set("total_breaks_taken", value)

    @property
    def daily_goal_minutes(self):
        return max(5, self.get_int("daily_goal_minutes", 120))

    @daily_goal_minutes.setter
    def daily_goal_minutes(self, value):
        self.set("daily_goal_minutes", value)

    @property
    def daily_focus_seconds(self):
        return self.get_int("daily_focus_seconds", 0)

    @daily_focus_seconds.setter
    def daily_focus_seconds(self, value):
        self.set("daily_focus_seconds", value)

    @property
    def daily_focus_date(self):
        return self.get_str("daily_focus_date", date.today().isoformat())

    @daily_focus_date.setter
    def daily_focus_date(self, value):
        self.set("daily_focus_date", value)

    @property
    def preset_key(self):
        return self.get_str("preset_key", "classic")

    @preset_key.setter
    def preset_key(self, value):
        self.set("preset_key", value)

    @property
    def queue_mode(self):
        return self.get_bool("queue_mode", False)

    @queue_mode.setter
    def queue_mode(self, value):
        self.set("queue_mode", value)

    @property
    def queue_index(self):
        return self.get_int("queue_index", 0)

    @queue_index.setter
    def queue_index(self, value):
        self.set("queue_index", value)

    @property
    def session_queue(self):
        raw = self.get_str("session_queue", "")
        if not raw:
            return []
        try:
            parsed = json.loads(raw)
        except (ValueError, TypeError):
            return []
        if not isinstance(parsed, list):
            return []
        return parsed

    @session_queue.setter
    def session_queue(self, value):
        self.set("session_queue", json.dumps(value, ensure_ascii=False))

    @property
    def task_history(self):
        return self.get_list("task_history", [])

    @task_history.setter
    def task_history(self, value):
        self.set("task_history", value)

    # ---- Student-focused persistence ----

    @property
    def student_subjects(self):
        return self.get_list("student_subjects", [])

    @student_subjects.setter
    def student_subjects(self, value):
        self.set("student_subjects", value)

    @property
    def focus_mode(self):
        return self.get_bool("focus_mode", False)

    @focus_mode.setter
    def focus_mode(self, value):
        self.set("focus_mode", value)

    @property
    def weekly_focus_by_subject(self):
        return self.get_dict("weekly_focus_by_subject", {})

    @weekly_focus_by_subject.setter
    def weekly_focus_by_subject(self, value):
        self.set_dict("weekly_focus_by_subject", value)

    @property
    def weekly_goal_hours(self):
        return self.get_int("weekly_goal_hours", 10)

    @weekly_goal_hours.setter
    def weekly_goal_hours(self, value):
        self.set("weekly_goal_hours", value)

    @property
    def streak_days(self):
        return self.get_int("streak_days", 0)

    @streak_days.setter
    def streak_days(self, value):
        self.set("streak_days", value)

    @property
    def _last_streak_date(self):
        return self.get_str("_last_streak_date", None)

    @_last_streak_date.setter
    def _last_streak_date(self, value):
        self.set("_last_streak_date", value)

    @property
    def achievements(self):
        return self.get_dict("achievements", {})

    @achievements.setter
    def achievements(self, value):
        self.set_dict("achievements", value)

    # ---- Welcome / first launch ----

    @property
    def first_launch(self):
        return self.get_bool("first_launch", True)

    @first_launch.setter
    def first_launch(self, value):
        self.set("first_launch", value)

    # ---- Monthly goals ----

    @property
    def monthly_goal_hours(self):
        return self.get_int("monthly_goal_hours", 40)

    @monthly_goal_hours.setter
    def monthly_goal_hours(self, value):
        self.set("monthly_goal_hours", value)

    @property
    def monthly_focus_by_month(self):
        return self.get_dict("monthly_focus_by_month", {})

    @monthly_focus_by_month.setter
    def monthly_focus_by_month(self, value):
        self.set_dict("monthly_focus_by_month", value)

    # ---- Custom accent color ----

    @property
    def accent_color(self):
        return self.get_str("accent_color", "")

    @accent_color.setter
    def accent_color(self, value):
        self.set("accent_color", value)


__all__ = ["SettingsStore", "SETTINGS_ORG", "SETTINGS_APP"]
