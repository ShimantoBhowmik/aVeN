#!/usr/bin/env python3
"""
PDF Content Processor with OCR capabilities
"""

import os
import re
from typing import List, Dict, Optional
from pathlib import Path

try:
    import PyPDF2
    import pdfplumber
    import pytesseract
    from PIL import Image
    from pdf2image import convert_from_path
except ImportError as e:
    print(
        f"Missing PDF processing libraries. Please install: pip install PyPDF2 pdfplumber pytesseract Pillow pdf2image"
    )
    raise e

from constants import (
    DEFAULT_PDF_FOLDER,
    DEFAULT_OUTPUT_FOLDER,
    MIN_CONTENT_LENGTH,
    PDF_URL_MAPPING,
)
from logger_utils import get_content_logger, get_file_logger


class PDFContentData:
    """Data class for storing PDF content"""

    def __init__(
        self,
        filename: str,
        title: str = "",
        content: str = "",
        method: str = "",
        pages: int = 0,
        status: str = "",
    ):
        self.filename = filename
        self.title = title
        self.content = content
        self.method = method  # extraction method used
        self.pages = pages
        self.status = status

    def to_dict(self) -> Dict[str, any]:
        return {
            "filename": self.filename,
            "title": self.title,
            "content": self.content,
            "method": self.method,
            "pages": self.pages,
            "status": self.status,
        }


