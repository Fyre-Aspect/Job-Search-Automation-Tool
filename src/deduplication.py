"""
Deduplication Module
Handles persistence and deduplication of previously sent jobs.
Uses URL-based hashing to prevent duplicate emails.
"""

import json
import hashlib
import os
from typing import List, Dict, Set
from datetime import datetime


class JobDeduplicator:
    """
    Manages deduplication of job listings to prevent duplicate emails.
    
    Uses a JSON file to persist previously sent job identifiers.
    Jobs are identified by a hash of their URL (most reliable unique identifier).
    """
    
    DEFAULT_STORAGE_FILE = "data/sent_jobs.json"
    
    def __init__(self, storage_file: str = None):
        """
        Initialize the deduplicator.
        
        Args:
            storage_file: Path to JSON file for storing sent job hashes.
                         Defaults to data/sent_jobs.json
        """
        self.storage_file = storage_file or self.DEFAULT_STORAGE_FILE
        self.sent_hashes: Set[str] = set()
        self.metadata: Dict = {}
        
        self._ensure_storage_dir()
        self._load_sent_jobs()
    
    def _ensure_storage_dir(self):
        """Ensure the storage directory exists."""
        storage_dir = os.path.dirname(self.storage_file)
        if storage_dir and not os.path.exists(storage_dir):
            os.makedirs(storage_dir)
            print(f"[Dedup] Created storage directory: {storage_dir}")
    
    def _generate_hash(self, job: Dict) -> str:
        """
        Generate a unique hash for a job listing.
        
        Primary identifier is the URL. Falls back to title+company
        if URL is missing or invalid.
        """
        # Primary: URL-based hash
        url = job.get('url', '')
        if url and url != '#':
            return hashlib.sha256(url.encode()).hexdigest()[:16]
        
        # Fallback: title + company hash
        identifier = f"{job.get('title', '')}|{job.get('company', '')}".lower()
        return hashlib.sha256(identifier.encode()).hexdigest()[:16]
    
    def _load_sent_jobs(self):
        """Load previously sent job hashes from storage."""
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.sent_hashes = set(data.get('sent_hashes', []))
                    self.metadata = data.get('metadata', {})
                    print(f"[Dedup] Loaded {len(self.sent_hashes)} previously sent jobs")
            except (json.JSONDecodeError, IOError) as e:
                print(f"[Dedup] Error loading storage file: {e}")
                self.sent_hashes = set()
                self.metadata = {}
        else:
            print("[Dedup] No existing storage file. Starting fresh.")
            self.sent_hashes = set()
            self.metadata = {}
    
    def _save_sent_jobs(self):
        """Save sent job hashes to storage."""
        try:
            data = {
                'sent_hashes': list(self.sent_hashes),
                'metadata': {
                    'last_updated': datetime.now().isoformat(),
                    'total_jobs_sent': len(self.sent_hashes),
                    **self.metadata
                }
            }
            
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            print(f"[Dedup] Saved {len(self.sent_hashes)} job hashes to storage")
            
        except IOError as e:
            print(f"[Dedup] Error saving storage file: {e}")
    
    def filter_new_jobs(self, jobs: List[Dict]) -> List[Dict]:
        """
        Filter out jobs that have already been sent.
        
        Args:
            jobs: List of job dictionaries
            
        Returns:
            List of jobs that haven't been sent before
        """
        new_jobs = []
        duplicate_count = 0
        
        for job in jobs:
            job_hash = self._generate_hash(job)
            
            if job_hash not in self.sent_hashes:
                job['_hash'] = job_hash  # Store hash for later marking
                new_jobs.append(job)
            else:
                duplicate_count += 1
        
        print(f"[Dedup] Found {len(new_jobs)} new jobs, {duplicate_count} duplicates filtered")
        return new_jobs
    
    def mark_as_sent(self, jobs: List[Dict]):
        """
        Mark jobs as sent (add their hashes to the sent set).
        Call this AFTER successfully sending the email.
        
        Args:
            jobs: List of job dictionaries to mark as sent
        """
        for job in jobs:
            # Use stored hash or generate new one
            job_hash = job.get('_hash') or self._generate_hash(job)
            self.sent_hashes.add(job_hash)
        
        # Update metadata
        self.metadata['last_sent_date'] = datetime.now().isoformat()
        self.metadata['last_batch_count'] = len(jobs)
        
        # Persist to storage
        self._save_sent_jobs()
    
    def get_stats(self) -> Dict:
        """Get statistics about the deduplication storage."""
        return {
            'total_sent': len(self.sent_hashes),
            'last_updated': self.metadata.get('last_updated', 'Never'),
            'last_sent_date': self.metadata.get('last_sent_date', 'Never'),
            'last_batch_count': self.metadata.get('last_batch_count', 0)
        }
    
    def clear_history(self):
        """Clear all sent job history. Use with caution!"""
        self.sent_hashes = set()
        self.metadata = {'cleared_at': datetime.now().isoformat()}
        self._save_sent_jobs()
        print("[Dedup] History cleared!")
    
    def prune_old_entries(self, keep_count: int = 10000):
        """
        Prune old entries if the storage grows too large.
        Keeps the most recent entries.
        
        Note: Since we only store hashes, we can't determine age.
        This just limits total count.
        """
        if len(self.sent_hashes) > keep_count:
            # Convert to list, keep last N entries
            hash_list = list(self.sent_hashes)
            self.sent_hashes = set(hash_list[-keep_count:])
            self._save_sent_jobs()
            print(f"[Dedup] Pruned to {keep_count} entries")


if __name__ == "__main__":
    # Test the deduplicator
    deduplicator = JobDeduplicator(storage_file="data/test_sent_jobs.json")
    
    # Sample jobs
    test_jobs = [
        {'title': 'Job 1', 'company': 'Company A', 'url': 'https://example.com/job1'},
        {'title': 'Job 2', 'company': 'Company B', 'url': 'https://example.com/job2'},
        {'title': 'Job 3', 'company': 'Company C', 'url': 'https://example.com/job3'},
    ]
    
    print("\n--- First run ---")
    new_jobs = deduplicator.filter_new_jobs(test_jobs)
    print(f"New jobs: {len(new_jobs)}")
    
    # Mark first two as sent
    deduplicator.mark_as_sent(new_jobs[:2])
    
    print("\n--- Second run ---")
    new_jobs = deduplicator.filter_new_jobs(test_jobs)
    print(f"New jobs: {len(new_jobs)}")  # Should be 1
    
    print("\n--- Stats ---")
    print(deduplicator.get_stats())
    
    # Cleanup test file
    import os
    if os.path.exists("data/test_sent_jobs.json"):
        os.remove("data/test_sent_jobs.json")
        print("\nTest file cleaned up.")
