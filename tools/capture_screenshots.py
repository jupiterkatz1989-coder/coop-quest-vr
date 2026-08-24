#!/usr/bin/env python3
"""Genera las cuatro capturas de aceptación mediante Chrome DevTools."""
from __future__ import annotations

import argparse
import base64
import json
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path

import websocket

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CHROME = Path("/home/jupi/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome")


class CDP:
    def __init__(self, url: str):
        self.socket = websocket.create_connection(url, timeout=30, origin="http://127.0.0.1:9224")
        self.sequence = 0

    def call(self, method: str, params: dict | None = None) -> dict:
        self.sequence += 1
        request_id = self.sequence
        self.socket.send(json.dumps({"id": request_id, "method": method, "params": params or {}}))
        while True:
            response = json.loads(self.socket.recv())
            if response.get("id") == request_id:
                if "error" in response:
                    raise RuntimeError(response["error"])
                return response.get("result", {})

    def evaluate(self, expression: str) -> None:
        result = self.call("Runtime.evaluate", {"expression": expression, "awaitPromise": True, "returnByValue": True})
        value = result.get("result", {})
        if value.get("subtype") == "error":
            raise RuntimeError(value.get("description", "Error JavaScript"))

    def screenshot(self, path: Path) -> None:
        payload = self.call("Page.captureScreenshot", {"format": "png", "captureBeyondViewport": False})
        path.write_bytes(base64.b64decode(payload["data"]))


def wait_debugger(port: int) -> list[dict]:
    endpoint = f"http://127.0.0.1:{port}/json/list"
    for _ in range(100):
        try:
            pages = json.load(urllib.request.urlopen(endpoint, timeout=2))
            if any(item.get("type") == "page" for item in pages):
                return pages
        except Exception:
            pass
        time.sleep(0.1)
    raise RuntimeError("Chrome DevTools no llegó a estar disponible")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:4173/coop-quest-vr/")
    parser.add_argument("--chrome", type=Path, default=DEFAULT_CHROME)
    args = parser.parse_args()
    output = ROOT / "screenshots"
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="coopquest-chrome-") as profile:
        process = subprocess.Popen([
            str(args.chrome), "--headless=new", "--no-sandbox", "--disable-gpu",
            "--remote-allow-origins=*", "--remote-debugging-port=9224",
            f"--user-data-dir={profile}", "--window-size=1440,1000", args.url,
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            pages = wait_debugger(9224)
            page = next(item for item in pages if item.get("type") == "page")
            cdp = CDP(page["webSocketDebuggerUrl"])
            cdp.call("Page.enable")
            cdp.call("Runtime.enable")
            cdp.call("Emulation.setDeviceMetricsOverride", {
                "width": 1440, "height": 1000, "deviceScaleFactor": 1, "mobile": False,
            })
            time.sleep(2)
            cdp.evaluate("document.fonts.ready")
            cdp.screenshot(output / "galeria-ampliada.png")

            cdp.evaluate("""
              (() => { const label=[...document.querySelectorAll('.filters label')].find(x=>x.textContent.includes('Tipo de plataforma'));
                const select=label.querySelector('select'); select.value='pcvr'; select.dispatchEvent(new Event('change',{bubbles:true})); window.scrollTo(0,0); })()
            """)
            time.sleep(1)
            cdp.screenshot(output / "filtro-tipo-plataforma-pcvr.png")

            cdp.evaluate("""
              (() => { const platform=[...document.querySelectorAll('.filters label')].find(x=>x.textContent.includes('Tipo de plataforma')).querySelector('select');
                platform.value='all'; platform.dispatchEvent(new Event('change',{bubbles:true}));
                const input=document.querySelector('.filters input[placeholder]'); const setter=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set;
                setter.call(input,'Demeo'); input.dispatchEvent(new Event('input',{bubbles:true})); })()
            """)
            time.sleep(1)
            cdp.evaluate("[...document.querySelectorAll('.card-main')].find(x=>x.textContent.includes('Demeo'))?.click()")
            time.sleep(1)
            cdp.screenshot(output / "ficha-precio-eur.png")

            cdp.evaluate("document.querySelector('.close')?.click()")
            cdp.evaluate("""
              (() => { const input=document.querySelector('.filters input[placeholder]'); const setter=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set;
                setter.call(input,'A Township Tale'); input.dispatchEvent(new Event('input',{bubbles:true})); })()
            """)
            time.sleep(1)
            cdp.evaluate("[...document.querySelectorAll('.card-main')].find(x=>x.textContent.includes('A Township Tale'))?.click()")
            time.sleep(1)
            cdp.screenshot(output / "ficha-meta-precio-no-verificado.png")
        finally:
            process.terminate()
            process.wait(timeout=10)


if __name__ == "__main__":
    main()
