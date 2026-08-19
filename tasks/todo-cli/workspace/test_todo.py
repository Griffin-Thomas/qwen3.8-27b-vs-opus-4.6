import unittest

import cli
import storage
from models import Status, Task


class TestTodo(unittest.TestCase):
    def test_add_assigns_incrementing_ids(self):
        tasks = []
        first = cli.add(tasks, "write report")
        second = cli.add(tasks, "send report")
        self.assertEqual((first.id, second.id), (1, 2))

    def test_mark_done_sets_status(self):
        tasks = [Task(id=1, title="write report")]
        cli.mark_done(tasks, 1)
        self.assertIs(tasks[0].status, Status.DONE)

    def test_mark_done_unknown_id_exits(self):
        with self.assertRaises(SystemExit):
            cli.mark_done([], 7)

    def test_list_hides_done_by_default(self):
        tasks = [
            Task(id=1, title="write report", status=Status.DONE),
            Task(id=2, title="send report"),
        ]
        output = cli.format_list(tasks)
        self.assertNotIn("write report", output)
        self.assertIn("send report", output)

    def test_list_all_shows_done_with_checkbox(self):
        tasks = [Task(id=1, title="write report", status=Status.DONE)]
        output = cli.format_list(tasks, show_all=True)
        self.assertIn("[x] 1: write report", output)

    def test_load_missing_file_returns_empty(self):
        self.assertEqual(storage.load("does-not-exist.json"), [])


if __name__ == "__main__":
    unittest.main()
