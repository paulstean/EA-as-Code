#!/usr/bin/env python3
"""Launch the EA Visualiser in Chrome, falling back to Edge."""

import os
import shutil
import subprocess
import sys
import platform

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_PATH = os.path.join(SCRIPT_DIR, "visualiser.html")


def find_browser():
    system = platform.system()

    # --- Chrome ---
    chrome_candidates = []

    if system == "Linux":
        chrome_candidates = [
            "google-chrome",
            "google-chrome-stable",
            "chromium-browser",
            "chromium",
        ]
    elif system == "Darwin":
        chrome_candidates = [
            "google-chrome",
            "google-chrome-stable",
            "chromium",
        ]
        chrome_path = (
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        )
        if os.path.isfile(chrome_path):
            chrome_candidates.insert(0, chrome_path)
    elif system == "Windows":
        chrome_candidates = ["google-chrome", "chrome"]
        for prog in [
            os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(
                r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
            ),
            os.path.expandvars(
                r"%LocalAppData%\Google\Chrome\Application\chrome.exe"
            ),
        ]:
            if os.path.isfile(prog):
                chrome_candidates.insert(0, prog)

    for c in chrome_candidates:
        exe = shutil.which(c) if not os.path.isfile(c) else c
        if exe:
            return exe, "Chrome"

    # --- Edge ---
    edge_candidates = []

    if system == "Linux":
        edge_candidates = ["microsoft-edge", "microsoft-edge-stable"]
    elif system == "Darwin":
        edge_candidates = ["microsoft-edge", "microsoft-edge-stable"]
        edge_path = "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"
        if os.path.isfile(edge_path):
            edge_candidates.insert(0, edge_path)
    elif system == "Windows":
        edge_candidates = ["microsoft-edge", "msedge"]
        for prog in [
            os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
            os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
        ]:
            if os.path.isfile(prog):
                edge_candidates.insert(0, prog)

    for e in edge_candidates:
        exe = shutil.which(e) if not os.path.isfile(e) else e
        if exe:
            return exe, "Edge"

    return None, None


def main():
    if not os.path.isfile(HTML_PATH):
        print(
            f"Error: visualiser.html not found at {HTML_PATH}",
            file=sys.stderr,
        )
        sys.exit(1)

    browser, name = find_browser()
    if not browser:
        print("Chrome or Edge not available", file=sys.stderr)
        sys.exit(1)

    print(f"Launching EA Visualiser in {name}...")
    if platform.system() == "Darwin":
        subprocess.Popen(["open", HTML_PATH])
    else:
        subprocess.Popen([browser, HTML_PATH])


if __name__ == "__main__":
    main()
