"""
Pytest fixtures for AI-Watcher test suite.

This module provides shared fixtures for mocking environment variables,
HTTP responses, database connections, and sample test data.
"""

import os
import sys
import json
import sqlite3
import tempfile
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
import pytest

# Mock crewai modules before any imports that might need them
# This allows tests to run without crewai being installed
sys.modules['crewai'] = MagicMock()
sys.modules['crewai_tools'] = MagicMock()


# ---------------------------------------------------------------------------
# Environment Variable Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables used throughout the application."""
    env_vars = {
        'GITHUB_TOKEN': 'test_github_token_123',
        'MAILGUN_API': 'test_mailgun_api_key',
        'MAILGUN_DOMAIN': 'test.example.com',
        'EMAIL_FROM': 'AI Watcher <test@example.com>',
        'EMAIL_RECIPIENTS': 'user1@example.com,user2@example.com',
        'SERPER_API_KEY': 'test_serper_key',
        'TWITTER_BEARER_TOKEN': 'test_twitter_token',
        'REDDIT_CLIENT_ID': 'test_reddit_id',
        'REDDIT_CLIENT_SECRET': 'test_reddit_secret',
        'ALPHA_VANTAGE_API_KEY': 'test_alpha_vantage_key',
        'FINNHUB_API_KEY': 'test_finnhub_key',
    }
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    return env_vars


@pytest.fixture
def mock_env_minimal(monkeypatch):
    """Mock minimal environment variables (no optional API keys)."""
    env_vars = {
        'MAILGUN_API': 'test_mailgun_api_key',
        'EMAIL_FROM': 'AI Watcher <test@example.com>',
    }
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    # Clear optional API keys
    for key in ['GITHUB_TOKEN', 'TWITTER_BEARER_TOKEN', 'REDDIT_CLIENT_ID',
                'REDDIT_CLIENT_SECRET', 'ALPHA_VANTAGE_API_KEY', 'FINNHUB_API_KEY']:
        monkeypatch.delenv(key, raising=False)
    return env_vars


@pytest.fixture
def no_mailgun_env(monkeypatch):
    """Mock environment without Mailgun API key."""
    monkeypatch.delenv('MAILGUN_API', raising=False)


# ---------------------------------------------------------------------------
# Database Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def temp_db():
    """Create a temporary SQLite database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create tables matching init_db()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS repositories (
            url TEXT PRIMARY KEY,
            name TEXT,
            first_seen DATE,
            last_seen DATE,
            stars_history TEXT,
            description TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tools (
            name TEXT PRIMARY KEY,
            category TEXT,
            first_seen DATE,
            last_seen DATE,
            description TEXT,
            url TEXT
        )
    ''')
    conn.commit()

    yield conn

    conn.close()
    os.unlink(db_path)


@pytest.fixture
def populated_db(temp_db):
    """Create a populated database with sample data."""
    cursor = temp_db.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

    # Insert sample repositories
    sample_repos = [
        ('https://github.com/test/repo1', 'repo1', week_ago, today,
         json.dumps({week_ago: 100, today: 200}), 'Test repo with growth'),
        ('https://github.com/test/repo2', 'repo2', week_ago, today,
         json.dumps({week_ago: 500, today: 510}), 'Stable repo'),
        ('https://github.com/test/repo3', 'repo3', week_ago, yesterday,
         json.dumps({week_ago: 50}), 'Old repo'),
    ]

    cursor.executemany('''
        INSERT INTO repositories (url, name, first_seen, last_seen, stars_history, description)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', sample_repos)

    # Insert sample tools
    sample_tools = [
        ('TestTool1', 'Agent Frameworks', week_ago, today, 'A test agent tool', 'https://example.com/tool1'),
        ('TestTool2', 'LLM Tools', week_ago, today, 'An LLM integration tool', 'https://example.com/tool2'),
    ]

    cursor.executemany('''
        INSERT INTO tools (name, category, first_seen, last_seen, description, url)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', sample_tools)

    temp_db.commit()
    return temp_db


# ---------------------------------------------------------------------------
# Sample Data Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_article():
    """Sample article data for testing."""
    return {
        'headline': 'OpenAI Announces GPT-5 with Revolutionary Capabilities',
        'summary': 'Microsoft-backed OpenAI unveils breakthrough in machine learning and artificial intelligence.',
        'url': 'https://example.com/article/openai-gpt5',
        'source': 'Tech News',
        'date': datetime.now().strftime("%Y-%m-%d"),
        'credibility_score': 8,
        'impact_score': 9,
        'stakeholders': ['OpenAI', 'Microsoft', 'Sam Altman']
    }


@pytest.fixture
def sample_articles():
    """Multiple sample articles for testing."""
    return [
        {
            'headline': 'OpenAI Announces GPT-5 with Revolutionary Capabilities',
            'summary': 'OpenAI unveils breakthrough in deep learning and transformer technology.',
            'url': 'https://example.com/article/1',
            'source': 'Tech News',
            'stakeholders': ['OpenAI', 'Microsoft']
        },
        {
            'headline': 'Google DeepMind Achieves AGI Milestone',
            'summary': 'Alphabet subsidiary demonstrates amazing neural network capabilities.',
            'url': 'https://example.com/article/2',
            'source': 'AI Weekly',
            'stakeholders': ['Google', 'DeepMind']
        },
        {
            'headline': 'NVIDIA Reports Record AI Chip Sales',
            'summary': 'NVIDIA GPU sales surge as AI demand grows exponentially.',
            'url': 'https://example.com/article/3',
            'source': 'Finance Daily',
            'stakeholders': ['NVIDIA']
        }
    ]


@pytest.fixture
def sample_github_repo_data():
    """Sample GitHub repository API response data."""
    # Use a recent date to avoid timezone issues with the health calculation
    recent_date = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%dT%H:%M:%S")
    return {
        "stargazers_count": 5000,
        "pushed_at": f"{recent_date}Z",
        "license": {"spdx_id": "MIT"},
        "description": "A powerful AI agent framework",
        "topics": ["ai", "agents", "llm", "python", "ml"],
        "language": "Python",
        "forks_count": 500,
        "open_issues_count": 25,
        "created_at": "2023-06-15T10:00:00Z",
        "homepage": "https://example.com",
        "default_branch": "main"
    }


@pytest.fixture
def sample_markdown_content():
    """Sample markdown content for email conversion tests."""
    return """# AI Intelligence Report

