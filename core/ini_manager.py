"""Reader and writer for the DXX-Redux command-line arguments INI file.

The file format is one argument per line. Active options start with a dash:
    -window
    -maxfps 200
Commented-out options start with a semicolon:
    ;-window
    ;-maxfps 200
Blank lines and lines that are plain text headings are left untouched.
"""

import re
from pathlib import Path

_OPTION_LINE = re.compile(r"^(;?\s*)-(\S+)(?:\s+(\S+))?")


class IniManager:
    def __init__(self, path: str) -> None:
        self.path = Path(path)

    def _read_lines(self) -> list[str]:
        if not self.path.exists():
            return []
        return self.path.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)

    def _write_lines(self, lines: list[str]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text("".join(lines), encoding="utf-8")

    def _find_flag_index(self, lines: list[str], flag: str) -> int:
        for index, line in enumerate(lines):
            match = _OPTION_LINE.match(line)
            if match and match.group(2) == flag:
                return index
        return -1

    def get_flag(self, flag: str) -> bool:
        """Returns True if the flag is present and not commented out."""
        lines = self._read_lines()
        index = self._find_flag_index(lines, flag)
        if index == -1:
            return False
        match = _OPTION_LINE.match(lines[index])
        return ";" not in match.group(1)

    def get_value(self, flag: str) -> str | None:
        """Returns the first token after an active flag, or None if missing or commented."""
        lines = self._read_lines()
        index = self._find_flag_index(lines, flag)
        if index == -1:
            return None
        match = _OPTION_LINE.match(lines[index])
        if ";" in match.group(1):
            return None
        return match.group(3)

    def set_flag(self, flag: str, enabled: bool) -> None:
        """Enable or disable a boolean flag (no value)."""
        lines = self._read_lines()
        index = self._find_flag_index(lines, flag)
        if index != -1:
            lines[index] = f"-{flag}\n" if enabled else f";-{flag}\n"
        elif enabled:
            lines.append(f"-{flag}\n")
        self._write_lines(lines)

    def set_value(self, flag: str, value: str) -> None:
        """Write an active flag with a value, adding it if not already present."""
        lines = self._read_lines()
        index = self._find_flag_index(lines, flag)
        if index != -1:
            lines[index] = f"-{flag} {value}\n"
        else:
            lines.append(f"-{flag} {value}\n")
        self._write_lines(lines)

    def remove_flag(self, flag: str) -> None:
        """Remove the flag line entirely, whether active or commented."""
        lines = self._read_lines()
        index = self._find_flag_index(lines, flag)
        if index != -1:
            lines.pop(index)
        self._write_lines(lines)
