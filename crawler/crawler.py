#!/usr/bin/env python3
"""
Web Crawler for JavaScript-enabled websites
"""

import asyncio
from playwright.async_api import async_playwright
import os
import re
from urllib.parse import urlparse
from typing import List, Dict, Optional

from constants import (
    DEFAULT_OUTPUT_FOLDER,
    DEFAULT_TIMEOUT,
    DEFAULT_WAIT_TIME,
    DEFAULT_DELAY_BETWEEN_REQUESTS,
    USER_AGENT,
    MAIN_CONTENT_SELECTORS,
    ELEMENTS_TO_REMOVE,
    MIN_CONTENT_LENGTH,
)
from logger_utils import get_crawler_logger, get_content_logger, get_file_logger


class ContentData:
    """Data class for storing webpage content"""

    def __init__(self, url: str, title: str = "", content: str = "", status: str = ""):
        self.url = url
        self.title = title
        self.content = content
        self.status = status

    def to_dict(self) -> Dict[str, str]:
        return {
            "url": self.url,
            "title": self.title,
            "content": self.content,
            "status": self.status,
        }


class Crawler:
    """
    JavaScript-enabled web crawler using Playwright
    """

    def __init__(self, output_folder: str = DEFAULT_OUTPUT_FOLDER):
        self.output_folder = output_folder
        self.logger = get_crawler_logger()
        self.content_logger = get_content_logger()
        self.file_logger = get_file_logger()

        # Create output folder if it doesn't exist
        self._ensure_output_folder()

        self.logger.info(
            f"Crawler initialized with output folder: {self.output_folder}"
        )

    def _ensure_output_folder(self) -> None:
        """Ensure the output folder exists"""
        try:
            os.makedirs(self.output_folder, exist_ok=True)
            self.file_logger.info(
                f"Output folder created/verified: {self.output_folder}"
            )
        except Exception as e:
            self.file_logger.error(
                f"Failed to create output folder {self.output_folder}: {e}"
            )
            raise

    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize text content

        Args:
            text: Raw text to clean

        Returns:
            Cleaned text
        """
        if not text:
            return ""

        # Remove extra whitespace and normalize
        lines = [line.strip() for line in text.splitlines()]
        lines = [line for line in lines if line]
        cleaned = "\n".join(lines)

        self.content_logger.debug(
            f"Cleaned text from {len(text)} to {len(cleaned)} characters"
        )
        return cleaned

    def _generate_safe_filename(self, url: str, title: str = "") -> str:
        """
        Generate a safe filename from URL and title

        Args:
            url: Page URL
            title: Page title

        Returns:
            Safe filename for the content
        """
        # Use title if available, otherwise use URL path
        if title and title.strip():
            base_name = re.sub(r"[^\w\s-]", "", title)[:50]
        else:
            parsed_url = urlparse(url)
            base_name = parsed_url.path.replace("/", "_")
            if not base_name or base_name == "_":
                base_name = parsed_url.netloc.replace(".", "")

        # Clean filename
        safe_name = re.sub(r"[^\w\s-]", "", base_name)
        safe_name = re.sub(r"[-\s]+", "-", safe_name)
        safe_name = safe_name.strip("-")

        filename = f"{safe_name}.txt"

        self.file_logger.debug(f"Generated filename '{filename}' for URL: {url}")
        return filename

    async def _extract_content_from_page(self, page, url: str) -> ContentData:
        """
        Extract text content from a webpage using Playwright

        Args:
            page: Playwright page object
            url: URL being processed

        Returns:
            ContentData object with extracted information
        """
        try:
            self.logger.info(f"Loading page: {url}")

            # Navigate to the page
            await page.goto(url, wait_until="networkidle", timeout=DEFAULT_TIMEOUT)

            # Wait for dynamic content to load
            await page.wait_for_timeout(DEFAULT_WAIT_TIME)

            # Extract title
            title = await page.title()
            self.content_logger.info(f"Page title: {title}")

            # Remove unwanted elements
            await self._remove_unwanted_elements(page)

            # Extract main content
            main_content = await self._extract_main_content(page)

            # Clean up content
            cleaned_content = self._clean_text(main_content)

            self.content_logger.info(
                f"Extracted {len(cleaned_content)} characters from {url}"
            )

            return ContentData(
                url=url, title=title, content=cleaned_content, status="success"
            )

        except Exception as e:
            error_msg = f"Error processing {url}: {str(e)}"
            self.logger.error(error_msg)
            return ContentData(url=url, title="", content="", status=f"error: {str(e)}")

    async def _remove_unwanted_elements(self, page) -> None:
        """Remove unwanted elements from the page"""
        try:
            await page.evaluate(
                f"""
                const elementsToRemove = {ELEMENTS_TO_REMOVE};
                
                elementsToRemove.forEach(selector => {{
                    const elements = document.querySelectorAll(selector);
                    elements.forEach(el => el.remove());
                }});
            """
            )
            self.content_logger.debug("Removed unwanted elements from page")
        except Exception as e:
            self.content_logger.warning(f"Failed to remove unwanted elements: {e}")

    async def _extract_main_content(self, page) -> str:
        """Extract main content from the page"""
        main_content = ""

        # Try to find main content area
        for selector in MAIN_CONTENT_SELECTORS:
            try:
                element = page.locator(selector).first
                if await element.count() > 0:
                    main_content = await element.inner_text()
                    self.content_logger.debug(
                        f"Found content using selector: {selector}"
                    )
                    break
            except Exception as e:
                self.content_logger.debug(f"Selector '{selector}' failed: {e}")
                continue

        # Fallback to body content if no main content found
        if not main_content or len(main_content.strip()) < MIN_CONTENT_LENGTH:
            try:
                main_content = await page.locator("body").inner_text()
                self.content_logger.debug("Used body content as fallback")
            except Exception as e:
                self.content_logger.error(f"Failed to extract body content: {e}")
                main_content = ""

        return main_content

    def _save_content_to_file(self, content_data: ContentData) -> Optional[str]:
        """
        Save extracted content to a file

        Args:
            content_data: ContentData object to save

        Returns:
            File path if successful, None otherwise
        """
        filename = self._generate_safe_filename(content_data.url, content_data.title)
        filepath = os.path.join(self.output_folder, filename)

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"URL: {content_data.url}\n")
                f.write(f"Title: {content_data.title}\n")
                f.write("=" * 50 + "\n\n")
                f.write(content_data.content)

            self.file_logger.info(f"Saved content to: {filename}")
            return filepath

        except Exception as e:
            self.file_logger.error(f"Error saving {filename}: {str(e)}")
            return None

    def _is_content_valid(self, content_data: ContentData) -> bool:
        """
        Check if content is valid and meaningful

        Args:
            content_data: ContentData to validate

        Returns:
            True if content is valid, False otherwise
        """
        if content_data.status != "success":
            return False

        if not content_data.content.strip():
            return False

        if len(content_data.content) < MIN_CONTENT_LENGTH:
            self.content_logger.warning(
                f"Content too short for {content_data.url}: {len(content_data.content)} chars"
            )
            return False

        # Check for JavaScript error messages
        if (
            "javascript" in content_data.content.lower()
            and len(content_data.content) < 200
        ):
            self.content_logger.warning(
                f"Detected JavaScript error message for {content_data.url}"
            )
            return False

        return True

    async def crawl_urls(self, urls: List[str]) -> Dict[str, any]:
        """
        Crawl a list of URLs and save content

        Args:
            urls: List of URLs to crawl

        Returns:
            Dictionary with crawling results
        """
        self.logger.info(f"Starting crawl of {len(urls)} URLs")

        results = {"successful": 0, "failed": 0, "files_created": [], "errors": []}

        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(user_agent=USER_AGENT)
            page = await context.new_page()

            self.logger.info("Browser launched successfully")

            for i, url in enumerate(urls, 1):
                self.logger.info(f"Processing [{i}/{len(urls)}]: {url}")

                # Extract content
                content_data = await self._extract_content_from_page(page, url)

                # Validate and save content
                if self._is_content_valid(content_data):
                    filepath = self._save_content_to_file(content_data)
                    if filepath:
                        results["successful"] += 1
                        results["files_created"].append(filepath)
                        self.logger.info(f"Successfully processed: {url}")
                    else:
                        results["failed"] += 1
                        results["errors"].append(f"Failed to save content for {url}")
                else:
                    results["failed"] += 1
                    error_msg = f"Invalid content for {url}: {content_data.status}"
                    results["errors"].append(error_msg)
                    self.logger.warning(error_msg)

                # Delay between requests
                if i < len(urls):
                    await asyncio.sleep(DEFAULT_DELAY_BETWEEN_REQUESTS)

            await browser.close()
            self.logger.info("Browser closed")

        # Log final results
        self.logger.info(
            f"Crawl completed - Success: {results['successful']}, Failed: {results['failed']}"
        )

        return results
