#!/usr/bin/env python3
"""
netcheck - a small network health checker.

For every target listed in a CSV file it:
  1. resolves the hostname (DNS),
  2. opens a few TCP connections to the given port,
  3. measures the connection latency,
  4. prints a status table and appends the results to a CSV log.

Only the Python standard library is used, so it runs on Windows, Linux and macOS.
Use it only on hosts you own or are allowed to test.
"""

import argparse
import csv
import socket
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path

LOG_FIELDS = ["timestamp", "name", "host", "port", "ip", "status",
              "avg_ms", "min_ms", "max_ms", "loss_pct"]


def load_targets(path):
    """Read targets from a CSV file with the columns: name,host,port."""
    targets = []
    with open(path, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            name = (row.get("name") or "").strip()
            if not name or name.startswith("#"):
                continue  # skip empty lines and commented-out lines
            targets.append({
                "name": name,
                "host": row["host"].strip(),
                "port": int(row["port"]),
            })
    return targets


def resolve(host):
    """Return the IPv4 address of a host, or None if DNS fails."""
    try:
        return socket.gethostbyname(host)
    except socket.gaierror:
        return None


def tcp_latency(ip, port, timeout):
    """Return the TCP connect time in milliseconds, or None on failure."""
    start = time.perf_counter()
    try:
        with socket.create_connection((ip, port), timeout=timeout):
            return (time.perf_counter() - start) * 1000
    except OSError:
        return None


def check_target(target, attempts, timeout, slow_ms):
    """Check one target and return a result dictionary."""
    result = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "name": target["name"],
        "host": target["host"],
        "port": target["port"],
        "ip": "",
        "status": "",
        "avg_ms": "",
        "min_ms": "",
        "max_ms": "",
        "loss_pct": 100,
    }

    ip = resolve(target["host"])
    if ip is None:
        result["status"] = "DNS_FAIL"
        return result
    result["ip"] = ip

    samples = [tcp_latency(ip, target["port"], timeout) for _ in range(attempts)]
    ok = [s for s in samples if s is not None]
    result["loss_pct"] = round(100 * (attempts - len(ok)) / attempts)

    if not ok:
        result["status"] = "DOWN"
        return result

    average = statistics.mean(ok)
    result["avg_ms"] = round(average, 1)
    result["min_ms"] = round(min(ok), 1)
    result["max_ms"] = round(max(ok), 1)
    result["status"] = "SLOW" if average > slow_ms else "UP"
    return result


def print_table(results):
    """Print the results as an aligned text table."""
    header = f"{'NAME':<20} {'HOST':<22} {'PORT':>5} {'STATUS':<9} {'AVG ms':>8} {'LOSS %':>7}"
    print(header)
    print("-" * len(header))
    for r in results:
        print(f"{r['name']:<20} {r['host']:<22} {r['port']:>5} "
              f"{r['status']:<9} {str(r['avg_ms']):>8} {r['loss_pct']:>7}")


def append_log(results, log_path):
    """Append results to a CSV log file (the header is written only once)."""
    path = Path(log_path)
    is_new = not path.exists()
    with open(path, "a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=LOG_FIELDS)
        if is_new:
            writer.writeheader()
        writer.writerows(results)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Simple TCP/DNS network health checker.")
    parser.add_argument("--hosts", default="hosts.csv", help="CSV file with targets (default: hosts.csv)")
    parser.add_argument("--attempts", type=int, default=3, help="connection attempts per target (default: 3)")
    parser.add_argument("--timeout", type=float, default=2.0, help="timeout per attempt in seconds (default: 2)")
    parser.add_argument("--slow", type=float, default=150.0, help="latency in ms above which a target is SLOW (default: 150)")
    parser.add_argument("--log", default="netcheck_log.csv", help="CSV log file (default: netcheck_log.csv)")
    parser.add_argument("--no-log", action="store_true", help="do not write a log file")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    try:
        targets = load_targets(args.hosts)
    except (OSError, KeyError, ValueError) as error:
        print(f"Could not read '{args.hosts}': {error}", file=sys.stderr)
        return 2

    results = [check_target(t, args.attempts, args.timeout, args.slow) for t in targets]
    print_table(results)

    down = [r for r in results if r["status"] in ("DOWN", "DNS_FAIL")]
    print(f"\nChecked {len(results)} targets: {len(results) - len(down)} reachable, {len(down)} unreachable.")

    if not args.no_log:
        append_log(results, args.log)
        print(f"Results appended to {args.log}")

    return 1 if down else 0  # non-zero exit code makes it usable in scripts


if __name__ == "__main__":
    sys.exit(main())
