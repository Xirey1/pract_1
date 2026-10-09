"""Генератор небольших тестовых ZIP (запускается из корня проекта)."""

from pathlib import Path
import zipfile


def make_archive(path, files, directories=()):
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as output:
        for folder in directories:
            output.writestr(folder.rstrip("/") + "/", b"")
        for name, data in files.items():
            output.writestr(name, data.encode("utf-8") if isinstance(data, str) else data)


def main():
    folder = Path(__file__).resolve().parent
    make_archive(folder / "demo_vfs.zip", {
        "motd": "Добро пожаловать в VFS! Вариант №11.\nВсе изменения выполняются только в памяти.\n",
        "README.txt": "Это виртуальная файловая система из ZIP.\n",
        ".hidden.txt": "Скрытый файл.\n",
        "docs/tutorial/intro.txt": "Введение в виртуальную оболочку.\n",
        "docs/tutorial/advanced/tips.txt": "Используйте cd, ls, cat и rm.\n",
        "notes/todo.txt": "Проверить все этапы.\n",
        "data/raw.bin": bytes([0, 1, 255, 126, 13, 10]),
    }, directories=["empty/"])
    make_archive(folder / "minimal_vfs.zip", {"hello.txt": "Привет!\n"})
    make_archive(folder / "nested_vfs.zip", {
        "one/two/three/four.txt": "Четвертый уровень.\n",
        "one/two/other.txt": "Второй уровень.\n",
        "one/root.txt": "Первый уровень.\n",
    })
    (folder / "invalid_vfs.zip").write_text("Это не ZIP-архив!", encoding="utf-8")
    print("Созданы demo_vfs.zip, minimal_vfs.zip, nested_vfs.zip, invalid_vfs.zip")


if __name__ == "__main__":
    main()
