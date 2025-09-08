#!/usr/bin/env python3
"""
Simple Network Troubleshooter

Tasks implemented:
- Task 1: argparse for -n/--no-ping, -q/--quiet, and -p/--ping (repeatable)
- Task 2: Local IP, DNS server list, Public IP
- Task 3: ICMP "ping" with scapy (default DNS, public DNS, and user-specified)
- Graceful fallbacks & clear messages when dependencies/permissions are missing

Notes on flags (matching the assignment examples):
- Default behavior: print network info (local IP, DNS, public IP) AND ping default+public DNS.
- -n/--no-ping : print ONLY the network info. No pings are performed (takes precedence over -q).
- -q/--quiet   : suppress network info; DO show ping results (default DNS + public 8.8.8.8 + any -p).
- -p/--ping    : may be used multiple times; each adds one target (IP or domain).

The script avoids exiting with errors if scapy/permissions are missing; it prints informative statuses.
"""

from __future__ import annotations
import argparse
import socket
import sys
from typing import List, Optional, Tuple

# --- Optional deps: handle import errors gracefully ---
SCAPY_AVAILABLE = True
try:
    from scapy.all import sr1, conf  # type: ignore
    from scapy.layers.inet import IP, ICMP  # type: ignore
    from scapy.layers.inet6 import IPv6, ICMPv6EchoRequest, ICMPv6EchoReply  # type: ignore
    conf.verb = 0  # silence scapy
except Exception:
    SCAPY_AVAILABLE = False

DNSPYTHON_AVAILABLE = True
try:
    import dns.resolver  # type: ignore
except Exception:
    DNSPYTHON_AVAILABLE = False

REQUESTS_AVAILABLE = True
try:
    import requests  # type: ignore
except Exception:
    REQUESTS_AVAILABLE = False


WELCOME = "Welcome to the python network troubleshooter!"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="ca.py",
        add_help=True,
        formatter_class=argparse.RawTextHelpFormatter,
        description="Network troubleshooting helper using Python + Scapy."
    )
    parser.add_argument(
        "-n", "--no-ping",
        action="store_true",
        help="just outputs the network information"
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="only output the results of pinging (suppresses network info)"
    )
    parser.add_argument(
        "-p", "--ping",
        action="append",
        metavar="address",
        help="list of addresses to ping (may be specified multiple times)"
    )
    return parser.parse_args()


# --------------------------
# Task 2: Network Information
# --------------------------

