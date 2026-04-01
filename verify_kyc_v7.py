import asyncio
import os
import time
from playwright.async_api import async_playwright

async def run_verification():
    async with async_playwright() as p:
        # Connect to existing browser or launch new one
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 800})
        page = await context.new_page()

        print("Starting KYC Verification Flow...")

        # 1. Go to Auth page
        try:
            await page.goto("http://localhost:3000/auth", wait_until="networkidle")
        except Exception as e:
            print(f"Failed to load page: {e}")
            await browser.close()
            return

        # Ensure we are on Signup mode
        if await page.get_by_text("Welcome back").is_visible():
            print("Switching to Sign Up mode...")
            await page.click("[data-testid='auth-toggle-mode']")

        # --- Step 1: Account ---
        print("Filling Step 1: Account...")
        email = f"test_kyc_{int(time.time())}@example.com"
        password = "Password123!" # Valid password (U+l+n)

        await page.fill("[data-testid='signup-name-input']", "John Doe Test")
        await page.fill("[data-testid='auth-email-input']", email)
        await page.fill("[data-testid='auth-password-input']", password)

        await page.screenshot(path="verification/screenshots/kyc_step1_filled.png")
        print("Clicking Continue...")
        await page.click("[data-testid='auth-submit-button']")

        # --- Step 2: Personal + Referral ---
        print("Waiting for Step 2...")
        try:
            await page.wait_for_selector("text=Step 2: Personal + Referral", timeout=5000)
        except:
            print("Step 2 indicator not found, checking if we are still on step 1")
            await page.screenshot(path="verification/screenshots/kyc_step1_error.png")
            # Maybe validation failed?

        print("Filling Step 2: Personal details...")
        # These don't have data-testids in the provided code, using labels or ids
        await page.fill("#phoneNumber", "+15551234567")
        await page.fill("#country", "United States")
        await page.fill("#city", "New York")

        await page.screenshot(path="verification/screenshots/kyc_step2_filled.png")
        print("Clicking Create Account...")
        await page.click("[data-testid='auth-submit-button']")

        # 2. Wait for OTP Modal
        print("Waiting for OTP Modal...")
        try:
            # The modal has data-testid="otp-verification-modal"
            await page.wait_for_selector("[data-testid='otp-verification-modal']", timeout=15000)
            print("OTP Modal appeared!")
        except Exception as e:
            print(f"OTP Modal did not appear: {e}")
            await page.screenshot(path="verification/screenshots/kyc_step2_error.png")
            await browser.close()
            return

        # 3. Enter OTP (Mock is 123456)
        print("Entering OTP...")
        otp = "123456"
        for i, digit in enumerate(otp):
            await page.fill(f"[data-testid='otp-input-{i}']", digit)

        # The modal usually auto-submits when last digit is entered or has a verify button
        # Based on OTPVerificationModal.tsx (from previous history), it calls onVerify

        print("Waiting for Dashboard redirect...")
        try:
            await page.wait_for_url("**/dashboard", timeout=10000)
            print("Successfully redirected to Dashboard!")
        except Exception as e:
            print(f"Redirection failed: {e}")
            await page.screenshot(path="verification/screenshots/kyc_otp_error.png")
            await browser.close()
            return

        # 4. Navigate to KYC
        print("Navigating to KYC page...")
        await page.goto("http://localhost:3000/kyc")
        await page.wait_for_load_state("networkidle")

        # 5. Fill KYC Steps
        # Step 1: Personal
        print("Filling KYC Step 1: Personal...")
        await page.fill("input[name='firstName']", "John")
        await page.fill("input[name='lastName']", "Doe")
        await page.fill("input[name='dob']", "1990-01-01")
        await page.click("button:has-text('Next')")

        # Step 2: Address
        print("Filling KYC Step 2: Address...")
        await page.fill("input[name='address']", "123 Main St")
        await page.fill("input[name='city']", "New York")
        await page.fill("input[name='zipCode']", "10001")
        await page.click("button:has-text('Next')")

        # Step 3: ID Upload
        print("Filling KYC Step 3: ID Upload...")
        # Mocking file upload if input exists
        # await page.set_input_files("input[type='file']", "test_id.png")
        await page.click("button:has-text('Next')")

        # Step 4: Selfie
        print("Filling KYC Step 4: Selfie...")
        # await page.set_input_files("input[type='file']", "test_selfie.png")
        await page.click("button:has-text('Submit KYC')")

        print("Waiting for KYC success message...")
        try:
            await page.wait_for_selector("text=KYC submitted successfully", timeout=10000)
            print("KYC Flow Complete!")
            await page.screenshot(path="verification/screenshots/kyc_success.png")
        except:
            print("KYC submission failed or success message not found")
            await page.screenshot(path="verification/screenshots/kyc_final_error.png")

        await browser.close()

if __name__ == "__main__":
    if not os.path.exists("verification/screenshots"):
        os.makedirs("verification/screenshots")
    asyncio.run(run_verification())
