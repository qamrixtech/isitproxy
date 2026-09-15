#!/usr/bin/env python3
"""
ISITPROXY v1.1 — Advanced Proxy Checker & Intelligence Tool
Made with <3 by Hayder
"""

import asyncio
import aiohttp
import requests
import json
import os
import sys
import time
import socket
import struct
import subprocess
import shutil
import warnings
import platform
import gc
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Tuple, Set

try:
    from aiohttp_socks import ProxyType, ProxyConnector
    HAS_AIOHTTP_SOCKS = True
except ImportError:
    HAS_AIOHTTP_SOCKS = False

try:
    import readchar
    HAS_READCHAR = True
except ImportError:
    HAS_READCHAR = False

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import (
    Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
)
from rich.text import Text
from rich.align import Align
from rich.rule import Rule
from rich import box
from rich.markup import escape
from rich.style import Style

warnings.filterwarnings("ignore")
console = Console()

VERSION = "1.1"


class SystemProfile:
    def __init__(self):
        self.os_name = platform.system()
        self.cpus = os.cpu_count() or 2
        self.ram_mb = self._get_ram_mb()
        self.optimal_conc = self._calc_optimal_conc()
        self.optimal_timeout = self._calc_optimal_timeout()

    def _get_ram_mb(self) -> int:
        try:
            if self.os_name == "Linux":
                with open("/proc/meminfo") as f:
                    for line in f:
                        if line.startswith("MemAvailable:"):
                            return int(line.split()[1]) // 1024
            elif self.os_name == "Darwin":
                out = subprocess.check_output(
                    ["sysctl", "-n", "hw.memsize"], timeout=2
                ).decode().strip()
                return int(out) // (1024 * 1024)
            elif self.os_name == "Windows":
                import ctypes
                kernel32 = ctypes.windll.kernel32
                c_ulonglong = ctypes.c_ulonglong
                class MEMORYSTATUSEX(ctypes.Structure):
                    _fields_ = [
                        ("dwLength", ctypes.c_ulong),
                        ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", c_ulonglong),
                        ("ullAvailPhys", c_ulonglong),
                        ("ullTotalPageFile", c_ulonglong),
                        ("ullAvailPageFile", c_ulonglong),
                        ("ullTotalVirtual", c_ulonglong),
                        ("ullAvailVirtual", c_ulonglong),
                        ("ullAvailExtendedVirtual", c_ulonglong),
                    ]
                    def __init__(self):
                        self.dwLength = ctypes.sizeof(self)
                mem = MEMORYSTATUSEX()
                kernel32.GlobalMemoryStatusEx(ctypes.byref(mem))
                return mem.ullAvailPhys // (1024 * 1024)
        except Exception:
            pass
        return 4096

    def _calc_optimal_conc(self) -> int:
        base = min(self.cpus * 25, 200)
        if self.ram_mb < 2048:
            base = min(base, 50)
        elif self.ram_mb < 4096:
            base = min(base, 100)
        elif self.ram_mb < 8192:
            base = min(base, 150)
        elif self.ram_mb > 32768:
            base = min(base + 100, 500)
        if self.os_name == "Windows":
            base = min(base, 150)
        return max(10, base)

    def _calc_optimal_timeout(self) -> float:
        if self.ram_mb < 2048:
            return 5.0
        elif self.cpus <= 2:
            return 6.0
        return 8.0

    def __str__(self):
        return (f"OS={self.os_name} CPUs={self.cpus} "
                f"RAM={self.ram_mb}MB Conc={self.optimal_conc} "
                f"Timeout={self.optimal_timeout}s")


SYS = SystemProfile()

CONFIG_FILE = Path("config.json")


def load_config() -> dict:
    defaults = {"output_dir": "proxies", "replace_after_check": False, "save_mode": "categorized"}
    if CONFIG_FILE.exists():
        try:
            cfg = json.loads(CONFIG_FILE.read_text())
            defaults.update(cfg)
            return defaults
        except Exception:
            pass
    return defaults


def save_config(cfg: dict):
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2))


C_ACCENT  = "bright_cyan"
C_GOLD    = "yellow"
C_GREEN   = "bright_green"
C_RED     = "bright_red"
C_BLUE    = "bright_blue"
C_MAGENTA = "bright_magenta"
C_DIM     = "grey50"
C_ORANGE  = "dark_orange"
C_WHITE   = "bright_white"

PROVIDERS_FILE = "providers.txt"
PROXY_FILE     = "proxy.txt"
PROXIES_DIR = Path(load_config().get("output_dir", "proxies"))
PROXYCHECK_URL = "https://proxycheck.io/v3/{ip}?vpn=1&asn=1&risk=1&port={port}"


def get_api_key() -> str:
    cfg = load_config()
    return cfg.get("proxycheck_key", os.environ.get("PROXYCHECK_KEY", ""))


def build_proxycheck_url(ip: str, port: int) -> str:
    base = PROXYCHECK_URL.format(ip=ip, port=port)
    key = get_api_key()
    if key:
        base += f"&key={key}"
    return base

DEFAULT_PROVIDERS = [
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt",
    "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
    "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt",
    "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-socks4.txt",
    "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-socks5.txt",
    "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=5000&country=all",
    "https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks4&timeout=5000&country=all",
    "https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks5&timeout=5000&country=all",
]

BANNER = r"""
  ██╗███████╗██╗████████╗██████╗ ██████╗  ██████╗ ██╗  ██╗██╗   ██╗
  ██║██╔════╝██║╚══██╔══╝██╔══██╗██╔══██╗██╔═══██╗╚██╗██╔╝╚██╗ ██╔╝
  ██║███████╗██║   ██║   ██████╔╝██████╔╝██║   ██║ ╚███╔╝  ╚████╔╝ 
  ██║╚════██║██║   ██║   ██╔═══╝ ██╔══██╗██║   ██║ ██╔██╗   ╚██╔╝  
  ██║███████║██║   ██║   ██║     ██║  ██║╚██████╔╝██╔╝ ██╗   ██║   
  ╚═╝╚══════╝╚═╝   ╚═╝   ╚═╝     ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝  
"""

BRAND_FOOTER = "Made with <3 by Hayder"


def ensure_dirs():
    PROXIES_DIR.mkdir(exist_ok=True)
    if not Path(PROXY_FILE).exists():
        Path(PROXY_FILE).write_text("# Add proxies here, one per line: ip:port\n")
    if not Path(PROVIDERS_FILE).exists():
        Path(PROVIDERS_FILE).write_text("\n".join(DEFAULT_PROVIDERS) + "\n")
    for fname in ["http.txt", "https.txt", "socks4.txt", "socks5.txt", "httpgoogle.txt"]:
        fpath = PROXIES_DIR / fname
        if not fpath.exists():
            fpath.write_text("")


def load_providers() -> List[str]:
    if not Path(PROVIDERS_FILE).exists():
        return list(DEFAULT_PROVIDERS)
    lines = Path(PROVIDERS_FILE).read_text().splitlines()
    return [l.strip() for l in lines if l.strip() and not l.startswith("#")]


def parse_proxies_from_text(text: str) -> List[str]:
    proxies = []
    for sep in (",", "|", ";"):
        text = text.replace(sep, "\n")
    for line in text.splitlines():
        line = line.strip()
        for prefix in ("socks5://", "socks4://", "http://", "https://"):
            if line.lower().startswith(prefix):
                line = line[len(prefix):]
        line = line.split("#")[0].strip()
        parts = line.split(":")
        if len(parts) == 2:
            host, port = parts
            if host and port.isdigit() and 1 <= int(port) <= 65535:
                proxies.append(f"{host}:{port}")
    return proxies


def load_local_proxies() -> List[str]:
    if not Path(PROXY_FILE).exists():
        return []
    return list(set(parse_proxies_from_text(Path(PROXY_FILE).read_text())))


def save_proxies_to_file(proxies: List[str]) -> int:
    existing = set(load_local_proxies())
    new = set(proxies) - existing
    if not new:
        return 0
    if Path(PROXY_FILE).exists():
        content = Path(PROXY_FILE).read_text()
        if content and not content.endswith("\n"):
            with open(PROXY_FILE, "a") as f:
                f.write("\n")
    with open(PROXY_FILE, "a") as f:
        for p in sorted(new):
            f.write(p + "\n")
    return len(new)


class ResultFileWriter:
    def __init__(self):
        self._cache: Dict[str, Set[str]] = {}
        for fname in ["http.txt", "https.txt", "socks4.txt", "socks5.txt", "httpgoogle.txt"]:
            path = PROXIES_DIR / fname
            if path.exists():
                self._cache[fname] = set(
                    l.strip() for l in path.read_text().splitlines() if l.strip()
                )
            else:
                self._cache[fname] = set()

    def append(self, fname: str, proxy: str) -> bool:
        if proxy in self._cache[fname]:
            return False
        self._cache[fname].add(proxy)
        with open(PROXIES_DIR / fname, "a") as f:
            f.write(proxy + "\n")
        return True

    def counts(self) -> Dict[str, int]:
        return {k: len(v) for k, v in self._cache.items()}


