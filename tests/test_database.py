import os
import tempfile
import unittest

from kopyahon.database import Database
from kopyahon.settings import DEFAULTS, Settings


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.db = Database(":memory:")

    def tearDown(self):
        self.db.close()

    def test_add_and_preserve_text_exactly(self):
        text = "line one\r\n  indented line\n\nlast line é ñ 漢字\t"
        res = self.db.add_clip(text)
        self.assertEqual(res.status, "added")
        self.assertEqual(self.db.get_clip(res.clip_id).content, text)

    def test_duplicate_modes(self):
        a = self.db.add_clip("hello", "move")
        self.db.add_clip("other", "move")
        b = self.db.add_clip("hello", "move")
        self.assertEqual((b.status, b.clip_id), ("moved", a.clip_id))
        self.assertEqual(self.db.count_clips(), 2)
        self.assertEqual(self.db.get_clips()[0].content, "hello")  # bumped to top

        self.assertEqual(self.db.add_clip("hello", "skip").status, "skipped")
        self.assertEqual(self.db.count_clips(), 2)

        self.assertEqual(self.db.add_clip("hello", "allow").status, "added")
        self.assertEqual(self.db.count_clips(), 3)

    def test_history_limit_prunes_oldest_but_keeps_favorites(self):
        first = self.db.add_clip("clip 0").clip_id
        self.db.set_favorite(first, True)
        for i in range(1, 8):
            self.db.add_clip(f"clip {i}", history_limit=3)
        contents = {c.content for c in self.db.get_clips()}
        self.assertIn("clip 0", contents)                 # favorite survives
        self.assertEqual(len(contents), 4)                # favorite + newest 3
        self.assertTrue({"clip 5", "clip 6", "clip 7"} <= contents)

    def test_count_prunable_and_prune(self):
        for i in range(10):
            self.db.add_clip(f"c{i}")
        self.assertEqual(self.db.count_prunable(4), 6)
        self.assertEqual(self.db.prune(4), 6)
        self.assertEqual(self.db.count_clips(), 4)

    def test_search_is_case_insensitive_multi_term_and_literal(self):
        self.db.add_clip("Maayong Buntag sa tanan")
        self.db.add_clip("100% sure_thing")
        self.db.add_clip("plain text")
        self.assertEqual(self.db.count_clips("maayong TANAN"), 1)
        self.assertEqual(self.db.count_clips("100%"), 1)      # % is not a wildcard
        self.assertEqual(self.db.count_clips("sure_t"), 1)
        self.assertEqual(self.db.count_clips("s_re"), 0)      # _ is not a wildcard
        self.assertEqual(self.db.count_clips("ÑANDÚ"), 0)
        self.db.add_clip("Ñandú")
        self.assertEqual(self.db.count_clips("ñandú"), 1)     # unicode folding

    def test_sorting(self):
        self.db.add_clip("bbb")
        self.db.add_clip("a")
        self.db.add_clip("cccccc")
        self.assertEqual([c.content for c in self.db.get_clips(sort="longest")], ["cccccc", "bbb", "a"])
        self.assertEqual([c.content for c in self.db.get_clips(sort="shortest")], ["a", "bbb", "cccccc"])
        self.assertEqual([c.content for c in self.db.get_clips(sort="alphabetical")], ["a", "bbb", "cccccc"])
        self.assertEqual([c.content for c in self.db.get_clips(sort="newest")], ["cccccc", "a", "bbb"])
        self.assertEqual([c.content for c in self.db.get_clips(sort="oldest")], ["bbb", "a", "cccccc"])

    def test_pagination(self):
        for i in range(25):
            self.db.add_clip(f"item {i:02d}")
        page = self.db.get_clips(limit=10, offset=10)
        self.assertEqual(len(page), 10)
        self.assertEqual(page[0].content, "item 14")

    def test_favorites_and_stats(self):
        a = self.db.add_clip("a").clip_id
        self.db.add_clip("b")
        self.assertTrue(self.db.toggle_favorite(a))
        self.assertEqual(self.db.stats(), {"total": 2, "today": 2, "favorites": 1})
        self.assertEqual([c.content for c in self.db.get_clips(favorites_only=True)], ["a"])
        self.assertFalse(self.db.toggle_favorite(a))
        self.assertIsNone(self.db.toggle_favorite(9999))

    def test_delete_and_clear(self):
        ids = [self.db.add_clip(f"x{i}").clip_id for i in range(5)]
        self.db.set_favorite(ids[0], True)
        self.assertEqual(self.db.delete_clips(ids[1:3]), 2)
        self.assertEqual(self.db.delete_clips([]), 0)
        self.assertEqual(self.db.clear_history(keep_favorites=True), 2)
        self.assertEqual(self.db.count_clips(), 1)
        self.assertEqual(self.db.clear_history(keep_favorites=False), 1)
        self.assertEqual(self.db.count_clips(), 0)

    def test_snippets_crud_and_search(self):
        sid = self.db.add_snippet("  Email sign-off ", "Salamat,\nJoshua")
        snip = self.db.get_snippet(sid)
        self.assertEqual(snip.title, "Email sign-off")
        self.assertEqual(snip.content, "Salamat,\nJoshua")
        self.db.update_snippet(sid, "Closing", "Palihog ug balos")
        self.assertEqual(self.db.get_snippets("balos")[0].title, "Closing")
        self.assertEqual(self.db.get_snippets("nomatch"), [])
        self.db.delete_snippet(sid)
        self.assertEqual(self.db.count_snippets(), 0)


class PersistenceTests(unittest.TestCase):
    def test_data_and_settings_survive_reopen(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "k.db")
            db = Database(path)
            settings = Settings(db)
            self.assertEqual(settings.get("theme"), DEFAULTS["theme"])
            settings.set("theme", "light")
            settings.set("history_limit", 250)
            settings.set("monitoring", False)
            settings.set("duplicate_mode", "skip")
            db.add_clip("persist me")
            db.close()

            db2 = Database(path)
            s2 = Settings(db2)
            self.assertEqual(s2.get("theme"), "light")
            self.assertEqual(s2.get("history_limit"), 250)
            self.assertFalse(s2.get("monitoring"))
            self.assertEqual(s2.get("duplicate_mode"), "skip")
            self.assertEqual(db2.get_clips()[0].content, "persist me")
            db2.close()

    def test_invalid_values_fall_back_to_defaults(self):
        db = Database(":memory:")
        settings = Settings(db)
        self.assertEqual(settings.set("theme", "neon"), DEFAULTS["theme"])
        self.assertEqual(settings.set("history_limit", 1), DEFAULTS["history_limit"])
        with self.assertRaises(KeyError):
            settings.set("nope", 1)


if __name__ == "__main__":
    unittest.main()
