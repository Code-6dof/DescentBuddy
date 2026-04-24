"""Launch and monitor the DXX-Redux game process."""

import os
import stat
import subprocess
import sys
from pathlib import Path


class GameLauncher:
    """Wraps a DXX-Redux executable and manages its subprocess lifecycle."""

    def __init__(self) -> None:
        self._process: subprocess.Popen | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def launch(self, executable_path: str, extra_args: list[str] | None = None) -> None:
        """Start the game process.

        Raises RuntimeError if the process is already running or the
        executable does not exist.
        """
        if self.is_running():
            raise RuntimeError("Game is already running.")

        path = Path(executable_path)
        if not path.is_file():
            raise FileNotFoundError(f"Executable not found: {executable_path}")

        # Ensure the file is executable (important for AppImage on Linux)
        if sys.platform != "win32":
            self._ensure_executable(path)

        env = os.environ.copy()
        if sys.platform != "win32" and path.suffix.lower() == ".appimage":
            env["APPIMAGE_EXTRACT_AND_RUN"] = "1"

        cmd = [str(path)] + (extra_args or [])
        self._process = subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
        )

    def stop(self) -> None:
        """Terminate the game process if it is running."""
        if self._process and self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
        self._process = None

    def is_running(self) -> bool:
        """Return True if the game process is currently alive."""
        if self._process is None:
            return False
        if self._process.poll() is not None:
            self._process = None
            return False
        return True

    def poll(self) -> int | None:
        """Return the exit code if the process has finished, else None."""
        if self._process is None:
            return None
        return self._process.poll()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _ensure_executable(path: Path) -> None:
        """Add executable permission bits to a file if missing."""
        current = path.stat().st_mode
        if not (current & stat.S_IXUSR):
            path.chmod(current | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
