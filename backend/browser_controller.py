import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from screenshot_handler import ScreenshotHandler
import re


class BrowserController:
    def __init__(self):
        self.browser = None
        self.page = None
        self.screenshot_handler = ScreenshotHandler()

    # ─────────────────────────── BROWSER SET-UP ────────────────────────────
    async def launch_browser(self) -> None:
        pw = await async_playwright().start()

        chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"  # adjust if needed

        self.browser = await pw.chromium.launch(
            headless=False,
            executable_path=chrome_path,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-dev-shm-usage'
            ]
        )

        context = await self.browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"
            )
        )
        self.page = await context.new_page()

        # Hide webdriver
        await self.page.add_init_script(
            "Object.defineProperty(navigator,'webdriver',{get:() => undefined});"
        )

    async def navigate_to_gmail(self) -> None:
        await self.page.goto("https://mail.google.com")
        await self.page.wait_for_load_state("networkidle")
        await self.screenshot_handler.capture(self.page, "gmail_homepage.png")

    # ────────────────────────── UTILITY HELPERS ────────────────────────────
    async def try_click(self, selectors: list[str], timeout: int = 4000) -> bool:
        """
        Loop through selectors; click the first one that exists & is visible.
        Returns True on success, False otherwise.
        """
        for sel in selectors:
            try:
                await self.page.wait_for_selector(sel, timeout=timeout)
                await self.page.click(sel)
                print(f"✓ Clicked selector → {sel}")
                return True
            except PlaywrightTimeout:
                print(f"✗ Selector not found in time → {sel}")
            except Exception as exc:
                print(f"✗ Click failed for {sel} → {exc}")
        return False

    async def dismiss_popups(self) -> None:
        """Close stray educational/feature pop-ups that overlay the UI."""
        ideoverlays = [
            'button:has-text("Got it")',
            'span:has-text("Got it")',
            'button:has-text("OK")',
            'button:has-text("Ok")',
            'button:has-text("Dismiss")',
            'div[role="button"]:has-text("Done")'
        ]
        await self.try_click(ideoverlays, timeout=1500)

    # ─────────────────────────── LOGIN SECTION ────────────────────────────
    async def login(self, email: str, password: str, step_callback=None) -> str:
        try:
            await self.page.wait_for_selector('input[type="email"]', timeout=10000)
            await self.page.fill('input[type="email"]', email)
            await self.screenshot_handler.capture(self.page, "email_filled.png")
            if step_callback:
                await step_callback("Email filled", "email_filled.png")

            await self.try_click(
                ['#identifierNext', 'button[jsname="LgbsSe"]', 'div:has-text("Next")']
            )
            await asyncio.sleep(2)
            if step_callback:
                await step_callback("Clicked Next after email", None)

            # Handle optional “sign-in faster” / passkey dialog
            await self.try_click(
                [
                    'button:has-text("Not now")',
                    'div[role="button"]:has-text("Not now")',
                    '.VfPpkd-LgbsSe:has-text("Not now")'
                ],
                timeout=3000
            )
            if step_callback:
                await step_callback("Handled 'Not now' dialog if present", None)

            await self.page.wait_for_selector('input[type="password"]', timeout=10000)
            await self.page.fill('input[type="password"]', password)
            await self.screenshot_handler.capture(self.page, "password_filled.png")
            if step_callback:
                await step_callback("Password filled", "password_filled.png")

            await self.try_click(
                ['#passwordNext', 'button[jsname="LgbsSe"]', 'div:has-text("Next")']
            )
            if step_callback:
                await step_callback("Clicked Next after password", None)

            # ──────────────── 2FA (Google Prompt) HANDLING ────────────────
            twofa_prompt_selectors = [
                'div:has-text("Check your phone")',
                'div:has-text("Yes, it\'s you")',
                'div:has-text("Did you get a notification?")',
                'div:has-text("Google Prompt")',
                'div:has-text("Try another way")',
                'h1:has-text("Check your phone")',
                'h1:has-text("Yes, it\'s you")',
            ]
            twofa_detected = False
            for sel in twofa_prompt_selectors:
                try:
                    await self.page.wait_for_selector(sel, timeout=4000)
                    twofa_detected = True
                    await self.screenshot_handler.capture(self.page, "2fa_prompt_detected.png")
                    if step_callback:
                        await step_callback("2FA prompt detected. Waiting for approval on your phone...", "2fa_prompt_detected.png")
                    break
                except PlaywrightTimeout:
                    continue
            if twofa_detected:
                max_wait = 120  # seconds
                poll_interval = 3
                waited = 0
                while waited < max_wait:
                    try:
                        await self.page.wait_for_selector('[gh="cm"], [data-tooltip*="Compose"]', timeout=2000)
                        await self.screenshot_handler.capture(self.page, "2fa_approved_inbox_loaded.png")
                        if step_callback:
                            await step_callback("2FA approved, inbox loaded", "2fa_approved_inbox_loaded.png")
                        break
                    except PlaywrightTimeout:
                        pass
                    try:
                        for sel in twofa_prompt_selectors:
                            if await self.page.query_selector(sel):
                                await self.screenshot_handler.capture(self.page, f"2fa_still_waiting_{waited}s.png")
                                if step_callback:
                                    await step_callback(f"Still waiting for 2FA approval... ({waited}s)", f"2fa_still_waiting_{waited}s.png")
                                break
                        else:
                            break
                    except Exception:
                        pass
                    await asyncio.sleep(poll_interval)
                    waited += poll_interval
                else:
                    await self.screenshot_handler.capture(self.page, "2fa_timeout.png")
                    if step_callback:
                        await step_callback("2FA approval timeout.", "2fa_timeout.png")
                    return "2FA approval timeout. Please approve the login on your phone."

            await self.page.wait_for_selector('[gh="cm"], [data-tooltip*="Compose"]', timeout=30000)
            await self.screenshot_handler.capture(self.page, "inbox_loaded.png")
            if step_callback:
                await step_callback("Inbox loaded", "inbox_loaded.png")
            return "Login successful."

        except Exception as exc:
            await self.screenshot_handler.capture(self.page, "gmail_login_error.png")
            return f"Login error → {exc}"

    # ───────────────────────── COMPOSE SECTION ────────────────────────────
    async def open_compose_window(self) -> bool:
        compose_selectors = [
            'div[gh="cm"]',                   # primary Gmail compose button
            '[data-tooltip="Compose"]',
            '[data-tooltip^="Compose"]',
            'div:has-text("Compose")',
            '.T-I.T-I-KE.L3'
        ]
        clicked = await self.try_click(compose_selectors, timeout=6000)
        if not clicked:
            # Fallback: keyboard shortcut "c"
            await self.page.keyboard.press('c')
            clicked = True
        await asyncio.sleep(1.5)
        return clicked

    async def compose_email(self, recipient: str, subject: str, body: str, step_callback=None) -> str:
        try:
            await self.dismiss_popups()
            if step_callback:
                await step_callback("Dismissed popups", None)

            if not await self.open_compose_window():
                if step_callback:
                    await step_callback("Could not launch compose window.", None)
                return "Could not launch compose window."
            if step_callback:
                await step_callback("Compose window opened", None)

            # --- RECIPIENT ---
            recipient = recipient.strip()
            if not ("@" in recipient and "." in recipient):
                await self.screenshot_handler.capture(self.page, "recipient_invalid.png")
                if step_callback:
                    await step_callback(f"Recipient email '{recipient}' is not valid.", "recipient_invalid.png")
                return f"Recipient email '{recipient}' is not valid."

            to_locators = [
                'textarea[name="to"]',
                'input[name="to"]',
                'input[aria-label^="To"]',
                'textarea[aria-label^="To"]',
                'div[aria-label="To"] div[contenteditable="true"]',
                '.aoD.az6 input',
                '.vO'
            ]
            found_to = False
            for sel in to_locators:
                try:
                    await self.page.wait_for_selector(sel, timeout=6000)
                    await self.page.fill(sel, recipient)
                    found_to = True
                    fname = f"recipient_filled_{sanitize_filename(sel)}.png"
                    await self.screenshot_handler.capture(self.page, fname)
                    if step_callback:
                        await step_callback(f"Recipient filled using selector {sel}", fname)
                    break
                except PlaywrightTimeout:
                    continue
            if not found_to:
                await self.screenshot_handler.capture(self.page, "recipient_not_found.png")
                if step_callback:
                    await step_callback("Recipient field not found.", "recipient_not_found.png")
                return "Recipient field not found."

            # --- SUBJECT ---
            subj_locators = [
                'input[name="subjectbox"]',
                'input[aria-label^="Subject"]',
                '.aoT input'
            ]
            found_subject = False
            for sel in subj_locators:
                try:
                    await self.page.wait_for_selector(sel, timeout=6000)
                    await self.page.fill(sel, subject)
                    found_subject = True
                    fname = f"subject_filled_{sanitize_filename(sel)}.png"
                    await self.screenshot_handler.capture(self.page, fname)
                    if step_callback:
                        await step_callback(f"Subject filled using selector {sel}", fname)
                    break
                except PlaywrightTimeout:
                    continue
            if not found_subject:
                await self.screenshot_handler.capture(self.page, "subject_not_found.png")
                if step_callback:
                    await step_callback("Subject field not found.", "subject_not_found.png")
                return "Subject field not found."

            # --- BODY ---
            body_locators = [
                'div[aria-label="Message Body"]',
                'div[role="textbox"]',
                '.Am.Al.editable'
            ]
            found_body = False
            for sel in body_locators:
                try:
                    await self.page.wait_for_selector(sel, timeout=6000)
                    await self.page.fill(sel, body)
                    found_body = True
                    fname = f"body_filled_{sanitize_filename(sel)}.png"
                    await self.screenshot_handler.capture(self.page, fname)
                    if step_callback:
                        await step_callback(f"Body filled using selector {sel}", fname)
                    break
                except PlaywrightTimeout:
                    continue
            if not found_body:
                await self.screenshot_handler.capture(self.page, "body_not_found.png")
                if step_callback:
                    await step_callback("Body field not found.", "body_not_found.png")
                return "Body field not found."

            # --- SEND ---
            send_locators = [
                'div[role="button"][data-tooltip^="Send"]',
                'div[role="button"]:has-text("Send")',
                '.T-I.J-J5-Ji.aoO.v7.T-I-atl'
            ]
            sent = await self.try_click(send_locators, timeout=4000)
            if not sent:
                await self.page.keyboard.press("Control+Enter")
                if step_callback:
                    await step_callback("Send button not found, used keyboard shortcut.", None)
            else:
                if step_callback:
                    await step_callback("Clicked Send button", None)

            await asyncio.sleep(2)
            await self.screenshot_handler.capture(self.page, "sent_confirmation.png")
            if step_callback:
                await step_callback("Email sent confirmation", "sent_confirmation.png")
            return "Email sent successfully."

        except Exception as exc:
            await self.screenshot_handler.capture(self.page, "gmail_compose_error.png")
            if step_callback:
                await step_callback(f"Compose/send error → {exc}", "gmail_compose_error.png")
            return f"Compose/send error → {exc}"

    # ───────────────────────────── CLEAN-UP ────────────────────────────────
    async def close(self):
        if self.browser:
            await self.browser.close()


# ───────────────────────────── LOCAL TEST ─────────────────────────────────
if __name__ == "__main__":
    async def _demo():
        bot = BrowserController()
        await bot.launch_browser()
        await bot.navigate_to_gmail()

        login_status = await bot.login("test9646123@gmail.com", "Test@9646")
        print(login_status)

        if login_status.startswith("Login successful"):
            send_status = await bot.compose_email(
                recipient="reportinsurebuzz@gmail.com",
                subject="AI Agent Task - Demo",
                body="This is a demo email sent by the Playwright browser-control agent."
            )
            print(send_status)

        await asyncio.sleep(5)
        await bot.close()

    asyncio.run(_demo())


def sanitize_filename(s: str) -> str:
    return re.sub(r'[<>:"/\\|?*^\[\]= ]', '_', s)
