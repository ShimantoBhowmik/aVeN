"""
Constants for the web crawler application
"""

# Aven website URLs to crawl
AVEN_URLS = [
    "https://www.aven.com/",
    "https://www.aven.com/education",
    "https://www.aven.com/reviews",
    "https://www.aven.com/support",
    "https://www.aven.com/app",
    "https://www.aven.com/about",
    "https://www.aven.com/contact",
    "https://www.aven.com/testimonials",
    "https://www.aven.com/careers",
    "https://www.aven.com/press",
    "https://www.aven.com/privacy",
    "https://www.aven.com/licenses",
    "https://www.aven.com/disclosures",
    "https://www.aven.com/press/series-d",
    "https://www.aven.com/docs/PrivacyPolicy.html",
    "https://www.coastalbank.com/privacy-center/"
]

# Configuration settings
DEFAULT_OUTPUT_FOLDER = "../knowledge-base"
DEFAULT_LOGS_FOLDER = "logs"
DEFAULT_PDF_FOLDER = "aven-pdfs"
DEFAULT_TIMEOUT = 30000
DEFAULT_WAIT_TIME = 3000
DEFAULT_DELAY_BETWEEN_REQUESTS = 2

# Browser settings
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

# Content selectors for finding main content
MAIN_CONTENT_SELECTORS = [
    'main', 
    'article', 
    '[role="main"]', 
    '.content', 
    '.main-content', 
    '#content', 
    '#main', 
    '.post-content', 
    '.entry-content',
    '.article-body', 
    '.page-content'
]

# Elements to remove from pages
ELEMENTS_TO_REMOVE = [
    'script', 
    'style', 
    'nav', 
    'footer', 
    'header', 
    '.nav', 
    '.navigation', 
    '.menu', 
    '.sidebar',
    '.cookie-banner', 
    '.popup', 
    '.modal'
]

# Minimum content length to consider valid
MIN_CONTENT_LENGTH = 10
