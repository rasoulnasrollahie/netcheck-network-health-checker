# netcheck - Simple Network Health Checker

A small command-line tool I wrote in Python to check whether network services are reachable and how fast they respond. I built it to practice networking fundamentals (DNS, TCP handshakes, latency, packet loss) and to have a lightweight tool for monitoring services without installing heavy software.

## What it does

For every target in a CSV file, `netcheck`:

1. resolves the hostname with DNS,
2. opens several TCP connections to the given port,
3. measures the connection time (average, min, max) and the loss rate,
4. prints a status table (`UP`, `SLOW`, `DOWN`, `DNS_FAIL`),
5. appends the results to a CSV log so I can compare runs over time.

The exit code is `0` when everything is reachable and `1` when at least one target is down, so the tool can be used in scripts and scheduled jobs.

## Requirements

- Python 3.8 or newer
- No external packages (standard library only)

## Usage

```bash
python netcheck.py
python netcheck.py --hosts hosts.csv --attempts 5 --timeout 1.5 --slow 100
python netcheck.py --no-log
```

| Option       | Default            | Description                                   |
|--------------|--------------------|-----------------------------------------------|
| `--hosts`    | `hosts.csv`        | CSV file with the columns `name,host,port`    |
| `--attempts` | `3`                | TCP connection attempts per target            |
| `--timeout`  | `2.0`              | Timeout per attempt in seconds                |
| `--slow`     | `150`              | Average latency (ms) above which a target is `SLOW` |
| `--log`      | `netcheck_log.csv` | Log file                                      |
| `--no-log`   | off                | Do not write a log file                       |

## Example output

```text
NAME                 HOST                    PORT STATUS      AVG ms  LOSS %
----------------------------------------------------------------------------
GitHub HTTPS         github.com               443 UP            18.4       0
Debian HTTPS         www.debian.org           443 UP            22.9       0
Localhost SSH        127.0.0.1                 22 DOWN                   100

Checked 3 targets: 2 reachable, 1 unreachable.
```

## Adding your own targets

Edit `hosts.csv`. Lines starting with `#` are ignored. The file already contains commented examples for industrial protocols (Modbus TCP on port 502 and OPC UA on port 4840), because I come from an industrial automation background and wanted the tool to be useful for OT networks as well.

## Running the tests

```bash
python -m unittest -v
```

The tests start a small local TCP server, so they work without internet access.

## Notes and limitations

- It measures TCP connect time, not ICMP ping (ICMP needs elevated privileges on many systems).
- Only IPv4 is resolved at the moment.
- Targets are checked one after another. A possible improvement is checking them in parallel with `concurrent.futures`.
- Use it only on systems you own or are allowed to test.

## Ideas for the next version

- Parallel checks with a thread pool
- IPv6 support
- Alerts by e-mail or webhook when a target goes down
- A small chart of latency over time from the CSV log

## Author

Rasoul Nasrollahi
