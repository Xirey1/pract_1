"""Проверки загрузки ZIP, base64, навигации и RAM-only удаления."""

import hashlib
from pathlib import Path
import tempfile
import unittest
import zipfile

from vfs_shell.vfs import VFSError, VirtualFS


ROOT = Path(__file__).resolve().parent.parent
ARCHIVE = ROOT / "demos" / "demo_vfs.zip"


class VFSTests(unittest.TestCase):
    def setUp(self):
        self.vfs = VirtualFS.from_zip(ARCHIVE)

    def test_root_and_implicit_directories(self):
        self.assertTrue(self.vfs.is_dir("/"))
        self.assertTrue(self.vfs.is_dir("/docs/tutorial/advanced"))
        self.assertTrue(self.vfs.is_dir("/data"))
        self.assertTrue(self.vfs.is_dir("/empty"))

    def test_nested_read_and_non_ascii_text(self):
        actual = self.vfs.read_file("/docs/tutorial/advanced/tips.txt")
        self.assertIn("Используйте".encode("utf-8"), actual)

    def test_binary_data_roundtrip_base64(self):
        self.assertEqual(self.vfs.read_file("/data/raw.bin"), bytes([0, 1, 255, 126, 13, 10]))
        self.assertIsInstance(self.vfs.files["/data/raw.bin"], str)
        self.assertNotIn("/data/raw.bin", self.vfs.dirs)

    def test_paths_absolute_relative_parent(self):
        resolve = VirtualFS.resolve
        self.assertEqual(resolve("/docs/tutorial", "../tutorial/advanced"), "/docs/tutorial/advanced")
        self.assertEqual(resolve("/docs", "/notes/todo.txt"), "/notes/todo.txt")
        self.assertEqual(resolve("/docs", "~/notes"), "/notes")
        self.assertEqual(resolve("/", "../../docs"), "/docs")

    def test_list_is_sorted(self):
        self.assertEqual([entry.name for entry in self.vfs.list_dir("/docs/tutorial")], ["advanced", "intro.txt"])

    def test_list_single_file(self):
        items = self.vfs.list_dir("/README.txt")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].name, "README.txt")
        self.assertFalse(items[0].is_dir)

    def test_cat_error_for_directory_and_missing_file(self):
        with self.assertRaises(VFSError):
            self.vfs.read_file("/docs")
        with self.assertRaises(VFSError):
            self.vfs.read_file("/does-not-exist")

    def test_rm_only_changes_memory(self):
        digest_before = hashlib.sha256(ARCHIVE.read_bytes()).hexdigest()
        self.vfs.remove("/notes/todo.txt")
        self.vfs.remove("/docs/tutorial", recursive=True)
        self.assertFalse(self.vfs.exists("/notes/todo.txt"))
        self.assertFalse(self.vfs.exists("/docs/tutorial/advanced/tips.txt"))
        self.assertTrue(self.vfs.exists("/docs"))
        self.assertEqual(hashlib.sha256(ARCHIVE.read_bytes()).hexdigest(), digest_before)
        restored = VirtualFS.from_zip(ARCHIVE)
        self.assertTrue(restored.exists("/notes/todo.txt"))
        self.assertTrue(restored.exists("/docs/tutorial/advanced/tips.txt"))

    def test_rm_directory_needs_recursive(self):
        with self.assertRaises(VFSError):
            self.vfs.remove("/docs")
        self.assertTrue(self.vfs.exists("/docs"))

    def test_rm_missing_force_and_root_protection(self):
        self.vfs.remove("/none", force=True)
        with self.assertRaises(VFSError):
            self.vfs.remove("/none")
        with self.assertRaises(VFSError):
            self.vfs.remove("/", recursive=True, force=True)

    def test_error_invalid_archive(self):
        with self.assertRaises(VFSError):
            VirtualFS.from_zip(ROOT / "demos" / "invalid_vfs.zip")
        with self.assertRaises(VFSError):
            VirtualFS.from_zip(ROOT / "demos" / "missing.zip")

    def test_zip_traversal_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            archive_path = Path(folder) / "unsafe.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("../outside.txt", b"escape")
            with self.assertRaises(VFSError):
                VirtualFS.from_zip(archive_path)
            self.assertFalse((Path(folder).parent / "outside.txt").exists())

    def test_zip_conflict_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            archive_path = Path(folder) / "conflict.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("one/two.txt", "hello")
                archive.writestr("one", "conflict")
            with self.assertRaises(VFSError):
                VirtualFS.from_zip(archive_path)


if __name__ == "__main__":
    unittest.main()
