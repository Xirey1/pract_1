"""Интеграционные тесты реального CLI (в том числе режимов ошибок)."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parent.parent
VFS_ARGS = ["--vfs", "demos/demo_vfs.zip"]


def run_shell(*args, input_text=None, env=None):
    return subprocess.run(
        [sys.executable, "main.py", *args],
        cwd=ROOT,
        input=input_text,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=10,
        env=env,
        encoding="utf-8",
        errors="replace",
    )


class ShellTests(unittest.TestCase):
    def test_stage2_configuration_script(self):
        result = run_shell(*VFS_ARGS, "--script", "demos/stage2_ok.vfs", "--batch")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("vfs=demos/demo_vfs.zip", result.stdout)
        self.assertIn("script=demos/stage2_ok.vfs", result.stdout)
        self.assertIn("batch=true", result.stdout)

    def test_stage3_minimal_and_nested_archives(self):
        for archive, script in (("minimal_vfs.zip", "stage3_minimal.vfs"),
                                ("nested_vfs.zip", "stage3_nested.vfs")):
            with self.subTest(archive=archive):
                result = run_shell("--vfs", "demos/" + archive,
                                   "--script", "demos/" + script, "--batch")
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_motd_on_start(self):
        result = run_shell(*VFS_ARGS, input_text="exit\n")
        self.assertEqual(result.returncode, 0)
        self.assertIn("Добро пожаловать", result.stdout)

    def test_ls_cd_cat_who_uptime_script(self):
        result = run_shell(*VFS_ARGS, "--script", "demos/stage4_success.vfs", "--batch")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("/docs/tutorial", result.stdout)
        self.assertIn("Введение в виртуальную оболочку", result.stdout)
        self.assertIn("up 0:", result.stdout)
        self.assertIn("  vfs  ", result.stdout)
        self.assertIn(".hidden.txt", result.stdout)

    def test_script_stops_at_first_error(self):
        result = run_shell(*VFS_ARGS, "--script", "demos/stage4_error.vfs", "--batch")
        self.assertEqual(result.returncode, 1)
        self.assertIn("строка 3", result.stderr)
        self.assertIn("файл не найден", result.stderr)
        self.assertNotIn("who", result.stdout)

    def test_rm_and_non_persistence(self):
        result = run_shell(*VFS_ARGS, "--script", "demos/stage5_success.vfs", "--batch")
        self.assertEqual(result.returncode, 0, result.stderr)
        fresh = run_shell(*VFS_ARGS, input_text="ls /notes\nexit\n")
        self.assertEqual(fresh.returncode, 0)
        self.assertIn("todo.txt", fresh.stdout)

    def test_rm_without_recursive_stops_script(self):
        result = run_shell(*VFS_ARGS, "--script", "demos/stage5_error.vfs", "--batch")
        self.assertEqual(result.returncode, 1)
        self.assertIn("используйте rm -r", result.stderr)
        self.assertNotIn("who", result.stdout)

    def test_root_delete_rejected(self):
        result = run_shell(*VFS_ARGS, input_text="rm -rf /\nexit\n")
        self.assertEqual(result.returncode, 0)
        self.assertIn("нельзя удалять корень", result.stderr)

    def test_current_directory_delete_rejected(self):
        result = run_shell(*VFS_ARGS, input_text="cd /docs/tutorial\nrm -rf /docs\npwd\nexit\n")
        self.assertEqual(result.returncode, 0)
        self.assertIn("нельзя удалять текущий каталог", result.stderr)
        self.assertIn("/docs/tutorial", result.stdout)

    def test_unknown_command_repl_continues(self):
        result = run_shell(*VFS_ARGS, input_text="nope\npwd\nexit\n")
        self.assertEqual(result.returncode, 0)
        self.assertIn("неизвестная команда", result.stderr)
        self.assertIn("VFS:/$ /", result.stdout)

    def test_command_arguments_checked(self):
        result = run_shell(*VFS_ARGS, input_text="who unexpected\nls -z\ncat\nexit extra\nexit\n")
        self.assertEqual(result.returncode, 0)
        self.assertIn("who: команда не принимает аргументы", result.stderr)
        self.assertIn("ls: неизвестный параметр", result.stderr)
        self.assertIn("cat: укажите", result.stderr)
        self.assertIn("exit: команда не принимает аргументы", result.stderr)

    def test_real_environment_variable_expansion(self):
        env = os.environ.copy()
        env["VARIANT11_ENV_TEST"] = "environment_is_real"
        result = run_shell(*VFS_ARGS, input_text='echo "$VARIANT11_ENV_TEST"\nexit\n', env=env)
        self.assertEqual(result.returncode, 0)
        self.assertIn("environment_is_real", result.stdout)

    def test_unterminated_quote(self):
        result = run_shell(*VFS_ARGS, input_text='cat "unterminated\npwd\nexit\n')
        self.assertEqual(result.returncode, 0)
        self.assertIn("ошибка синтаксиса", result.stderr)
        self.assertIn("VFS:/$ /", result.stdout)

    def test_error_zip_missing_and_invalid(self):
        for name in ("missing.zip", "invalid_vfs.zip"):
            with self.subTest(name=name):
                result = run_shell("--vfs", "demos/" + name)
                self.assertEqual(result.returncode, 2)
                self.assertIn("Ошибка VFS", result.stderr)

    def test_missing_script(self):
        result = run_shell(*VFS_ARGS, "--script", "demos/missing.vfs", "--batch")
        self.assertEqual(result.returncode, 1)
        self.assertIn("Ошибка запуска сценария", result.stderr)

    def test_cli_rejects_missing_arguments(self):
        self.assertEqual(run_shell("--batch").returncode, 2)
        self.assertEqual(run_shell("--script", "demos/stage2_ok.vfs", "--batch").returncode, 2)

    def test_exit_stops_script(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "short.vfs"
            path.write_text("pwd\nexit\nwho\n", encoding="utf-8")
            result = run_shell(*VFS_ARGS, "--script", str(path), "--batch")
            self.assertEqual(result.returncode, 0)
            self.assertNotIn("who", result.stdout)

    def test_script_then_interactive(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "short.vfs"
            path.write_text("ls /empty\n", encoding="utf-8")
            result = run_shell(*VFS_ARGS, "--script", str(path), input_text="pwd\nexit\n")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("VFS:/$ /", result.stdout)


if __name__ == "__main__":
    unittest.main()
