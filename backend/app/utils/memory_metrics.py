# Log the backend process's memory at each start-up stage (numbers only, never
# any content), so it is clear where memory goes.

import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

_PROC_STATUS = "/proc/self/status"
# /proc/self/status field -> output name: current, peak, swapped out
_FIELDS = {"VmRSS": "rss_mb", "VmHWM": "peak_mb", "VmSwap": "swap_mb"}


def read_memory_snapshot(path: str = _PROC_STATUS) -> Dict[str, Optional[float]]:
    """Current process memory in MB. On non-Linux systems or read errors every value is None; never raises."""
    snapshot: Dict[str, Optional[float]] = {name: None for name in _FIELDS.values()}
    try:
        with open(path, encoding="ascii", errors="ignore") as handle:
            for line in handle:
                key, _, rest = line.partition(":")
                name = _FIELDS.get(key)
                if not name:
                    continue
                parts = rest.split()
                if parts and parts[0].isdigit():
                    snapshot[name] = round(int(parts[0]) / 1024, 1)  # kB -> MB
    except OSError:
        pass
    return snapshot


def log_memory(stage: str) -> Dict[str, Optional[float]]:
    """Write one log line with the memory numbers for this stage; return them for tests."""
    snapshot = read_memory_snapshot()
    values = " ".join(
        f"{name}={value if value is not None else 'unavailable'}"
        for name, value in snapshot.items()
    )
    logger.info(f"[memory] stage={stage} {values}")
    return snapshot
