# Smart Price Tracker

A comprehensive web scraping tool that tracks product listings from Amazon and other e-commerce platforms, providing automated price monitoring, notifications, and business intelligence features.

## Features

- **Multi-Platform Support**: Amazon scraper with extensible architecture for eBay, Walmart, AliExpress
- **Historical Tracking**: Timestamped data storage for price history analysis
- **Automated Exports**: Daily updates to Google Sheets and Excel files
- **Smart Notifications**: Email, Telegram, and Slack alerts for price drops and stock changes
- **Profit Analysis**: Built-in profit estimation with platform fee calculations
- **Interactive Dashboard**: Price history charts, availability status, and seller comparisons
- **Anti-Bot Protection**: Rotating user agents, proxy support, and request delays
- **Automated Scheduling**: Configurable intervals for continuous monitoring

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Mukhammad-develop/smart-price-tracker.git
cd smart-price-tracker
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

## Usage

### Basic Usage
```python
from src.scrapers.amazon_scraper import AmazonScraper
from src.core.tracker import PriceTracker

# Initialize tracker
tracker = PriceTracker()

# Add product to track
product_url = "https://amazon.com/product-url"
tracker.add_product(product_url, target_price=50.00)

# Run tracking
tracker.run_tracking()
```

### Web Interface
```bash
python src/dashboard/app.py
```

## Project Structure

```
smart-price-tracker/
├── src/
│   ├── core/           # Core tracking logic
│   ├── scrapers/       # Platform-specific scrapers
│   ├── models/         # Data models
│   ├── notifications/  # Notification services
│   ├── storage/        # Database and export functionality
│   ├── dashboard/      # Web dashboard
│   └── utils/          # Utility functions
├── data/              # Data storage
├── config/            # Configuration files
└── tests/             # Test suite
```

## Configuration

Create a `.env` file with the following variables:
```
# Database
DATABASE_URL=sqlite:///data/price_tracker.db

# Google Sheets
GOOGLE_SHEETS_CREDENTIALS=path/to/credentials.json
GOOGLE_SHEETS_ID=your_sheet_id

# Notifications
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_ADDRESS=your_email@gmail.com
EMAIL_PASSWORD=your_app_password

TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

SLACK_BOT_TOKEN=your_slack_token
SLACK_CHANNEL=your_channel

# Proxy (optional)
PROXY_LIST=proxy1:port,proxy2:port
```

## License

MIT License - see LICENSE file for details. 