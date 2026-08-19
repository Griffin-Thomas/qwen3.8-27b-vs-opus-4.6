# Task: todo-cli

## Prompt given to both agents

Bug report, confirmed by multiple users: tasks they marked done show up as pending again the next time they run the CLI. Within a single run everything looks correct; it's after restarting that completed work reappears as pending.

Find the root cause and fix it. Don't paper over the symptom in the list command. Files that were written by the affected version should still load sensibly after your fix if that's achievable. Existing tests must pass, and add a regression test for the bug (python3 -m unittest). Work autonomously; do not ask questions.

## Baseline project (before either agent ran)

### cli.py
```python
"""Command-line interface: add, done, list."""

import sys

import storage
from models import Status, Task

DEFAULT_PATH = "todo.json"


def add(tasks, title):
    next_id = max((task.id for task in tasks), default=0) + 1
    task = Task(id=next_id, title=title)
    tasks.append(task)
    return task


def mark_done(tasks, task_id):
    for task in tasks:
        if task.id == task_id:
            task.status = Status.DONE
            return task
    raise SystemExit(f"no task with id {task_id}")


def format_list(tasks, show_all=False):
    lines = []
    for task in tasks:
        if not show_all and task.status is Status.DONE:
            continue
        box = "x" if task.status is Status.DONE else " "
        lines.append(f"[{box}] {task.id}: {task.title}")
    return "\n".join(lines)


def main(argv=None, path=DEFAULT_PATH):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        raise SystemExit("usage: todo add <title> | done <id> | list [--all]")
    command, args = argv[0], argv[1:]
    tasks = storage.load(path)
    if command == "add":
        task = add(tasks, " ".join(args))
        storage.save(tasks, path)
        print(f"added {task.id}: {task.title}")
    elif command == "done":
        task = mark_done(tasks, int(args[0]))
        storage.save(tasks, path)
        print(f"done {task.id}: {task.title}")
    elif command == "list":
        print(format_list(tasks, show_all="--all" in args))
    else:
        raise SystemExit(f"unknown command: {command}")


if __name__ == "__main__":
    main()
```

### models.py
```python
from dataclasses import dataclass
from enum import Enum


class Status(Enum):
    PENDING = "pending"
    DONE = "done"


@dataclass
class Task:
    id: int
    title: str
    status: Status = Status.PENDING
```

### storage.py
```python
"""JSON persistence for the task list."""

import json
from pathlib import Path

from models import Status, Task


def save(tasks, path):
    payload = [
        {"id": task.id, "title": task.title, "status": str(task.status)}
        for task in tasks
    ]
    Path(path).write_text(json.dumps(payload, indent=2))


def _status_from(raw):
    try:
        return Status(raw)
    except ValueError:
        # Tolerate hand-edited or legacy files rather than crashing.
        return Status.PENDING


def load(path):
    path = Path(path)
    if not path.exists():
        return []
    payload = json.loads(path.read_text())
    return [
        Task(id=item["id"], title=item["title"], status=_status_from(item.get("status")))
        for item in payload
    ]
```

### test_todo.py
```python
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
```