## Executive Summary

Today's **key developments** in AI include:

- OpenAI announced GPT-5 with *revolutionary* capabilities
- Google DeepMind achieved new benchmarks
- NVIDIA reports record chip sales

### Trending Repositories

| Repository | Stars | Growth |
|------------|-------|--------|
| test/repo1 | 5000  | +500   |
| test/repo2 | 3000  | +200   |

Visit [OpenAI](https://openai.com) for more information.

```python
def hello_ai():
    print("Hello, AI!")
```

---

That's all for today's report.
"""


@pytest.fixture
def sample_html_page():
    """Sample HTML page for image extraction tests."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta property="og:image" content="https://example.com/og-image.jpg">
        <meta property="og:title" content="Test Article Title">
        <meta name="twitter:image" content="https://example.com/twitter-image.jpg">
        <meta name="twitter:title" content="Twitter Title">
    </head>
    <body>
        <article>
            <img class="featured-image" src="/images/featured.jpg" alt="Featured Image" width="800" height="600">
            <div class="article-content">
                <p>Article content here.</p>
                <img src="/images/content1.jpg" alt="Content Image 1" width="400" height="300">
                <img src="/images/content2.jpg" alt="Content Image 2" width="400" height="300">
            </div>
        </article>
        <img src="/images/small.jpg" alt="Small Image" width="50" height="50">
    </body>
    </html>
    """


# ---------------------------------------------------------------------------
# HTTP Mock Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_requests_get():
    """Mock requests.get for HTTP calls."""
    with patch('requests.get') as mock_get:
        yield mock_get


@pytest.fixture
def mock_requests_post():
    """Mock requests.post for HTTP calls."""
    with patch('requests.post') as mock_post:
        yield mock_post


@pytest.fixture
def mock_successful_github_response(sample_github_repo_data):
    """Mock a successful GitHub API response."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = sample_github_repo_data
    return mock_response


@pytest.fixture
def mock_github_commits_response():
    """Mock GitHub commits API response."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {"sha": "abc123", "commit": {"message": "Fix bug"}},
        {"sha": "def456", "commit": {"message": "Add feature"}},
        {"sha": "ghi789", "commit": {"message": "Update docs"}},
    ]
    return mock_response


@pytest.fixture
def mock_github_languages_response():
    """Mock GitHub languages API response."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"Python": 50000, "JavaScript": 10000, "TypeScript": 5000}
    return mock_response


@pytest.fixture
def mock_mailgun_success_response():
    """Mock successful Mailgun API response."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"id": "<message_id>", "message": "Queued. Thank you."}
    return mock_response


@pytest.fixture
def mock_mailgun_error_response():
    """Mock Mailgun API error response."""
    mock_response = MagicMock()
    mock_response.status_code = 403
    mock_response.json.return_value = {"message": "Access denied"}
    mock_response.text = "Forbidden"
    return mock_response


@pytest.fixture
def mock_twitter_response():
    """Mock Twitter API search response."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": [
            {
                "text": "Amazing breakthrough in AI! This is revolutionary and exciting!",
                "created_at": "2024-01-15T10:00:00Z",
                "public_metrics": {"like_count": 100, "retweet_count": 50}
            },
            {
                "text": "Concerning developments in AI safety. This is dangerous.",
                "created_at": "2024-01-15T11:00:00Z",
                "public_metrics": {"like_count": 25, "retweet_count": 10}
            }
        ]
    }
    return mock_response


@pytest.fixture
def mock_alpha_vantage_response():
    """Mock Alpha Vantage API response."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "Global Quote": {
            "01. symbol": "NVDA",
            "05. price": "500.00",
            "09. change": "10.50",
            "10. change percent": "2.15%",
            "06. volume": "50000000",
            "07. latest trading day": "2024-01-15"
        }
    }
    return mock_response


@pytest.fixture
def mock_finnhub_response():
    """Mock Finnhub API response."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "c": 500.00,  # Current price
        "pc": 490.00,  # Previous close
        "h": 510.00,  # High
        "l": 485.00,  # Low
        "o": 492.00,  # Open
        "v": 50000000  # Volume
    }
    return mock_response


@pytest.fixture
def mock_image_head_response():
    """Mock HEAD response for image validation."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {
        'content-type': 'image/jpeg',
        'content-length': '150000',
        'last-modified': 'Mon, 15 Jan 2024 10:00:00 GMT'
    }
    return mock_response


# ---------------------------------------------------------------------------
# Session/Request Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_requests_session():
    """Mock requests.Session for web scraping."""
    with patch('requests.Session') as mock_session_class:
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        yield mock_session


# ---------------------------------------------------------------------------
# Utility Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def cleanup_db_file():
    """Cleanup any test database files after test."""
    yield
    if os.path.exists('ai-intel.db'):
        os.unlink('ai-intel.db')


@pytest.fixture(autouse=True)
def reset_singleton_state():
    """Reset any singleton state between tests."""
    yield
    # Clean up any global state if needed
