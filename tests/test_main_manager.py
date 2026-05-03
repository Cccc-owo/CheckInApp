from __future__ import annotations

import builtins
import io
import importlib.util
import types
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

MAIN_PATH = Path(__file__).resolve().parents[1] / "main.py"
MAIN_SPEC = importlib.util.spec_from_file_location("main", MAIN_PATH)
assert MAIN_SPEC is not None and MAIN_SPEC.loader is not None
main = importlib.util.module_from_spec(MAIN_SPEC)
MAIN_SPEC.loader.exec_module(main)


class BackendManagerUvTests(unittest.TestCase):
    def test_backend_check_missing_dependency_points_to_uv_sync(self) -> None:
        original_import = builtins.__import__

        def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name == "backend.main":
                raise ModuleNotFoundError("No module named 'fastapi'", name="fastapi")
            return original_import(name, globals, locals, fromlist, level)

        args = types.SimpleNamespace(check=True)
        stderr = io.StringIO()

        with patch("builtins.__import__", side_effect=fake_import), redirect_stderr(stderr):
            exit_code = main.run_backend(args)

        self.assertEqual(exit_code, 2)
        self.assertIn("uv sync", stderr.getvalue())
        self.assertNotIn("pip install -r", stderr.getvalue())

    def test_backend_daemon_uses_uv_run_python(self) -> None:
        args = types.SimpleNamespace(host="127.0.0.1", port=8000, log_level="info")
        proc = Mock(pid=12345)

        with TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            with (
                patch.object(main, "BACKEND_PID", tmp / "backend.pid"),
                patch.object(main, "BACKEND_LOG", tmp / "backend.log"),
                patch.object(main, "LOGS_DIR", tmp),
                patch("subprocess.Popen", return_value=proc) as popen,
            ):
                exit_code = main.start_backend_daemon(args)

        self.assertEqual(exit_code, 0)
        cmd = popen.call_args.args[0]
        self.assertEqual(Path(cmd[0]).name, "uv")
        self.assertEqual(cmd[1:3], ["run", "python"])
        self.assertEqual(cmd[3:5], [str(main.REPO_ROOT / "main.py"), "backend"])


if __name__ == "__main__":
    unittest.main()
