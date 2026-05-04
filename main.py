#!/usr/bin/env python3
"""Cross-platform project manager for CheckIn App."""

from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent
APPS_DIR = REPO_ROOT / "apps"
BACKEND_DIR = APPS_DIR / "backend"
FRONTEND_DIR = APPS_DIR / "frontend"
UV_BIN = os.environ.get("UV", "uv")
BACKEND_PID = REPO_ROOT / "backend.pid"
FRONTEND_PID = REPO_ROOT / "frontend.pid"
LOGS_DIR = REPO_ROOT / "logs"
BACKEND_LOG = LOGS_DIR / "backend.log"
FRONTEND_LOG = LOGS_DIR / "frontend.log"

BACKEND_PORT = 8000
FRONTEND_PORT = 3000


def ensure_import_path() -> None:
    apps_path = str(APPS_DIR)
    if apps_path not in sys.path:
        sys.path.insert(0, apps_path)
    os.chdir(REPO_ROOT)


def ensure_runtime_dirs() -> None:
    for path in (REPO_ROOT / "data", LOGS_DIR, REPO_ROOT / "sessions"):
        path.mkdir(parents=True, exist_ok=True)


def get_python() -> str:
    return sys.executable


def backend_manager_command(*args: str) -> list[str]:
    return [UV_BIN, "run", "python", str(REPO_ROOT / "main.py"), *args]


def read_pid(path: Path) -> int | None:
    try:
        return int(path.read_text(encoding="utf-8").strip())
    except (FileNotFoundError, ValueError):
        return None


def is_process_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def stop_pid_file(path: Path, name: str) -> bool:
    pid = read_pid(path)
    if pid is None:
        print(f"{name}: not running")
        return False
    if not is_process_alive(pid):
        path.unlink(missing_ok=True)
        print(f"{name}: stale pid removed")
        return False
    sig = signal.CTRL_BREAK_EVENT if os.name == "nt" else signal.SIGTERM
    os.kill(pid, sig)
    path.unlink(missing_ok=True)
    print(f"{name}: stopped pid {pid}")
    return True


def backend_env() -> dict[str, str]:
    env = os.environ.copy()
    existing = env.get("PYTHONPATH")
    apps_path = str(APPS_DIR)
    env["PYTHONPATH"] = apps_path if not existing else os.pathsep.join([apps_path, existing])
    return env


def run_backend(args: argparse.Namespace) -> int:
    ensure_import_path()
    ensure_runtime_dirs()
    if args.check:
        try:
            import backend.main  # noqa: F401
        except ModuleNotFoundError as exc:
            print(f"backend import path OK; missing dependency: {exc.name}", file=sys.stderr)
            print("install dependencies with: uv sync", file=sys.stderr)
            return 2
        print("backend.main:app import OK")
        return 0

    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        reload_dirs=[str(BACKEND_DIR)] if args.reload else None,
        log_level=args.log_level,
        access_log=True,
    )
    return 0


def run_backend_migrations(_: argparse.Namespace) -> int:
    ensure_import_path()
    from backend.scripts.run_migrations import main as run_migrations_main

    return run_migrations_main()


def start_backend_daemon(args: argparse.Namespace) -> int:
    ensure_runtime_dirs()
    if BACKEND_PID.exists():
        pid = read_pid(BACKEND_PID)
        if pid is not None and is_process_alive(pid):
            print(f"backend: already running pid {pid}")
            return 0
        BACKEND_PID.unlink(missing_ok=True)

    cmd = backend_manager_command(
        "backend",
        "--host",
        args.host,
        "--port",
        str(args.port),
        "--no-reload",
        "--log-level",
        args.log_level,
    )
    BACKEND_LOG.parent.mkdir(parents=True, exist_ok=True)
    log_file = BACKEND_LOG.open("a", encoding="utf-8")
    try:
        proc = subprocess.Popen(
            cmd,
            cwd=REPO_ROOT,
            env=backend_env(),
            stdout=log_file,
            stderr=subprocess.STDOUT,
            start_new_session=os.name != "nt",
        )
    except FileNotFoundError:
        print("uv executable not found; install uv and run: uv sync", file=sys.stderr)
        return 1
    BACKEND_PID.write_text(str(proc.pid), encoding="utf-8")
    print(f"backend: started pid {proc.pid}")
    print(f"log: {BACKEND_LOG}")
    return 0


def frontend_env() -> dict[str, str]:
    return os.environ.copy()


def run_frontend(args: argparse.Namespace) -> int:
    if not FRONTEND_DIR.exists():
        print(f"frontend directory not found: {FRONTEND_DIR}", file=sys.stderr)
        return 1
    cmd = ["pnpm", "dev", "--host", args.host, "--port", str(args.port)]
    return subprocess.call(cmd, cwd=FRONTEND_DIR, env=frontend_env())


