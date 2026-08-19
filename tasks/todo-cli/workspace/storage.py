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
