import os
import shutil
import signal
import socket
import subprocess
from pathlib import Path

from ..config import settings


def _find_free_port(start: int = 8001, end: int = 9000) -> int:
    for port in range(start, end):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    raise RuntimeError("No free port found")


def _detect_entry_command(config_path: str, port: int) -> str:
    path = Path(config_path)
    python = shutil.which("python") or "python"
    if path.is_file() and path.suffix == ".py":
        return f"{python} {path}"
    if path.is_dir():
        if (path / "langgraph.json").exists():
            langgraph = shutil.which("langgraph") or "langgraph"
            return f"{langgraph} dev --port {port} --host 127.0.0.1"
        if (path / "main.py").exists():
            return f"{python} {path / 'main.py'}"
        if (path / "app.py").exists():
            uvicorn = shutil.which("uvicorn") or "uvicorn"
            return f"{uvicorn} app:app --port {port} --host 127.0.0.1"
    raise ValueError(f"Cannot detect entry point for {config_path}")


def _logs_dir() -> Path:
    d = Path(settings.deployment_logs_dir)
    d.mkdir(parents=True, exist_ok=True)
    return d


class LocalDeploymentManager:
    def start(self, deployment) -> None:
        if deployment.port is None:
            deployment.port = _find_free_port()

        cmd = deployment.command or _detect_entry_command(deployment.config_path, deployment.port)
        deployment.command = cmd

        env = os.environ.copy()
        env.update(deployment.env_vars or {})
        env["LANGSMITH_ENDPOINT"] = f"http://127.0.0.1:{settings.port}/api/v1"
        env["LANGSMITH_API_KEY"] = settings.api_key
        env["PORT"] = str(deployment.port)

        log_file = _logs_dir() / f"{deployment.id}.log"
        cwd = str(deployment.config_path) if Path(deployment.config_path).is_dir() else None

        with open(log_file, "a") as f:
            proc = subprocess.Popen(
                cmd,
                shell=True,
                stdout=f,
                stderr=subprocess.STDOUT,
                cwd=cwd,
                env=env,
                preexec_fn=os.setsid,
            )

        deployment.pid = proc.pid
        deployment.status = "running"
        deployment.container_url = f"http://127.0.0.1:{deployment.port}"

    def stop(self, deployment) -> None:
        if deployment.pid:
            try:
                os.killpg(os.getpgid(deployment.pid), signal.SIGTERM)
            except ProcessLookupError:
                pass
            deployment.pid = None
        deployment.status = "stopped"
        deployment.container_url = None

    def get_status(self, deployment) -> str:
        if deployment.pid is None:
            return deployment.status
        try:
            os.kill(deployment.pid, 0)
            return "running"
        except ProcessLookupError:
            return "stopped"

    def get_logs(self, deployment_id) -> str:
        log_file = _logs_dir() / f"{deployment_id}.log"
        if not log_file.exists():
            return ""
        return log_file.read_text()
