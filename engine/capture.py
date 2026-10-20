"""Deterministic frame capture: render(t) -> browser screenshot -> JPEG sequence."""
from __future__ import annotations

import argparse
import asyncio
import time
from pathlib import Path

from playwright.async_api import async_playwright


async def run(args):
    html = Path(args.html).resolve()
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    url = html.as_uri()

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            channel="chrome",
            headless=True,
            args=["--hide-scrollbars", "--force-color-profile=srgb", "--disable-lcd-text"],
        )
        page = await browser.new_page(
            viewport={"width": args.width, "height": args.height},
            device_scale_factor=1,
        )
        page.set_default_timeout(120000)
        await page.goto(url, wait_until="load")
        await page.wait_for_function("window.__ready === true")
        await page.evaluate("document.fonts.ready.then(() => true)")
        await page.evaluate("(t) => window.render(t)", 0.0)

        if args.still:
            for item in args.still.split(","):
                t = float(item)
                await page.evaluate("(t) => window.render(t)", t)
                await page.wait_for_timeout(60)
                path = out / f"still_{t:07.2f}.png"
                await page.screenshot(path=str(path), clip={"x": 0, "y": 0, "width": args.width, "height": args.height})
                print(f"still {t:.2f}s -> {path.name}", flush=True)
            await browser.close()
            return

        total = int(round(args.duration * args.fps))
        start_frame = 0
        if args.resume:
            existing = sorted(out.glob("*.jpg"))
            start_frame = len(existing)
            if start_frame:
                print(f"resume at frame {start_frame}", flush=True)
        t0 = time.time()
        for i in range(start_frame, total):
            t = i / args.fps
            await page.evaluate("(t) => window.render(t)", t)
            path = out / f"{i:06d}.jpg"
            await page.screenshot(
                path=str(path),
                type="jpeg",
                quality=args.quality,
                clip={"x": 0, "y": 0, "width": args.width, "height": args.height},
            )
            if i % 120 == 0 or i == total - 1:
                elapsed = time.time() - t0
                rate = (i - start_frame + 1) / max(elapsed, 1e-6)
                eta = (total - i - 1) / max(rate, 1e-6)
                print(f"frame {i + 1}/{total}  {rate:.1f} fps  eta {eta / 60:.1f} min", flush=True)
        await browser.close()
        print(f"done {total} frames in {(time.time() - t0) / 60:.2f} min", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--html", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--width", type=int, default=1920)
    ap.add_argument("--height", type=int, default=1080)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--duration", type=float, required=True)
    ap.add_argument("--quality", type=int, default=94)
    ap.add_argument("--still", default="")
    ap.add_argument("--resume", action="store_true")
    asyncio.run(run(ap.parse_args()))


if __name__ == "__main__":
    main()
