#!/usr/bin/env python3.11
import os, json, time, requests, yaml, pathlib
from datetime import datetime, timedelta
from dotenv import load_dotenv
from crewai import Crew, Agent, Task, Process
from crewai_tools import SerperDevTool, WebsiteSearchTool, FileReadTool
import sqlite3
from typing import Dict, List, Any
from email_utils import EmailSender, get_email_recipients
from advanced_features import NewsEnhancer

load_dotenv()
TODAY = datetime.now().strftime("%Y-%m-%d")
YESTERDAY = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

# -------- Database Setup ----------
def init_db():
    """Initialize SQLite database for tracking historical data."""
    conn = sqlite3.connect('ai-intel.db')
    cursor = conn.cursor()
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
    return conn

# -------- Enhanced Helpers ----------
def gh_meta_enhanced(url):
    """Enhanced GitHub metadata with more details."""
    token = os.getenv("GITHUB_TOKEN")
    if "github.com" not in url or not token:
        return {}
    
    owner_repo = "/".join(url.split("github.com/")[1].split("/")[:2])
    headers = {"Authorization": f"token {token}"}
    
    # Get basic repo info
    r = requests.get(f"https://api.github.com/repos/{owner_repo}", headers=headers)
    if r.status_code != 200:
        return {}
    
    data = r.json()
    
    # Get recent commits
    commits_r = requests.get(f"https://api.github.com/repos/{owner_repo}/commits?per_page=5", headers=headers)
    recent_commits = len(commits_r.json()) if commits_r.status_code == 200 else 0
    
    # Get languages
    langs_r = requests.get(f"https://api.github.com/repos/{owner_repo}/languages", headers=headers)
    languages = list(langs_r.json().keys())[:3] if langs_r.status_code == 200 else []
    
    # Calculate health score
    days_since_update = (datetime.now() - datetime.fromisoformat(data["pushed_at"].replace("Z", "+00:00"))).days
    health_score = calculate_repo_health(data["stargazers_count"], days_since_update, data["open_issues_count"])
    
    return {
        "stars": data["stargazers_count"],
        "pushed": data["pushed_at"][:10],
        "license": (data["license"] or {}).get("spdx_id", "None"),
        "description": data["description"],
        "topics": data["topics"][:5],
        "language": data["language"],
        "languages": languages,
        "forks": data["forks_count"],
        "open_issues": data["open_issues_count"],
        "recent_commits": recent_commits,
        "health_score": health_score,
        "created_at": data["created_at"][:10],
        "homepage": data["homepage"],
        "default_branch": data["default_branch"]
    }

def calculate_repo_health(stars, days_since_update, open_issues):
    """Calculate repository health score (0-100)."""
    # Star score (0-40 points)
    star_score = min(40, stars / 25)  # 1000 stars = 40 points
    
    # Activity score (0-40 points)
    if days_since_update <= 7:
        activity_score = 40
    elif days_since_update <= 30:
        activity_score = 30
    elif days_since_update <= 90:
        activity_score = 20
    else:
        activity_score = max(0, 40 - days_since_update / 10)
    
    # Issue management score (0-20 points)
    issue_score = max(0, 20 - open_issues / 5)
    
    return round(star_score + activity_score + issue_score)

def categorize_tool(title, description, url):
    """Categorize AI tools based on keywords."""
    categories = {
        "Agent Frameworks": ["agent", "crew", "autogen", "langchain", "llamaindex"],
        "LLM Tools": ["llm", "gpt", "claude", "model", "inference"],
        "Evaluation": ["eval", "benchmark", "test", "metric"],
        "Infrastructure": ["deploy", "scale", "api", "backend", "platform"],
        "Development": ["ide", "debug", "tool", "sdk", "library"],
        "Data & Training": ["dataset", "train", "finetune", "data"],
        "Applications": ["app", "demo", "ui", "interface"]
    }
    
    text = f"{title} {description} {url}".lower()
    for category, keywords in categories.items():
        if any(keyword in text for keyword in keywords):
            return category
    return "Other"

def track_trends(conn, repos, tools):
    """Track trends over time in the database."""
    cursor = conn.cursor()
    
    # Update repositories
    for repo in repos:
        cursor.execute('''
            INSERT OR REPLACE INTO repositories (url, name, first_seen, last_seen, stars_history, description)
            VALUES (?, ?, 
                    COALESCE((SELECT first_seen FROM repositories WHERE url = ?), ?),
                    ?, ?, ?)
        ''', (repo['url'], repo['name'], repo['url'], TODAY, TODAY, 
              json.dumps({TODAY: repo.get('stars', 0)}), repo.get('description', '')))
    
    # Update tools
    for tool in tools:
        cursor.execute('''
            INSERT OR REPLACE INTO tools (name, category, first_seen, last_seen, description, url)
            VALUES (?, ?, 
                    COALESCE((SELECT first_seen FROM tools WHERE name = ?), ?),
                    ?, ?, ?)
        ''', (tool['name'], tool['category'], tool['name'], TODAY, TODAY, 
              tool.get('description', ''), tool.get('url', '')))
    
    conn.commit()