def batch_save(
    results: List[dict], fast_ms: int, writer: ResultFileWriter
) -> int:
    saved = 0
    for r in results:
        if r.get("status") != "online":
            continue
        lat = r.get("latency_ms", -1)
        if lat < 0 or lat >= fast_ms:
            continue
        pt = r.get("proxy_type", "").lower()
        proxy = r.get("proxy", "")
        google = r.get("google", False)
        if "socks5" in pt:
            fname = "socks5.txt"
        elif "socks4" in pt:
            fname = "socks4.txt"
        elif "https" in pt:
            fname = "https.txt"
        elif "http" in pt:
            fname = "http.txt"
        else:
            continue
        if writer.append(fname, proxy):
            saved += 1
        if google:
            writer.append("httpgoogle.txt", proxy)
    return saved


def write_categorized(results: List[dict]) -> Dict[str, int]:
    cats: Dict[str, Set[str]] = {
        "http.txt": set(), "https.txt": set(), "socks4.txt": set(),
        "socks5.txt": set(), "httpgoogle.txt": set(),
    }
    for r in results:
        if r.get("status") != "online":
            continue
        pt = r.get("proxy_type", "").lower()
        google = r.get("google", False)
        proxy = r.get("proxy", "")
        if "socks5" in pt:
            cats["socks5.txt"].add(proxy)
        elif "socks4" in pt:
            cats["socks4.txt"].add(proxy)
        elif "https" in pt:
            cats["https.txt"].add(proxy)
            if google:
                cats["httpgoogle.txt"].add(proxy)
        elif "http" in pt:
            cats["http.txt"].add(proxy)
            if google:
                cats["httpgoogle.txt"].add(proxy)
    for fname, pl in cats.items():
        path = PROXIES_DIR / fname
        path.write_text("\n".join(sorted(pl)) + ("\n" if pl else ""))
    return {k: len(v) for k, v in cats.items()}


def write_single(results: List[dict]) -> Dict[str, int]:
    all_proxies: Set[str] = set()
    for r in results:
        if r.get("status") == "online":
            all_proxies.add(r.get("proxy", ""))
    path = PROXIES_DIR / "all.txt"
    path.write_text("\n".join(sorted(all_proxies)) + ("\n" if all_proxies else ""))
    return {"all.txt": len(all_proxies)}


def count_result_files() -> Dict[str, int]:
    counts = {}
    for f in PROXIES_DIR.glob("*.txt"):
        lines = [l for l in f.read_text().splitlines() if l.strip()]
        counts[f.name] = len(lines)
    return counts


def anon_color(a: str) -> str:
    return {"elite": C_GREEN, "anonymous": C_BLUE, "transparent": C_ORANGE}.get(a, C_DIM)


def type_color(t: str) -> str:
    return {"socks5": C_MAGENTA, "socks4": C_BLUE, "https": C_GREEN, "http": C_ACCENT}.get(t.lower(), C_DIM)


def latency_color(ms: float) -> str:
    if ms < 0:
        return C_RED
    if ms < 300:
        return C_GREEN
    if ms < 800:
        return C_GOLD
    return C_RED


def latency_str(ms: float) -> str:
    if ms < 0:
        return "-"
    return f"{ms:.0f}ms"


def bool_icon(v: bool) -> str:
    return "Y" if v else "N"


def risk_color(r: int) -> str:
    if r < 33:
        return C_GREEN
    if r < 66:
        return C_GOLD
    return C_RED


def trunc(s: str, w: int) -> str:
    if len(s) > w:
        return s[: w - 1] + "\u2026"
    return s.ljust(w)


def get_columns(width: int) -> List[dict]:
    if width >= 160:
        return [
            {"k": "st",     "w": 2,  "l": ""},
            {"k": "proxy",  "w": 21, "l": "Proxy"},
            {"k": "type",   "w": 7,  "l": "Type"},
            {"k": "speed",  "w": 7,  "l": "Speed"},
            {"k": "anon",   "w": 11, "l": "Anonymity"},
            {"k": "country","w": 8,  "l": "Country"},
            {"k": "city",   "w": 10, "l": "City"},
            {"k": "google", "w": 3,  "l": "G"},
            {"k": "https",  "w": 3,  "l": "S"},
            {"k": "vpn",    "w": 3,  "l": "V"},
            {"k": "risk",   "w": 4,  "l": "Risk"},
            {"k": "isp",    "w": 20, "l": "ISP"},
            {"k": "asn",    "w": 8,  "l": "ASN"},
        ]
    if width >= 120:
        return [
            {"k": "st",     "w": 2,  "l": ""},
            {"k": "proxy",  "w": 21, "l": "Proxy"},
            {"k": "type",   "w": 7,  "l": "Type"},
            {"k": "speed",  "w": 7,  "l": "Speed"},
            {"k": "anon",   "w": 11, "l": "Anonymity"},
            {"k": "country","w": 8,  "l": "Country"},
            {"k": "google", "w": 3,  "l": "G"},
            {"k": "https",  "w": 3,  "l": "S"},
            {"k": "vpn",    "w": 3,  "l": "V"},
            {"k": "risk",   "w": 4,  "l": "Risk"},
        ]
    if width >= 80:
        return [
            {"k": "st",     "w": 2,  "l": ""},
            {"k": "proxy",  "w": 21, "l": "Proxy"},
            {"k": "type",   "w": 7,  "l": "Type"},
            {"k": "speed",  "w": 7,  "l": "Speed"},
            {"k": "country","w": 8,  "l": "Country"},
            {"k": "google", "w": 3,  "l": "G"},
            {"k": "risk",   "w": 4,  "l": "Risk"},
        ]
    return [
        {"k": "st",     "w": 2,  "l": ""},
        {"k": "proxy",  "w": 21, "l": "Proxy"},
        {"k": "type",   "w": 6,  "l": "Type"},
        {"k": "speed",  "w": 7,  "l": "Speed"},
        {"k": "risk",   "w": 3,  "l": "R"},
    ]


def render_fields(r: dict) -> dict:
    online = r["status"] == "online"
    pt = r.get("proxy_type", "unknown")
    lat = r.get("latency_ms", -1)
    country = r.get("country", "?")
    city = r.get("city", "?")
    anon = r.get("anonymity", "?")
    google = r.get("google", False)
    is_vpn = r.get("is_vpn", False)
    risk = r.get("risk", 0)
    isp = r.get("isp", "?")
    asn = r.get("asn", "?")
    https = "https" in pt.lower()

    f = {}
    f["st"] = f"[{C_GREEN}]{trunc('>', 2)}[/]" if online else f"[{C_RED}]{trunc('x', 2)}[/]"
    f["proxy"]  = f"[bold {C_WHITE}]{trunc(r['proxy'], 21)}[/]"
    f["type"]   = f"[{type_color(pt)}]{trunc(pt.upper() if online else '?', 7)}[/]"
    f["speed"]  = f"[{latency_color(lat)}]{trunc(latency_str(lat) if online else '-', 7)}[/]"
    f["anon"]   = f"[{anon_color(anon)}]{trunc(anon, 11)}[/]" if online else f"[{C_DIM}]{trunc('-', 11)}[/]"
    f["country"]= f"[{C_WHITE}]{trunc(country, 8)}[/]"
    f["city"]   = f"[{C_WHITE}]{trunc(city, 10)}[/]"
    f["google"] = f"[{C_GREEN}]{trunc(bool_icon(google), 3)}[/]" if online and google else \
                  f"[{C_RED}]{trunc(bool_icon(google), 3)}[/]" if online else f"[{C_DIM}]{trunc('-', 3)}[/]"
    f["https"]  = f"[{C_GREEN}]{trunc(bool_icon(https), 3)}[/]" if online and https else \
                  f"[{C_RED}]{trunc(bool_icon(https), 3)}[/]" if online else f"[{C_DIM}]{trunc('-', 3)}[/]"
    f["vpn"]    = f"[{C_GREEN}]{trunc(bool_icon(is_vpn), 3)}[/]" if online and is_vpn else \
                  f"[{C_RED}]{trunc(bool_icon(is_vpn), 3)}[/]" if online else f"[{C_DIM}]{trunc('-', 3)}[/]"
    f["risk"]   = f"[{risk_color(risk)}]{trunc(str(risk), 4)}[/]"
    f["isp"]    = f"[{C_WHITE}]{trunc(isp, 20)}[/]"
    f["asn"]    = f"[{C_WHITE}]{trunc(str(asn), 8)}[/]"
    return f


def format_row(r: dict, cols: List[dict]) -> str:
    fields = render_fields(r)
    return " ".join(fields.get(c["k"], "") for c in cols)


def print_header(cols: List[dict]) -> None:
    parts = [f"[bold {C_GOLD}]{c['l']:<{c['w']}}[/]" for c in cols]
    w = sum(c["w"] for c in cols) + len(cols) - 1
    console.print(f"[bold {C_DIM}]{'=' * w}[/]")
    console.print(" ".join(parts))
    console.print(f"[bold {C_DIM}]{'=' * w}[/]")


def print_footer_line(width: int) -> None:
    console.print(f"[bold {C_DIM}]{'=' * width}[/]")


