"""Kill processes listening on a TCP port (Windows)."""
from __future__ import annotations

import re
import subprocess
import sys


def pids_on_port(port: int) -> list[int]:
    result = subprocess.run(
        ["netstat", "-ano"],
        capture_output=True,
        text=True,
        check=False,
    )
    pids: set[int] = set()
    pattern = re.compile(rf"127\.0\.0\.1:{port}\s+.*LISTENING\s+(\d+)")
    for line in result.stdout.splitlines():
        match = pattern.search(line)
        if match:
            pids.add(int(match.group(1)))
    return sorted(pids)


def kill_pids(pids: list[int]) -> None:
    for pid in pids:
        proc = subprocess.run(
            ["taskkill", "/PID", str(pid), "/F"],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode == 0:
            print(f"Durduruldu PID={pid}")
        else:
            print(f"PID={pid} durdurulamadi: {proc.stderr.strip() or proc.stdout.strip()}")


def main() -> None:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    pids = pids_on_port(port)
    if not pids:
        print(f"Port {port} bos.")
        return
    print(f"Port {port} dinleyen: {pids}")
    kill_pids(pids)


if __name__ == "__main__":
    main()
