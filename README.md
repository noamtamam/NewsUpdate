# AI News Update Agent

An intelligent agent that automatically scrapes daily news articles, summarizes them using AI, and delivers concise updates via Whatsapp.

## Features

- Automated news scraping from multiple sources
- AI-powered article summarization
- Scheduled daily Whatapp message delivery
- Customizable news categories and preferences
- Efficient content filtering and processing

## Prerequisites

- Python 3.8+
- OpenAI API key
- NewsAPI key

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/news-update-agent.git
cd news-update-agent
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory with your API keys:
```env
OPENAI_API_KEY=your_openai_api_key
NEWS_API_KEY=your_news_api_key
```

## Project Structure

```
.
├── agent/              # Core agent implementation
├── graph_properties/   # Configuration and properties
├── playground/         # Testing and development area
├── main.py            # Main application entry point
├── requirements.txt   # Project dependencies
└── .env              # Environment variables
```

## Usage

1. Configure your news preferences in the agent settings
2. Run the main application:
```bash
python main.py
```

The agent will:
- Scrape news articles based on your preferences
- Process and summarize the content
- Send the daily digest via email

## Configuration

You can customize the following aspects:
- News sources and categories
- Summary length and style
- Email delivery schedule
- Content filtering rules

## Dependencies

- LangChain & LangGraph for AI processing
- NewsAPI for news aggregation
- BeautifulSoup4 for web scraping
- Schedule for task scheduling
- Python-dotenv for environment management

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please open an issue in the GitHub repository or contact the maintainers. 