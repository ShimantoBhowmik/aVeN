#!/usr/bin/env python3
"""
Main entry point for the web crawler application
"""

import asyncio
import os
import sys
from datetime import datetime

from crawler import Crawler
from constants import AVEN_URLS, DEFAULT_OUTPUT_FOLDER, DEFAULT_PDF_FOLDER
from logger_utils import get_crawler_logger
from pdf_processor import PDFProcessor


def print_banner():
    """Print application banner"""
    print("=" * 60)
    print("Aven Website Content Crawler")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Target URLs: {len(AVEN_URLS)}")
    print(f"Output folder: {DEFAULT_OUTPUT_FOLDER}")
    print(f"Logs folder: logs/")
    print("-" * 60)


def print_results(results: dict):
    """Print crawling results"""
    print("\n" + "=" * 60)
    print("CRAWLING RESULTS")
    print("=" * 60)
    print(f"Successful: {results['successful']}")
    print(f"Failed: {results['failed']}")
    print(f"Files created: {len(results['files_created'])}")

    if results['files_created']:
        print(f"\nFiles created:")
        for filepath in results['files_created']:
            filename = os.path.basename(filepath)
            print(f"   • {filename}")
    
    if results['errors']:
        print(f"\n Errors encountered:")
        for error in results['errors']:
            print(f"   • {error}")
    
    print("\n" + "=" * 60)
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


def print_pdf_banner():
    """Print PDF processing banner"""
    print("\n" + "=" * 60)
    print("PDF Content Processor with OCR")
    print("=" * 60)
    print(f"PDF folder: {DEFAULT_PDF_FOLDER}")
    print(f"Output folder: {DEFAULT_OUTPUT_FOLDER}")
    print("-" * 60)


def print_pdf_results(results: dict):
    """Print PDF processing results"""
    print("\n" + "=" * 60)
    print("PDF PROCESSING RESULTS")
    print("=" * 60)
    print(f"Successful: {results['successful']}")
    print(f"Failed: {results['failed']}")
    print(f"Files processed: {results['files_processed']}")
    print(f"Text files created: {len(results['files_created'])}")

    if results['files_created']:
        print(f"\nFiles created:")
        for filepath in results['files_created']:
            filename = os.path.basename(filepath)
            print(f"   • {filename}")
    
    if results['errors']:
        print(f"\nErrors encountered:")
        for error in results['errors']:
            print(f"   • {error}")


async def main():
    """Main application entry point"""
    logger = get_crawler_logger()
    
    try:
        print_banner()
        
        # Initialize crawler
        logger.info("Initializing crawler")
        crawler = Crawler(output_folder=DEFAULT_OUTPUT_FOLDER)
        
        # Start crawling
        logger.info(f"Starting to crawl {len(AVEN_URLS)} URLs")
        results = await crawler.crawl_urls(AVEN_URLS)
        
        # Print results
        print_results(results)
        
        # Log final status
        if results['successful'] > 0:
            logger.info(f"Crawling completed successfully. {results['successful']} pages processed.")
            return 0
        else:
            logger.error("No pages were successfully processed")
            return 1
            
    except KeyboardInterrupt:
        print("\n⏹️  Crawling interrupted by user")
        logger.info("Crawling interrupted by user")
        return 1
        
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        logger.error(f"Fatal error: {str(e)}")
        return 1


def run_crawler():
    """Entry point for running the crawler and PDF processor"""
    try:
        # Run web crawler
        print("Web Content Crawling")
        crawler_exit_code = asyncio.run(main())
        
        # Run PDF processor
        print("\nPDF Content Processing")
        pdf_success = run_pdf_processor()
        
        # Determine overall exit code
        if crawler_exit_code == 0 or pdf_success:
            print(f"\nContent processing completed!")
            print(f"All extracted content is in: {os.path.abspath(DEFAULT_OUTPUT_FOLDER)}")
            sys.exit(0)
        else:
            print(f"\nSome processing failed. Check logs for details.")
            sys.exit(1)
            
    except Exception as e:
        print(f"Failed to start processing: {e}")
        sys.exit(1)


def run_pdf_processor():
    """Run PDF processor"""
    logger = get_crawler_logger()
    
    try:
        print_pdf_banner()
        
        # Check if PDF folder exists and has files
        if not os.path.exists(DEFAULT_PDF_FOLDER):
            print(f"Creating PDF folder: {DEFAULT_PDF_FOLDER}")
            os.makedirs(DEFAULT_PDF_FOLDER, exist_ok=True)
            print(f"Place your PDF files in: {os.path.abspath(DEFAULT_PDF_FOLDER)}")
            return True
        
        # Count PDF files
        pdf_files = [f for f in os.listdir(DEFAULT_PDF_FOLDER) if f.lower().endswith('.pdf')]
        if not pdf_files:
            print(f"No PDF files found in: {os.path.abspath(DEFAULT_PDF_FOLDER)}")
            print(f"Place your PDF files there and run again")
            return True
        
        print(f"Found {len(pdf_files)} PDF file(s) to process")
        
        # Initialize PDF processor
        logger.info("Initializing PDF processor")
        pdf_processor = PDFProcessor()
        
        # Process PDFs
        logger.info(f"Starting to process {len(pdf_files)} PDF files")
        results = pdf_processor.process_pdfs()
        
        # Print results
        print_pdf_results(results)
        
        # Log final status
        if results['successful'] > 0:
            logger.info(f"PDF processing completed successfully. {results['successful']} files processed.")
            return True
        else:
            logger.warning("No PDF files were successfully processed")
            return False
            
    except Exception as e:
        print(f"PDF processing error: {str(e)}")
        logger.error(f"PDF processing error: {str(e)}")
        return False


if __name__ == "__main__":
    run_crawler()
    run_pdf_processor()