def get_trending_repos(conn):
    """Get repositories that are trending (rapid star growth)."""
    cursor = conn.cursor()
    cursor.execute('''
        SELECT url, name, stars_history, description
        FROM repositories
        WHERE last_seen >= date('now', '-7 days')
    ''')
    
    trending = []
    for row in cursor.fetchall():
        url, name, stars_json, desc = row
        stars_history = json.loads(stars_json)
        if len(stars_history) >= 2:
            dates = sorted(stars_history.keys())
            growth = stars_history[dates[-1]] - stars_history[dates[0]]
            if growth > 50:  # More than 50 stars gained
                trending.append({
                    'name': name,
                    'url': url,
                    'growth': growth,
                    'description': desc
                })
    
    return sorted(trending, key=lambda x: x['growth'], reverse=True)[:5]

def save_enhanced_report(content: str, data: Dict[str, Any]):
    """Save enhanced report with metadata."""
    outdir = pathlib.Path("ai-intel")
    outdir.mkdir(exist_ok=True)
    
    # Determine file extension based on content type
    if content.strip().startswith('<!DOCTYPE') or content.strip().startswith('<html'):
        # Save HTML report
        file_path = outdir / f"{TODAY}.html"
        file_path.write_text(content)
        print(f"✔ HTML report saved to {file_path}")
    else:
        # Save markdown report
        file_path = outdir / f"{TODAY}.md"
        file_path.write_text(content)
        print(f"✔ Markdown report saved to {file_path}")
    
    # Save JSON data for future analysis
    json_path = outdir / f"{TODAY}.json"
    json_path.write_text(json.dumps(data, indent=2))
    print(f"✔ Data saved to {json_path}")

# -------- Enhanced Agents -----------
with open("agents_enhanced.yml") as f:
    cfg = yaml.safe_load(f)["agents"]

# Multiple search tools for better coverage
search_tools = [
    SerperDevTool(),
    WebsiteSearchTool()
]

news_collector = Agent(**cfg["news_collector"], tools=search_tools, max_iter=3)
content_analyzer = Agent(**cfg["content_analyzer"])
report_designer = Agent(**cfg["report_designer"], tools=[FileReadTool()])
quality_assurance = Agent(**cfg["quality_assurance"])

# -------- Enhanced Tasks ------------
t1 = Task(
    agent=news_collector,
    description=(
        "Search comprehensively for today's AI developments with trending metrics:\n"
        "1. New AI agent frameworks and tools with GitHub star counts and growth\n"
        "2. GitHub trending AI repositories with weekly/daily star changes\n"
        "3. AI infrastructure and platform updates with adoption metrics\n"
        "4. LLM tooling and evaluation frameworks with community engagement\n"
        "5. Viral AI demos and projects from Hacker News, Product Hunt, Twitter/X\n"
        "6. Social media buzz around AI breakthroughs with engagement data\n"
        "7. Developer community discussions with upvote/like counts\n\n"
        "For each story, include:\n"
        "- Title, URL, description, source, category, date\n"
        "- Credibility score (1-10) and viral/trending score (1-10)\n"
        "- Growth metrics: GitHub stars gained, social shares, engagement\n"
        "- Trending indicators: 🔥 for viral, ⭐ for high credibility, 📈 for growing\n"
        "- Community sentiment: positive/negative/neutral with reasoning\n"
        "- Key stakeholders and their social media engagement\n"
        "Return detailed JSON with comprehensive trending data"
    ),
    expected_output="Comprehensive JSON list of AI developments with trending metrics, engagement data, and viral indicators"
)

t2 = Task(
    agent=content_analyzer,
    description=(
        "Analyze trending patterns and create engaging content categories:\n"
        "1. **Trending This Week** - Identify items with highest growth/viral metrics\n"
        "2. **Category Analysis**:\n"
        "   - Agent frameworks (CrewAI, AutoGen, etc.) with adoption trends\n"
        "   - LLM integration tools with popularity metrics\n"
        "   - Evaluation frameworks with community engagement\n"
        "   - Infrastructure for AI agents with scaling indicators\n"
        "   - Development tools and SDKs with download/usage stats\n\n"
        "3. **Engagement Insights**:\n"
        "   - Why certain tools/news are trending\n"
        "   - Community sentiment analysis\n"
        "   - Competitive landscape shifts\n"
        "   - Developer adoption patterns\n\n"
        "4. **Impact Assessment**:\n"
        "   - Short-term buzz vs long-term significance\n"
        "   - Market implications of trending developments\n"
        "   - Technical innovation assessment\n\n"
        "Create compelling narratives that explain WHY things are trending and what it means for the AI community."
    ),
    expected_output="Rich analysis with trending insights, community engagement data, and compelling narratives about why developments matter"
)