class PDFProcessor:
    """
    PDF content processor with multiple extraction methods including OCR
    """

    def __init__(
        self,
        pdf_folder: str = DEFAULT_PDF_FOLDER,
        output_folder: str = DEFAULT_OUTPUT_FOLDER,
    ):
        self.pdf_folder = pdf_folder
        self.output_folder = output_folder
        self.content_logger = get_content_logger()
        self.file_logger = get_file_logger()

        # Ensure folders exist
        self._ensure_folders()

        self.content_logger.info(f"PDF Processor initialized")
        self.content_logger.info(f"PDF folder: {self.pdf_folder}")
        self.content_logger.info(f"Output folder: {self.output_folder}")

    def _ensure_folders(self) -> None:
        """Ensure required folders exist"""
        try:
            os.makedirs(self.pdf_folder, exist_ok=True)
            os.makedirs(self.output_folder, exist_ok=True)
            self.file_logger.info(
                f"Folders verified: {self.pdf_folder}, {self.output_folder}"
            )
        except Exception as e:
            self.file_logger.error(f"Failed to create folders: {e}")
            raise

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content"""
        if not text:
            return ""

        # Remove extra whitespace and normalize
        lines = [line.strip() for line in text.splitlines()]
        lines = [line for line in lines if line.strip()]
        cleaned = "\n".join(lines)

        # Remove excessive repeated characters
        cleaned = re.sub(r"(.)\1{4,}", r"\1\1", cleaned)

        self.content_logger.debug(
            f"Cleaned text from {len(text)} to {len(cleaned)} characters"
        )
        return cleaned

    def _generate_safe_filename(self, pdf_filename: str) -> str:
        """Generate a safe filename for output"""
        # Remove extension and clean name
        base_name = Path(pdf_filename).stem
        safe_name = re.sub(r"[^\w\s-]", "", base_name)
        safe_name = re.sub(r"[-\s]+", "-", safe_name)
        safe_name = safe_name.strip("-")

        output_filename = f"PDF_{safe_name}.txt"

        self.file_logger.debug(
            f"Generated filename '{output_filename}' for PDF: {pdf_filename}"
        )
        return output_filename

    def _extract_with_pypdf2(self, pdf_path: str) -> PDFContentData:
        """Extract text using PyPDF2"""
        try:
            content = ""
            page_count = 0

            with open(pdf_path, "rb") as file:
                pdf_reader = PyPDF2.PdfReader(file)
                page_count = len(pdf_reader.pages)

                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            content += f"\n--- Page {page_num + 1} ---\n"
                            content += page_text
                    except Exception as e:
                        self.content_logger.warning(
                            f"Failed to extract page {page_num + 1}: {e}"
                        )

            cleaned_content = self._clean_text(content)

            return PDFContentData(
                filename=os.path.basename(pdf_path),
                content=cleaned_content,
                method="PyPDF2",
                pages=page_count,
                status="success" if cleaned_content else "no_text_found",
            )

        except Exception as e:
            self.content_logger.error(f"PyPDF2 extraction failed for {pdf_path}: {e}")
            return PDFContentData(
                filename=os.path.basename(pdf_path),
                method="PyPDF2",
                status=f"error: {str(e)}",
            )

    def _extract_with_pdfplumber(self, pdf_path: str) -> PDFContentData:
        """Extract text using pdfplumber"""
        try:
            content = ""
            page_count = 0

            with pdfplumber.open(pdf_path) as pdf:
                page_count = len(pdf.pages)

                for page_num, page in enumerate(pdf.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            content += f"\n--- Page {page_num + 1} ---\n"
                            content += page_text
                    except Exception as e:
                        self.content_logger.warning(
                            f"Failed to extract page {page_num + 1}: {e}"
                        )

            cleaned_content = self._clean_text(content)

            return PDFContentData(
                filename=os.path.basename(pdf_path),
                content=cleaned_content,
                method="pdfplumber",
                pages=page_count,
                status="success" if cleaned_content else "no_text_found",
            )

        except Exception as e:
            self.content_logger.error(
                f"pdfplumber extraction failed for {pdf_path}: {e}"
            )
            return PDFContentData(
                filename=os.path.basename(pdf_path),
                method="pdfplumber",
                status=f"error: {str(e)}",
            )

    def _extract_with_ocr(self, pdf_path: str) -> PDFContentData:
        """Extract text using OCR (Tesseract)"""
        try:
            self.content_logger.info(f"Starting OCR extraction for {pdf_path}")

            # Convert PDF to images
            images = convert_from_path(pdf_path, dpi=300)
            content = ""
            page_count = len(images)

            for page_num, image in enumerate(images):
                try:
                    # Perform OCR on the image
                    page_text = pytesseract.image_to_string(image, lang="eng")
                    if page_text.strip():
                        content += f"\n--- Page {page_num + 1} (OCR) ---\n"
                        content += page_text

                    self.content_logger.debug(f"OCR completed for page {page_num + 1}")
                except Exception as e:
                    self.content_logger.warning(
                        f"OCR failed for page {page_num + 1}: {e}"
                    )

            cleaned_content = self._clean_text(content)

            return PDFContentData(
                filename=os.path.basename(pdf_path),
                content=cleaned_content,
                method="OCR",
                pages=page_count,
                status="success" if cleaned_content else "no_text_found",
            )

        except Exception as e:
            self.content_logger.error(f"OCR extraction failed for {pdf_path}: {e}")
            return PDFContentData(
                filename=os.path.basename(pdf_path),
                method="OCR",
                status=f"error: {str(e)}",
            )

    def _extract_pdf_content(self, pdf_path: str) -> PDFContentData:
        """
        Extract content from PDF using multiple methods
        Tries PyPDF2 first, then pdfplumber, then OCR as fallback
        """
        self.content_logger.info(
            f"Extracting content from: {os.path.basename(pdf_path)}"
        )

        # Try PyPDF2 first (fastest)
        result = self._extract_with_pypdf2(pdf_path)
        if result.status == "success" and len(result.content) > MIN_CONTENT_LENGTH:
            self.content_logger.info(
                f"Successfully extracted with PyPDF2: {len(result.content)} chars"
            )
            return result

        # Try pdfplumber (more accurate)
        self.content_logger.info("PyPDF2 insufficient, trying pdfplumber...")
        result = self._extract_with_pdfplumber(pdf_path)
        if result.status == "success" and len(result.content) > MIN_CONTENT_LENGTH:
            self.content_logger.info(
                f"Successfully extracted with pdfplumber: {len(result.content)} chars"
            )
            return result

        # Fall back to OCR (for scanned PDFs)
        self.content_logger.info("Text extraction insufficient, trying OCR...")
        result = self._extract_with_ocr(pdf_path)
        if result.status == "success":
            self.content_logger.info(
                f"Successfully extracted with OCR: {len(result.content)} chars"
            )
        else:
            self.content_logger.warning("All extraction methods failed")

        return result

    def _save_content_to_file(self, content_data: PDFContentData) -> Optional[str]:
        """Save extracted content to a text file"""
        output_filename = self._generate_safe_filename(content_data.filename)
        output_path = os.path.join(self.output_folder, output_filename)

        try:
            with open(output_path, "w", encoding="utf-8") as f:
                # Get the URL mapping for this PDF
                pdf_url = PDF_URL_MAPPING.get(
                    content_data.filename, content_data.filename
                )

                f.write(f"URL: {pdf_url}\n")
                f.write("=" * 50 + "\n\n")
                f.write(content_data.content)

            self.file_logger.info(f"Saved PDF content to: {output_filename}")
            return output_path

        except Exception as e:
            self.file_logger.error(f"Error saving {output_filename}: {e}")
            return None

    def _find_pdf_files(self) -> List[str]:
        """Find all PDF files in the PDF folder"""
        try:
            pdf_files = []
            if os.path.exists(self.pdf_folder):
                for filename in os.listdir(self.pdf_folder):
                    if filename.lower().endswith(".pdf"):
                        pdf_path = os.path.join(self.pdf_folder, filename)
                        pdf_files.append(pdf_path)

            self.file_logger.info(
                f"Found {len(pdf_files)} PDF files in {self.pdf_folder}"
            )
            return pdf_files

        except Exception as e:
            self.file_logger.error(f"Error finding PDF files: {e}")
            return []

    def _is_content_valid(self, content_data: PDFContentData) -> bool:
        """Check if extracted content is valid"""
        if content_data.status != "success":
            return False

        if not content_data.content or not content_data.content.strip():
            return False

        if len(content_data.content) < MIN_CONTENT_LENGTH:
            self.content_logger.warning(
                f"Content too short for {content_data.filename}: {len(content_data.content)} chars"
            )
            return False

        return True

    def process_pdfs(self) -> Dict[str, any]:
        """
        Process all PDFs in the PDF folder

        Returns:
            Dictionary with processing results
        """
        self.content_logger.info("Starting PDF processing")

        # Find PDF files
        pdf_files = self._find_pdf_files()

        if not pdf_files:
            self.content_logger.warning(f"No PDF files found in {self.pdf_folder}")
            return {
                "successful": 0,
                "failed": 0,
                "files_processed": 0,
                "files_created": [],
                "errors": [f"No PDF files found in {self.pdf_folder}"],
            }

        results = {
            "successful": 0,
            "failed": 0,
            "files_processed": len(pdf_files),
            "files_created": [],
            "errors": [],
        }

        # Process each PDF
        for i, pdf_path in enumerate(pdf_files, 1):
            filename = os.path.basename(pdf_path)
            self.content_logger.info(f"Processing [{i}/{len(pdf_files)}]: {filename}")

            try:
                # Extract content
                content_data = self._extract_pdf_content(pdf_path)

                # Validate and save content
                if self._is_content_valid(content_data):
                    output_path = self._save_content_to_file(content_data)
                    if output_path:
                        results["successful"] += 1
                        results["files_created"].append(output_path)
                        self.content_logger.info(f"Successfully processed: {filename}")
                    else:
                        results["failed"] += 1
                        error_msg = f"Failed to save content for {filename}"
                        results["errors"].append(error_msg)
                else:
                    results["failed"] += 1
                    error_msg = f"Invalid/insufficient content for {filename}: {content_data.status}"
                    results["errors"].append(error_msg)
                    self.content_logger.warning(error_msg)

            except Exception as e:
                results["failed"] += 1
                error_msg = f"Error processing {filename}: {str(e)}"
                results["errors"].append(error_msg)
                self.content_logger.error(error_msg)

        # Log final results
        self.content_logger.info(
            f"PDF processing completed - Success: {results['successful']}, Failed: {results['failed']}"
        )

        return results
