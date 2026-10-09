"""Этап 1: минимальный интерактивный REPL с заглушками команд."""

import os
import shlex


class ShellError(Exception):
    """Ошибка команды оболочки."""


class Shell:
    def __init__(self):
        self.running = True

    @staticmethod
    def parse(line):
        try:
            return [os.path.expandvars(token) for token in shlex.split(line, comments=True)]
        except ValueError as error:
            raise ShellError(f"ошибка синтаксиса: {error}") from error

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
        else:
            raise ShellError(f"неизвестная команда: {command}")

    def repl(self):
        while self.running:
            try:
                line = input("VFS:/$ ")
            except (EOFError, KeyboardInterrupt):
                print()
                return 0
            try:
                self.execute_line(line)
            except ShellError as error:
                print(f"Ошибка: {error}")
        return 0


def main():
    return Shell().repl()