class ArrowMenu:
    def __init__(self, items: List[Tuple[str, str, str]], title: str = "Main Menu"):
        self.items = items
        self.title = title
        self.sel = 0

    def render(self):
        console.clear()
        print_banner()

        proxies = load_local_proxies()
        providers = load_providers()

        stats = Table.grid(expand=True, padding=(0, 3))
        stats.add_column(justify="center")
        stats.add_column(justify="center")
        stats.add_column(justify="center")
        stats.add_row(
            f"[{C_DIM}]Proxies[/]\n[bold {C_WHITE}]{len(proxies)}[/]",
            f"[{C_DIM}]Providers[/]\n[bold {C_WHITE}]{len(providers)}[/]",
            f"[{C_DIM}]Results[/]\n[bold {C_WHITE}]{PROXIES_DIR}[/]",
        )
        console.print(Panel(stats, border_style=C_DIM, padding=(0, 4)))
        console.print()

        lines = []
        for i, (_, label, color) in enumerate(self.items):
            if i == self.sel:
                lines.append(f"  [bold {C_GOLD}]>>[/] [{color}]{label}[/]")
            else:
                lines.append(f"  [{C_DIM}]   {label}[/]")

        console.print(Panel(
            "\n".join(lines),
            title=f"[bold {C_ACCENT}]* {self.title} *[/]",
            border_style=C_ACCENT,
            padding=(1, 4),
            subtitle=f"[{C_DIM}]\\[Up/Down] Navigate  \\[Enter] Select  \\[Q] Quit[/]",
        ))
        console.print()
        console.print(Align.center(
            Text(f"v{VERSION}  {BRAND_FOOTER}", style=f"italic {C_DIM}")
        ))

    def run(self) -> Optional[str]:
        if not HAS_READCHAR:
            return self._fallback()
        while True:
            self.render()
            key = readchar.readkey()
            if key == readchar.key.UP:
                self.sel = (self.sel - 1) % len(self.items)
            elif key == readchar.key.DOWN:
                self.sel = (self.sel + 1) % len(self.items)
            elif key in (readchar.key.ENTER, "\r", "\n"):
                return self.items[self.sel][0]
            elif key.lower() == "q":
                return "Q"

    def _fallback(self) -> Optional[str]:
        self.render()
        choice = console.input(f"\n[{C_GOLD}]Select: [/]").strip().upper()
        return choice


UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
CONNECT_REQ = b"CONNECT {target}:{port} HTTP/1.1\r\nHost: {target}:{port}\r\nUser-Agent: {ua}\r\nProxy-Connection: keep-alive\r\n\r\n"


async def _safe_close(writer):
    try:
        writer.close()
    except Exception:
        pass
    try:
        await asyncio.wait_for(writer.wait_closed(), timeout=1)
    except Exception:
        pass


async def _try_http(host: str, port: int, timeout: float) -> Tuple[bool, float]:
    start = time.time()
    ct = min(timeout, 1.5)
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port), timeout=ct
        )
        writer.write(
            b"GET http://icanhazip.com/ HTTP/1.1\r\n"
            b"Host: icanhazip.com\r\nUser-Agent: " + UA.encode() +
            b"\r\nConnection: close\r\n\r\n"
        )
        await writer.drain()
        data = b""
        try:
            while True:
                chunk = await asyncio.wait_for(reader.read(4096), timeout=ct)
                if not chunk:
                    break
                data += chunk
                if len(data) > 4096:
                    break
        except (asyncio.TimeoutError, asyncio.CancelledError):
            pass
        await _safe_close(writer)
        header = data.split(b"\r\n", 1)[0:1][0:1]
        if header and b"200" in header[0]:
            return True, round((time.time() - start) * 1000, 1)
    except (Exception, asyncio.CancelledError):
        pass
    return False, -1


async def _try_https(host: str, port: int, timeout: float) -> Tuple[bool, float]:
    start = time.time()
    ct = min(timeout, 1.5)
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port), timeout=ct
        )
        writer.write(CONNECT_REQ.format(target="icanhazip.com", port=443, ua=UA))
        await writer.drain()
        try:
            resp = await asyncio.wait_for(reader.read(256), timeout=ct)
        except (asyncio.TimeoutError, asyncio.CancelledError):
            await _safe_close(writer)
            return False, -1
        if b"200" not in resp.split(b"\r\n", 1)[0:1][0:1][0]:
            await _safe_close(writer)
            return False, -1
        writer.write(
            b"GET / HTTP/1.1\r\nHost: icanhazip.com\r\nUser-Agent: " +
            UA.encode() + b"\r\nConnection: close\r\n\r\n"
        )
        await writer.drain()
        data = b""
        try:
            while True:
                chunk = await asyncio.wait_for(reader.read(4096), timeout=ct)
                if not chunk:
                    break
                data += chunk
                if len(data) > 4096:
                    break
        except (asyncio.TimeoutError, asyncio.CancelledError):
            pass
        await _safe_close(writer)
        header = data.split(b"\r\n", 1)[0:1][0:1]
        if header and b"200" in header[0]:
            return True, round((time.time() - start) * 1000, 1)
    except (Exception, asyncio.CancelledError):
        pass
    return False, -1


async def _try_socks5(host: str, port: int, timeout: float) -> Tuple[bool, float]:
    start = time.time()
    ct = min(timeout, 1.5)
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port), timeout=ct
        )
        writer.write(b"\x05\x01\x00")
        await writer.drain()
        data = await asyncio.wait_for(reader.read(2), timeout=ct)
        if data != b"\x05\x00":
            await _safe_close(writer)
            return False, -1
        target = b"icanhazip.com"
        writer.write(
            b"\x05\x01\x00\x03" + bytes([len(target)]) + target + struct.pack(">H", 80)
        )
        await writer.drain()
        resp = await asyncio.wait_for(reader.read(20), timeout=ct)
        if not resp or resp[1] != 0x00:
            await _safe_close(writer)
            return False, -1
        writer.write(
            b"GET / HTTP/1.1\r\nHost: icanhazip.com\r\nUser-Agent: " +
            UA.encode() + b"\r\nConnection: close\r\n\r\n"
        )
        await writer.drain()
        data = b""
        try:
            while True:
                chunk = await asyncio.wait_for(reader.read(4096), timeout=ct)
                if not chunk:
                    break
                data += chunk
                if len(data) > 4096:
                    break
        except (asyncio.TimeoutError, asyncio.CancelledError):
            pass
        await _safe_close(writer)
        header = data.split(b"\r\n", 1)[0:1][0:1]
        if header and b"200" in header[0]:
            return True, round((time.time() - start) * 1000, 1)
    except (Exception, asyncio.CancelledError):
        pass
    return False, -1


async def _try_socks4(host: str, port: int, timeout: float) -> Tuple[bool, float]:
    start = time.time()
    ct = min(timeout, 1.5)
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port), timeout=ct
        )
        ip_bytes = socket.inet_aton("1.1.1.1")
        writer.write(b"\x04\x01" + struct.pack(">H", 80) + ip_bytes + b"\x00")
        await writer.drain()
        resp = await asyncio.wait_for(reader.read(8), timeout=ct)
        if len(resp) < 2 or resp[1] != 0x5A:
            await _safe_close(writer)
            return False, -1
        writer.write(
            b"GET / HTTP/1.1\r\nHost: icanhazip.com\r\nUser-Agent: " +
            UA.encode() + b"\r\nConnection: close\r\n\r\n"
        )
        await writer.drain()
        data = b""
        try:
            while True:
                chunk = await asyncio.wait_for(reader.read(4096), timeout=ct)
                if not chunk:
                    break
                data += chunk
                if len(data) > 4096:
                    break
        except (asyncio.TimeoutError, asyncio.CancelledError):
            pass
        await _safe_close(writer)
        header = data.split(b"\r\n", 1)[0:1][0:1]
        if header and b"200" in header[0]:
            return True, round((time.time() - start) * 1000, 1)
    except (Exception, asyncio.CancelledError):
        pass
    return False, -1


async def detect_type(
    host: str, port: int, timeout: float, types: List[str]
) -> Tuple[str, float]:
    start = time.time()
    fns = []
    if "http" in types:
        fns.append(("http", _try_http))
    if "https" in types:
        fns.append(("https", _try_https))
    if "socks5" in types:
        fns.append(("socks5", _try_socks5))
    if "socks4" in types:
        fns.append(("socks4", _try_socks4))
    for name, fn in fns:
        remaining = timeout - (time.time() - start)
        if remaining <= 0.3:
            break
        ok, lat = await fn(host, port, remaining)
        if ok:
            return name, lat
    return "unknown", -1


async def detect_anonymity(
    host: str, port: int, ptype: str, session: aiohttp.ClientSession, timeout: float
) -> str:
    try:
        if ptype in ("socks4", "socks5"):
            return "elite"
        proxy_url = f"http://{host}:{port}"
        async with session.get(
            "http://httpbin.org/headers", proxy=proxy_url,
            timeout=aiohttp.ClientTimeout(total=min(timeout, 5)),
            headers={"User-Agent": UA}, ssl=False,
        ) as resp:
            if resp.status != 200:
                return "unknown"
            data = await resp.json()
            headers = {k.lower() for k in data.get("headers", {}).keys()}
            via = {"via", "x-forwarded-for", "x-real-ip", "forwarded", "proxy-connection"}
            if via & headers:
                return "transparent" if "x-forwarded-for" in headers else "anonymous"
            return "elite"
    except Exception:
        return "unknown"


