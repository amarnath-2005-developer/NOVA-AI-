"""
NOVA AI 2.0 — Universal Browser Controller
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Playwright-based async browser engine.
NO app-specific logic — all interactions are generic.
Persistent context with session reuse for speed.
"""

import os
import asyncio


class BrowserController:
    """
    Universal browser interaction controller.
    Lazy-initialized: Playwright only starts when first needed.
    Persistent context for session reuse (cookies, auth, etc.).
    """

    def __init__(self):
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None
        self._initialized = False

    async def initialize(self):
        """Start Playwright and create a persistent browser context."""
        if self._initialized:
            return
        try:
            from playwright.async_api import async_playwright
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=False,  # Visible for user observation
                args=["--start-maximized", "--disable-blink-features=AutomationControlled"]
            )
            self._context = await self._browser.new_context(
                viewport=None,  # Use full window size
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            self._page = await self._context.new_page()
            self._initialized = True
        except Exception as e:
            raise RuntimeError(f"Browser initialization failed: {e}")

    async def _ensure_page(self):
        """Ensure we have an active page."""
        if not self._initialized:
            await self.initialize()
        if self._page.is_closed():
            self._page = await self._context.new_page()
        return self._page

    async def goto(self, url: str):
        """Navigate to a URL."""
        page = await self._ensure_page()
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)

    async def click(self, selector: str):
        """
        Click an element using smart selector resolution.
        Tries: CSS selector → text content → aria-label → placeholder.
        """
        page = await self._ensure_page()

        strategies = [
            selector,                                    # Direct CSS
            f"text={selector}",                          # Text content
            f"[aria-label*='{selector}' i]",            # Aria label
            f"[placeholder*='{selector}' i]",           # Placeholder
            f"button:has-text('{selector}')",            # Button text
            f"a:has-text('{selector}')",                # Link text
            f"[title*='{selector}' i]",                 # Title attribute
        ]

        for strat in strategies:
            try:
                el = page.locator(strat).first
                if await el.is_visible(timeout=2000):
                    await el.click(timeout=5000)
                    return
            except Exception:
                continue

        raise Exception(f"Could not find clickable element: {selector}")

    async def type_text(self, selector: str, text: str):
        """Type text into an input element with smart selector resolution."""
        page = await self._ensure_page()

        strategies = [
            selector,
            f"[placeholder*='{selector}' i]",
            f"[aria-label*='{selector}' i]",
            f"[name*='{selector}' i]",
            f"input[type='text']",
        ]

        for strat in strategies:
            try:
                el = page.locator(strat).first
                if await el.is_visible(timeout=2000):
                    await el.fill(text, timeout=5000)
                    return
            except Exception:
                continue

        raise Exception(f"Could not find input element: {selector}")

    async def extract_text(self, selector: str = "body") -> str:
        """Extract visible text from page or specific element."""
        page = await self._ensure_page()
        try:
            el = page.locator(selector).first
            return await el.inner_text(timeout=5000)
        except Exception:
            return await page.inner_text("body")

    async def screenshot(self, path: str):
        """Capture page screenshot."""
        page = await self._ensure_page()
        await page.screenshot(path=path, full_page=False)

    async def scroll(self, direction: str = "down", amount: int = 500):
        """Scroll the page."""
        page = await self._ensure_page()
        delta = amount if direction == "down" else -amount
        await page.mouse.wheel(0, delta)

    async def wait_for(self, selector: str, timeout: int = 10000):
        """Wait for an element to appear."""
        page = await self._ensure_page()
        await page.wait_for_selector(selector, timeout=timeout)

    async def upload_file(self, selector: str, file_path: str):
        """Upload a file to a file input."""
        page = await self._ensure_page()
        await page.set_input_files(selector, file_path)

    async def get_page_url(self) -> str:
        """Get current page URL."""
        page = await self._ensure_page()
        return page.url

    async def get_page_title(self) -> str:
        """Get current page title."""
        page = await self._ensure_page()
        return await page.title()

    async def press_key(self, key: str):
        """Press a keyboard key."""
        page = await self._ensure_page()
        await page.keyboard.press(key)

    async def close(self):
        """Clean up browser resources."""
        try:
            if self._context: await self._context.close()
            if self._browser: await self._browser.close()
            if self._playwright: await self._playwright.stop()
        except Exception:
            pass
        self._initialized = False
