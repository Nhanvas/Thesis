"""record_demo.py — records the fallback demo video for the thesis defense (CC_DEMO_PREP.md
step 8). Lives OUTSIDE the repository (F:/Study/Thesis/Defense/demo/), never under web_demo/
or src/. Drives the already-running SzScan web demo (backend on :8000, frontend on :5173)
with Playwright for Python, chb03, the event chosen in DEMO_EVENT.md (Recording 1 / Event 1,
onset 388.0s / offset 444.0s).

Never prints ADMIN_USER / ADMIN_PASS; reads them from web_demo/backend/.env at run time only.
"""
import re
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ENV_PATH = Path("F:/Study/Thesis/Code/web_demo/backend/.env")
BASE_URL = "http://localhost:5173"
VIDEO_DIR = Path("F:/Study/Thesis/Defense/demo/rehearsal_20261017/video_raw")
SHOT_DIR = Path("F:/Study/Thesis/Defense/demo/rehearsal_20261017")
TARGET_SECONDS = 88  # middle of the required 1:20-1:40 window


def read_env_credentials(path: Path) -> tuple[str, str]:
    text = path.read_text()
    user = re.search(r"^ADMIN_USER=(.*)$", text, re.M).group(1).strip()
    pw = re.search(r"^ADMIN_PASS=(.*)$", text, re.M).group(1).strip()
    return user, pw


def main():
    user, pw = read_env_credentials(ENV_PATH)  # never printed below
    VIDEO_DIR.mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            record_video_dir=str(VIDEO_DIR),
            record_video_size={"width": 1920, "height": 1080},
        )
        page = context.new_page()

        # 1. Log in, land on the patient list (Database screen).
        page.goto(BASE_URL)
        page.fill("#username", user)
        page.fill("#password", pw)
        page.click("button:has-text('Log in')")
        page.wait_for_selector("text=Create new", timeout=20000)
        page.wait_for_timeout(8000)
        page.screenshot(path=str(SHOT_DIR / "demo_shot_1.png"))  # patient list
        print(f"[{time.time()-t0:5.1f}s] patient list shown", flush=True)

        # 2. Open chb03 (its first file by start_time is Recording 1 = chb03_01.edf, the
        # same file DEMO_EVENT.md's chosen event lives in).
        page.click("text='chb03'")
        page.click("button:has-text('Open')")
        page.wait_for_selector("text=Seizure detection", timeout=20000)
        print(f"[{time.time()-t0:5.1f}s] chb03 opened", flush=True)

        # 3. Score timeline, long enough for a viewer to register it.
        page.wait_for_timeout(14000)
        print(f"[{time.time()-t0:5.1f}s] score timeline shown", flush=True)

        # 4. Click the chosen event (the only AI event in this file) — jumps Panel EEG to
        # its onset and expands the Panel Event row. NOTE: once the view window includes
        # the event, EegPanel's own "Event Time" strip ALSO renders a (non-interactive)
        # "Event 1" label, so exact-text "Event 1" has two matches from here on; .last is
        # the Panel Event list row (DOM order: EEG panel column first, then Panel Event
        # column) — confirmed empirically, see rehearsal_20261017 handback notes.
        page.locator("text='Event 1'").last.click()
        page.wait_for_timeout(4000)
        print(f"[{time.time()-t0:5.1f}s] event selected, EEG jumped to onset", flush=True)

        # 5. EEG around onset/offset; play at 2x for a few seconds.
        page.wait_for_timeout(6000)
        page.click("button:has-text('1x')")
        page.click("text='2x'")
        page.wait_for_timeout(300)
        page.click("button[aria-label='Play']")
        page.wait_for_timeout(10000)
        page.screenshot(path=str(SHOT_DIR / "demo_shot_2.png"))  # EEG playing at 2x
        page.click("button[aria-label='Pause']")
        page.wait_for_timeout(4000)
        print(f"[{time.time()-t0:5.1f}s] played EEG at 2x around the event", flush=True)

        # 6. Channel panel (Attribution), already docked below Panel Event once an event
        # is selected — long enough to look at it.
        page.wait_for_timeout(14000)
        page.screenshot(path=str(SHOT_DIR / "demo_shot_3.png"))  # channel panel
        print(f"[{time.time()-t0:5.1f}s] channel panel shown", flush=True)

        # 7. Accept the event with the demo comment, then Save. NOTE: "Accept"/"Save" also
        # appear once per channel row in the Attribution panel below (19 "Accept" matches
        # total for chb03_01.edf's 18 channels + this one) — .first is the Panel Event
        # (AiExpand) button, which renders before Attribution Panel in the DOM.
        page.fill("textarea[placeholder='Comment']", "reviewed in the demo")
        page.locator("button:has-text('Accept')").first.click()
        page.locator("button:has-text('Save')").first.click()
        page.wait_for_timeout(6000)
        print(f"[{time.time()-t0:5.1f}s] event accepted and saved", flush=True)

        # 8. Back to the timeline: collapse the event row.
        page.locator("text='Event 1'").last.click()
        page.wait_for_timeout(8000)
        page.screenshot(path=str(SHOT_DIR / "demo_shot_4.png"))  # back to timeline
        print(f"[{time.time()-t0:5.1f}s] back to timeline", flush=True)

        elapsed = time.time() - t0
        pad = TARGET_SECONDS - elapsed
        if pad > 0:
            page.wait_for_timeout(min(pad, 60) * 1000)
        print(f"[{time.time()-t0:5.1f}s] total elapsed before close", flush=True)

        context.close()  # video file is finalized on context close
        browser.close()

        video_path = page.video.path()
        print(f"RAW_VIDEO={video_path}", flush=True)


if __name__ == "__main__":
    sys.exit(main())
