"""ZIP -> виртуальная файловая система исключительно в оперативной памяти.

Файлы хранятся в словаре как строки base64. ZIP никогда не распаковывается
на физическую файловую систему, а позднейшие изменения не записываются назад.
"""

import base64
from dataclasses import dataclass
import posixpath
from pathlib import Path
import zipfile


class VFSError(Exception):
    """Ошибка виртуальной файловой системы."""


@dataclass(frozen=True)
class DirEntry:
    name: str
    is_dir: bool
    size: int


class VirtualFS:
    def __init__(self):
        self.dirs = {"/"}
        self.files = {}  # /path -> base64-текст исходных байтов

    @classmethod
    def from_zip(cls, archive_path):
        path = Path(archive_path)
        if not path.is_file():
            raise VFSError(f"файл ZIP не найден: {path}")
        vfs = cls()
        try:
            with zipfile.ZipFile(path, "r") as archive:
                bad_file = archive.testzip()
                if bad_file is not None:
                    raise VFSError(f"поврежденный файл в ZIP: {bad_file}")
                for info in archive.infolist():
                    name = info.filename
                    if not name or name.startswith("/") or "\\" in name or "\x00" in name:
                        raise VFSError(f"недопустимое имя внутри ZIP: {name!r}")
                    parts = name.rstrip("/").split("/")
                    if any(part in ("", ".", "..") for part in parts):
                        raise VFSError(f"небезопасный путь внутри ZIP: {name!r}")
                    full_path = "/" + "/".join(parts)
                    if info.is_dir() or name.endswith("/"):
                        if full_path in vfs.files:
                            raise VFSError(f"конфликт файлов и каталогов: {full_path}")
                        vfs.dirs.add(full_path)
                    else:
                        if full_path in vfs.files or full_path in vfs.dirs:
                            raise VFSError(f"повторяющийся путь внутри ZIP: {full_path}")
                        vfs.files[full_path] = base64.b64encode(archive.read(info)).decode("ascii")
                    ancestor = posixpath.dirname(full_path)
                    while ancestor != "/":
                        if ancestor in vfs.files:
                            raise VFSError(f"файл используется как каталог: {ancestor}")
                        vfs.dirs.add(ancestor)
                        ancestor = posixpath.dirname(ancestor)
                if vfs.dirs.intersection(vfs.files):
                    raise VFSError("файл и каталог имеют одинаковый путь")
        except (OSError, zipfile.BadZipFile, zipfile.LargeZipFile, RuntimeError, EOFError) as error:
            raise VFSError(f"не удалось загрузить ZIP {path}: {error}") from error
        return vfs

    @staticmethod
    def resolve(cwd, user_path):
        """Нормализация POSIX-пути (никогда не затрагивает реальную ФС)."""
        if not user_path:
            raise VFSError("укажите путь")
        if user_path == "~":
            return "/"
        if user_path.startswith("~/"):
            user_path = user_path[1:]
        if user_path.startswith("/"):
            return posixpath.normpath(user_path)
        return posixpath.normpath(posixpath.join(cwd, user_path))

    def exists(self, path):
        return path in self.dirs or path in self.files

    def is_dir(self, path):
        return path in self.dirs

    def size_of(self, path):
        if path in self.files:
            return len(base64.b64decode(self.files[path]))
        if path in self.dirs:
            return 0
        raise VFSError(f"нет такого файла или каталога: {path}")

    def read_file(self, path):
        if path in self.dirs:
            raise VFSError(f"это каталог: {path}")
        if path not in self.files:
            raise VFSError(f"файл не найден: {path}")
        return base64.b64decode(self.files[path])

    def list_dir(self, path):
        if path in self.files:
            return [DirEntry(posixpath.basename(path), False, self.size_of(path))]
        if path not in self.dirs:
            raise VFSError(f"каталог не найден: {path}")
        results = []
        for directory in self.dirs:
            if directory != path and posixpath.dirname(directory) == path:
                results.append(DirEntry(posixpath.basename(directory), True, 0))
        for filename in self.files:
            if posixpath.dirname(filename) == path:
                results.append(DirEntry(posixpath.basename(filename), False, self.size_of(filename)))
        return sorted(results, key=lambda entry: entry.name)

    def remove(self, path, recursive=False, force=False):
        """Удаляет узел из RAM, не изменяя ZIP-архив на диске."""
        if path == "/":
            raise VFSError("нельзя удалить корень VFS")
        if path in self.files:
            del self.files[path]
            return
        if path in self.dirs:
            if not recursive:
                raise VFSError(f"это каталог (используйте rm -r): {path}")
            prefix = path + "/"
            for filename in tuple(self.files):
                if filename.startswith(prefix):
                    del self.files[filename]
            for dirname in tuple(self.dirs):
                if dirname == path or dirname.startswith(prefix):
                    self.dirs.remove(dirname)
            return
        if not force:
            raise VFSError(f"файл или каталог не найден: {path}")
