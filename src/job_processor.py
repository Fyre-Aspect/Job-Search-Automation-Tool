"""
Job Processor Module
Handles filtering, validation, and processing of job listings.
Enforces hard filters to exclude non-qualifying roles.
"""

import re
from typing import List, Dict, Optional
from datetime import datetime


class JobProcessor:
    """
    Processes and filters job listings according to defined criteria.
    
    Hard Filters (automatic exclusion):
    - Requires bachelor's degree
    - Requires being enrolled in university
    - Mid-level or senior positions
    - Requires 3+ years of experience
    
    Preferred Criteria (prioritized):
    - Entry-level or beginner-friendly
    - Open to self-taught developers
    - Skills-based or portfolio-based roles
    
    Location Rules:
    - Remote roles: Global or North America
    - On-site: Only Kitchener-Waterloo, Ontario
    """
    
    # Keywords that indicate EXCLUSION (job should be filtered out)
    EXCLUSION_KEYWORDS = [
        # Degree requirements
        r"bachelor'?s?\s+degree\s+required",
        r"bs\s+degree\s+required",
        r"ba\s+degree\s+required",
        r"degree\s+required",
        r"must\s+have\s+(?:a\s+)?(?:bachelor|bs|ba|b\.s\.|b\.a\.)\s+degree",
        r"requires?\s+(?:a\s+)?(?:bachelor|bs|ba)\s+degree",
        r"(?:bachelor|bs|ba)\s+degree\s+(?:is\s+)?required",
        
        # University enrollment requirements
        r"currently\s+enrolled",
        r"must\s+be\s+enrolled",
        r"pursuing\s+(?:a\s+)?degree",
        r"enrolled\s+in\s+(?:a\s+)?(?:university|college)",
        r"working\s+towards?\s+(?:a\s+)?degree",
        r"studying\s+(?:towards?)?\s+(?:a\s+)?degree",
        r"undergraduate\s+student",
        r"graduate\s+student\s+required",
        r"currently\s+studying",
        
        # Senior/mid-level positions
        r"\bsenior\b",
        r"\bsr\.\s",
        r"\bsr\s",
        r"\blead\s+(?:developer|engineer|software)",
        r"\bprincipal\b",
        r"\bstaff\s+(?:developer|engineer)",
        r"\barchitect\b",
        r"\bmanager\b",
        r"\bdirector\b",
        r"\bmid-?level\b",
        r"\bmid\s+level\b",
        r"\bintermediate\b",
        
        # Experience requirements (3+ years)
        r"[3-9]\+?\s*(?:years?|yrs?)\s+(?:of\s+)?experience",
        r"[1-9][0-9]\+?\s*(?:years?|yrs?)\s+(?:of\s+)?experience",
        r"(?:minimum|at\s+least)\s+[3-9]\+?\s*(?:years?|yrs?)",
        r"[3-9]\+?\s*(?:years?|yrs?)\s+(?:of\s+)?(?:professional|industry)",
    ]
    
    # Keywords that indicate INCLUSION (job is relevant)
    INCLUSION_KEYWORDS = [
        r"\bjunior\b",
        r"\bjr\.?\b",
        r"\bentry[\s-]?level\b",
        r"\bintern\b",
        r"\binternship\b",
        r"\bgraduate\s+program\b",
        r"\bgrad\s+program\b",
        r"\btrainee\b",
        r"\bapprentice\b",
        r"\bbootcamp\s+grad",
        r"\bself[\s-]?taught",
        r"\bno\s+degree\s+required",
        r"\bno\s+experience\s+required",
        r"\bwilling\s+to\s+train",
        r"\bfreshers?\b",
        r"\bnew\s+grad",
        r"\brecent\s+grad",
        r"\b0-[12]\s*(?:years?|yrs?)",
        r"\bportfolio[\s-]?based",
        r"\bskills[\s-]?based",
    ]
    
    # Valid remote indicators
    REMOTE_KEYWORDS = [
        r"\bremote\b",
        r"\bwork\s+from\s+home\b",
        r"\bwfh\b",
        r"\bfully\s+remote\b",
        r"\b100%\s+remote\b",
        r"\bhybrid\b",
        r"\bflexible\s+location\b",
        r"\banywhere\b",
    ]
    
    # Valid on-site locations (Kitchener-Waterloo area)
    VALID_ONSITE_LOCATIONS = [
        r"kitchener",
        r"waterloo",
        r"cambridge,?\s*(?:on|ontario)",
        r"guelph",  # Close enough to KW area
    ]
    
    def __init__(self):
        # Compile regex patterns for efficiency
        self.exclusion_patterns = [re.compile(p, re.IGNORECASE) for p in self.EXCLUSION_KEYWORDS]
        self.inclusion_patterns = [re.compile(p, re.IGNORECASE) for p in self.INCLUSION_KEYWORDS]
        self.remote_patterns = [re.compile(p, re.IGNORECASE) for p in self.REMOTE_KEYWORDS]
        self.location_patterns = [re.compile(p, re.IGNORECASE) for p in self.VALID_ONSITE_LOCATIONS]
    
    def _should_exclude(self, job: Dict) -> tuple[bool, str]:
        """
        Check if job should be excluded based on hard filters.
        Returns (should_exclude, reason).
        """
        # Combine searchable text
        searchable_text = ' '.join([
            job.get('title', ''),
            job.get('description', ''),
            job.get('skills', ''),
            job.get('job_type', ''),
        ]).lower()
        
        # Check exclusion patterns
        for pattern in self.exclusion_patterns:
            match = pattern.search(searchable_text)
            if match:
                return True, f"Matched exclusion pattern: {match.group()}"
        
        return False, ""
    
    def _is_valid_location(self, job: Dict) -> tuple[bool, str]:
        """
        Check if job location is valid (remote or Kitchener-Waterloo).
        Returns (is_valid, reason).
        """
        location = job.get('location', '').lower()
        description = job.get('description', '').lower()
        title = job.get('title', '').lower()
        
        combined_text = f"{location} {description} {title}"
        
        # Check for remote indicators
        for pattern in self.remote_patterns:
            if pattern.search(combined_text):
                return True, "Remote position"
        
        # Check for valid on-site locations
        for pattern in self.location_patterns:
            if pattern.search(location):
                return True, "Valid on-site location (KW area)"
        
        # If location is not specified, include it (benefit of the doubt)
        if not location or location in ['not specified', 'see listing', '']:
            return True, "Location unspecified - included"
        
        # Exclude other on-site locations
        return False, f"Invalid on-site location: {job.get('location', 'unknown')}"
    
    def _has_inclusion_signals(self, job: Dict) -> bool:
        """Check if job has positive signals for entry-level/beginner roles."""
        searchable_text = ' '.join([
            job.get('title', ''),
            job.get('description', ''),
            job.get('job_type', ''),
        ]).lower()
        
        for pattern in self.inclusion_patterns:
            if pattern.search(searchable_text):
                return True
        
        return False
    
    def _calculate_relevance_score(self, job: Dict) -> int:
        """
        Calculate a relevance score for sorting.
        Higher score = more relevant to entry-level candidates.
        """
        score = 0
        searchable_text = ' '.join([
            job.get('title', ''),
            job.get('description', ''),
            job.get('job_type', ''),
        ]).lower()
        
        # Positive signals
        if 'intern' in searchable_text:
            score += 10
        if 'entry' in searchable_text and 'level' in searchable_text:
            score += 10
        if 'junior' in searchable_text or 'jr' in searchable_text:
            score += 8
        if 'no degree' in searchable_text or 'self-taught' in searchable_text:
            score += 15
        if 'bootcamp' in searchable_text:
            score += 5
        if 'portfolio' in searchable_text:
            score += 5
        if 'remote' in job.get('location', '').lower():
            score += 3
        
        # Compensation bonus
        comp = job.get('compensation', '').lower()
        if comp and comp != 'not specified':
            if 'paid' in comp or '$' in comp:
                score += 5
        
        # Recency bonus (prefer newer postings)
        posted_date = job.get('posted_date')
        if posted_date:
            try:
                days_ago = (datetime.now() - datetime.strptime(posted_date, "%Y-%m-%d")).days
                if days_ago <= 1:
                    score += 5
                elif days_ago <= 3:
                    score += 3
                elif days_ago <= 7:
                    score += 1
            except (ValueError, TypeError):
                pass
        
        return score
    
    def process_jobs(self, jobs: List[Dict]) -> List[Dict]:
        """
        Process and filter a list of jobs.
        
        Args:
            jobs: List of job dictionaries from scrapers
            
        Returns:
            Filtered and sorted list of qualifying jobs
        """
        qualifying_jobs = []
        stats = {
            'total': len(jobs),
            'excluded_filters': 0,
            'excluded_location': 0,
            'passed': 0
        }
        
        print(f"\n[Processor] Processing {len(jobs)} jobs...")
        
        for job in jobs:
            # Apply hard exclusion filters
            should_exclude, exclude_reason = self._should_exclude(job)
            if should_exclude:
                stats['excluded_filters'] += 1
                continue
            
            # Apply location filter
            is_valid_location, location_reason = self._is_valid_location(job)
            if not is_valid_location:
                stats['excluded_location'] += 1
                continue
            
            # Calculate relevance score
            job['relevance_score'] = self._calculate_relevance_score(job)
            job['location_note'] = location_reason
            
            qualifying_jobs.append(job)
            stats['passed'] += 1
        
        # Sort by relevance score (highest first)
        qualifying_jobs.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        # Print stats
        print(f"[Processor] Results:")
        print(f"  - Total input: {stats['total']}")
        print(f"  - Excluded (filters): {stats['excluded_filters']}")
        print(f"  - Excluded (location): {stats['excluded_location']}")
        print(f"  - Qualifying jobs: {stats['passed']}")
        
        return qualifying_jobs
    
    def format_job_for_display(self, job: Dict) -> Dict:
        """Format a job dictionary for email display."""
        return {
            'title': job.get('title', 'Unknown Position'),
            'company': job.get('company', 'Unknown Company'),
            'url': job.get('url', '#'),
            'location': job.get('location', 'Not specified'),
            'job_type': job.get('job_type', 'Not specified'),
            'compensation': job.get('compensation', 'Not specified'),
            'skills': job.get('skills', 'Not specified'),
            'posted_date': job.get('posted_date', 'Not specified'),
            'source': job.get('source', 'Unknown'),
        }


