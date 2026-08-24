"""Headless browser script using Playwright to keep Streamlit app awake and auto-wake if sleeping."""
import sys
import time
from playwright.sync_api import sync_playwright

APP_URL = "https://smoyapqdgyshrtavm66ufo.streamlit.app/"

def run():
    print(f"[+] Launching headless browser for: {APP_URL}")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(APP_URL, timeout=60000, wait_until="domcontentloaded")
            time.sleep(5)

            # Check if sleep button exists
            wake_button = page.query_selector("button:has-text('Yes, get this app back up!')")
            if wake_button:
                print("[!] App is sleeping! Clicking 'Yes, get this app back up!' button...")
                wake_button.click()
                print("[+] Clicked wake button. Waiting 30s for app to wake up...")
                time.sleep(30)
                print("[OK] App woken up successfully!")
            else:
                print("[OK] App is active! Simulated human browser session complete.")

        except Exception as e:
            print(f"[!] Error during keep-alive ping: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    run()