async def check_google(
    host: str, port: int, ptype: str, session: aiohttp.ClientSession, timeout: float
) -> bool:
    try:
        if ptype in ("socks4", "socks5"):
            if not HAS_AIOHTTP_SOCKS:
                return False
            proxy_type = ProxyType.SOCKS5 if ptype == "socks5" else ProxyType.SOCKS4
            connector = ProxyConnector(proxy_type=proxy_type, host=host, port=port)
            async with aiohttp.ClientSession(connector=connector) as sess:
                async with sess.get(
                    "http://www.google.com",
                    timeout=aiohttp.ClientTimeout(total=min(timeout, 8)),
                    headers={"User-Agent": UA}, allow_redirects=True, ssl=False,
                ) as resp:
                    return resp.status == 200 and "google" in str(resp.url)
        else:
            proxy_url = f"http://{host}:{port}"
            async with session.get(
                "http://www.google.com", proxy=proxy_url,
                timeout=aiohttp.ClientTimeout(total=min(timeout, 8)),
                headers={"User-Agent": UA}, allow_redirects=True, ssl=False,
            ) as resp:
                return resp.status == 200 and "google" in str(resp.url)
    except Exception:
        return False


async def proxycheck_intel(host: str, port: int, session: aiohttp.ClientSession) -> dict:
    try:
        url = build_proxycheck_url(host, port)
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
            data = await resp.json()
            d = data.get(host, {})
            if not d:
                for k, v in data.items():
                    if isinstance(v, dict) and "detections" in v:
                        d = v
                        break
            det = d.get("detections", {})
            net = d.get("network", {})
            loc = d.get("location", {})
            country = loc.get("country_code", loc.get("country_name", "?"))
            city = loc.get("city_name", "?")
            isp = net.get("provider", net.get("isp", "?"))
            org = net.get("organisation", net.get("org", "?"))
            asn = net.get("asn", "?")
            return {
                "is_proxy": bool(det.get("proxy", False)) or bool(det.get("vpn", False)),
                "is_vpn": bool(det.get("vpn", False)),
                "is_tor": bool(det.get("tor", False)),
                "is_hosting": bool(det.get("hosting", False)),
                "risk": int(det.get("risk", 0)),
                "country": country,
                "isp": isp,
                "org": org,
                "asn": asn,
                "city": city,
            }
    except Exception:
        return {}


async def check_one(
    proxy_str: str, timeout: float,
    sem: asyncio.Semaphore,
    session: aiohttp.ClientSession, types: List[str],
) -> dict:
    HARD_TIMEOUT = min(timeout + 5, 15.0)
    r = {
        "proxy": proxy_str, "host": "", "port": 0, "status": "offline",
        "proxy_type": "unknown", "anonymity": "unknown", "latency_ms": -1,
        "google": False, "is_proxy": False, "is_vpn": False, "is_tor": False,
        "is_hosting": False, "risk": 0,
        "country": "?", "isp": "?", "org": "?", "asn": "?", "city": "?",
        "checked_at": datetime.now().strftime("%H:%M:%S"),
    }
    parts = proxy_str.strip().split(":")
    if len(parts) != 2:
        return r
    host, ps = parts
    if not ps.isdigit():
        return r
    port = int(ps)
    r["host"] = host
    r["port"] = port

    try:
        async def _check():
            async with sem:
                use_timeout = min(timeout, HARD_TIMEOUT)
                ptype, lat = await detect_type(host, port, use_timeout, types)
                if ptype == "unknown":
                    return r
                r["status"] = "online"
                r["proxy_type"] = ptype
                r["latency_ms"] = lat
                anon, google, intel = await asyncio.gather(
                    detect_anonymity(host, port, ptype, session, use_timeout),
                    check_google(host, port, ptype, session, use_timeout),
                    proxycheck_intel(host, port, session),
                )
                r["anonymity"] = anon
                r["google"] = google
                r.update(intel)
                return r
        return await asyncio.wait_for(_check(), timeout=HARD_TIMEOUT)
    except asyncio.TimeoutError:
        return r


def print_banner():
    console.print(f"[bold {C_ACCENT}]{BANNER}[/]", justify="center")
    console.print(Align.center(
        Text("Advanced Proxy Checker & Intelligence Tool", style=f"bold {C_GOLD}")
    ))
    console.print(Align.center(
        Text(
            f"v{VERSION}  SOCKS4 | SOCKS5 | HTTP | HTTPS | Anonymity | Google | proxycheck.io",
            style=C_DIM,
        )
    ))
    console.print()


def print_summary(results: List[dict], elapsed: float, cats: dict):
    online  = [r for r in results if r["status"] == "online"]
    offline = [r for r in results if r["status"] != "online"]
    google  = [r for r in online if r.get("google")]
    elite   = [r for r in online if r.get("anonymity") == "elite"]
    anon    = [r for r in online if r.get("anonymity") == "anonymous"]
    transp  = [r for r in online if r.get("anonymity") == "transparent"]
    lats    = [r["latency_ms"] for r in online if r["latency_ms"] > 0]
    avg     = sum(lats) / len(lats) if lats else 0
    types_c: Dict[str, int] = {}
    for r in online:
        t = r.get("proxy_type", "unknown")
        types_c[t] = types_c.get(t, 0) + 1

    g = Table.grid(expand=True, padding=(0, 2))
    g.add_column(justify="left")
    g.add_column(justify="left")
    g.add_column(justify="left")
    g.add_row(
        f"[{C_GOLD}]Total Checked:[/]  [{C_WHITE}]{len(results)}[/]",
        f"[{C_GREEN}]Online:[/]         [{C_GREEN}]{len(online)}[/]",
        f"[{C_RED}]Offline:[/]        [{C_RED}]{len(offline)}[/]",
    )
    g.add_row(
        f"[{C_GOLD}]Elapsed:[/]        [{C_WHITE}]{elapsed:.1f}s[/]",
        f"[{C_GREEN}]Google OK:[/]      [{C_GREEN}]{len(google)}[/]",
        f"[{C_BLUE}]Avg Latency:[/]    [{latency_color(avg)}]{avg:.0f}ms[/]",
    )
    g.add_row(
        f"[{C_GREEN}]Elite:[/]          [{C_GREEN}]{len(elite)}[/]",
        f"[{C_BLUE}]Anonymous:[/]      [{C_BLUE}]{len(anon)}[/]",
        f"[{C_ORANGE}]Transparent:[/]   [{C_ORANGE}]{len(transp)}[/]",
    )
    trow = "  ".join(f"[{type_color(k)}]{k.upper()}[/] [{C_WHITE}]{v}[/]" for k, v in types_c.items())
    g.add_row(f"[{C_GOLD}]By Type:[/]", trow, "")
    crow = "  ".join(f"[{C_DIM}]{fn}:[/] [{C_WHITE}]{n}[/]" for fn, n in cats.items())
    g.add_row(f"[{C_GOLD}]In-memory:[/]", crow, "")

    disk = count_result_files()
    drow = "  ".join(f"[{C_DIM}]{fn}:[/] [{C_WHITE}]{n}[/]" for fn, n in disk.items())
    g.add_row(f"[{C_GOLD}]On Disk:[/]", drow, "")

    console.print()
    console.print(Panel(g, title=f"[bold {C_ACCENT}]* Check Summary *[/]", border_style=C_ACCENT, padding=(1, 2)))
    console.print()
    console.print(Panel(
        f"[bold {C_ACCENT}]* Thanks for using ISITPROXY -- {BRAND_FOOTER} *[/]",
        border_style=C_GOLD, padding=(0, 2),
    ))


def post_check_menu(results: List[dict]):
    while True:
        console.print()
        console.print(
            f"[{C_DIM}]\\[f] Filter   \\[e] Export   \\[v] View All   \\[Enter] Back[/]"
        )
        choice = console.input(f"[{C_GOLD}]>> [/]").strip().lower()
        if choice == "f":
            action_filter(results)
        elif choice == "e":
            action_export(results)
        elif choice == "v":
            cols = get_columns(console.width)
            print_header(cols)
            for r in results:
                console.print(format_row(r, cols))
        else:
            break


