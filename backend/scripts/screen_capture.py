#!/usr/bin/env python3
"""Corvus Screen Capture — lightweight frame pump for the Advisor pipeline.

Captures screenshots at a configurable interval and POSTs them to the
Corvus capture endpoint. The backend handles all intelligence: OCR,
duplicate detection, novelty scoring, adaptive cadence, and buffering.

Uses scrot for screen capture (works on ChromeOS Crostini, X11, and
most Linux desktops). Falls back to mss if scrot is unavailable.

Usage:
    python scripts/screen_capture.py                    # defaults: 3s interval
    python scripts/screen_capture.py --interval 5       # 5 second interval
    python scripts/screen_capture.py --port 8002        # custom backend port

Requires: requests, Pillow (both in the backend venv)
System:   scrot (apt install scrot)
"""

import argparse
import io
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from PIL import Image

DEFAULT_INTERVAL = 3
DEFAULT_QUALITY = 60
DEFAULT_MAX_DIM = 1920
API_URL_TEMPLATE = "http://localhost:{port}/corvus/capture"
MAX_CONSECUTIVE_ERRORS = 10


def _check_scrot() -> bool:
    """Verify scrot is installed."""
    try:
        subprocess.run(["scrot", "--version"], capture_output=True, timeout=5)
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _capture_screenshot(tmp_path: str, quality: int) -> Image.Image:
    """Capture a screenshot using scrot and return as PIL Image.

    scrot captures the entire visible screen — program-agnostic.
    """
    subprocess.run(
        ["scrot", "-q", str(quality), "-o", tmp_path],
        check=True, capture_output=True, timeout=10,
    )
    return Image.open(tmp_path)


def _compress_and_post(
    img: Image.Image, port: int, quality: int, max_dim: int,
) -> str:
    """Downscale, compress to JPEG, and POST to the capture endpoint."""
    w, h = img.size
    if max(w, h) > max_dim:
        scale = max_dim / max(w, h)
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality)
    buf.seek(0)

    timestamp = datetime.now(timezone.utc).isoformat()
    url = API_URL_TEMPLATE.format(port=port)

    resp = requests.post(
        url,
        files={"frame": ("frame.jpg", buf, "image/jpeg")},
        data={
            "timestamp": timestamp,
            "width": str(img.size[0]),
            "height": str(img.size[1]),
        },
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    return data.get("status", "ok")


def run_capture_loop(args: argparse.Namespace):
    """Main capture loop — bounded iteration with error tracking."""
    url = API_URL_TEMPLATE.format(port=args.port)
    print(f"[Corvus Capture] Interval {args.interval}s, quality {args.quality}%")
    print(f"[Corvus Capture] Posting to {url}")
    print(f"[Corvus Capture] Press Ctrl+C to stop\n")

    consecutive_errors = 0
    frames_sent = 0
    duplicates = 0

    # Use a temp file for scrot output — reused each iteration
    tmp_dir = tempfile.mkdtemp(prefix="corvus_capture_")
    tmp_path = str(Path(tmp_dir) / "frame.jpg")

    # Bounded loop — ~38 days at 1s interval (JPL-2 compliance)
    max_iterations = 3_300_000
    for _i in range(max_iterations):
        try:
            img = _capture_screenshot(tmp_path, args.quality)
            status = _compress_and_post(img, args.port, args.quality, args.max_dim)
            img.close()
            consecutive_errors = 0
            frames_sent += 1

            if status == "duplicate":
                duplicates += 1
                marker = "·"
            else:
                marker = "▪"

            print(
                f"\r  {marker} {frames_sent} sent, {duplicates} dup, "
                f"last: {status}    ",
                end="", flush=True,
            )

        except KeyboardInterrupt:
            print(f"\n\n[Corvus Capture] Stopped. {frames_sent} frames sent.")
            break
        except requests.ConnectionError:
            consecutive_errors += 1
            print(
                f"\r  ! Backend not reachable "
                f"({consecutive_errors}/{MAX_CONSECUTIVE_ERRORS})",
                end="", flush=True,
            )
            if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                print(f"\n[Corvus Capture] Backend unreachable. Exiting.")
                sys.exit(1)
        except Exception as e:
            consecutive_errors += 1
            print(f"\n  ! Error: {e}")
            if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                print(f"[Corvus Capture] Too many errors. Exiting.")
                sys.exit(1)

        time.sleep(args.interval)

    # Cleanup temp file
    Path(tmp_path).unlink(missing_ok=True)
    Path(tmp_dir).rmdir()


def main():
    """Parse arguments and run."""
    parser = argparse.ArgumentParser(
        description="Corvus Screen Capture — feed screen data to the Advisor",
    )
    parser.add_argument(
        "--interval", type=float, default=DEFAULT_INTERVAL,
        help=f"Capture interval in seconds (default: {DEFAULT_INTERVAL})",
    )
    parser.add_argument(
        "--port", type=int, default=8002,
        help="Backend port (default: 8002)",
    )
    parser.add_argument(
        "--quality", type=int, default=DEFAULT_QUALITY,
        help=f"JPEG quality 1-100 (default: {DEFAULT_QUALITY})",
    )
    parser.add_argument(
        "--max-dim", type=int, default=DEFAULT_MAX_DIM,
        help=f"Max image dimension in px (default: {DEFAULT_MAX_DIM})",
    )
    args = parser.parse_args()

    if not _check_scrot():
        print("Error: scrot is required. Install with: sudo apt install scrot")
        sys.exit(1)

    run_capture_loop(args)


if __name__ == "__main__":
    main()
