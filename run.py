#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════╗
║  ISITPROXY Launcher — cross-platform, auto-detects & sets up ║
╚═══════════════════════════════════════════════════════════════╝

Usage:
    python run.py          # Linux / macOS / Windows
    python3 run.py         # Linux / macOS
    py run.py              # Windows (py launcher)
    ./run.sh               # Linux / macOS (shell wrapper)
"""

import os
import sys
import subprocess
import shutil
import platform
from pathlib import Path

# ═══════════════════════════════════════════════════════════════════
#  CONFIG
# ═══════════════════════════════════════════════════════════════════

SCRIPT_DIR = Path(__file__).resolve().parent
VENV_DIR = SCRIPT_DIR / "venv"
MAIN_SCRIPT = SCRIPT_DIR / "isit.py"
REQUIREMENTS = ["aiohttp", "aiohttp-socks", "requests", "rich", "readchar"]

MIN_PYTHON = (3, 10)
IS_WINDOWS = platform.system() == "Windows"

# ═══════════════════════════════════════════════════════════════════
#  COLORS (ANSI — works in most Windows terminals, PowerShell, WSL)
# ═══════════════════════════════════════════════════════════════════

if IS_WINDOWS:
    os.system("")  # enable ANSI escape codes on Windows 10+

C_RED    = "\033[0;31m"
C_GREEN  = "\033[0;32m"
C_YELLOW = "\033[1;33m"
C_CYAN   = "\033[0;36m"
C_BOLD   = "\033[1m"
C_DIM    = "\033[2m"
C_RESET  = "\033[0m"


def info(msg):  print(f"{C_CYAN}[*]{C_RESET} {msg}")
def ok(msg):    print(f"{C_GREEN}[+]{C_RESET} {msg}")
def warn(msg):  print(f"{C_YELLOW}[!]{C_RESET} {msg}")
def fail(msg):  print(f"{C_RED}[x]{C_RESET} {msg}"); sys.exit(1)


# ═══════════════════════════════════════════════════════════════════
#  FIND PYTHON
# ═══════════════════════════════════════════════════════════════════

def find_python() -> str:
    """Find a suitable Python 3.10+ interpreter."""
    candidates = ["python3.14", "python3.13", "python3.12", "python3.11", "python3.10", "python3", "python"]

    # On Windows, also try the py launcher
    if IS_WINDOWS:
        candidates.insert(0, "py")

    for cmd in candidates:
        try:
            out = subprocess.run(
                [cmd, "--version"],
                capture_output=True, text=True, timeout=5,
            )
            if out.returncode == 0:
                version_str = out.stdout.strip()  # "Python 3.14.7"
                parts = version_str.split()
                if len(parts) >= 2:
                    ver = parts[1].split(".")
                    major, minor = int(ver[0]), int(ver[1])
                    if major >= MIN_PYTHON[0] and minor >= MIN_PYTHON[1]:
                        return cmd
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            continue
    return ""


# ═══════════════════════════════════════════════════════════════════
#  VENV
# ═══════════════════════════════════════════════════════════════════

def get_activate_cmd() -> list:
    """Return the shell command to activate the venv for the current platform."""
    if IS_WINDOWS:
        bat = VENV_DIR / "Scripts" / "activate.bat"
        ps1 = VENV_DIR / "Scripts" / "Activate.ps1"
        # Check if we're in PowerShell
        if "powershell" in os.environ.get("PSModulePath", "").lower() or \
           "pwsh" in sys.executable.lower():
            if ps1.exists():
                return ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(ps1)]
        if bat.exists():
            return ["cmd", "/c", str(bat), "&&"]
        return []
    else:
        # Unix: just return the source command — the caller handles it
        return []


def get_python_in_venv() -> str:
    """Return the path to the Python executable inside the venv."""
    if IS_WINDOWS:
        return str(VENV_DIR / "Scripts" / "python.exe")
    return str(VENV_DIR / "bin" / "python")


def create_venv(python_cmd: str):
    """Create the virtual environment."""
    info("Creating virtual environment...")
    subprocess.run(
        [python_cmd, "-m", "venv", str(VENV_DIR)],
        check=True,
    )
    ok(f"Created venv at {VENV_DIR}")


def ensure_deps():
    """Install missing dependencies inside the venv."""
    venv_python = get_python_in_venv()
    if not Path(venv_python).exists():
        fail(f"Venv Python not found: {venv_python}")

    # Check which packages are missing
    missing = []
    for pkg in REQUIREMENTS:
        import_name = pkg.replace("-", "_")
        result = subprocess.run(
            [venv_python, "-c", f"import {import_name}"],
            capture_output=True,
        )
        if result.returncode != 0:
            missing.append(pkg)

    if missing:
        info(f"Installing: {' '.join(missing)}")
        subprocess.run(
            [venv_python, "-m", "pip", "install", "--upgrade", "pip", "-q"],
            capture_output=True,
        )
        subprocess.run(
            [venv_python, "-m", "pip", "install", *missing, "-q"],
            check=True,
        )
        ok("Dependencies installed")
    else:
        ok("All dependencies satisfied")


# ═══════════════════════════════════════════════════════════════════
#  RUN
# ═══════════════════════════════════════════════════════════════════

def main():
    print()
    print(f"{C_BOLD}{C_CYAN}  ╔═══════════════════════════════════════╗{C_RESET}")
    print(f"{C_BOLD}{C_CYAN}  ║       ISITPROXY  v1.0  Launcher       ║{C_RESET}")
    print(f"{C_BOLD}{C_CYAN}  ╚═══════════════════════════════════════╝{C_RESET}")
    print()

    if not MAIN_SCRIPT.exists():
        fail(f"Main script not found: {MAIN_SCRIPT}")

    # 1. Find Python
    info("Looking for Python 3.10+...")
    python_cmd = find_python()
    if not python_cmd:
        fail("Python 3.10+ not found. Install Python and try again.")
    ok(f"Found: {python_cmd}")

    # 2. Create venv if missing
    activate_bat = VENV_DIR / "Scripts" / "activate.bat" if IS_WINDOWS else VENV_DIR / "bin" / "activate"
    if not activate_bat.exists():
        create_venv(python_cmd)
    else:
        ok("Virtual environment exists")

    # 3. Ensure dependencies
    info("Checking dependencies...")
    ensure_deps()

    # 4. Run the main script using venv Python
    venv_python = get_python_in_venv()
    if not Path(venv_python).exists():
        fail(f"Venv Python not found: {venv_python}")

    print()
    os.chdir(SCRIPT_DIR)
    result = subprocess.run(
        [venv_python, str(MAIN_SCRIPT)] + sys.argv[1:],
    )
    sys.exit(result.returncode)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        sys.exit(0)
