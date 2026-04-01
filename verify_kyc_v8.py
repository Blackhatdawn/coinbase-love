import asyncio
from playwright.async_api import async_playwright
import time
import os

async def run_verification():
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=True)
        # Create context with detailed logging
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 800},
            record_video_dir="verification/videos/"
        )
        page = await context.new_page()

        # Log all console messages
        page.on("console", lambda msg: print(f"BROWSER CONSOLE: {msg.type}: {msg.text}"))
        # Log all network requests
        page.on("request", lambda request: print(f"NET REQUEST: {request.method} {request.url}"))
        page.on("response", lambda response: print(f"NET RESPONSE: {response.status} {response.url}"))

        print("Navigating to Auth page...")
        await page.goto("http://localhost:3000/auth")

        # Wait for page to load
        await page.wait_for_selector("text=Welcome back")

        # Switch to Sign Up
        print("Switching to Sign Up...")
        await page.click("text=Sign up")
        await page.wait_for_selector("text=Create account")

        # Step 1: Account Info
        print("Filling Step 1...")
        test_email = f"test_kyc_{int(time.time())}@example.com"
        await page.fill('input[placeholder="John Doe"]', "Test User")
        await page.fill('input[placeholder="you@example.com"]', test_email)
        await page.fill('input[placeholder="••••••••"]', "Password123!")

        print("Clicking Continue...")
        await page.click("text=Continue")

        # Step 2: Personal Info
        print("Filling Step 2...")
        await page.wait_for_selector("text=Step 2: Personal + Referral")
        await page.fill('input[placeholder="+1 555 123 4567"]', "+15551234567")
        await page.fill('input[placeholder="United States"]', "United States")
        await page.fill('input[placeholder="New York"]', "New York")

        # Take screenshot before submission
        os.makedirs("verification/screenshots", exist_ok=True)
        await page.screenshot(path="verification/screenshots/kyc_step2_filled_v8.png")

        print("Clicking Create Account...")
        # Use a more specific selector for the submit button to avoid ambiguity
        await page.click('button[data-testid="auth-submit-button"]')

        # Wait for OTP modal or error
        print("Waiting for OTP Modal or error...")
        try:
            # Increase timeout and wait for either the modal or a toast error
            await page.wait_for_selector("text=Verify Your Email", timeout=30000)
            print("OTP Modal appeared successfully!")
            await page.screenshot(path="verification/screenshots/kyc_otp_success_v8.png")
        except Exception as e:
            print(f"Failed to see OTP Modal: {str(e)}")
            await page.screenshot(path="verification/screenshots/kyc_step2_error_v8.png")

            # Check for toast messages
            toasts = await page.query_selector_all(".toast")
            for toast in toasts:
                print(f"TOAST MESSAGE: {await toast.inner_text()}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_verification())