def start_frontend_daemon(args: argparse.Namespace) -> int:
    if FRONTEND_PID.exists():
        pid = read_pid(FRONTEND_PID)
        if pid is not None and is_process_alive(pid):
            print(f"frontend: already running pid {pid}")
            return 0
        FRONTEND_PID.unlink(missing_ok=True)

    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = FRONTEND_LOG.open("a", encoding="utf-8")
    cmd = [
        get_python(),
        str(REPO_ROOT / "main.py"),
        "frontend",
        "--host",
        args.host,
        "--port",
        str(args.port),
    ]
    proc = subprocess.Popen(
        cmd,
        cwd=REPO_ROOT,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        start_new_session=os.name != "nt",
    )
    FRONTEND_PID.write_text(str(proc.pid), encoding="utf-8")
    print(f"frontend: started pid {proc.pid}")
    print(f"log: {FRONTEND_LOG}")
    return 0


def build_frontend(args: argparse.Namespace) -> int:
    if not FRONTEND_DIR.exists():
        print(f"frontend directory not found: {FRONTEND_DIR}", file=sys.stderr)
        return 1
    if args.install and not (FRONTEND_DIR / "node_modules").exists():
        result = subprocess.call(["pnpm", "install"], cwd=FRONTEND_DIR)
        if result != 0:
            return result
    return subprocess.call(["pnpm", "build"], cwd=FRONTEND_DIR)


def deploy_frontend(args: argparse.Namespace) -> int:
    dist = FRONTEND_DIR / "dist"
    if not dist.exists():
        print(f"build output not found: {dist}", file=sys.stderr)
        print("run: python main.py frontend-build", file=sys.stderr)
        return 1
    print(f"frontend build output ready: {dist}")
    print("copy this directory to the web server root configured by nginx")
    return 0


def status(_: argparse.Namespace) -> int:
    for name, pid_file, log_file in (
        ("backend", BACKEND_PID, BACKEND_LOG),
        ("frontend", FRONTEND_PID, FRONTEND_LOG),
    ):
        pid = read_pid(pid_file)
        running = pid is not None and is_process_alive(pid)
        state = "RUNNING" if running else "NOT RUNNING"
        print(f"{name}: {state}")
        if pid is not None:
            print(f"  pid: {pid}")
        print(f"  log: {log_file}")
    return 0


def stop(args: argparse.Namespace) -> int:
    stopped = False
    targets = ("backend", "frontend") if args.target == "all" else (args.target,)
    for target in targets:
        if target == "backend":
            stopped = stop_pid_file(BACKEND_PID, "backend") or stopped
        elif target == "frontend":
            stopped = stop_pid_file(FRONTEND_PID, "frontend") or stopped
    return 0 if stopped or args.target in {"backend", "frontend", "all"} else 1


def add_backend_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=BACKEND_PORT)
    parser.add_argument("--reload", dest="reload", action="store_true", default=True)
    parser.add_argument("--no-reload", dest="reload", action="store_false")
    parser.add_argument("--log-level", default="info")
    parser.add_argument("--check", action="store_true", help="only verify backend.main:app imports")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CheckIn App project manager")
    sub = parser.add_subparsers(dest="command", required=True)

    backend = sub.add_parser("backend", help="run backend in the foreground")
    add_backend_args(backend)
    backend.set_defaults(func=run_backend)

    backend_migrate = sub.add_parser("backend-migrate", help="run backend database migrations")
    backend_migrate.set_defaults(func=run_backend_migrations)

    backend_daemon = sub.add_parser("backend-daemon", help="start backend in the background")
    backend_daemon.add_argument("--host", default="0.0.0.0")
    backend_daemon.add_argument("--port", type=int, default=BACKEND_PORT)
    backend_daemon.add_argument("--log-level", default="info")
    backend_daemon.set_defaults(func=start_backend_daemon)

    frontend = sub.add_parser("frontend", help="run frontend dev server in the foreground")
    frontend.add_argument("--host", default="0.0.0.0")
    frontend.add_argument("--port", type=int, default=FRONTEND_PORT)
    frontend.set_defaults(func=run_frontend)

    frontend_daemon = sub.add_parser(
        "frontend-daemon", help="start frontend dev server in the background"
    )
    frontend_daemon.add_argument("--host", default="0.0.0.0")
    frontend_daemon.add_argument("--port", type=int, default=FRONTEND_PORT)
    frontend_daemon.set_defaults(func=start_frontend_daemon)

    frontend_build = sub.add_parser("frontend-build", help="build frontend")
    frontend_build.add_argument(
        "--install", action="store_true", help="run pnpm install if node_modules is missing"
    )
    frontend_build.set_defaults(func=build_frontend)

    deploy = sub.add_parser("frontend-deploy", help="show frontend deployment output path")
    deploy.set_defaults(func=deploy_frontend)

    service_status = sub.add_parser("status", help="show managed process status")
    service_status.set_defaults(func=status)

    service_stop = sub.add_parser("stop", help="stop managed daemon processes")
    service_stop.add_argument(
        "target", choices=["backend", "frontend", "all"], nargs="?", default="all"
    )
    service_stop.set_defaults(func=stop)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