def action_filter(results: List[dict]):
    console.print(Panel(
        f"[{C_GOLD}]Filter by:[/]\n"
        f"  [{C_ACCENT}]\\[1][/] Type (http/socks4/socks5)\n"
        f"  [{C_ACCENT}]\\[2][/] Country code\n"
        f"  [{C_ACCENT}]\\[3][/] Anonymity (elite/anonymous/transparent)\n"
        f"  [{C_ACCENT}]\\[4][/] Online only\n"
        f"  [{C_ACCENT}]\\[5][/] Google supported\n"
        f"  [{C_ACCENT}]\\[6][/] Fast (< 300ms)\n"
        f"  [{C_DIM}]Enter to cancel[/]",
        border_style=C_ACCENT, title=f"[bold {C_ACCENT}]* Filter Results *[/]",
    ))
    c = console.input(f"[{C_GOLD}]>> [/]").strip()
    filtered = results
    if c == "1":
        ft = console.input(f"[{C_GOLD}]Type: [/]").strip().lower()
        filtered = [r for r in results if ft in r.get("proxy_type", "").lower()]
    elif c == "2":
        fc = console.input(f"[{C_GOLD}]Country (e.g. US): [/]").strip().upper()
        filtered = [r for r in results if r.get("country", "").upper() == fc]
    elif c == "3":
        fa = console.input(f"[{C_GOLD}]Anonymity: [/]").strip().lower()
        filtered = [r for r in results if r.get("anonymity", "").lower() == fa]
    elif c == "4":
        filtered = [r for r in results if r["status"] == "online"]
    elif c == "5":
        filtered = [r for r in results if r.get("google")]
    elif c == "6":
        filtered = [r for r in results if 0 < r.get("latency_ms", -1) < 300]
    else:
        return

    console.print(f"\n[{C_GREEN}]Found {len(filtered)} proxies[/]")
    cols = get_columns(console.width)
    print_header(cols)
    for r in filtered:
        console.print(format_row(r, cols))


def action_export(results: List[dict]):
    online = [r for r in results if r["status"] == "online"]
    console.print(Panel(
        f"[{C_GOLD}]Export format:[/]\n"
        f"  [{C_ACCENT}]\\[1][/] CSV\n"
        f"  [{C_ACCENT}]\\[2][/] JSON\n"
        f"  [{C_ACCENT}]\\[3][/] TXT (proxy:port)\n"
        f"  [{C_DIM}]Enter to cancel[/]",
        border_style=C_ACCENT, title=f"[bold {C_ACCENT}]* Export *[/]",
    ))
    c = console.input(f"[{C_GOLD}]>> [/]").strip()
    if c not in ("1", "2", "3"):
        return
    default = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    ext = {"1": "csv", "2": "json", "3": "txt"}[c]
    fname = console.input(f"[{C_GOLD}]Filename [{default}]: [/]").strip() or default
    fp = f"{fname}.{ext}"

    if c == "1":
        with open(fp, "w") as f:
            f.write("proxy,type,status,latency_ms,anonymity,country,city,isp,org,asn,risk,google,vpn,checked_at\n")
            for r in online:
                f.write(
                    f"{r['proxy']},{r['proxy_type']},online,{r['latency_ms']},"
                    f"{r['anonymity']},{r['country']},{r['city']},{r['isp']},"
                    f"{r['org']},{r['asn']},{r['risk']},{r['google']},{r['is_vpn']},"
                    f"{r['checked_at']}\n"
                )
    elif c == "2":
        with open(fp, "w") as f:
            json.dump(online, f, indent=2)
    else:
        with open(fp, "w") as f:
            for r in online:
                f.write(r["proxy"] + "\n")

    console.print(f"[{C_GREEN}]Exported {len(online)} proxies to {fp}[/]")


