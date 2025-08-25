<div align="center">

# 🛍️ Smart Price Tracker

**The Ultimate E-commerce Price Monitoring & Business Intelligence Platform**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](Dockerfile)
[![Selenium](https://img.shields.io/badge/Selenium-Enhanced-orange.svg)](https://selenium.dev)
[![Dash](https://img.shields.io/badge/Dashboard-Interactive-purple.svg)](https://dash.plotly.com)

*Track prices, maximize profits, automate decisions*

[🚀 Quick Start](#-quick-start) • [📊 Features](#-features) • [🎯 Demo](#-demo) • [📖 Documentation](#-documentation) • [🤝 Contributing](#-contributing)

</div>

---

## 🌟 Overview

**Smart Price Tracker** is a comprehensive, enterprise-grade price monitoring and business intelligence platform designed for e-commerce professionals, resellers, and businesses. Built with Python and modern web technologies, it provides real-time price tracking, automated notifications, profit analysis, and advanced business intelligence across multiple platforms.

### 🎯 Why Smart Price Tracker?

- **💰 Maximize Profits**: Advanced profit calculation with platform-specific fee analysis
- **⚡ Real-time Monitoring**: Automated tracking with intelligent scheduling
- **📊 Business Intelligence**: Interactive dashboards with trend analysis and insights  
- **🔔 Smart Notifications**: Multi-channel alerts (Email, Telegram, Slack)
- **🤖 Anti-bot Protection**: Advanced stealth scraping with session rotation
- **🎨 Modern UI**: Beautiful, responsive dashboards built with Dash
- **🐳 Production Ready**: Docker deployment with comprehensive monitoring

---

## ✨ Features

### 🛒 **Multi-Platform Support**
- **Amazon** - Complete integration with advanced selectors
- **eBay** - Full marketplace support (coming soon)
- **Walmart** - Enterprise marketplace tracking (coming soon)  
- **AliExpress** - Global marketplace support (coming soon)
- **Extensible Architecture** - Easy to add new platforms

### 📈 **Advanced Analytics & Intelligence**
- **Real-time Price Tracking** with historical data
- **Profit Margin Analysis** with platform-specific fees
- **Seller Comparison** across multiple platforms
- **Trend Analysis** with predictive insights
- **ROI Calculations** and break-even analysis
- **Performance Metrics** and success rate tracking

### 🔔 **Smart Notification System**
- **Multi-channel Alerts**: Email, Telegram, Slack
- **Intelligent Triggers**: Price drops, stock changes, target prices
- **Customizable Priorities**: Low, Medium, High, Urgent
- **Rich Formatting**: HTML emails, Slack blocks, Telegram markup
- **Bulk Notifications**: Daily summaries and weekly reports

### 🎨 **Interactive Dashboards**
- **Main Dashboard**: Real-time metrics, charts, and analytics
- **URL Manager**: Easy product addition and management
- **Profit Calculator**: Live fee calculations and comparisons
- **System Monitor**: Health checks and performance metrics
- **Export Tools**: Excel, Google Sheets integration

### 🤖 **Advanced Anti-Bot Protection**
- **Stealth Scraping**: Undetected Chrome with fingerprint rotation
- **Session Management**: Automatic rotation and cleanup
- **Human Behavior Simulation**: Mouse movements, scrolling, delays
- **CAPTCHA Detection**: Intelligent handling and recovery
- **Proxy Support**: Rotating proxy pools for anonymity
- **Request Throttling**: Smart delays and retry logic

### ⚙️ **Automation & Orchestration**
- **Smart Scheduler**: Configurable job scheduling with priorities
- **System Monitoring**: Real-time health checks and metrics
- **Automated Exports**: Daily reports and data synchronization
- **Database Management**: Automatic cleanup and optimization
- **Error Recovery**: Intelligent retry and fallback mechanisms
- **Graceful Shutdown**: Clean resource management

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.11+**
- **Docker** (optional, recommended)
- **Chrome/Chromium** (for Selenium mode)

### 🐳 Docker Deployment (Recommended)

```bash
# Clone the repository
git clone https://github.com/Mukhammad-develop/smart-price-tracker.git
cd smart-price-tracker

# Configure environment
cp env.example .env
# Edit .env with your settings

# Deploy with Docker Compose
docker-compose up -d

# Access dashboards
# Main Dashboard: http://localhost:8050
# URL Manager: http://localhost:8051
```

### 🐍 Local Installation

```bash
# Clone and setup
git clone https://github.com/Mukhammad-develop/smart-price-tracker.git
cd smart-price-tracker

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp env.example .env
# Edit .env file with your configuration

# Initialize database
python main.py

# Start automation system
python src/automation/orchestrator.py
```

---

## 📊 Architecture

<div align="center">

```mermaid
graph TB
    A[Web Scraping Layer] --> B[Data Processing]
    B --> C[Database Storage]
    C --> D[Analytics Engine]
    D --> E[Notification System]
    D --> F[Dashboard UI]
    
    G[Scheduler] --> A
    H[Monitoring] --> I[Health Checks]
    I --> E
    
    J[API Layer] --> C
    J --> F
    
    subgraph "Anti-Bot Protection"
        A1[Proxy Rotation]
        A2[User Agent Rotation] 
        A3[Session Management]
        A4[CAPTCHA Handling]
    end
    
    subgraph "Notifications"
        E1[Email]
        E2[Telegram]
        E3[Slack]
    end
    
    subgraph "Export Systems"
        F1[Excel Export]
        F2[Google Sheets]
        F3[CSV Export]
    end
```

</div>

### 🏗️ **Core Components**

| Component | Description | Technology |
|-----------|-------------|------------|
| **Scraping Engine** | Advanced web scraping with anti-bot protection | Selenium, BeautifulSoup, Undetected Chrome |
| **Data Layer** | Robust data storage and management | SQLAlchemy, SQLite/PostgreSQL |
| **Analytics Engine** | Business intelligence and profit analysis | Pandas, NumPy |
| **Notification System** | Multi-channel alert delivery | SMTP, Telegram API, Slack API |
| **Dashboard UI** | Interactive web interfaces | Dash, Plotly, HTML/CSS |
| **Automation Layer** | Job scheduling and system orchestration | Threading, Schedule |
| **Monitoring System** | Health checks and performance metrics | psutil, Custom metrics |

---

## 🎯 Demo

### 📱 **Interactive Dashboards**

<div align="center">

**Main Dashboard**
![Dashboard Preview](https://via.placeholder.com/800x400/667eea/ffffff?text=Interactive+Price+Dashboard)

**Real-time Analytics**
![Analytics Preview](https://via.placeholder.com/800x400/764ba2/ffffff?text=Advanced+Analytics+%26+Charts)

</div>

### 🚀 **Quick Demo Commands**

```bash
# Add a product for tracking
python main.py --add-product "https://amazon.com/product-url" --target-price 25.99

# Run immediate price check
python main.py --check-now

# Export current data
python main.py --export excel

# Test notifications
python main.py --test-notifications

# View system status
python main.py --status
```

---

## 📖 Documentation

### 🔧 **Configuration**

The system uses environment variables for configuration. Copy `env.example` to `.env` and configure:

```bash
# Database Configuration
DATABASE_URL=sqlite:///data/price_tracker.db

# Notification Services
EMAIL_ADDRESS=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
SLACK_BOT_TOKEN=your_slack_bot_token

# Scraping Configuration
REQUEST_DELAY_MIN=2
REQUEST_DELAY_MAX=8
USE_PROXY=false
PROXY_LIST=proxy1:8080,proxy2:8080

# Scheduling
TRACKING_INTERVAL_HOURS=1
QUICK_CHECK_INTERVAL_HOURS=0.25
```

### 📊 **API Usage**

```python
from src.core.tracker import PriceTracker
from src.utils.config import Config

# Initialize tracker
config = Config()
tracker = PriceTracker(config)

# Add product
product_id = tracker.add_product(
    url="https://amazon.com/product-url",
    target_price=25.99,
    user_cost_price=15.00
)

# Run tracking
results = tracker.run_tracking()
print(f"Updated {results['updated']} products")

# Get analytics
analytics = tracker.get_analytics(days=30)
print(f"Average price: ${analytics['average_price']:.2f}")

# Export data
export_result = tracker.export_data("excel")
print(f"Exported to: {export_result['filepath']}")
```

### 🎨 **Dashboard Access**

| Dashboard | URL | Description |
|-----------|-----|-------------|
| **Main Dashboard** | http://localhost:8050 | Real-time analytics and charts |
| **URL Manager** | http://localhost:8051 | Product management interface |
| **System Monitor** | http://localhost:8052 | Health and performance metrics |

### 📧 **Notification Setup**

<details>
<summary><strong>📨 Email Notifications</strong></summary>

```bash
# Gmail Setup
EMAIL_ADDRESS=your_email@gmail.com
EMAIL_PASSWORD=your_app_password  # Generate from Google Account Settings
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

</details>

<details>
<summary><strong>💬 Telegram Notifications</strong></summary>

1. Create a bot with [@BotFather](https://t.me/BotFather)
2. Get your chat ID from [@userinfobot](https://t.me/userinfobot)
3. Configure:

```bash
TELEGRAM_BOT_TOKEN=123456789:ABCDEF...
TELEGRAM_CHAT_ID=your_chat_id
```

</details>

<details>
<summary><strong>💼 Slack Notifications</strong></summary>

1. Create a Slack app at [api.slack.com](https://api.slack.com)
2. Add OAuth scopes: `chat:write`, `channels:read`
3. Install to workspace and get token:

```bash
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_CHANNEL=#price-alerts
```

</details>

---

## 🔄 Automation & Scheduling

### ⏰ **Default Schedule**

| Job | Frequency | Description |
|-----|-----------|-------------|
| **Main Tracking** | Every hour | Complete price check for all products |
| **Quick Check** | Every 15 min | Priority products with target prices |
| **Daily Export** | 2:00 AM | Automated data export and reports |
| **Weekly Report** | Sunday 9:00 AM | Comprehensive analytics summary |
| **Health Check** | Every 30 min | System monitoring and alerts |
| **Database Cleanup** | 3:00 AM | Remove old data (90+ days) |

### 🎛️ **Custom Job Management**

```python
from src.automation.orchestrator import AutomationOrchestrator

orchestrator = AutomationOrchestrator()

# Add custom job
orchestrator.add_custom_job(
    job_id="custom_export",
    name="Custom Export Job", 
    function=my_export_function,
    schedule_type="daily",
    schedule_value="18:00"  # 6 PM daily
)

# Manage jobs
orchestrator.pause_job("quick_check")
orchestrator.resume_job("quick_check")
orchestrator.execute_job_now("main_tracking")
```

---

## 🛡️ Anti-Bot Protection

### 🕵️ **Stealth Features**

- **Browser Fingerprint Rotation**: Multiple realistic browser profiles
- **Session Management**: Automatic rotation every 45 minutes
- **Human Behavior Simulation**: Mouse movements, scrolling, typing delays
- **CAPTCHA Detection & Handling**: Intelligent recovery mechanisms
- **Proxy Pool Support**: Rotating IP addresses for anonymity
- **Request Pattern Randomization**: Variable delays and retry logic

### 🔧 **Configuration**

```python
from src.scrapers.enhanced_scraper import EnhancedScraper

scraper = EnhancedScraper(
    use_selenium=True,          # Enable advanced stealth mode
    headless=True,              # Run in background
    use_proxy=True,             # Enable proxy rotation
    proxy_list=['proxy1:8080', 'proxy2:8080']
)
```

---

## 📊 Profit Analysis

### 💰 **Platform Fee Calculations**

| Platform | Fees Calculated |
|----------|-----------------|
| **Amazon** | Referral fees, FBA fees, storage costs, return processing |
| **eBay** | Final value fees, PayPal fees, promoted listings |
| **Walmart** | Referral fees, fulfillment services, advertising |

### 📈 **Profit Metrics**

```python
from src.utils.profit_calculator import ProfitCalculator

calc = ProfitCalculator()

# Calculate Amazon profit
profit_data = calc.calculate_profit_for_platform(
    platform="amazon",
    selling_price=35.00,
    cost_price=15.00,
    category="electronics"
)

print(f"Net Profit: ${profit_data['net_profit']:.2f}")
print(f"Profit Margin: {profit_data['profit_margin_percent']:.1f}%")
print(f"ROI: {profit_data['roi_percent']:.1f}%")
```

---

## 🔍 Monitoring & Health Checks

### 📊 **System Metrics**

- **CPU & Memory Usage**: Real-time resource monitoring
- **Network Activity**: Request/response tracking
- **Database Performance**: Query times and optimization
- **Scraper Success Rates**: Platform-specific performance
- **Notification Delivery**: Success/failure tracking

### 🏥 **Health Checks**

- **Database Connectivity**: Connection and query performance
- **Network Connectivity**: External service availability
- **Disk Space**: Storage capacity monitoring
- **Service Health**: Component status verification

```python
# Get system health
health_status = orchestrator.get_system_health()
print(f"Overall Status: {health_status['overall_status']}")

# Export metrics
orchestrator.export_system_metrics("metrics_24h.json", hours=24)
```

---

## 🚀 Deployment

### 🐳 **Docker Production Deployment**

```bash
# Production deployment
docker-compose -f docker-compose.prod.yml up -d

# Scale services
docker-compose up -d --scale price-tracker=3

# Monitor logs
docker-compose logs -f price-tracker

# Update deployment
docker-compose pull && docker-compose up -d
```

### ☁️ **Cloud Deployment**

<details>
<summary><strong>🌊 DigitalOcean Droplet</strong></summary>

```bash
# Create droplet
doctl compute droplet create price-tracker \
  --size s-2vcpu-4gb \
  --image docker-20-04 \
  --region nyc3

# Deploy application
scp -r . root@your-droplet-ip:/app
ssh root@your-droplet-ip
cd /app && docker-compose up -d
```

</details>

<details>
<summary><strong>☁️ AWS EC2</strong></summary>

```bash
# Launch EC2 instance with Docker
aws ec2 run-instances \
  --image-id ami-0c02fb55956c7d316 \
  --instance-type t3.medium \
  --key-name your-key-pair

# Deploy with user data script
#!/bin/bash
yum update -y
yum install -y docker
systemctl start docker
# ... deployment commands
```

</details>

---

## 🤝 Contributing

We welcome contributions! Here's how to get started:

### 🛠️ **Development Setup**

```bash
# Fork and clone
git clone https://github.com/your-username/smart-price-tracker.git
cd smart-price-tracker

# Create feature branch
git checkout -b feature/amazing-feature

# Setup development environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# Submit pull request
git push origin feature/amazing-feature
```

### 📋 **Contribution Guidelines**

- **Code Style**: Follow PEP 8 and use type hints
- **Testing**: Add tests for new features
- **Documentation**: Update README and docstrings
- **Commits**: Use conventional commit messages
- **Issues**: Use provided templates

### 🎯 **Areas for Contribution**

- **New Platform Scrapers**: eBay, Walmart, AliExpress
- **Enhanced Analytics**: ML-based price prediction
- **Mobile App**: React Native or Flutter app
- **API Improvements**: REST API with FastAPI
- **Testing**: Comprehensive test coverage
- **Documentation**: Tutorials and guides

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Selenium Team** - Web automation framework
- **Plotly/Dash** - Interactive dashboard framework  
- **SQLAlchemy** - Database ORM
- **BeautifulSoup** - HTML parsing
- **Undetected ChromeDriver** - Stealth browser automation
- **Open Source Community** - Inspiration and libraries

---

## 📞 Support

<div align="center">

**Need Help? We're Here!**

[![GitHub Issues](https://img.shields.io/badge/GitHub-Issues-red.svg)](https://github.com/Mukhammad-develop/smart-price-tracker/issues)
[![Documentation](https://img.shields.io/badge/Docs-Wiki-blue.svg)](https://github.com/Mukhammad-develop/smart-price-tracker/wiki)
[![Discussions](https://img.shields.io/badge/GitHub-Discussions-purple.svg)](https://github.com/Mukhammad-develop/smart-price-tracker/discussions)

**⭐ Star this repository if you find it useful!**

</div>

---

<div align="center">

**Built with ❤️ by developers, for developers**

*Smart Price Tracker - Empowering E-commerce Success*

</div> 