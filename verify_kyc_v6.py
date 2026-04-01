import asyncio
from playwright.async_api import async_playwright
import os
import time

async def run_verification():
    async with async_playwright() as p:
        # Use a consistent viewport
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 800})
        page = await context.new_page()

        print("Starting KYC Verification Flow Test...")

        try:
            # 1. Navigate to Auth Page
            print("Navigating to /auth...")
            await page.goto("http://localhost:3000/auth")
            await page.wait_for_load_state("networkidle")

            # Ensure we are on Signup mode
            if await page.query_selector("text=Already have an account?"):
                pass
            else:
                print("Toggling to Signup mode...")
                await page.click("[data-testid='auth-toggle-mode']")

            # Step 1 of Signup
            print("Filling Signup Step 1...")
            await page.fill("[data-testid='signup-name-input']", "John Doe Test")
            await page.click("[data-testid='auth-submit-button']")

            # Step 2 of Signup
            print("Filling Signup Step 2...")
            test_email = f"test_kyc_{int(time.time())}@example.com"
            await page.fill("[data-testid='auth-email-input']", test_email)
            await page.fill("[data-testid='auth-password-input']", "Password123!")
            await page.screenshot(path="/home/jules/verification/screenshots/kyc_step0_signup.png")
            await page.click("[data-testid='auth-submit-button']")

            # 2. Handle OTP Modal
            print("Waiting for OTP Modal...")
            await page.wait_for_selector("[data-testid='otp-verification-modal']", timeout=15000)
            print("Entering OTP 123456...")

            # The OTP component auto-focuses and moves. We can just type or fill individual inputs.
            # Typing might be more reliable for auto-advance.
            await page.focus("[data-testid='otp-input-0']")
            await page.keyboard.type("123456")

            await page.screenshot(path="/home/jules/verification/screenshots/kyc_step1_otp_entered.png")

            # Wait for success animation and redirection to dashboard/setup
            print("Waiting for redirection after OTP...")
            await page.wait_for_url("**/dashboard", timeout=20000)
            print("Successfully reached Dashboard.")

            # 3. Navigate to KYC
            print("Navigating to KYC...")
            await page.goto("http://localhost:3000/kyc")
            await page.wait_for_load_state("networkidle")
            await page.screenshot(path="/home/jules/verification/screenshots/kyc_step2_start.png")

            # 4. Fill Personal Info (Step 0)
            print("Filling KYC Personal Info...")
            await page.fill("input[placeholder='As shown on ID']", "John Doe Test")
            await page.fill("input[type='date']", "1990-01-01")
            await page.fill("input[placeholder='+1 (555) 000-0000']", "+15550123456")
            await page.fill("input[placeholder='e.g. Software Engineer']", "Engineer")
            await page.click("text=Next Step")

            # 5. Fill Address (Step 1)
            print("Filling KYC Address...")
            await page.fill("input[placeholder='Unit, Street, etc.']", "123 Test St")
            await page.fill("input[placeholder='City']", "Test City")
            await page.fill("input[placeholder='Code']", "12345")
            await page.fill("input[placeholder='Country']", "Test Country")
            await page.click("text=Next Step")

            # 6. Upload Documents (Step 2)
            print("Uploading KYC Documents...")
            # We need to create dummy files
            with open("dummy_id.png", "wb") as f:
                f.write(b"dummy image data")

            # ID Front
            # The input is hidden inside FileUploadBox
            inputs = await page.query_selector_all("input[type='file']")
            print(f"Found {len(inputs)} file inputs")

            await inputs[0].set_input_files("dummy_id.png") # ID Front
            await inputs[1].set_input_files("dummy_id.png") # Address Proof (index 1 is proof of address in current layout if passport)

            await page.screenshot(path="/home/jules/verification/screenshots/kyc_step3_docs_uploaded.png")
            await page.click("text=Next Step")

            # 7. Selfie (Step 3)
            print("Uploading Selfie...")
            inputs = await page.query_selector_all("input[type='file']")
            # In step 3, there's only one FileUploadBox rendered
            await inputs[0].set_input_files("dummy_id.png")

            await page.screenshot(path="/home/jules/verification/screenshots/kyc_step4_selfie_uploaded.png")

            print("Submitting KYC...")
            await page.click("text=Submit Verification")

            # 8. Verify Submission
            await page.wait_for_selector("text=Application Pending", timeout=20000)
            print("KYC Application Pending! Test Passed.")
            await page.screenshot(path="/home/jules/verification/screenshots/kyc_step5_final.png")

        except Exception as e:
            print(f"Test failed: {e}")
            await page.screenshot(path="/home/jules/verification/screenshots/kyc_failure.png")
            raise e
        finally:
            await browser.close()
            if os.path.exists("dummy_id.png"):
                os.remove("dummy_id.png")

if __name__ == "__main__":
    asyncio.run(run_verification())
