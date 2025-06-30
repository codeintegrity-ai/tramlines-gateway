import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Simple singleton logger implementation
# ---------------------------------------------------------------------------


class _TramlinesLogger:
    def __init__(self) -> None:
        self.tramlines_home = Path.home() / ".tramlines"
        self.log_dir = self.tramlines_home / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / "tramlines.log"

    # ---------------------------------------------------------------------
    # Logging helpers
    # ---------------------------------------------------------------------

    def _write(self, level: str, message: str) -> None:  # noqa: D401
        """Compose and emit a single log line."""
        try:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            log_message = f"{timestamp} | {level} | {message}"

            # File output --------------------------------------------------
            with self.log_file.open("a") as fp:
                fp.write(log_message + "\n")

            # Stderr echo --------------------------------------------------
            print(log_message, file=sys.stderr)
        except Exception:  # pragma: no cover – never fail on logging
            print(message, file=sys.stderr)

    # Public helpers -------------------------------------------------------

    def debug(self, message: str) -> None:  # noqa: D401
        self._write("DEBUG", message)

    def info(self, message: str) -> None:  # noqa: D401
        self._write("INFO", message)

    def warning(self, message: str) -> None:  # noqa: D401
        self._write("WARNING", message)

    def error(self, message: str) -> None:  # noqa: D401
        self._write("ERROR", message)


# Export a single shared instance that the rest of the codebase can import.
logger = _TramlinesLogger()
