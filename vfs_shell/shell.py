"""Этап 2: REPL, параметры командной строки и стартовые сценарии."""

import argparse
import os
from pathlib import Path
import shlex
import sys


class ShellError(Exception):
    """Ошибка команды оболочки."""


class Shell:
    def __init__(self, vfs_path=None, script_path=None, batch=False):
        self.vfs_path = vfs_path
        self.script_path = script_path
        self.batch = batch
        self.running = True

    @staticmethod
    def parse(line):
        try:
            return [os.path.expandvars(token) for token in shlex.split(line, comments=True)]
        except ValueError as error:
            raise ShellError(f"ошибка синтаксиса: {error}") from error

    def prompt(self):
        return "VFS:/$ "

    def execute_line(self, line):
        tokens = self.parse(line)
        if not tokens:
            return
        command, *args = tokens
        if command == "exit":
            if args:
                raise ShellError("exit: команда не принимает аргументы")
            self.running = False
        elif command in {"ls", "cd"}:
            print(f"{command}: аргументы = {args!r} (заглушка)")
        elif command == "conf-dump":
            if args:
                raise ShellError("conf-dump: команда не принимает аргументы")
            print(f"vfs={self.vfs_path if self.vfs_path is not None else '<не задан>'}")
            print(f"script={self.script_path if self.script_path is not None else '<не задан>'}")
            print(f"batch={str(self.batch).lower()}")
        else:
            raise ShellError(f"неизвестная команда: {command}")

    def run_script(self):
        if self.script_path is None:
            return 0
        try:
            lines = Path(self.script_path).read_text(encoding="utf-8-sig").splitlines()
        except OSError as error:
            print(f"Ошибка запуска сценария: {error}", file=sys.stderr)
            return 1
        for number, line in enumerate(lines, start=1):
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            print(f"{self.prompt()}{line}")
            try:
                self.execute_line(line)
            except ShellError as error:
                print(f"Ошибка сценария, строка {number}: {error}", file=sys.stderr)
                return 1
            if not self.running:
                break
        return 0

    def repl(self):
        while self.running:
            try:
                line = input(self.prompt())
            except (EOFError, KeyboardInterrupt):
                print()
                break
            try:
                self.execute_line(line)
            except ShellError as error:
                print(f"Ошибка: {error}", file=sys.stderr)
        return 0

    def run(self):
        code = self.run_script()
        if code or self.batch or not self.running:
            return code
        return self.repl()


def main(argv=None):
    parser = argparse.ArgumentParser(description="Эмулятор UNIX-оболочки с VFS (вариант 11)")
    parser.add_argument("--vfs", help="путь к ZIP-архиву виртуальной файловой системы")
    parser.add_argument("--script", help="путь к стартовому скрипту с командами")
    parser.add_argument("--batch", action="store_true", help="завершить работу после стартового скрипта")
    args = parser.parse_args(argv)
    if args.batch and not args.script:
        parser.error("--batch требует --script")
    return Shell(args.vfs, args.script, args.batch).run()
