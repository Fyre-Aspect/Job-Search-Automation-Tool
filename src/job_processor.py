"""
Job Processor Module
Handles filtering, validation, and processing of job listings.
Enforces hard filters to exclude non-qualifying roles.
Focused on PART-TIME jobs suitable for a 17-year-old.
"""

import re
from typing import List, Dict, Optional
from datetime import datetime


class JobProcessor:
    """
    Processes and filters job listings for part-time jobs suitable for teens.
    
    Hard Filters (automatic exclusion):
    - Full-time positions (must be part-time)
    - Requires bachelor's degree
    - Requires being enrolled in university
    - Mid-level or senior positions
    - Requires 2+ years of experience
    - Age restricted (21+, 19+)
    
    Preferred Criteria (prioritized):
    - Part-time positions
    - Retail, food service, summer jobs
    - No experience required
    - Student-friendly schedules
    - Beginner tech internships
    
    Location Rules:
    - On-site: Kitchener-Waterloo-Cambridge area only
    - Remote: Only for simple tech internships
    """
    
    # Keywords that indicate EXCLUSION (job should be filtered out)
    EXCLUSION_KEYWORDS = [
        # Degree requirements
        r"bachelor'?s?\s+degree\s+required",
        r"bs\s+degree\s+required",
        r"degree\s+required",
        r"must\s+have\s+(?:a\s+)?(?:bachelor|bs|ba)\s+degree",
        r"requires?\s+(?:a\s+)?(?:bachelor|bs|ba)\s+degree",
        r"college\s+degree\s+required",
        
        # University enrollment requirements
        r"must\s+be\s+enrolled",
        r"enrolled\s+in\s+(?:a\s+)?(?:university|college)",
        r"university\s+student\s+required",
        
        # Senior/mid-level positions
        r"\bsenior\b",
        r"\bsr\.\s",
        r"\blead\s+",
        r"\bprincipal\b",
        r"\bstaff\s+(?:developer|engineer)",
        r"\barchitect\b",
        r"\bmanager\b",
        r"\bdirector\b",
        r"\bmid-?level\b",
        r"\bintermediate\b",
        r"\bexperienced\s+(?:developer|engineer)",
        
        # Experience requirements (2+ years for teens)
        r"[2-9]\+?\s*(?:years?|yrs?)\s+(?:of\s+)?experience",
        r"[1-9][0-9]\+?\s*(?:years?|yrs?)\s+(?:of\s+)?experience",
        r"(?:minimum|at\s+least)\s+[2-9]\+?\s*(?:years?|yrs?)",
        
        # Age restrictions
        r"\b(?:must\s+be\s+)?(?:19|21)\+",
        r"(?:19|21)\s+(?:years?\s+)?(?:or\s+)?older",
        r"minimum\s+age\s+(?:19|21)",
        
        # Full-time only indicators (we want part-time)
        r"full[\s-]?time\s+only",
        r"no\s+part[\s-]?time",
        
        # Complex tech requirements (not beginner-friendly)
        r"kubernetes",
        r"microservices\s+architecture",
        r"distributed\s+systems",
        r"machine\s+learning\s+engineer",
        r"data\s+scientist",
        r"devops\s+engineer",
        r"cloud\s+architect",
        r"security\s+engineer",
    ]
    
    # Keywords that indicate INCLUSION (job is relevant)
    INCLUSION_KEYWORDS = [
        # Part-time indicators (IMPORTANT)
        r"\bpart[\s-]?time\b",
        r"\bflexible\s+hours\b",
        r"\bflexible\s+schedule\b",
        r"\bweekend\s+(?:shifts?|hours?|work)",
        r"\bevening\s+(?:shifts?|hours?)",
        r"\bafter\s+school\b",
        
        # Teen-friendly job types
        r"\bretail\b",
        r"\bsales\s+associate\b",
        r"\bcashier\b",
        r"\bstore\s+associate\b",
        r"\bbarista\b",
        r"\bcrew\s+member\b",
        r"\bteam\s+member\b",
        r"\bfood\s+service\b",
        r"\brestaurant\b",
        r"\bserver\b",
        r"\bhost(?:ess)?\b",
        
        # Summer jobs
        r"\bsummer\s+(?:job|position|work|student)\b",
        r"\bseasonal\b",
        r"\bcamp\s+counselor\b",
        r"\blifeguard\b",
        
        # Entry-level tech
        r"\bintern\b",
        r"\binternship\b",
        r"\bjunior\b",
        r"\bentry[\s-]?level\b",
        r"\bno\s+experience\s+(?:required|needed|necessary)\b",
        r"\bwill\s+train\b",
        r"\btraining\s+provided\b",
        r"\bfirst\s+job\b",
        r"\bstudent\b",
        r"\bhiring\s+immediately\b",
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
        Check if job location is valid.
        For part-time/retail: Must be in Kitchener-Waterloo-Cambridge area.
        For tech internships: Remote is OK.
        """
        location = job.get('location', '').lower()
        description = job.get('description', '').lower()
        title = job.get('title', '').lower()
        job_type = job.get('job_type', '').lower()
        
        combined_text = f"{location} {description} {title}"
        
        # Check for valid on-site locations (KW area) - PREFERRED
        for pattern in self.location_patterns:
            if pattern.search(location):
                return True, "Local job (KW area)"
        
        # For tech internships only, allow remote
        is_tech_internship = ('intern' in combined_text or 'developer' in combined_text or 'tech' in combined_text)
        if is_tech_internship:
            for pattern in self.remote_patterns:
                if pattern.search(combined_text):
                    return True, "Remote tech internship"
        
        # If location is not specified and it's a known local company, include
        if not location or location in ['not specified', 'see listing', '']:
            return True, "Location unspecified - included"
        
        # Exclude jobs outside KW area
        return False, f"Not in KW area: {job.get('location', 'unknown')}"
    
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
        Higher score = more suitable for a 17-year-old seeking part-time work.
        """
        score = 0
        searchable_text = ' '.join([
            job.get('title', ''),
            job.get('description', ''),
            job.get('job_type', ''),
        ]).lower()
        
        location = job.get('location', '').lower()
        
        # PART-TIME is most important
        if 'part-time' in searchable_text or 'part time' in searchable_text:
            score += 20
        if 'flexible' in searchable_text:
            score += 10
        
        # Local jobs preferred
        if 'kitchener' in location or 'waterloo' in location or 'cambridge' in location:
            score += 15
        
        # Teen-friendly job types
        if 'retail' in searchable_text:
            score += 10
        if 'summer' in searchable_text:
            score += 12
        if any(store in searchable_text for store in ['footlocker', 'foot locker', 'bluenotes', 'tim hortons', 'mcdonalds', 'subway']):
            score += 10
        
        # Entry-level tech (simple)
        if 'intern' in searchable_text:
            score += 8
        if 'no experience' in searchable_text:
            score += 15
        if 'will train' in searchable_text or 'training provided' in searchable_text:
            score += 12
        if 'student' in searchable_text:
            score += 8
        if 'first job' in searchable_text:
            score += 10
        
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
