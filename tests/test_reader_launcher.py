"""Synthetic launcher tests: no real backend, workspace, browser, or services."""

from __future__ import annotations

import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import unittest
import uuid


REPOSITORY = Path(__file__).resolve().parents[1]
LAUNCHER = REPOSITORY / "paper-reader-app.command"
POSIX_SHELL = shutil.which("sh") if os.name == "posix" else None
POSIX_ONLY = "Requires a native POSIX shell on macOS/Linux; unavailable on this host."


class LauncherFileTests(unittest.TestCase):
    def test_posix_shebang_and_lf(self) -> None:
        source = LAUNCHER.read_bytes()
        self.assertTrue(source.startswith(b"#!/bin/sh\n"))
        self.assertNotIn(b"\r", source)

    def test_git_preserves_command_lf(self) -> None:
        attributes = (REPOSITORY / ".gitattributes").read_text(encoding="utf-8")
        self.assertIn("*.command text eol=lf", attributes.splitlines())


@unittest.skipUnless(POSIX_SHELL, POSIX_ONLY)
class LauncherExecutionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parent / f".launcher-fixture-{uuid.uuid4().hex}"
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.repo = self.root / "reader 论文's $tools"
        self.bin = self.root / "bin"
        self.caller = self.root / "unrelated 工作目录"
        for folder in (self.repo, self.bin, self.caller, self.root / "home"):
            folder.mkdir(parents=True)
        self.launcher = self.repo / LAUNCHER.name
        shutil.copyfile(LAUNCHER, self.launcher)
        self.launcher.chmod(0o755)
        (self.repo / "paper_reader_agent.py").write_text(
            "raise AssertionError('The real backend must not run in launcher tests.')\n",
            encoding="utf-8",
        )
        self.run_log = self.root / "run.bin"
        self.check_log = self.root / "check.bin"
        self.env = {
            "PATH": str(self.bin),
            "HOME": str(self.root / "home"),
            "LAUNCHER_RUN_LOG": str(self.run_log),
            "LAUNCHER_CHECK_LOG": str(self.check_log),
        }

    def fake_python(self, path: Path | None = None, *, version: str = "") -> Path:
        path = path or self.bin / "python3"
        path.parent.mkdir(parents=True, exist_ok=True)
        version_check = (
            "import sys\n"
            "if sys.argv[1]:\n"
            "    sys.version = sys.argv[1] + ' (synthetic launcher test)'\n"
            "    sys.version_info = tuple(map(int, sys.argv[1].split('.'))) + ('final', 0)\n"
            "exec(sys.argv[2])\n"
        )
        source = (
            "#!/bin/sh\n"
            'if [ "${1-}" = "-c" ]; then\n'
            '    printf \'%s\\000\' "$0" "$PWD" "$$" "${PAPER_READER_WORKSPACE-}" "$@" > "$LAUNCHER_CHECK_LOG"\n'
            '    if [ -n "${LAUNCHER_CHECK_EXIT-}" ]; then exit "$LAUNCHER_CHECK_EXIT"; fi\n'
            f"    exec {shlex.quote(sys.executable)} -I -S -c {shlex.quote(version_check)} "
            f'{shlex.quote(version)} "$2"\n'
            "fi\n"
            'printf \'%s\\000\' "$0" "$PWD" "$$" "${PAPER_READER_WORKSPACE-}" "$@" > "$LAUNCHER_RUN_LOG"\n'
            'printf \'%s\' "${LAUNCHER_STDOUT-}"\n'
            'printf \'%s\' "${LAUNCHER_STDERR-}" >&2\n'
            'exit "${LAUNCHER_EXIT-0}"\n'
        )
        path.write_text(source, encoding="utf-8", newline="\n")
        path.chmod(0o755)
        return path

    def launch(self, *arguments: str, **environment: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [POSIX_SHELL, str(self.launcher), *arguments],
            cwd=self.caller,
            env={**self.env, **environment},
            capture_output=True,
            encoding="utf-8",
            timeout=10,
            check=False,
        )

    def record(self, path: Path | None = None) -> dict:
        fields = (path or self.run_log).read_bytes().split(b"\0")
        self.assertEqual(fields.pop(), b"")
        executable, cwd, pid, workspace, *argv = [value.decode("utf-8") for value in fields]
        return {"executable": executable, "cwd": cwd, "pid": int(pid), "workspace": workspace, "argv": argv}

    def assert_not_launched(self) -> None:
        self.assertFalse(self.run_log.exists())

    def test_posix_shell_syntax(self) -> None:
        result = subprocess.run(
            [POSIX_SHELL, "-n", str(self.launcher)],
            capture_output=True,
            encoding="utf-8",
            timeout=10,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_python3_defaults_and_repository_cwd(self) -> None:
        python = self.fake_python()
        result = self.launch()
        self.assertEqual(result.returncode, 0, result.stderr)
        record = self.record()
        self.assertEqual(record["executable"], str(python))
        self.assertEqual(record["cwd"], str(self.repo.resolve()))
        self.assertEqual(
            record["argv"],
            [str(self.repo / "paper_reader_agent.py"), "serve", "--host", "127.0.0.1", "--port", "8765", "--open"],
        )
        self.assertEqual(self.record(self.check_log)["argv"][0], "-c")

    def test_repository_venv_precedes_path_python(self) -> None:
        self.fake_python()
        venv = self.fake_python(self.repo / ".venv" / "bin" / "python")
        result = self.launch()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.record()["executable"], str(venv))

    def test_explicit_python_precedes_venv_and_path(self) -> None:
        self.fake_python()
        self.fake_python(self.repo / ".venv" / "bin" / "python")
        selected = self.fake_python(self.root / "custom 解释器's python")
        result = self.launch(PAPER_READER_PYTHON=str(selected))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.record()["executable"], str(selected))

    def test_missing_python_has_actionable_failure(self) -> None:
        workspace = self.root / "absent disk" / "library"
        result = self.launch("--workspace", str(workspace))
        self.assertEqual(result.returncode, 127)
        self.assertIn("Python 3.10+", result.stderr)
        self.assertIn("PAPER_READER_PYTHON", result.stderr)
        self.assertIn(".venv", result.stderr)
        self.assertFalse(workspace.exists())
        self.assert_not_launched()

    def test_missing_explicit_python_does_not_fall_back(self) -> None:
        self.fake_python()
        selected = self.root / "missing interpreter"
        result = self.launch(PAPER_READER_PYTHON=str(selected))
        self.assertEqual(result.returncode, 127)
        self.assertIn(str(selected), result.stderr)
        self.assert_not_launched()

    def test_python_override_is_not_a_shell_command(self) -> None:
        python = self.fake_python()
        marker = self.root / "override-was-evaluated"
        result = self.launch(PAPER_READER_PYTHON=f"{python}; printf unsafe > {shlex.quote(str(marker))}")
        self.assertEqual(result.returncode, 127)
        self.assertFalse(marker.exists())
        self.assert_not_launched()

    def test_old_selected_python_is_rejected_without_fallback(self) -> None:
        self.fake_python()
        self.fake_python(self.repo / ".venv" / "bin" / "python", version="3.9.23")
        result = self.launch()
        self.assertEqual(result.returncode, 1)
        self.assertIn("3.10+", result.stderr)
        self.assertIn("3.9.23", result.stderr)
        self.assert_not_launched()

    def test_python_310_boundary_is_accepted(self) -> None:
        self.fake_python(version="3.10.0")
        result = self.launch()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(self.run_log.exists())

    def test_broken_interpreter_check_preserves_exit_code(self) -> None:
        self.fake_python()
        result = self.launch(LAUNCHER_CHECK_EXIT="42")
        self.assertEqual(result.returncode, 42)
        self.assertIn("Python check failed", result.stderr)
        self.assert_not_launched()

    def test_quoted_workspace_host_and_port_are_single_arguments(self) -> None:
        self.fake_python()
        marker = self.root / "workspace-was-evaluated"
        workspace = f'Paper 库 "quotes" $HOME; $(printf unsafe > {shlex.quote(str(marker))})'
        result = self.launch("--workspace", workspace, "--port", "9876", "--host", "::1", "--no-browser")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            self.record()["argv"],
            [str(self.repo / "paper_reader_agent.py"), "--workspace", workspace, "serve", "--host", "::1", "--port", "9876"],
        )
        self.assertFalse(marker.exists())

    def test_equals_options_and_no_browser_alias(self) -> None:
        self.fake_python()
        result = self.launch("--workspace=relative 论文 library", "--host=localhost", "--port=8766", "--no-open")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            self.record()["argv"],
            [str(self.repo / "paper_reader_agent.py"), "--workspace", "relative 论文 library", "serve",
             "--host", "localhost", "--port", "8766"],
        )

    def test_workspace_environment_is_left_to_backend(self) -> None:
        self.fake_python()
        workspace = str(self.root / "环境 library $HOME")
        result = self.launch(PAPER_READER_WORKSPACE=workspace)
        self.assertEqual(result.returncode, 0, result.stderr)
        record = self.record()
        self.assertEqual(record["workspace"], workspace)
        self.assertNotIn("--workspace", record["argv"])

    def test_dotenv_is_not_sourced_or_used_to_select_python(self) -> None:
        self.fake_python()
        marker = self.root / "dotenv-was-sourced"
        (self.repo / ".env").write_text(
            f"printf unsafe > {shlex.quote(str(marker))}\n"
            "PAPER_READER_PYTHON=/not/an/interpreter\nexit 73\n",
            encoding="utf-8",
        )
        result = self.launch()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(marker.exists())

    def test_no_browser_or_port_probe_is_run_by_shell(self) -> None:
        self.fake_python()
        marker = self.root / "external-command-was-run"
        for name in ("open", "xdg-open", "curl", "wget", "nc"):
            path = self.bin / name
            path.write_text(f"#!/bin/sh\nprintf unsafe > {shlex.quote(str(marker))}\n", encoding="utf-8")
            path.chmod(0o755)
        result = self.launch()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--open", self.record()["argv"])
        self.assertFalse(marker.exists())

    def test_help_does_not_need_python(self) -> None:
        result = self.launch("--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--no-browser", result.stdout)
        self.assertIn("initialized", result.stdout)
        self.assert_not_launched()

    def test_bad_arguments_fail_before_python_or_workspace_access(self) -> None:
        for arguments in (
            ("--unknown",), ("serve",), ("--workspace",), ("--host",), ("--port",),
            ("--workspace", ""), ("--workspace", "--no-browser"), ("--port=",),
        ):
            with self.subTest(arguments=arguments):
                result = self.launch(*arguments)
                self.assertEqual(result.returncode, 2)
                self.assertTrue(result.stderr)
                self.assertFalse(self.check_log.exists())
                self.assert_not_launched()

    def test_backend_output_and_exit_codes_are_preserved(self) -> None:
        self.fake_python()
        for status in (0, 1, 7, 130, 143):
            with self.subTest(status=status):
                result = self.launch(LAUNCHER_EXIT=str(status), LAUNCHER_STDOUT="reader stdout", LAUNCHER_STDERR="reader stderr")
                self.assertEqual(result.returncode, status)
                self.assertEqual(result.stdout, "reader stdout")
                self.assertEqual(result.stderr, "reader stderr")

    def test_backend_replaces_foreground_shell(self) -> None:
        self.fake_python()
        with subprocess.Popen(
            [str(self.launcher), "--no-browser"],
            cwd=self.caller,
            env=self.env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ) as process:
            try:
                _, stderr = process.communicate(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.communicate()
                raise
            self.assertEqual(process.returncode, 0, stderr)
            self.assertEqual(self.record()["pid"], process.pid)


if __name__ == "__main__":
    unittest.main()
