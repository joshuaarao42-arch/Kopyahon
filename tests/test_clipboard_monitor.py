import threading
import time
import unittest

from kopyahon.clipboard_monitor import ClipboardMonitor


class FakeClipboard:
    def __init__(self, text=""):
        self.text = text
        self.fail = False
        self.lock = threading.Lock()

    def read(self):
        with self.lock:
            if self.fail:
                raise RuntimeError("clipboard locked")
            return self.text

    def write(self, text):
        with self.lock:
            self.text = text

    def set(self, text):
        with self.lock:
            self.text = text


def wait_for(predicate, timeout=3.0):
    end = time.time() + timeout
    while time.time() < end:
        if predicate():
            return True
        time.sleep(0.01)
    return predicate()


class MonitorLogicTests(unittest.TestCase):
    """Deterministic tests that drive check_now() directly (no thread)."""

    def make(self, text="start", **kw):
        self.clip = FakeClipboard(text)
        self.got = []
        mon = ClipboardMonitor(self.got.append, read=self.clip.read, write=self.clip.write, **kw)
        mon._sync_baseline()
        return mon

    def test_baseline_not_recorded_and_unchanged_content_ignored(self):
        mon = self.make("already here")
        self.assertIsNone(mon.check_now())
        self.clip.set("new text")
        self.assertEqual(mon.check_now(), "new text")
        self.assertIsNone(mon.check_now())
        self.assertIsNone(mon.check_now())
        self.assertEqual(self.got, ["new text"])

    def test_line_breaks_preserved(self):
        mon = self.make()
        self.clip.set("a\r\n\r\n  b\n")
        mon.check_now()
        self.assertEqual(self.got, ["a\r\n\r\n  b\n"])

    def test_blank_and_oversized_ignored(self):
        mon = self.make(max_chars=10)
        for value in ("   \n\t", "", "x" * 11):
            self.clip.set(value)
            self.assertIsNone(mon.check_now())
        self.assertEqual(self.got, [])

    def test_same_text_after_something_else_counts_as_new_copy(self):
        mon = self.make("")
        for value in ("abc", "", "abc"):     # "" ~ an image on the clipboard
            self.clip.set(value)
            mon.check_now()
        self.assertEqual(self.got, ["abc", "abc"])

    def test_copy_back_is_not_recorded(self):
        mon = self.make("old")
        mon.copy_to_clipboard("from history")
        self.assertEqual(self.clip.text, "from history")
        self.assertIsNone(mon.check_now())
        self.assertEqual(self.got, [])

    def test_callback_exception_does_not_break_monitor(self):
        clip = FakeClipboard("x")

        def boom(_):
            raise ValueError("bad callback")

        mon = ClipboardMonitor(boom, read=clip.read, write=clip.write)
        mon._sync_baseline()
        clip.set("y")
        self.assertEqual(mon.check_now(), "y")   # swallowed, logged


class MonitorThreadTests(unittest.TestCase):
    def setUp(self):
        self.clip = FakeClipboard("baseline")
        self.got, self.errors = [], []
        self.mon = ClipboardMonitor(self.got.append, self.errors.append,
                                    read=self.clip.read, write=self.clip.write, interval=0.01)

    def tearDown(self):
        self.mon.stop()

    def test_records_in_background_and_ignores_baseline(self):
        self.mon.start()
        self.assertTrue(self.mon.is_running and self.mon.is_active)
        time.sleep(0.1)
        self.assertEqual(self.got, [])
        self.clip.set("first")
        self.assertTrue(wait_for(lambda: self.got == ["first"]))
        self.clip.set("second")
        self.assertTrue(wait_for(lambda: self.got == ["first", "second"]))

    def test_pause_drops_clips_and_resume_uses_new_baseline(self):
        self.mon.start()
        self.mon.pause()
        time.sleep(0.05)
        self.clip.set("copied while paused")
        time.sleep(0.15)
        self.assertEqual(self.got, [])
        self.mon.resume()
        time.sleep(0.15)
        self.assertEqual(self.got, [])           # still not recorded after resume
        self.clip.set("after resume")
        self.assertTrue(wait_for(lambda: self.got == ["after resume"]))

    def test_start_paused(self):
        self.mon.start(paused=True)
        self.assertFalse(self.mon.is_active)
        self.clip.set("nope")
        time.sleep(0.12)
        self.assertEqual(self.got, [])

    def test_errors_reported_once_and_recovery(self):
        self.mon.start()
        self.clip.fail = True
        self.assertTrue(wait_for(lambda: len(self.errors) == 1))
        time.sleep(0.2)
        self.assertEqual(len(self.errors), 1)     # not spammed
        self.clip.fail = False
        self.clip.set("recovered")
        self.assertTrue(wait_for(lambda: "recovered" in self.got, timeout=6.0))

    def test_stop_joins_thread(self):
        self.mon.start()
        self.mon.stop()
        self.assertFalse(self.mon.is_running)


if __name__ == "__main__":
    unittest.main()
