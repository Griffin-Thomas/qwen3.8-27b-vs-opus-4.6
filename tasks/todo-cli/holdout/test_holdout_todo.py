import os
import tempfile
import unittest

import cli
import storage
from models import Status, Task


class TestHoldoutTodo(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        os.unlink(self.path)

    def tearDown(self):
        if os.path.exists(self.path):
            os.unlink(self.path)

    def test_done_survives_round_trip(self):
        tasks = [Task(id=1, title="write report", status=Status.DONE)]
        storage.save(tasks, self.path)
        reloaded = storage.load(self.path)
        self.assertIs(
            reloaded[0].status,
            Status.DONE,
            "completed task came back as pending after save/load",
        )

    def test_end_to_end_done_survives_restart(self):
        cli.main(["add", "write report"], path=self.path)
        cli.main(["done", "1"], path=self.path)
        reloaded = storage.load(self.path)
        self.assertIs(reloaded[0].status, Status.DONE)

    def test_plain_status_strings_still_load(self):
        with open(self.path, "w") as f:
            f.write('[{"id": 1, "title": "old task", "status": "done"}]')
        reloaded = storage.load(self.path)
        self.assertIs(
            reloaded[0].status,
            Status.DONE,
            'a legacy file with status "done" must load as DONE',
        )

    def test_pending_round_trip_unchanged(self):
        tasks = [Task(id=1, title="new task")]
        storage.save(tasks, self.path)
        self.assertIs(storage.load(self.path)[0].status, Status.PENDING)


if __name__ == "__main__":
    unittest.main()
