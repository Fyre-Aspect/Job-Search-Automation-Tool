#!/usr/bin/env python3
"""
Job Search Automation Tool - Main Orchestrator

This script coordinates the entire job search pipeline:
1. Scrapes jobs from multiple sources (Indeed RSS, RemoteOK, The Muse, Adzuna)
2. Filters jobs based on hard criteria (no degree required, entry-level, etc.)
3. Deduplicates against previously sent jobs
4. Sends email notification only if new qualifying jobs are found

Designed to run daily via GitHub Actions at 8:00 PM Eastern Time.

Author: Job Search Automation Tool
License: MIT
"""

import os
import sys
from datetime import datetime
from typing import List, Dict

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.scrapers import IndeedRSSScraper, RemoteOKScraper, TheMuseScraper, AdzunaScraper
from src.job_processor import JobProcessor
from src.deduplication import JobDeduplicator
from src.email_sender import EmailSender


def print_banner():
    """Print startup banner."""
    print("=" * 60)
    print("  🚀 JOB SEARCH AUTOMATION TOOL")
    print("=" * 60)
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()


def scrape_all_sources() -> List[Dict]:
    """
    Run all scrapers and collect jobs from all sources.
    
    Returns:
        Combined list of jobs from all sources
    """
    all_jobs = []
    
    # Initialize scrapers
    scrapers = [
        ("Indeed RSS", IndeedRSSScraper()),
        ("RemoteOK", RemoteOKScraper()),
        ("The Muse", TheMuseScraper()),
        ("Adzuna", AdzunaScraper()),
    ]
    
    print("\n" + "=" * 40)
    print("PHASE 1: SCRAPING JOB SOURCES")
    print("=" * 40)
    
    for name, scraper in scrapers:
        try:
            print(f"\n[{name}] Starting...")
            jobs = scraper.scrape()
            all_jobs.extend(jobs)
            print(f"[{name}] ✓ Collected {len(jobs)} jobs")
        except Exception as e:
            print(f"[{name}] ✗ Error: {e}")
            continue
    
    print(f"\n[Scraping Complete] Total jobs collected: {len(all_jobs)}")
    return all_jobs


def filter_jobs(jobs: List[Dict]) -> List[Dict]:
    """
    Apply filtering rules to remove non-qualifying jobs.
    
    Args:
        jobs: Raw list of jobs from scrapers
        
    Returns:
        Filtered list of qualifying jobs
    """
    print("\n" + "=" * 40)
    print("PHASE 2: FILTERING JOBS")
    print("=" * 40)
    
    processor = JobProcessor()
    filtered_jobs = processor.process_jobs(jobs)
    
    return filtered_jobs


def deduplicate_jobs(jobs: List[Dict]) -> List[Dict]:
    """
    Remove jobs that have already been sent in previous runs.
    
    Args:
        jobs: Filtered list of jobs
        
    Returns:
        List of new jobs not previously sent
    """
    print("\n" + "=" * 40)
    print("PHASE 3: DEDUPLICATION")
    print("=" * 40)
    
    deduplicator = JobDeduplicator()
    new_jobs = deduplicator.filter_new_jobs(jobs)
    
    # Store deduplicator for later use (to mark as sent)
    return new_jobs, deduplicator


def send_email_notification(jobs: List[Dict], deduplicator: JobDeduplicator) -> bool:
    """
    Send email notification with new jobs.
    
    Args:
        jobs: List of new jobs to send
        deduplicator: Deduplicator instance to mark jobs as sent
        
    Returns:
        True if email sent (or no email needed), False on error
    """
    print("\n" + "=" * 40)
    print("PHASE 4: EMAIL NOTIFICATION")
    print("=" * 40)
    
    if not jobs:
        print("[Email] No new jobs found. Skipping email.")
        return True
    
    sender = EmailSender()
    
    # Format jobs for display
    processor = JobProcessor()
    formatted_jobs = [processor.format_job_for_display(job) for job in jobs]
    
    # Send email
    success = sender.send_job_alert(formatted_jobs)
    
    if success:
        # Mark jobs as sent ONLY if email was successful
        deduplicator.mark_as_sent(jobs)
        print(f"[Email] ✓ Sent {len(jobs)} jobs and updated deduplication database")
    else:
        print("[Email] ✗ Failed to send email. Jobs NOT marked as sent.")
    
    return success


def print_summary(
    total_scraped: int,
    total_filtered: int,
    total_new: int,
    email_sent: bool
):
    """Print final summary of the run."""
    print("\n" + "=" * 60)
    print("  📊 RUN SUMMARY")
    print("=" * 60)
    print(f"  Jobs scraped:    {total_scraped}")
    print(f"  After filtering: {total_filtered}")
    print(f"  New jobs:        {total_new}")
    print(f"  Email sent:      {'Yes' if email_sent and total_new > 0 else 'No (not needed)' if total_new == 0 else 'Failed'}")
    print(f"  Completed:       {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)


def main():
    """Main entry point for the job search automation."""
    print_banner()
    
    # Phase 1: Scrape all sources
    all_jobs = scrape_all_sources()
    total_scraped = len(all_jobs)
    
    if not all_jobs:
        print("\n[Warning] No jobs scraped from any source.")
        print_summary(0, 0, 0, False)
        return
    
    # Phase 2: Filter jobs
    filtered_jobs = filter_jobs(all_jobs)
    total_filtered = len(filtered_jobs)
    
    if not filtered_jobs:
        print("\n[Info] No jobs passed the filters.")
        print_summary(total_scraped, 0, 0, False)
        return
    
    # Phase 3: Deduplicate
    new_jobs, deduplicator = deduplicate_jobs(filtered_jobs)
    total_new = len(new_jobs)
    
    # Phase 4: Send email (only if there are new jobs)
    email_sent = False
    if new_jobs:
        email_sent = send_email_notification(new_jobs, deduplicator)
    else:
        print("\n[Info] All jobs have been sent previously. No email needed.")
    
    # Print summary
    print_summary(total_scraped, total_filtered, total_new, email_sent)
    
    # Exit with appropriate code
    if total_new > 0 and not email_sent:
        sys.exit(1)  # Error: had jobs but failed to send
    
    sys.exit(0)  # Success


if __name__ == "__main__":
    main()