def get_local_ip(target_ip: str = "8.8.8.8", target_port: int = 80) -> Optional[str]:
    """
    Get local/private IPv4 address by connecting a non-blocking UDP socket
    to a well-known public address, then reading the local socket name.
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.0)  # non-blocking
        s.connect((target_ip, target_port))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return None


def get_dns_servers() -> List[str]:
    """
    Use dnspython to get system resolver nameservers.
    """
    if not DNSPYTHON_AVAILABLE:
        return []
    try:
        r = dns.resolver.Resolver()
        # r.nameservers is a list of IPs (v4 or v6)
        return [str(ns) for ns in r.nameservers]
    except Exception:
        return []


def get_public_ip(timeout: float = 3.0) -> Optional[str]:
    """
    Try a few services; prefer JSON ipify first.
    """
    if not REQUESTS_AVAILABLE:
        return None

    endpoints = [
        ("https://api.ipify.org?format=json", "json"),
        ("https://api64.ipify.org?format=json", "json"),
        ("https://ifconfig.me/ip", "text"),
    ]
    for url, kind in endpoints:
        try:
            r = requests.get(url, timeout=timeout)
            r.raise_for_status()
            if kind == "json":
                data = r.json()
                ip = data.get("ip")
                if ip:
                    return ip.strip()
            else:
                return r.text.strip()
        except Exception:
            continue
    return None


# --------------------------
# Task 3: ICMP Pinging w/Scapy
# --------------------------

def _is_ipv6(addr: str) -> bool:
    return ":" in addr


def _resolve_target(target: str) -> Tuple[str, Optional[str]]:
    """
    Resolve a hostname to an IPv4 address if possible for printing like:
      host 1.2.3.4: OK
    If it's already an IP literal, return (target, target).
    If resolution fails, return (target, None).
    """
    # If it's literal IPv4
    try:
        socket.inet_aton(target)
        return target, target
    except OSError:
        pass

    # IPv6 literal?
    try:
        socket.inet_pton(socket.AF_INET6, target)
        return target, target
    except OSError:
        pass

    # Hostname resolution (prefer IPv4 to match example style)
    try:
        ip = socket.gethostbyname(target)
        return target, ip
    except Exception:
        return target, None


def scapy_ping_once(dst: str, timeout: float = 1.0) -> str:
    """
    Return status string: OK | FAILED | NO_SCAPY | NO_PERM | RESOLVE_FAIL | ERROR
    """
    if not SCAPY_AVAILABLE:
        return "NO_SCAPY"

    name, ip = _resolve_target(dst)
    if ip is None:
        return "RESOLVE_FAIL"

    try:
        if _is_ipv6(ip):
            pkt = IPv6(dst=ip) / ICMPv6EchoRequest()
            ans = sr1(pkt, timeout=timeout)
            if ans is not None and ans.haslayer(ICMPv6EchoReply):
                return "OK"
            return "FAILED"
        else:
            pkt = IP(dst=ip) / ICMP()
            ans = sr1(pkt, timeout=timeout)
            # ICMP Echo Reply is type 0 in IPv4
            if ans is not None and ans.haslayer(ICMP) and int(ans.getlayer(ICMP).type) == 0:
                return "OK"
            return "FAILED"
    except PermissionError:
        # raw socket not permitted
        return "NO_PERM"
    except OSError as e:
        # e.g., Operation not permitted
        if "Operation not permitted" in str(e):
            return "NO_PERM"
        return "ERROR"
    except Exception:
        return "ERROR"


def print_network_info():
    local_ip = get_local_ip()
    dns_list = get_dns_servers()
    public_ip = get_public_ip()

    print()
    if local_ip:
        print(f"Local IP Address: {local_ip}")
    else:
        print("Local IP Address: <could not determine>")

    if dns_list:
        print(f"DNS Server(s): {', '.join(dns_list)}")
    else:
        if not DNSPYTHON_AVAILABLE:
            print("DNS Server(s): <dnspython not installed>")
        else:
            print("DNS Server(s): <could not determine>")

    if public_ip:
        print(f"Public IP Address: {public_ip}")
    else:
        if not REQUESTS_AVAILABLE:
            print("Public IP Address: <requests not installed>")
        else:
            print("Public IP Address: <could not determine>")


def print_pings(user_targets: Optional[List[str]], dns_list: List[str]):
    print()
    print("Pinging ...")

    # default DNS servers
    if dns_list:
        for ns in dns_list:
            status = scapy_ping_once(ns)
            print(f"default DNS Server {ns}: {status}")
    else:
        print("default DNS Server <none found>: SKIPPED")

    # public DNS server (example uses Google 8.8.8.8)
    public_dns = "8.8.8.8"
    status = scapy_ping_once(public_dns)
    print(f"public DNS Server {public_dns}: {status}")

    # user-provided targets
    if user_targets:
        for t in user_targets:
            name, ip = _resolve_target(t)
            status = scapy_ping_once(t)
            # Match example style: "host ip: OK" if we resolved a name
            if ip and name != ip:
                print(f"{name} {ip}: {status}")
            else:
                print(f"{name}: {status}")


def main():
    args = parse_args()
    print()
    print(WELCOME)

    # Gather DNS list once for reuse
    dns_list = get_dns_servers()

    if args.no_ping:
        # Only network info, no pings (takes precedence over -q)
        print_network_info()
        return 0

    if not args.quiet:
        # Default: show network info first
        print_network_info()

    # Then pings (default DNS + public DNS + user targets)
    print_pings(args.ping or [], dns_list)

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)

