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
