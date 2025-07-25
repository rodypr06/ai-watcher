# 🤖 AI-Watcher Enhanced

An intelligent AI news aggregation system built with CrewAI that provides comprehensive monitoring of AI developments worldwide. Features multi-agent intelligence pipeline, historical trend tracking, and professional magazine-quality reports with glass-style design.

## ✨ Features

### 🎯 **Core Capabilities**
- **Multi-agent Intelligence Pipeline**: 4 specialized agents for comprehensive analysis
- **Historical Trend Tracking**: SQLite database with GitHub repo monitoring and health scoring
- **Professional Reporting**: Magazine-quality HTML reports with responsive glass-style design
- **Social Sentiment Analysis**: Twitter/Reddit integration for community sentiment
- **Stock Market Integration**: AI company stock tracking and correlation analysis
- **Email Distribution**: Automated delivery with Mailgun integration

### 🏗️ **Agent Architecture**
1. **News Collector Agent** - Gathers trending AI developments from 20+ trusted sources
2. **Content Analyzer Agent** - Transforms raw data into meaningful insights with 6-category analysis
3. **Report Designer Agent** - Creates magazine-quality HTML reports with glass-style design
4. **Quality Assurance Agent** - Ensures accuracy, completeness, and professional presentation

### 🎨 **Visual Design**
- **Liquid Glass Design System**: Modern glass-morphism aesthetic
- **Responsive Layout**: Mobile-optimized with CSS Grid and Flexbox
- **Dark Theme**: Deep space backgrounds with vibrant cyan accents (#00BCD4)
- **Interactive Elements**: Hover effects, animations, and micro-interactions
- **Image Handling**: Smart fallbacks and error handling for article images

## 🚀 Quick Start

### Prerequisites
```bash
pip install -r requirements.txt
```

### Environment Setup
Create a `.env` file with:

```bash
# Core LLM Backend
OPENAI_API_KEY=your_openai_api_key_here

# Web Search (Required)
SERPER_API_KEY=your_serper_api_key_here

# Email Distribution (Required)
MAILGUN_API=your_mailgun_api_key_here
EMAIL_RECIPIENTS=email1@domain.com,email2@domain.com
EMAIL_FROM=AI Watcher <postmaster@rodytech.net>

# Optional: Enhanced Features
TWITTER_BEARER_TOKEN=your_twitter_bearer_token
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
FINNHUB_API_KEY=your_finnhub_key
GITHUB_TOKEN=your_github_token_for_repo_analysis
```

### Run the System
```bash
python crew_watch_improved.py
```

### Testing
```bash
python test_enhanced_system.py
```

## 📊 Database Schema

### Repository Tracking
- **URL**: GitHub repository URL (Primary Key)
- **Health Score**: 0-100 based on stars, activity, and issue management
- **Star History**: JSON tracking growth over time
- **Last Activity**: Recent commit tracking

### Tool Categorization
- **Auto-categorization**: 7 domains (Agent Frameworks, LLM Tools, etc.)
- **Community Metrics**: Adoption rates and engagement tracking

## 🏢 Architecture

### Data Flow
```
News Sources → Collector Agent → Analyzer Agent → Designer Agent → QA Agent → Email/Storage
```

### Enhanced Features
- **Social Sentiment**: Multi-platform analysis with scoring
- **Stock Tracking**: Real-time AI company performance monitoring  
- **Trend Analysis**: Historical pattern recognition and predictions
- **Image Enhancement**: Automatic article image extraction and processing

## 📧 Email Reports

Reports include 10 comprehensive sections:
1. **Executive Summary** - Strategic insights and key metrics
2. **Today's Headlines** - Top stories with credibility scores
3. **Trending This Week** - Rising tools and repositories
4. **Deep Dive Analysis** - Major themes and implications
5. **Market Pulse** - Funding rounds and stock movements
6. **Voices & Quotes** - Industry leader commentary
7. **Research Spotlight** - Academic breakthroughs
8. **What's Next** - Predictions and timeline
9. **Community Pulse** - Social sentiment analysis
10. **Sources & Methodology** - Transparency and attribution

## 🛠️ Development

### Project Structure
```
ai-watcher/
├── crew_watch_improved.py    # Main orchestration script
├── agents_enhanced.yml       # Agent configurations
├── email_utils.py           # Email system with glass styling
├── advanced_features.py     # Social sentiment & stock tracking
├── requirements.txt         # Dependencies
├── glass-style.md          # Design system guide
└── CLAUDE.md               # Development instructions
```

### Key Dependencies
- `crewai>=0.150.0` - Multi-agent framework
- `crewai-tools>=0.12.0` - Web search and file tools
- `python-dotenv>=1.0.0` - Environment management
- `requests>=2.31.0` - HTTP requests
- `beautifulsoup4` - HTML parsing for image extraction

## 🎯 Use Cases

- **AI Development Teams**: Stay current with tools and frameworks
- **Investment Research**: Track AI market trends and funding
- **Technology Leadership**: Strategic intelligence on AI developments
- **Developer Communities**: Discover trending tools and libraries

## 🔧 Customization

The system is highly extensible:
- **Add News Sources**: Modify agent configurations
- **Custom Analysis**: Extend Content Analyzer frameworks
- **Design Updates**: Modify glass-style templates
- **New Databases**: Add specialized tracking systems

## 📄 License

MIT License - See LICENSE file for details

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 🌟 Acknowledgments

- Built with [CrewAI](https://github.com/joaomdmoura/crewai)
- Inspired by modern AI development workflows
- Design system influenced by glass-morphism trends

---

**Generated with AI-Watcher Enhanced System** 🤖✨