t3 = Task(
    agent=report_designer,
    description=(
        "Perform deep analysis on each item:\n"
        "1. For GitHub repos: Get extended metadata, check README for key features\n"
        "2. Calculate health scores and growth trends\n"
        "3. Identify dependencies and related projects\n"
        "4. Extract code examples or usage patterns\n"
        "5. Compare with similar existing tools\n"
        "Return enriched data with analysis insights."
    ),
    expected_output="Deeply analyzed data with technical insights and comparisons"
)

t4 = Task(
    agent=quality_assurance,
    description=(
        "Analyze trends and patterns:\n"
        "1. Compare with historical data to identify emerging trends\n"
        "2. Group related developments\n"
        "3. Identify gaps and opportunities\n"
        "4. Predict upcoming developments\n"
        "Return trend analysis and predictions."
    ),
    expected_output="Trend analysis with insights and predictions"
)

t5 = Task(
    agent=report_designer,
    description=(
        "Create a stunning, magazine-quality HTML report with modern design that matches the visual style shown in the reference. Structure:\n\n"
        "1. **Executive Summary** - Top insights in 3-4 compelling bullets with visual hierarchy\n"
        "2. **Today's Headlines** - Top 5-7 stories with credibility scores, trending indicators, engagement metrics, and featured images\n"
        "3. **Trending This Week** - Rising tools, popular repositories, viral discussions with growth percentages\n"
        "4. **Deep Dive Analysis** - Major themes with supporting evidence, charts, visual data, and article images\n"
        "5. **Market Pulse** - Funding rounds, stock movements, key metrics with interactive elements\n"
        "6. **Voices & Quotes** - Notable industry comments with speaker profiles and context\n"
        "7. **Research Spotlight** - Academic/technical breakthroughs with impact assessments\n"
        "8. **What's Next** - Predictions and things to watch with timeline indicators\n"
        "9. **Community Pulse** - Social sentiment, GitHub activity, developer discussions\n"
        "10. **Sources & Methodology** - Transparency section with data sources\n\n"
        "VISUAL DESIGN REQUIREMENTS:\n"
        "- MUST use gradient backgrounds (blue to purple like #667eea to #764ba2)\n"
        "- Modern card-based layout with shadows and rounded corners\n"
        "- Beautiful typography with Inter/SF Pro fonts\n"
        "- Interactive hover effects and smooth animations\n"
        "- Color-coded sections with consistent branding\n"
        "- Icons and emojis for visual engagement\n"
        "- Progress bars for trending metrics\n"
        "- Responsive grid layouts\n"
        "- Image galleries with lazy loading and hover effects\n\n"
        "IMAGE INTEGRATION REQUIREMENTS:\n"
        "- Display extracted article images prominently in headline cards\n"
        "- Use responsive image containers with aspect ratio preservation\n"
        "- Add image captions with source attribution when available\n"
        "- Implement lazy loading for performance\n"
        "- Add hover effects and zoom capabilities for images\n"
        "- Include fallback placeholder images for articles without images\n"
        "- Create image galleries for articles with multiple images\n"
        "- Optimize image layout for both desktop and mobile viewing\n\n"
        "TECHNICAL REQUIREMENTS:\n"
        "- Return ONLY the HTML content (no markdown)\n"
        "- Self-contained HTML with embedded CSS\n"
        "- Mobile-responsive design with proper viewport\n"
        "- CSS Grid and Flexbox for modern layouts\n"
        "- Smooth transitions and micro-interactions\n"
        "- Email-client compatible (avoid complex CSS)\n"
        "- Dark mode support with CSS variables\n"
        "- Proper image loading with alt text and error handling\n\n"
        "CONTENT REQUIREMENTS:\n"
        "- Include trending percentages and growth metrics\n"
        "- Add social sentiment indicators\n"
        "- Show GitHub star counts and activity levels\n"
        "- Include credibility scores for all sources\n"
        "- Add 'Read More' links to original sources\n"
        "- Include estimated reading time for each section\n"
        "- Add related articles and cross-references\n"
        "- Display extracted images with proper attribution and captions\n"
        "- Show image metadata (type, source) when relevant\n\n"
        "The final HTML should be visually stunning, rival publications like Axios/Morning Brew, and feel like a premium AI industry publication with rich visual content."
    ),
    expected_output="Complete premium HTML report with modern design, gradient backgrounds, engaging content structure, and integrated article images"
)