if __name__ == "__main__":
    # Test the processor
    processor = JobProcessor()
    
    # Sample test jobs
    test_jobs = [
        {
            'title': 'Junior Web Developer',
            'company': 'Tech Startup',
            'description': 'Entry-level position. No degree required. Self-taught developers welcome.',
            'location': 'Remote',
            'job_type': 'Entry-Level',
            'url': 'https://example.com/job1'
        },
        {
            'title': 'Senior Software Engineer',
            'company': 'Big Corp',
            'description': 'Requires 5+ years of experience and bachelor\'s degree.',
            'location': 'New York',
            'job_type': 'Senior',
            'url': 'https://example.com/job2'
        },
        {
            'title': 'Software Developer Intern',
            'company': 'Startup Inc',
            'description': 'Summer internship for students. Must be enrolled in university.',
            'location': 'Kitchener, ON',
            'job_type': 'Internship',
            'url': 'https://example.com/job3'
        },
        {
            'title': 'Full Stack Developer',
            'company': 'Remote Co',
            'description': 'Junior position. 0-2 years experience. Portfolio-based hiring.',
            'location': 'Fully Remote',
            'job_type': 'Full-Time',
            'url': 'https://example.com/job4'
        },
    ]
    
    results = processor.process_jobs(test_jobs)
    
    print("\n" + "="*50)
    print("QUALIFYING JOBS:")
    print("="*50)
    
    for job in results:
        print(f"\n- {job['title']} at {job['company']}")
        print(f"  Score: {job.get('relevance_score', 0)}")
        print(f"  Location: {job['location']}")
