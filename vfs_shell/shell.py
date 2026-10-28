"""REPL, параметры командной строки и стартовые сценарии."""
import argparse
import os
import getpass
from datetime import datetime
import time
from pathlib import Path
import shlex
import sys

from .vfs import VFSError, VirtualFS


class ShellError(Exception):
    """Ошибка команды оболочки."""


class Shell:
    def __init__(self, vfs_path=None, script_path=None, batch=False):
        self.vfs_path = vfs_path
        self.script_path = script_path
        self.batch = batch
        self.running = True
        self.vfs = None
        self.cwd = "/"
        self.previous_cwd = None
        self.started_at = datetime.now().astimezone()
        self.started_monotonic = time.monotonic()

    @staticmethod
    def parse(line):
        try:
            return [os.path.expandvars(token) for token in shlex.split(line, comments=True)]
        except ValueError as error:
            raise ShellError(f"ошибка синтаксиса: {error}") from error

    def prompt(self):
        return f"VFS:{self.cwd}$ "

    def execute_line(self, line):
        tokens = self.parse(line)
        if not tokens:
            return
        command, *args = tokens
        try:
            if command == "exit":
                self._no_args(command, args)
                self.running = False
            elif command == "conf-dump":
                self._no_args(command, args)
                print(f"vfs={self.vfs_path}")
                print(f"script={self.script_path if self.script_path is not None else '<не задан>'}")
                print(f"batch={str(self.batch).lower()}")
            elif command == "ls":
                self.cmd_ls(args)
            elif command == "cd":
                self.cmd_cd(args)
            elif command == "rm":
                self.cmd_rm(args)
            elif command == "pwd":
                self._no_args(command, args)
                print(self.cwd)
            elif command == "cat":
                self.cmd_cat(args)
            elif command == "who":
                self._no_args(command, args)
                print(f"{getpass.getuser()}  vfs  {self.started_at:%Y-%m-%d %H:%M}")
            elif command == "uptime":
                self._no_args(command, args)
                seconds = int(time.monotonic() - self.started_monotonic)
                days, remainder = divmod(seconds, 86400)
                hours, remainder = divmod(remainder, 3600)
                minutes, seconds = divmod(remainder, 60)
                up = f"{hours}:{minutes:02}:{seconds:02}"
                if days:
                    up = f"{days} дн., {up}"
                print(f"{datetime.now().astimezone():%H:%M:%S} up {up}, 1 user (VFS)")
            elif command == "echo":
                print(" ".join(args))
            elif command == "help":
                self._no_args(command, args)
                print("Команды: ls [-al] [пути], cd [путь|-], pwd, cat [-n] файл...,")
                print("         rm [-rf] путь..., uptime, who, conf-dump, echo, help, exit")
            else:
                raise ShellError(f"неизвестная команда: {command}")
        except VFSError as error:
            raise ShellError(f"{command}: {error}") from error

    @staticmethod
    def _no_args(command, args):
        if args:
            raise ShellError(f"{command}: команда не принимает аргументы: {args!r}")

    def cmd_ls(self, args):
        show_all = False
        long = False
        paths = []
        options_done = False
        for arg in args:
            if arg == "--" and not options_done:
                options_done = True
            elif arg.startswith("-") and arg != "-" and not options_done:
                if arg == "--all":
                    show_all = True
                elif arg == "--long":
                    long = True
                else:
                    for letter in arg[1:]:
                        if letter == "a":
                            show_all = True
                        elif letter == "l":
                            long = True
                        else:
                            raise ShellError(f"ls: неизвестный параметр -{letter}")
            else:
                paths.append(arg)
        if not paths:
            paths = ["."]
        for index, raw_path in enumerate(paths):
            path = self.vfs.resolve(self.cwd, raw_path)
            items = self.vfs.list_dir(path)
            if show_all and self.vfs.is_dir(path):
                from .vfs import DirEntry
                items = [DirEntry(".", True, 0), DirEntry("..", True, 0)] + items
            if not show_all:
                items = [item for item in items if not item.name.startswith(".")]
            if index:
                print()
            if len(paths) > 1:
                print(f"{raw_path}:")
            for item in items:
                label = item.name + ("/" if item.is_dir and item.name not in (".", "..") else "")
                if long:
                    print(f"{'d' if item.is_dir else '-'} {item.size:>8} {label}")
                else:
                    print(label)

    def cmd_cd(self, args):
        if len(args) > 1:
            raise ShellError("cd: ожидается не более одного пути")
        if args and args[0] == "-":
            if self.previous_cwd is None:
                raise ShellError("cd: предыдущий каталог не задан")
            target = self.previous_cwd
            print(target)
        else:
            target = self.vfs.resolve(self.cwd, args[0] if args else "/")
        if not self.vfs.is_dir(target):
            if self.vfs.exists(target):
                raise ShellError(f"cd: не каталог: {target}")
            raise ShellError(f"cd: каталог не найден: {target}")
        self.previous_cwd, self.cwd = self.cwd, target

    def cmd_cat(self, args):
        numbered = False
        paths = []
        options_done = False
        for arg in args:
            if arg == "--" and not options_done:
                options_done = True
            elif arg.startswith("-") and arg != "-" and not options_done:
                if arg == "-n":
                    numbered = True
                else:
                    raise ShellError(f"cat: неизвестный параметр {arg}")
            else:
                paths.append(arg)
        if not paths:
            raise ShellError("cat: укажите один или несколько файлов")
        line_no = 1
        for raw_path in paths:
            path = self.vfs.resolve(self.cwd, raw_path)
            content = self.vfs.read_file(path).decode("utf-8", errors="replace")
            if numbered:
                for line in content.splitlines(keepends=True):
                    print(f"{line_no:>6}  ", end="")
                    sys.stdout.write(line)
                    line_no += 1
            else:
                sys.stdout.write(content)
        sys.stdout.flush()

    def cmd_rm(self, args):
        recursive = False
        force = False
        paths = []
        options_done = False
        for arg in args:
            if arg == "--" and not options_done:
                options_done = True
            elif arg.startswith("-") and arg != "-" and not options_done:
                if arg == "--recursive":
                    recursive = True
                elif arg == "--force":
                    force = True
                else:
                    for letter in arg[1:]:
                        if letter in ("r", "R"):
                            recursive = True
                        elif letter == "f":
                            force = True
                        else:
                            raise ShellError(f"rm: неизвестный параметр -{letter}")
            else:
                paths.append(arg)
        if not paths:
            if force:
                return
            raise ShellError("rm: не указан файл для удаления")
        for raw_path in paths:
            path = self.vfs.resolve(self.cwd, raw_path)
            if path == "/":
                raise ShellError("rm: нельзя удалять корень VFS")
            if self.vfs.is_dir(path) and (path == self.cwd or self.cwd.startswith(path + "/")):
                raise ShellError(f"rm: нельзя удалять текущий каталог или его предка: {path}")
            self.vfs.remove(path, recursive=recursive, force=force)

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
        try:
            self.vfs = VirtualFS.from_zip(self.vfs_path)
        except VFSError as error:
            print(f"Ошибка VFS: {error}", file=sys.stderr)
            return 2
        if self.vfs.exists("/motd") and not self.vfs.is_dir("/motd"):
            print(self.vfs.read_file("/motd").decode("utf-8", errors="replace"), end="")
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
    if not args.vfs:
        parser.error("необходимо указать --vfs ПУТЬ_К_ZIP")
    return Shell(args.vfs, args.script, args.batch).run()