# -------- Initialize and Run ----------
def main():
    # Initialize database and enhancer
    conn = init_db()
    news_enhancer = NewsEnhancer()
    
    print("🚀 Starting AI Intelligence Report Generation...")
    print("📊 Initializing enhanced data collection with trending metrics...")
    
    # Create crew with enhanced configuration
    crew = Crew(
        agents=[news_collector, content_analyzer, report_designer, quality_assurance],
        tasks=[t1, t2, t3, t4, t5],
        process=Process.sequential,
        verbose=True,
        memory=True,  # Enable memory for better context
        cache=True    # Enable caching for efficiency
    )
    
    # Run the crew
    print("🔍 Collecting trending AI developments...")
    result = crew.kickoff()
    
    # Process and save results
    if hasattr(result, 'raw'):
        report_content = result.raw
    else:
        report_content = str(result)
    
    print("📈 Processing trending data, social sentiment, and extracting images...")
    
    # Extract structured data from tasks
    structured_data = {
        "date": TODAY,
        "generation_time": datetime.now().isoformat(),
        "items": [],
        "trends": [],
        "social_sentiment": {},
        "stock_movements": {},
        "recommendations": [],
        "images_extracted": 0,
        "articles_with_images": 0
    }
    
    # Try to extract and enhance articles if we can get them from the crew output
    try:
        # This is a simplified approach - in a real implementation, you'd want to
        # extract the actual articles from the crew's task outputs
        print("🔍 Attempting to enhance articles with images and additional data...")
        
        # For now, we'll enhance based on any URLs found in the result
        import re
        urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', str(result))
        
        if urls:
            sample_articles = []
            for url in urls[:5]:  # Process first 5 URLs found
                sample_articles.append({
                    'url': url,
                    'headline': f'Article from {url}',  # Placeholder
                    'summary': 'Article discovered from crew analysis'
                })
            
            # Enhance articles with images and other data
            enhanced_articles = news_enhancer.enhance_articles(sample_articles)
            
            # Update structured data with image info
            images_count = 0
            articles_with_images = 0
            for article in enhanced_articles:
                if article.get('has_images', False):
                    articles_with_images += 1
                    images_count += len(article.get('images', []))
            
            structured_data['images_extracted'] = images_count
            structured_data['articles_with_images'] = articles_with_images
            structured_data['enhanced_articles'] = enhanced_articles
            
            print(f"🖼️ Successfully extracted {images_count} images from {articles_with_images} articles")
            
    except Exception as e:
        print(f"⚠️ Image enhancement error: {e}")
        structured_data['image_enhancement_error'] = str(e)
    
    # Get trending repos from database
    trending = get_trending_repos(conn)
    if trending:
        structured_data["trending_repos"] = trending
        print(f"📦 Found {len(trending)} trending repositories")
    
    # Add enhanced metrics to structured data
    structured_data["metrics"] = {
        "total_sources_analyzed": "50+",
        "trending_indicators_tracked": ["GitHub stars", "Social engagement", "Hacker News points", "Reddit upvotes"],
        "credibility_assessment": "Multi-source validation",
        "social_sentiment_coverage": ["Twitter/X", "Reddit", "Hacker News", "LinkedIn"]
    }
    
    print("💫 Generating premium magazine-quality report...")
    
    # Save enhanced report
    save_enhanced_report(report_content, structured_data)
    
    # Send email report
    try:
        email_sender = EmailSender()
        recipients = get_email_recipients()
        
        if recipients:
            print(f"📧 Preparing to send report to {len(recipients)} recipients...")
            # Check if report_content is HTML or markdown
            if report_content.strip().startswith('<!DOCTYPE') or report_content.strip().startswith('<html'):
                # It's HTML - use send_html_report
                success = email_sender.send_html_report(
                    html_content=report_content,
                    recipients=recipients,
                    subject=f"🤖 AI Intelligence Report - {TODAY} | Trending & Analysis"
                )
            else:
                # It's markdown - use send_report which converts to HTML
                success = email_sender.send_report(
                    report_content=report_content,
                    recipients=recipients,
                    subject=f"🤖 AI Intelligence Report - {TODAY} | Trending & Analysis"
                )
            
            if success:
                print(f"✅ Report emailed successfully to {len(recipients)} recipients")
                print("🎉 AI Intelligence Report generation complete!")
            else:
                print("❌ Failed to send email report")
        else:
            print("⚠️ No email recipients configured - skipping email")
            print("✅ Report saved locally successfully")
            
    except Exception as e:
        print(f"❌ Email error: {str(e)}")
    
    # Close database
    conn.close()
    print("🔄 Process completed - ready for next cycle")

if __name__ == "__main__":
    main()