def action_check():
    proxies = load_local_proxies()
    if not proxies:
        console.print(Panel(
            f"[{C_RED}]No proxies in {PROXY_FILE}. Scrape or add first.[/]",
            border_style=C_RED,
        ))
        console.input(f"[{C_DIM}]Press Enter to return[/]")
        return

    console.print(Panel(
        f"[{C_WHITE}]{len(proxies)}[/] proxies loaded",
        border_style=C_ACCENT, title=f"[bold {C_ACCENT}]* Check Settings *[/]",
    ))
    console.print()

    console.print(f"[{C_GOLD}]Select mode:[/]")
    console.print()
    console.print(f"  [{C_GREEN}]\\[F][/] [bold]Fast Mode[/]        [{C_DIM}]-- quick scan, high concurrency, HTTP only, < 300ms saves[/]")
    console.print(f"  [{C_BLUE}]\\[S][/] [bold]Standard[/]          [{C_DIM}]-- balanced, auto-tuned to your system ({SYS.optimal_conc} conc)[/]")
    console.print(f"  [{C_ACCENT}]\\[C][/] [bold]Custom[/]            [{C_DIM}]-- configure everything yourself[/]")
    console.print()
    preset = console.input(f"[{C_GOLD}]Select (F/S/C) [S]: [/]").strip().upper() or "S"

    if preset == "F":
        conc = min(SYS.optimal_conc * 2, 400)
        tout = 3
        types = ["http", "https"]
        show_all = False
        fast_ms = 300
    elif preset == "S":
        conc = SYS.optimal_conc
        tout = SYS.optimal_timeout
        types = ["http", "https", "socks4", "socks5"]
        show_all = False
        fast_ms = 99999
    else:
        conc = SYS.optimal_conc
        tout = SYS.optimal_timeout
        types = ["http", "https", "socks4", "socks5"]
        show_all = False
        fast_ms = 99999

        console.print(f"[{C_GOLD}]Concurrency (1-500) [{conc}]: [/]")
        raw = console.input().strip() or str(conc)
        try:
            conc = max(1, min(500, int(raw)))
        except ValueError:
            pass

        console.print(f"[{C_GOLD}]Timeout seconds (2-30) [{tout}]: [/]")
        raw = console.input().strip() or str(tout)
        try:
            tout = max(2, min(30, float(raw)))
        except ValueError:
            pass

        console.print(f"[{C_GOLD}]Proxy Types:[/]")
        console.print(f"  [{C_ACCENT}]\\[1][/] All (HTTP + SOCKS4 + SOCKS5)")
        console.print(f"  [{C_ACCENT}]\\[2][/] HTTP only")
        console.print(f"  [{C_ACCENT}]\\[3][/] SOCKS only (SOCKS4 + SOCKS5)")
        tc = console.input(f"[{C_GOLD}]Select (1/2/3) [1]: [/]").strip() or "1"
        if tc == "2":
            types = ["http", "https"]
        elif tc == "3":
            types = ["socks4", "socks5"]
        else:
            types = ["http", "https", "socks4", "socks5"]

        console.print(f"[{C_GOLD}]Fast proxy threshold:[/]")
        console.print(f"  [{C_DIM}]Only save proxies faster than this to result files[/]")
        console.print(f"  [{C_ACCENT}]\\[1][/] All online (no speed filter)")
        console.print(f"  [{C_ACCENT}]\\[2][/] Fast only (< 300ms)")
        console.print(f"  [{C_ACCENT}]\\[3][/] Medium+ (< 800ms)")
        console.print(f"  [{C_ACCENT}]\\[4][/] Custom ms")
        fc = console.input(f"[{C_GOLD}]Select (1/2/3/4) [1]: [/]").strip() or "1"
        if fc == "2":
            fast_ms = 300
        elif fc == "3":
            fast_ms = 800
        elif fc == "4":
            raw = console.input(f"[{C_GOLD}]Max latency ms: [/]").strip()
            try:
                fast_ms = max(1, int(raw))
            except ValueError:
                fast_ms = 99999
        else:
            fast_ms = 99999

    console.print()
    console.print(f"[{C_GOLD}]Display Mode:[/]")
    console.print(f"  [{C_ACCENT}]\\[Y][/] Stream -- show each proxy result in real-time")
    console.print(f"  [{C_ACCENT}]\\[N][/] Bar   -- progress bar only, no individual rows")
    mode = console.input(f"[{C_GOLD}]Stream results? (Y/N) [Y]: [/]").strip().upper() or "Y"
    stream = mode in ("Y", "YES", "")

    if stream:
        console.print(f"[{C_GOLD}]Show in stream:[/]")
        console.print(f"  [{C_ACCENT}]\\[1][/] All checks (online + offline)")
        console.print(f"  [{C_ACCENT}]\\[2][/] Only successful (online) proxies")
        sc = console.input(f"[{C_GOLD}]Select (1/2) [2]: [/]").strip() or "2"
        show_all = sc == "1"

    mode_label = "Fast" if preset == "F" else ("Standard" if preset == "S" else "Custom")
    type_label = " + ".join(t.upper() for t in types)
    batch_size = 500
    BATCH_CREATE = max(conc * 2, 400)
    console.print()
    console.print(Panel(
        f"[{C_WHITE}]{mode_label}[/] mode  |  "
        f"[{C_WHITE}]{len(proxies)}[/] proxies  |  "
        f"[{C_WHITE}]{conc}[/] concurrent  |  "
        f"[{C_WHITE}]{tout}s[/] timeout\n"
        f"[{C_WHITE}]{type_label}[/]  |  "
        f"[{C_WHITE}]{'Stream' if stream else 'Bar'}[/]  |  "
        f"[{C_WHITE}]batch {batch_size}[/]\n"
        f"[{C_WHITE}]Save:[/] {'< ' + str(fast_ms) + 'ms' if fast_ms < 99999 else 'all online'}"
        + (f"  |  [{C_WHITE}]Stream:[/] {'all' if show_all else 'online only'}" if stream else ""),
        border_style=C_ACCENT, title=f"[bold {C_ACCENT}]* Starting Check *[/]",
    ))

    results: List[dict] = []
    start_time = time.time()
    total = len(proxies)
    cols = get_columns(console.width)
    rfwriter = ResultFileWriter()

    def _save_batch(batch: List[dict]) -> int:
        s = batch_save(batch, fast_ms, rfwriter)
        if s > 0:
            console.print(f"  [{C_GREEN}]+ Batch saved:[/] [{C_WHITE}]{s}[/] valid proxies to files")
        return s

    def _update_progress(progress, task, done_n, online_n, saved_n, total):
        off = done_n - online_n
        pct = (done_n / total * 100) if total else 0
        rate = done_n / (time.time() - start_time) if (time.time() - start_time) > 0 else 0
        progress.update(
            task, completed=done_n,
            description=(
                f"[{C_GOLD}]Checked {done_n}/{total}[/] ({pct:.0f}%)  "
                f"[{C_GREEN}]{online_n} online[/]  "
                f"[{C_RED}]{off} offline[/]  "
                f"[{C_WHITE}]saved {saved_n}[/]  "
                f"[{C_DIM}]{rate:.0f}/s[/]"
            ),
        )

    async def _run_stream():
        sem = asyncio.Semaphore(conc)
        conn = aiohttp.TCPConnector(limit=conc, ssl=False, ttl_dns_cache=300)
        saved_n = 0
        done_n = 0
        online_n = 0
        async with aiohttp.ClientSession(connector=conn) as session:
            batch: List[dict] = []
            for i in range(0, len(proxies), BATCH_CREATE):
                chunk = proxies[i:i + BATCH_CREATE]
                tasks = [
                    asyncio.ensure_future(check_one(p, tout, sem, session, types))
                    for p in chunk
                ]
                for coro in asyncio.as_completed(tasks):
                    result = await coro
                    done_n += 1
                    results.append(result)
                    if result["status"] == "online":
                        online_n += 1
                    if stream and (show_all or result["status"] == "online"):
                        console.print(format_row(result, cols))
                    batch.append(result)
                    if len(batch) >= batch_size:
                        saved_n += _save_batch(batch)
                        batch = []
                    await asyncio.sleep(0)
                gc.collect()
            if batch:
                saved_n += _save_batch(batch)

    if stream:
        console.print()
        print_header(cols)
        try:
            asyncio.run(_run_stream())
        except KeyboardInterrupt:
            console.print(f"\n\n[{C_ACCENT}]* Check interrupted. Results so far will be saved. *[/]")
        print_footer_line(sum(c["w"] for c in cols) + len(cols))
    else:
        with Progress(
            SpinnerColumn(spinner_name="dots", style=C_ACCENT),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=40, style=C_ACCENT),
            TextColumn("[{task.percentage:>3.0f}%]"),
            TextColumn("({task.completed}/{task.total})"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            rich_task = progress.add_task(
                f"[{C_GOLD}]Starting...[/]", total=total
            )

            async def _run_bar():
                sem = asyncio.Semaphore(conc)
                conn = aiohttp.TCPConnector(limit=conc, ssl=False, ttl_dns_cache=300)
                saved_n = 0
                done_n = 0
                online_n = 0
                async with aiohttp.ClientSession(connector=conn) as session:
                    batch: List[dict] = []
                    for i in range(0, len(proxies), BATCH_CREATE):
                        chunk = proxies[i:i + BATCH_CREATE]
                        tasks = [
                            asyncio.ensure_future(check_one(p, tout, sem, session, types))
                            for p in chunk
                        ]
                        for coro in asyncio.as_completed(tasks):
                            result = await coro
                            done_n += 1
                            results.append(result)
                            if result["status"] == "online":
                                online_n += 1
                            _update_progress(progress, rich_task, done_n, online_n, saved_n, total)
                            progress.refresh()
                            batch.append(result)
                            if len(batch) >= batch_size:
                                saved_n += _save_batch(batch)
                                _update_progress(progress, rich_task, done_n, online_n, saved_n, total)
                                progress.refresh()
                                batch = []
                            await asyncio.sleep(0)
                        gc.collect()
                    if batch:
                        saved_n += _save_batch(batch)
                        _update_progress(progress, rich_task, done_n, online_n, saved_n, total)

            try:
                asyncio.run(_run_bar())
            except KeyboardInterrupt:
                console.print(f"\n\n[{C_ACCENT}]* Check interrupted. Results so far will be saved. *[/]")

    elapsed = time.time() - start_time
    cfg = load_config()
    save_mode = cfg.get("save_mode", "categorized")
    if save_mode == "single":
        cats = write_single(results)
    else:
        cats = write_categorized(results)
    print_summary(results, elapsed, cats)

    if cfg.get("replace_after_check", False):
        working = [r["proxy"] for r in results if r["status"] == "online"]
        if working:
            with open(PROXY_FILE, "w") as f:
                for p in sorted(set(working)):
                    f.write(p + "\n")
            console.print(f"[{C_GREEN}]Replaced {PROXY_FILE} with {len(working)} working proxies.[/]")
        else:
            console.print(f"[{C_DIM}]No working proxies found, {PROXY_FILE} unchanged.[/]")

    post_check_menu(results)


def action_scrape():
    providers = load_providers()
    console.print(Panel(
        f"[{C_DIM}][{C_WHITE}]{len(providers)}[/] providers loaded[/]",
        border_style=C_ACCENT, title=f"[bold {C_ACCENT}]* Scraping Online Proxies *[/]",
    ))
    all_proxies: List[str] = []
    failed = 0

    with Progress(
        SpinnerColumn(spinner_name="dots", style=C_ACCENT),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=30, style=C_ACCENT),
        TextColumn("{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
    ) as prog:
        task = prog.add_task(f"[{C_GOLD}]Fetching...[/]", total=len(providers))
        for url in providers:
            short = url[:60] + "\u2026" if len(url) > 60 else url
            prog.update(task, description=f"[{C_ACCENT}]{escape(short)}[/]")
            try:
                r = requests.get(url, timeout=10)
                parsed = parse_proxies_from_text(r.text)
                all_proxies.extend(parsed)
                prog.print(f"  [{C_GREEN}]+[/] [{C_DIM}]{escape(short)}[/] -> [{C_WHITE}]{len(parsed)}[/]")
            except Exception as e:
                prog.print(f"  [{C_RED}]x[/] [{C_DIM}]{escape(short)}[/] -> [{C_RED}]{escape(str(e))}[/]")
                failed += 1
            prog.advance(task)

    uniq = list(set(all_proxies))
    added = save_proxies_to_file(uniq)

    console.print()
    console.print(Panel(
        f"[{C_WHITE}]{len(uniq)}[/] unique proxies scraped\n"
        f"[{C_GREEN}]+{added}[/] new -> [{C_GOLD}]{PROXY_FILE}[/]\n"
        f"[{C_RED}]{failed}[/] providers failed",
        border_style=C_GREEN, title=f"[bold {C_GREEN}]* Scrape Complete *[/]",
    ))
    console.print(Panel(
        f"[bold {C_ACCENT}]* Thanks for using ISITPROXY -- {BRAND_FOOTER} *[/]",
        border_style=C_GOLD, padding=(0, 2),
    ))
    console.input(f"\n[{C_DIM}]Press Enter to return[/]")


def action_providers():
    providers = load_providers()
    t = Table(box=box.SIMPLE_HEAVY, border_style=C_ACCENT, header_style=f"bold {C_GOLD}", expand=True)
    t.add_column("#", width=4, justify="right")
    t.add_column("Provider URL")
    for i, p in enumerate(providers, 1):
        t.add_row(f"[{C_DIM}]{i}[/]", f"[{C_ACCENT}]{p}[/]")
    console.print(Panel(t, title=f"[bold {C_ACCENT}]* Providers ({len(providers)}) *[/]", border_style=C_ACCENT))

    console.print(f"[{C_DIM}]Add a new provider URL, or press Enter to return.[/]")
    url = console.input(f"[{C_GOLD}]Provider URL [/][{C_DIM}](empty to cancel)[/]: ").strip()
    if not url:
        return
    if not url.startswith("http"):
        console.print(f"[{C_RED}]x Invalid URL[/]")
    elif url in providers:
        console.print(f"[{C_GOLD}]Already exists[/]")
    else:
        with open(PROVIDERS_FILE, "a") as f:
            f.write(url + "\n")
        console.print(f"[{C_GREEN}]+ Added:[/] {url}")
    console.input(f"[{C_DIM}]Press Enter to return[/]")


def action_load_url():
    console.print(Panel(
        f"[{C_DIM}]Enter a URL with proxy list (one proxy per line)[/]",
        border_style=C_ACCENT, title=f"[bold {C_ACCENT}]* Load from URL *[/]",
    ))
    url = console.input(f"[{C_GOLD}]URL: [/]").strip()
    if not url or not url.startswith("http"):
        console.print(f"[{C_RED}]x Invalid URL[/]")
        console.input(f"[{C_DIM}]Press Enter to return[/]")
        return

    console.print(f"[{C_ACCENT}]Fetching...[/]")
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        parsed = parse_proxies_from_text(r.text)
        if not parsed:
            console.print(f"[{C_RED}]x No valid proxies found[/]")
        else:
            added = save_proxies_to_file(parsed)
            console.print(Panel(
                f"[{C_GREEN}][{C_WHITE}]{len(parsed)}[/] proxies found[/]\n"
                f"[{C_GREEN}]+{added}[/] new -> [{C_GOLD}]{PROXY_FILE}[/]",
                border_style=C_GREEN, title=f"[bold {C_GREEN}]+ Loaded *[/]",
            ))
    except Exception as e:
        console.print(f"[{C_RED}]x Failed: {escape(str(e))}[/]")
    console.input(f"[{C_DIM}]Press Enter to return[/]")


def action_paste_clipboard():
    console.print(Panel(
        f"[{C_DIM}]Read proxies from clipboard[/]",
        border_style=C_ACCENT, title=f"[bold {C_ACCENT}]* Paste from Clipboard *[/]",
    ))

    clip = ""
    for cmd in [
        ["xclip", "-selection", "clipboard", "-o"],
        ["xsel", "--clipboard", "--output"],
        ["pbpaste"],
        ["powershell", "-command", "Get-Clipboard"],
    ]:
        if shutil.which(cmd[0]):
            try:
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                clip = r.stdout
                break
            except Exception:
                continue

    if not clip:
        console.print(f"[{C_RED}]x Cannot read clipboard (install xclip/xsel).[/]")
        console.print(f"[{C_DIM}]Paste below, Ctrl+D when done:[/]")
        lines: List[str] = []
        try:
            while True:
                lines.append(console.input())
        except EOFError:
            pass
        clip = "\n".join(lines)

    if clip:
        parsed = parse_proxies_from_text(clip)
        if parsed:
            added = save_proxies_to_file(parsed)
            console.print(f"[{C_GREEN}]+ {len(parsed)} proxies found, {added} new added[/]")
        else:
            console.print(f"[{C_RED}]x No valid proxies in clipboard[/]")
    console.input(f"[{C_DIM}]Press Enter to return[/]")


def action_view_proxy_file():
    proxies = load_local_proxies()
    console.print(Panel(
        f"[{C_DIM}]{PROXY_FILE}[/] -- [{C_WHITE}]{len(proxies)}[/] proxies",
        border_style=C_ACCENT, title=f"[bold {C_ACCENT}]* Proxy File *[/]",
    ))
    if not proxies:
        console.print(f"  [{C_RED}]Empty[/]")
    else:
        t = Table(box=box.SIMPLE, border_style=C_DIM, expand=False)
        t.add_column("#", width=6, justify="right", style=C_DIM)
        t.add_column("Proxy", style=C_WHITE)
        for i, p in enumerate(proxies[:200], 1):
            t.add_row(str(i), p)
        if len(proxies) > 200:
            t.add_row("...", f"[{C_DIM}]+{len(proxies)-200} more[/]")
        console.print(t)
    console.input(f"[{C_DIM}]Press Enter to return[/]")


def action_view_results():
    files = list(PROXIES_DIR.glob("*.txt"))
    if not files:
        console.print(Panel(f"[{C_RED}]No results yet. Run a check first.[/]", border_style=C_RED))
        console.input(f"[{C_DIM}]Press Enter to return[/]")
        return
    t = Table(box=box.SIMPLE_HEAVY, border_style=C_ACCENT, header_style=f"bold {C_GOLD}", expand=True)
    t.add_column("File", style=C_GOLD)
    t.add_column("Count", justify="right", style=C_WHITE)
    t.add_column("Sample", style=C_DIM)
    for f in sorted(files):
        lines = [l for l in f.read_text().splitlines() if l.strip()]
        sample = ", ".join(lines[:3]) + ("\u2026" if len(lines) > 3 else "")
        t.add_row(f.name, str(len(lines)), sample)
    console.print(Panel(t, title=f"[bold {C_ACCENT}]* Saved Results *[/]", border_style=C_ACCENT))
    console.input(f"[{C_DIM}]Press Enter to return[/]")


def action_settings():
    global PROXIES_DIR
    cfg = load_config()
    sel = 0

    def _get():
        return load_config()

    def _save(c):
        save_config(c)

    def _render():
        c = _get()
        key = c.get("proxycheck_key", "")
        masked = key[:4] + "****" + key[-4:] if len(key) > 8 else (key or "(not set)")
        out_dir = c.get("output_dir", "proxies")
        replace = c.get("replace_after_check", False)
        save_mode = c.get("save_mode", "categorized")

        items = [
            ("key",    f"API Key          [{C_WHITE}]{masked}[/]", "input"),
            ("dir",    f"Output Directory [{C_WHITE}]{out_dir}/[/]", "input"),
            ("replace", f"Replace proxy.txt after check", "toggle", replace),
            ("single",  f"Single file mode (all.txt)", "toggle", save_mode == "single"),
        ]

        console.clear()
        console.print(Panel(
            f"[{C_DIM}]Navigate with [Up/Down], toggle with [Space], press [Q] to save & return[/]",
            border_style=C_DIM, title=f"[bold {C_ACCENT}]* Settings *[/]", padding=(0, 2),
        ))
        console.print()
        lines = []
        for i, item in enumerate(items):
            label = item[1]
            kind = item[2]
            if kind == "toggle":
                on = item[3]
                mark = f"[{C_GREEN}]\u2588\u2588 ON [/]" if on else f"[{C_RED}]\u2591\u2591 OFF[/]"
                if i == sel:
                    lines.append(f"  [bold {C_GOLD}]>>[/] {label}  {mark}")
                else:
                    lines.append(f"  [{C_DIM}]   {label}  {mark}[/]")
            else:
                if i == sel:
                    lines.append(f"  [bold {C_GOLD}]>>[/] {label}  [{C_DIM}]press Enter to edit[/]")
                else:
                    lines.append(f"  [{C_DIM}]   {label}  press Enter to edit[/]")

        console.print(Panel(
            "\n".join(lines),
            border_style=C_ACCENT, padding=(1, 2),
        ))

    if not HAS_READCHAR:
        _render_settings_fallback(cfg)
        return

    while True:
        _render()
        key = readchar.readkey()
        if key == readchar.key.UP:
            sel = (sel - 1) % 4
        elif key == readchar.key.DOWN:
            sel = (sel + 1) % 4
        elif key == " ":
            c = _get()
            if sel == 2:
                c["replace_after_check"] = not c.get("replace_after_check", False)
                _save(c)
            elif sel == 3:
                c["save_mode"] = "categorized" if c.get("save_mode", "categorized") == "single" else "single"
                _save(c)
        elif key in (readchar.key.ENTER, "\r", "\n"):
            c = _get()
            if sel == 0:
                console.print(f"\n[{C_GOLD}]Current key:[/] {c.get('proxycheck_key', '(not set)')}")
                new_key = console.input(f"[{C_GOLD}]New key (empty to keep): [/]").strip()
                if new_key:
                    c["proxycheck_key"] = new_key
                    _save(c)
                    console.print(f"[{C_GREEN}]API key saved.[/]")
                time.sleep(0.5)
            elif sel == 1:
                current = c.get("output_dir", "proxies")
                console.print(f"\n[{C_GOLD}]Current:[/] {current}/")
                new_dir = console.input(f"[{C_GOLD}]New directory (empty to keep): [/]").strip()
                if new_dir:
                    new_dir = new_dir.strip("/").strip("\\")
                    if new_dir and new_dir != current:
                        old_path = PROXIES_DIR
                        c["output_dir"] = new_dir
                        _save(c)
                        PROXIES_DIR = Path(new_dir)
                        PROXIES_DIR.mkdir(parents=True, exist_ok=True)
                        for fname in ["http.txt", "https.txt", "socks4.txt", "socks5.txt", "httpgoogle.txt"]:
                            src = old_path / fname
                            dst = PROXIES_DIR / fname
                            if src.exists() and not dst.exists():
                                shutil.copy2(src, dst)
                        console.print(f"[{C_GREEN}]Destination changed to {new_dir}/[/]")
                    else:
                        console.print(f"[{C_DIM}]No changes.[/]")
                time.sleep(0.5)
            else:
                break
        elif key.lower() == "q":
            break


def _render_settings_fallback(cfg):
    global PROXIES_DIR
    key = cfg.get("proxycheck_key", "")
    masked = key[:4] + "****" + key[-4:] if len(key) > 8 else (key or "(not set)")
    out_dir = cfg.get("output_dir", "proxies")
    replace = cfg.get("replace_after_check", False)
    save_mode = cfg.get("save_mode", "categorized")
    save_label = "Single file (all.txt)" if save_mode == "single" else "Categorized (http.txt, socks4.txt...)"

    console.print(Panel(
        f"[bold {C_GOLD}]━━━ Current Settings ━━━[/]\n\n"
        f"  [{C_DIM}][1][/] API Key:       [{C_WHITE}]{masked}[/]\n"
        f"  [{C_DIM}][2][/] Output Dir:    [{C_WHITE}]{out_dir}/[/]\n"
        f"  [{C_DIM}][3][/] Replace:       [{C_WHITE}]{'ON' if replace else 'OFF'}[/]\n"
        f"  [{C_DIM}][4][/] Save Mode:     [{C_WHITE}]{save_label}[/]\n",
        border_style=C_ACCENT, title=f"[bold {C_ACCENT}]* Settings *[/]",
    ))
    console.print(f"[{C_DIM}]Enter number to toggle/change, Enter to return[/]")
    choice = console.input(f"[{C_GOLD}]>> [/]").strip()
    if choice == "1":
        new_key = console.input(f"[{C_GOLD}]Enter API key (empty to keep): [/]").strip()
        if new_key:
            cfg["proxycheck_key"] = new_key
            save_config(cfg)
            console.print(f"[{C_GREEN}]API key saved.[/]")
    elif choice == "2":
        new_dir = console.input(f"[{C_GOLD}]New directory (empty to keep): [/]").strip()
        if new_dir:
            new_dir = new_dir.strip("/").strip("\\")
            if new_dir and new_dir != out_dir:
                old_path = PROXIES_DIR
                cfg["output_dir"] = new_dir
                save_config(cfg)
                PROXIES_DIR = Path(new_dir)
                PROXIES_DIR.mkdir(parents=True, exist_ok=True)
                for fname in ["http.txt", "https.txt", "socks4.txt", "socks5.txt", "httpgoogle.txt"]:
                    src = old_path / fname
                    dst = PROXIES_DIR / fname
                    if src.exists() and not dst.exists():
                        shutil.copy2(src, dst)
                console.print(f"[{C_GREEN}]Destination changed to {new_dir}/[/]")
    elif choice == "3":
        cfg["replace_after_check"] = not replace
        save_config(cfg)
        console.print(f"[{C_GREEN}]Replace set to {'ON' if not replace else 'OFF'}.[/]")
    elif choice == "4":
        cfg["save_mode"] = "single" if save_mode == "categorized" else "categorized"
        save_config(cfg)
        console.print(f"[{C_GREEN}]Save mode updated.[/]")


def action_help():
    help_lines = [
        f"[bold {C_GOLD}]ISITPROXY v{VERSION}[/] — Advanced Proxy Checker & Intelligence Tool",
        f"[{C_DIM}]Made with <3 by Hayder[/]",
        "",
        f"[bold {C_ACCENT}]━━━ Main Menu ━━━[/]",
        f"  [{C_GREEN}]\\[1][/{C_GREEN}] Check Proxies",
        f"    Load proxies from [bold]proxy.txt[/] or previously loaded list, then check",
        f"    each one for connectivity, type (HTTP/SOCKS4/SOCKS5), speed, anonymity,",
        f"    Google support, and risk via proxycheck.io intelligence.",
        f"    Options: stream/bar mode, concurrency, timeout, proxy type filter,",
        f"    fast-proxy threshold, batch auto-save every 500 to [bold]proxies/*.txt[/].",
        "",
        f"  [{C_BLUE}]\\[2][/{C_BLUE}] Scrape Online Proxies",
        f"    Fetch proxy lists from all URLs in [bold]providers.txt[/], parse and",
        f"    append unique proxies to [bold]proxy.txt[/].",
        "",
        f"  [{C_MAGENTA}]\\[3][/{C_MAGENTA}] Load Proxy List from URL",
        f"    Fetch a proxy list from a custom URL (e.g. GitHub raw, API).",
        "",
        f"  [{C_ORANGE}]\\[4][/{C_ORANGE}] Paste from Clipboard",
        f"    Paste proxies directly from clipboard (one per line).",
        "",
        f"  [{C_MAGENTA}]\\[5][/{C_MAGENTA}] Manage Providers",
        f"    View all URLs in [bold]providers.txt[/] and add new ones.",
        "",
        f"  [{C_DIM}]\\[6][/{C_DIM}] View Proxy File — Show proxies in proxy.txt",
        f"  [{C_GOLD}]\\[7][/{C_GOLD}] View Saved Results — Browse proxies/*.txt result files",
        "",
        f"[bold {C_ACCENT}]━━━ Check Settings ━━━[/]",
        f"  [{C_WHITE}][F] Fast Mode[/]:     Auto-tuned concurrency ({min(SYS.optimal_conc*2, 400)}), 3s timeout, HTTP only, < 300ms saves",
        f"  [{C_WHITE}][S] Standard[/]:       Auto-tuned concurrency ({SYS.optimal_conc}), {SYS.optimal_timeout}s timeout, all types, all online saves",
        f"  [{C_WHITE}][C] Custom[/]:         configure every setting yourself",
        "",
        f"[bold {C_ACCENT}]━━━ Post-Check ━━━[/]",
        f"  After checking, you can filter results by type/country/anonymity/speed",
        f"  and export to CSV, JSON, or TXT format.",
        "",
        f"[bold {C_ACCENT}]━━━ Settings (S) ━━━[/]",
        f"  Navigate with [Up/Down], toggle with [Space], edit with [Enter], press [Q] to save & return.",
        f"  [bold]1. API Key[/] — Configure your proxycheck.io API key.",
        f"  [bold]2. Destination Directory[/] — Change where result files are saved.",
        f"  [bold]3. Replace After Check[/] — Auto-replace proxy.txt with working proxies.",
        f"  [bold]4. Single File Mode[/] — Save all proxies to one file (all.txt).",
        "",
        f"[bold {C_ACCENT}]━━━ Output Files ━━━[/]",
        f"  [bold]proxy.txt[/]       — input proxy list (ip:port per line)",
        f"  [bold]providers.txt[/]   — URLs to scrape for free proxies",
        f"  [bold]config.json[/]     — settings (API key, output dir, replace toggle)",
        f"  [bold]{PROXIES_DIR}/http.txt[/] — working HTTP proxies (auto-saved)",
        f"  [bold]{PROXIES_DIR}/https.txt[/] — working HTTPS proxies",
        f"  [bold]{PROXIES_DIR}/socks4.txt[/] — working SOCKS4 proxies",
        f"  [bold]{PROXIES_DIR}/socks5.txt[/] — working SOCKS5 proxies",
        f"  [bold]{PROXIES_DIR}/httpgoogle.txt[/] — HTTP proxies that support Google",
        "",
        f"[bold {C_ACCENT}]━━━ Tips ━━━[/]",
        f"  - Proxies are flaky: re-run checks for reliable results",
        f"  - Higher concurrency = faster but less accurate",
        f"  - Use fast threshold to skip slow proxies in saves",
        f"  - proxycheck.io v3 provides country, risk, ISP, ASN, city",
        f"  - Results are sorted by speed (fastest first)",
    ]
    console.print(Panel(
        "\n".join(help_lines),
        border_style=C_ACCENT, title=f"[bold {C_ACCENT}]* Help Manual *[/]",
        padding=(1, 2),
    ))
    console.input(f"[{C_DIM}]Press Enter to return[/]")


MENU_ITEMS = [
    ("1", "Check Proxies",            C_GREEN,  action_check),
    ("2", "Scrape Online Proxies",    C_BLUE,   action_scrape),
    ("3", "Load Proxy List from URL", C_MAGENTA, action_load_url),
    ("4", "Paste from Clipboard",     C_ORANGE, action_paste_clipboard),
    ("5", "Manage Providers",         C_MAGENTA, action_providers),
    ("6", "View Proxy File",          C_DIM,    action_view_proxy_file),
    ("7", "View Saved Results",       C_GOLD,   action_view_results),
    ("S", "Settings",                 C_ACCENT, action_settings),
    ("H", "Help",                     C_GOLD,   action_help),
    ("Q", "Quit",                     C_RED,    None),
]


def check_internet() -> bool:
    urls = [
        "https://www.google.com",
        "https://1.1.1.1",
        "https://httpbin.org/ip",
    ]
    for url in urls:
        try:
            r = requests.get(url, timeout=3)
            if r.status_code < 400:
                return True
        except Exception:
            continue
    return False


def main():
    ensure_dirs()
    if not check_internet():
        console.print(Panel(
            f"[{C_RED}]No internet connection detected.[/]\n"
            f"[{C_DIM}]Some features require internet (scraping, proxycheck.io).\n"
            f"You can still manage local proxy files offline.[/]",
            border_style=C_RED, title=f"[bold {C_RED}]* No Internet *[/]",
        ))
        console.print(f"[{C_DIM}]Press Enter to continue anyway, or Ctrl+C to quit.[/]")
        try:
            console.input()
        except (EOFError, KeyboardInterrupt):
            sys.exit(1)
    menu = ArrowMenu(
        [(k, l, c) for k, l, c, _ in MENU_ITEMS],
        title="Main Menu",
    )
    while True:
        choice = menu.run()
        if choice is None or choice == "Q":
            console.print(f"\n[{C_ACCENT}]* Thanks for using ISITPROXY! Goodbye. *[/]\n")
            sys.exit(0)
        for key, label, color, action in MENU_ITEMS:
            if choice == key:
                if action is None:
                    console.print(f"\n[{C_ACCENT}]* Thanks for using ISITPROXY! Goodbye. *[/]\n")
                    sys.exit(0)
                console.clear()
                console.print(Rule(f"[bold {C_ACCENT}]* {label} *[/]", style=C_ACCENT))
                console.print()
                action()
                break
        else:
            console.print(f"[{C_RED}]x Invalid choice[/]")
            time.sleep(0.8)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print(f"\n\n[{C_ACCENT}]* Interrupted. Thanks for using ISITPROXY! Goodbye. *[/]\n")
        sys.exit(0)
