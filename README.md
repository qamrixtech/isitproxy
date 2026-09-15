<div align="center">

```
  ██╗███████╗██╗████████╗██████╗ ██████╗  ██████╗ ██╗  ██╗██╗   ██╗
  ██║██╔════╝██║╚══██╔══╝██╔══██╗██╔══██╗██╔═══██╗╚██╗██╔╝╚██╗ ██╔╝
  ██║███████╗██║   ██║   ██████╔╝██████╔╝██║   ██║ ╚███╔╝  ╚████╔╝ 
  ██║╚════██║██║   ██║   ██╔═══╝ ██╔══██╗██║   ██║ ██╔██╗   ╚██╔╝  
  ██║███████║██║   ██║   ██║     ██║  ██║╚██████╔╝██╔╝ ██╗   ██║   
  ╚═╝╚══════╝╚═╝   ╚═╝   ╚═╝     ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝  
```

# Advanced Async Proxy Checker & Intelligence Tool

**v1.1** | Developed By **Hayder** | Property of **Qamrix Tech**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Qamrix Tech](https://img.shields.io/badge/Made_by-Qamrix_Tech-cyan.svg)](https://github.com/qamrixtech/isitproxy)

*Building intelligent solutions that drive progress and shape the future.*

</div>

---

## About

**ISITPROXY** is a high-performance async proxy checker and intelligence tool built by **Hayder**, Owner of **Qamrix Tech**. It validates HTTP, HTTPS, SOCKS4, and SOCKS5 proxies with real-time latency measurement, anonymity detection, Google support check, and ISP/country/risk intelligence via proxycheck.io. Features an interactive TUI with arrow-key navigation, batch auto-save, and system-adaptive performance.

| | |
|---|---|
| **Email** | [qamrixtech@gmail.com](mailto:qamrixtech@gmail.com) |
| **GitHub** | [github.com/qamrixtech/isitproxy](https://github.com/qamrixtech/isitproxy) |

---

## Screenshots

<table>
  <tr>
    <td align="center"><b>Launcher</b></td>
    <td align="center"><b>Main Interface</b></td>
    <td align="center"><b>Settings</b></td>
  </tr>
  <tr>
    <td><img src="images/Launcher.jpg" width="320"></td>
    <td><img src="images/maininterface.jpg" width="320"></td>
    <td><img src="images/settings.jpg" width="320"></td>
  </tr>
  <tr>
    <td align="center"><b>Select Check Mode</b></td>
    <td align="center"><b>Configuration</b></td>
    <td align="center"><b>Checking (Stream)</b></td>
  </tr>
  <tr>
    <td><img src="images/selectcheckmode.jpg" width="320"></td>
    <td><img src="images/configurationebeforecheck.jpg" width="320"></td>
    <td><img src="images/checkingproxies.jpg" width="320"></td>
  </tr>
  <tr>
    <td align="center"><b>Bar Mode</b></td>
    <td align="center"><b>Check Complete</b></td>
    <td align="center"><b>Filter Tool</b></td>
  </tr>
  <tr>
    <td><img src="images/barmodeproxycheck.jpg" width="320"></td>
    <td><img src="images/checkingcomplete.jpg" width="320"></td>
    <td><img src="images/proxyfiltertool.jpg" width="320"></td>
  </tr>
  <tr>
    <td align="center"><b>Scraping Proxies</b></td>
    <td align="center"><b>Scrape Complete</b></td>
    <td align="center"><b>Saved Results</b></td>
  </tr>
  <tr>
    <td><img src="images/scrapingproxies.jpg" width="320"></td>
    <td><img src="images/scrapecomplete.jpg" width="320"></td>
    <td><img src="images/viewsavedresults.jpg" width="320"></td>
  </tr>
  <tr>
    <td align="center"><b>Manage Providers</b></td>
    <td align="center"><b>Google Filter</b></td>
    <td align="center"><b>Proxy Check Success</b></td>
  </tr>
  <tr>
    <td><img src="images/manageproviders.jpg" width="320"></td>
    <td><img src="images/filterproxygoogle.jpg" width="320"></td>
    <td><img src="images/proxychecksuccess.jpg" width="320"></td>
  </tr>
</table>

---

## Features

<table>
  <tr>
    <th>Proxy Detection</th>
    <th>Intelligence</th>
    <th>Performance</th>
  </tr>
  <tr>
    <td>

- HTTP/HTTPS (raw socket)
- SOCKS4/SOCKS5 (native)
- Real-time latency (ms)
- Batched async engine
- Fast-fail in <1.5s

</td>
    <td>

- Anonymity (Elite/Anonymous/Transparent)
- Google support check
- proxycheck.io v3 intel
- Country, city, ISP, ASN
- VPN & risk score

</td>
    <td>

- System profiler (CPU/RAM)
- Adaptive concurrency
- Batched task creation
- DNS caching (TTL)
- Batch auto-save

</td>
  </tr>
</table>

<table>
  <tr>
    <th>Interactive TUI</th>
    <th>Check Modes</th>
  </tr>
  <tr>
    <td>

- Arrow-key navigation (Up/Down/Enter)
- Stream mode (real-time results)
- Bar mode (progress bar)
- Adaptive columns (80/120/160+)
- Post-check filter & export

</td>
    <td>

| Mode | Conc | Timeout | Types | Filter |
|------|------|---------|-------|--------|
| **[F] Fast** | Auto x2 | 3s | HTTP/HTTPS | < 300ms |
| **[S] Standard** | Auto | 8s | All | All online |
| **[C] Custom** | User | User | User | User |

</td>
  </tr>
</table>

---

## Installation

### Prerequisites

- Python 3.8+
- pip

### Setup

```bash
git clone https://github.com/qamrixtech/isitproxy.git
cd isitproxy
python -m venv venv
source venv/bin/activate   # Linux/macOS
# venv\Scripts\activate    # Windows
pip install rich aiohttp aiohttp-socks requests readchar
```

### Launch

```bash
python isit.py
```

| Script | Platform | Command |
|--------|----------|---------|
| `run.py` | Cross-platform | `python run.py` |
| `run.sh` | Linux/macOS | `./run.sh` |

---

## Menu Overview

| Key | Option | Description |
|-----|--------|-------------|
| **1** | Check Proxies | Detect type/speed/anonymity/intel for loaded proxies |
| **2** | Scrape Online Proxies | Fetch from provider URLs, append to `proxy.txt` |
| **3** | Load Proxy List from URL | Import proxies from any URL |
| **4** | Paste from Clipboard | Paste proxies directly |
| **5** | Manage Providers | View/add proxy source URLs |
| **6** | View Proxy File | Browse proxies in `proxy.txt` |
| **7** | View Saved Results | Browse result files |
| **S** | Settings | API key, output dir, save mode, replace toggle |
| **H** | Help | Full help manual |
| **Q** | Quit | Exit the tool |

---

## Usage Guide

### Checking Proxies

**Step 1** -- Select **[1] Check Proxies** and choose a mode:

| Mode | Best For | Concurrency | Timeout | Types |
|------|----------|-------------|---------|-------|
| **[F] Fast** | Quick scan, large lists | Auto x2 | 3s | HTTP/HTTPS |
| **[S] Standard** | Balanced (recommended) | Auto | 8s | All |
| **[C] Custom** | Specific needs | User | User | User |

**Step 2** -- Choose display mode:
- **[Y] Stream** -- see each proxy result live
- **[N] Bar** -- progress bar only (faster for large lists)

**Step 3** -- After scan, use post-check menu:
- **[f] Filter** -- by type, country, anonymity, speed, Google
- **[e] Export** -- to CSV, JSON, or TXT
- **[v] View All** -- display all results

### Scraping Proxies

Select **[2] Scrape Online Proxies** to fetch from all provider URLs. New unique proxies are appended to `proxy.txt`.

### Loading Proxies

- **[3] Load from URL** -- enter any URL with proxy list
- **[4] Paste from Clipboard** -- paste proxies directly
- **[6] View Proxy File** -- browse loaded proxies

### Settings

Navigate with **Up/Down**, toggle with **Space**, edit with **Enter**, press **Q** to save & return.

| Setting | Description |
|---------|-------------|
| **API Key** | proxycheck.io key (free at proxycheck.io/register) |
| **Output Directory** | Where result files are saved (default: `proxies/`) |
| **Replace After Check** | Auto-replace `proxy.txt` with working proxies |
| **Single File Mode** | Save all proxies to `all.txt` instead of by type |

---

## Settings

### API Key

![Settings](images/settings.jpg)

Get a free key at [proxycheck.io/register](https://proxycheck.io/register) (100 queries/day free tier).

Set via:
1. **Menu**: Settings > API Key
2. **Config file**: `{"proxycheck_key": "your-key"}` in `config.json`
3. **Environment**: `export PROXYCHECK_KEY="your-key"`

### Save Mode

- **Categorized** -- split by type: `http.txt`, `https.txt`, `socks4.txt`, `socks5.txt`, `httpgoogle.txt`
- **Single** -- all working proxies in one file: `all.txt`

### Replace After Check

Toggle to automatically overwrite `proxy.txt` with only working proxies after each scan.

---

## Providers

ISITPROXY comes with 10 default proxy sources:

| Source | Types |
|--------|-------|
| TheSpeedX/PROXY-List | HTTP, SOCKS4, SOCKS5 |
| clarketm/proxy-list | HTTP |
| jetkai/proxy-list | HTTP, SOCKS4, SOCKS5 |
| ProxyScrape API | HTTP, SOCKS4, SOCKS5 |

Add custom providers via **[5] Manage Providers** or edit `providers.txt`.

---

## File Structure

```
isitproxy/
  isit.py              # Main tool (single-file)
  run.py               # Cross-platform launcher
  run.sh               # Linux/macOS launcher
  proxy.txt            # Input proxy list (ip:port per line)
  providers.txt        # URLs to scrape for free proxies
  config.json          # Settings (API key, output dir, save mode, replace)
  images/              # Screenshots
  proxies/             # Result directory (configurable)
    http.txt           # Working HTTP proxies
    https.txt          # Working HTTPS proxies
    socks4.txt         # Working SOCKS4 proxies
    socks5.txt         # Working SOCKS5 proxies
    httpgoogle.txt     # HTTP proxies that support Google
    all.txt            # All working proxies (single file mode)
```

---

## Proxy List Format

```
# One proxy per line: ip:port
# Supported prefixes: socks5://, socks4://, http://, https://
# Separators: newline, comma, pipe, semicolon

91.228.227.23:80
31.10.83.158:8080
socks5://10.0.0.1:1080
http://5.5.5.5:3128
```

---

## How It Works

1. **Load** proxies from `proxy.txt` or scrape from providers
2. **Profile** system (CPU/RAM) and auto-tune concurrency
3. **Scan** in batches of 200 to prevent OS resource exhaustion
4. **Per proxy**: connect > HTTP (direct) > HTTPS (CONNECT) > SOCKS5 > SOCKS4
5. **Intel**: detect anonymity, check Google, query proxycheck.io
6. **Save** valid proxies every 500 to result files
7. **Display** with adaptive columns, latency colors, type indicators

---

## Platform Support

| Platform | Status |
|----------|--------|
| Linux | Full support (primary) |
| macOS | Full support |
| Windows | Full support (WSL or native) |

---

## Dependencies

| Package | Purpose | Required |
|---------|---------|----------|
| `rich` | TUI rendering, progress bars | Yes |
| `aiohttp` | Async HTTP client | Yes |
| `aiohttp-socks` | SOCKS proxy support | Yes |
| `requests` | Scraping, internet check | Yes |
| `readchar` | Arrow-key menu navigation | Optional |

---

## License

```
Copyright (c) 2026 Qamrix Tech. All Rights Reserved.
Developed By Hayder
```

See [LICENSE](LICENSE) for details.

---

<div align="center">

![Qamrix Tech](images/QamrixBanner.png)

*Made with <3 by Hayder -- Qamrix Tech*

</div>
