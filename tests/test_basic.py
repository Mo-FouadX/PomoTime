"""
Unit tests for PomoTime core logic.

Run with:  python3 -m unittest discover -s tests -v
"""

import sys
import os
import json
import tempfile
import unittest

# Make the package importable when run directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pomotime.queue import SessionQueue
from pomotime.storage import SettingsStore
from pomotime.i18n import get_translation as t, SUPPORTED_LANGUAGES
from pomotime.themes import THEMES, DEFAULT_THEME


class SessionQueueTests(unittest.TestCase):
    def test_add_and_current(self):
        q = SessionQueue()
        self.assertTrue(q.is_empty)
        q.add_block("focus", 25, "Math")
        self.assertFalse(q.is_empty)
        block = q.current_block()
        self.assertEqual(block["kind"], "focus")
        self.assertEqual(block["minutes"], 25)
        self.assertEqual(block["task"], "Math")

    def test_advance_and_complete(self):
        q = SessionQueue()
        q.add_block("focus", 10)
        q.add_block("short_break", 5)
        q.add_block("focus", 10)
        self.assertEqual(q.current_block()["kind"], "focus")
        q.advance()
        self.assertEqual(q.current_block()["kind"], "short_break")
        q.advance()
        self.assertEqual(q.current_block()["kind"], "focus")
        q.advance()
        self.assertTrue(q.is_complete)

    def test_quick_cycle(self):
        q = SessionQueue()
        q.add_quick_cycle(25, 20)
        kinds = [b["kind"] for b in q]
        self.assertEqual(kinds, ["focus", "focus", "long_break"])

    def test_move_delete(self):
        q = SessionQueue()
        q.add_block("focus", 10, "A")
        q.add_block("short_break", 5, "B")
        q.add_block("focus", 10, "C")
        self.assertTrue(q.move_up(2))
        self.assertTrue(q.delete_block(1))
        self.assertEqual(len(q), 2)


class I18nTests(unittest.TestCase):
    def test_translation_english(self):
        self.assertEqual(t("focus", lang="en"), "Focus Session")
        self.assertEqual(t("cycles", lang="en", count=3, target=4), "Completed Cycles: 3 / 4")

    def test_translation_arabic(self):
        self.assertEqual(t("focus", lang="ar"), "جلسة تركيز")
        self.assertIn("دورات", t("cycles", lang="ar", count=1, target=4))

    def test_supported_languages(self):
        self.assertIn("en", SUPPORTED_LANGUAGES)
        self.assertIn("ar", SUPPORTED_LANGUAGES)


class ThemesTests(unittest.TestCase):
    def test_themes_have_required_keys(self):
        for theme in THEMES.values():
            for key in ("bg", "card", "text", "accent", "border"):
                self.assertIn(key, theme)

    def test_default_theme(self):
        self.assertIn(DEFAULT_THEME, THEMES)


class SettingsStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="pomotime_test_")
        self.store = SettingsStore(config_dir=self.tmpdir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_settings_roundtrip(self):
        store = self.store
        store.focus_minutes = 50
        store.current_theme = "midnight"
        store.language = "ar"
        store.session_queue = [{"kind": "focus", "minutes": 10, "task": "Test"}]
        store.student_subjects = [{"name": "Physics", "blocks_needed": 4, "blocks_done": 2}]
        store.weekly_focus_by_subject = {"2026-11-23": {"Physics": 50}}
        store.achievements = {"first": {"unlocked": True, "progress": 1, "need": 1}}
        store.sync()

        store2 = SettingsStore(config_dir=self.tmpdir)
        self.assertEqual(store2.focus_minutes, 50)
        self.assertEqual(store2.current_theme, "midnight")
        self.assertEqual(store2.language, "ar")
        self.assertEqual(store2.session_queue[0]["task"], "Test")
        self.assertEqual(store2.student_subjects[0]["name"], "Physics")
        self.assertEqual(store2.weekly_focus_by_subject["2026-11-23"]["Physics"], 50)
        self.assertTrue(store2.achievements["first"]["unlocked"])

    def test_settings_defaults(self):
        store = self.store
        self.assertEqual(store.focus_minutes, 25)
        self.assertEqual(store.current_theme, DEFAULT_THEME)
        self.assertEqual(store.session_queue, [])
        self.assertEqual(store.student_subjects, [])
        self.assertEqual(store.weekly_focus_by_subject, {})
        self.assertEqual(store.achievements, {})


if __name__ == "__main__":
    unittest.main()
