from playwright.sync_api import sync_playwright
import os

def run_cuj(page):
    try:
        page.goto("http://localhost:3000")
        page.wait_for_timeout(5000)

        # Type a math command
        page.get_by_placeholder("Ask Omnitropyc or enter command...").fill("solve x**2-9 x")
        page.wait_for_timeout(1000)
        page.get_by_role("button", name="Execute").click()
        page.wait_for_timeout(3000)

        # Type an optimization command
        page.get_by_placeholder("Ask Omnitropyc or enter command...").fill("optimize")
        page.wait_for_timeout(1000)
        page.get_by_role("button", name="Execute").click()
        page.wait_for_timeout(3000)

        # Take screenshot of the final state
        screenshot_path = os.path.abspath("verification/screenshots/verification.png")
        page.screenshot(path=screenshot_path)
        print(f"Screenshot saved to {screenshot_path}")
    except Exception as e:
        print(f"Error during CUJ: {e}")

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        video_dir = os.path.abspath("verification/videos")
        context = browser.new_context(
            record_video_dir=video_dir
        )
        page = context.new_page()
        try:
            run_cuj(page)
        finally:
            context.close()
            browser.close()
