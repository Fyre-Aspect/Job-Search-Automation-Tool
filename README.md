#Job Search Automation Tool

Automated daily job search system that scrapes entry-level developer positions and emails new matches.

## Features

- ** Multi-Source Scraping**: Indeed RSS, RemoteOK, The Muse, Adzuna (optional)
- ** Smart Filtering**: Excludes senior roles, degree requirements, 3+ years experience
- ** Location Aware**: Remote jobs globally, on-site only for Kitchener-Waterloo
- ** Email Alerts**: Beautiful HTML emails with job details
- ** Deduplication**: Never sends the same job twice
- ** Automated**: Runs daily at 8:00 PM Eastern via GitHub Actions

## Quick Start

### 1. Fork/Clone Repository

```bash
git clone https://github.com/Fyre-Aspect/Job-Search-Automation-Tool.git
cd Job-Search-Automation-Tool
```

### 2. Configure GitHub Secrets

Go to your repository: **Settings → Secrets and variables → Actions → New repository secret**

Add these secrets:

| Secret Name | Value | Required |
|-------------|-------|----------|
| `GMAIL_USER` | Your Gmail address |  Yes |
| `GMAIL_APP_PASSWORD` | 16-character app password |  Yes |
| `RECIPIENT_EMAIL` | Email to receive alerts (defaults to GMAIL_USER) |  Optional |
| `ADZUNA_APP_ID` | Adzuna API ID |  Optional |
| `ADZUNA_APP_KEY` | Adzuna API Key |  Optional |

### 3. Generate Gmail App Password

1. Enable 2-Factor Authentication on your Google account
2. Go to: https://myaccount.google.com/apppasswords
3. Select "Mail" and generate a password
4. Copy the 16-character password (remove spaces)

### 4. Enable GitHub Actions

The workflow runs automatically at **1:00 AM UTC daily** (8:00 PM EST).

To run manually:
1. Go to **Actions** tab
2. Select "Daily Job Search"
3. Click **Run workflow**

## Project Structure

```
Job-Search-Automation-Tool/
├── .github/
│   └── workflows/
│       └── daily-job-search.yml   # GitHub Actions workflow
├── src/
│   ├── scrapers/
│   │   ├── indeed_rss.py          # Indeed RSS feed scraper
│   │   ├── remoteok.py            # RemoteOK API scraper
│   │   ├── themuse.py             # The Muse API scraper
│   │   └── adzuna.py              # Adzuna API scraper (optional)
│   ├── job_processor.py           # Filtering & validation
│   ├── deduplication.py           # Duplicate detection
│   └── email_sender.py            # Gmail SMTP sender
├── templates/
│   └── email_template.html        # HTML email template
├── data/
│   └── sent_jobs.json             # Deduplication database
├── main.py                        # Main orchestrator
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

## Job Criteria

### Target Roles
- Web Developer
- Software Engineer/Developer
- Full Stack Developer
- Frontend/Backend Developer
- Junior Developer
- Software/Web Engineering Intern

### Hard Filters (Auto-Exclude)
-  Requires bachelor's degree
-  Requires university enrollment
-  Mid-level or senior positions
-  Requires 3+ years experience

### Preferred Criteria
-  Entry-level or beginner-friendly
-  Open to self-taught developers
-  Skills-based or portfolio-based

### Location Rules
-  Remote: Global or North America
-  On-site: Kitchener-Waterloo, Ontario only

## Local Development

### Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials
```

### Run Locally

```bash
# Set environment variables (Windows PowerShell)
$env:GMAIL_USER="your-email@gmail.com"
$env:GMAIL_APP_PASSWORD="your-app-password"

# Run the job search
python main.py
```

### Test Individual Components

```bash
# Test Indeed scraper
python -m src.scrapers.indeed_rss

# Test RemoteOK scraper
python -m src.scrapers.remoteok

# Test email sender (sends test email)
python -m src.email_sender
```

## Customization

### Add/Modify Search Keywords

Edit `src/scrapers/indeed_rss.py`:

```python
SEARCH_QUERIES = [
    "junior web developer",
    "your custom search",
    # Add more...
]
```

### Modify Exclusion Filters

Edit `src/job_processor.py`:

```python
EXCLUSION_KEYWORDS = [
    r"bachelor's degree required",
    r"your-custom-exclusion",
    # Add more regex patterns...
]
```

### Change Email Template

Edit `templates/email_template.html` with your preferred HTML/CSS styling.

## Troubleshooting

### Email not sending?

1. Verify `GMAIL_USER` and `GMAIL_APP_PASSWORD` secrets are set
2. Ensure you're using an App Password, not your regular password
3. Check GitHub Actions logs for error messages

### No jobs found?

1. Check if the job sources are accessible
2. Filters may be too strict - review `job_processor.py`
3. Try running individual scrapers to debug

### Workflow not running?

1. GitHub Actions may be disabled - check Settings → Actions
2. Repository must have been active in last 60 days
3. Check for YAML syntax errors in workflow file

## License

MIT License - Feel free to modify and use for your own job search!

## Contributing

Contributions welcome! Please open an issue or PR for any improvements.
