# AI Brand Optimization Tool

A Generative Engine Optimization (GEO) platform that helps brands monitor and optimize their presence across AI-powered search engines like ChatGPT and Gemini.

## Features

- **Multi-Platform AI Monitoring**: Track brand mentions across ChatGPT and Gemini
- **Intelligent Query Generation**: Automatically creates relevant search queries for monitoring
- **Brand Mention Analysis**: Analyze sentiment and context of brand mentions
- **AI-Powered Optimization**: Generate content and strategy recommendations
- **Comprehensive Reporting**: Performance dashboards and detailed analytics
- **Historical Tracking**: Store and analyze performance trends over time

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables

```bash
# Required
export OPENAI_API_KEY="your-openai-api-key"

# Optional (will fallback to OpenAI if not provided)
export GOOGLE_API_KEY="your-google-api-key"
```

### 3. Run the Application

```bash
python main.py
```

## Project Structure

```
ai-brand-optimizer/
├── main.py                 # Main application entry point
├── nodes.py                # PocketFlow node definitions
├── flow.py                 # Flow orchestration
├── utils/
│   ├── call_llm.py        # LLM wrapper functions
│   ├── ai_platforms.py    # AI platform API interfaces
│   ├── text_analysis.py   # Brand mention analysis
│   ├── report_generator.py # HTML report generation
│   └── database.py        # Simple JSON database
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## How It Works

The application follows a workflow pattern using PocketFlow:

1. **Query Generation**: AI generates relevant search queries for your brand
2. **Multi-Platform Querying**: Queries are executed across ChatGPT and Gemini
3. **Response Analysis**: AI responses are analyzed for brand mentions and sentiment
4. **Optimization Recommendations**: AI agent analyzes performance and suggests improvements
5. **Report Generation**: Comprehensive HTML reports are created
6. **Data Storage**: Results are stored for historical analysis

## Usage Examples

### Basic Brand Monitoring

```python
from flow import create_brand_monitoring_flow

# Set up brand configuration
shared = {
    "brand_config": {
        "name": "Tesla",
        "keywords": ["Tesla", "electric car", "EV"],
        "industry": "automotive"
    }
}

# Run monitoring
flow = create_brand_monitoring_flow()
flow.run(shared)

# View results
print(f"Found {shared['analysis']['total_mentions']} mentions")
print(f"Report saved as: {shared['reports']['filename']}")
```

### View Historical Data

```python
from utils.database import SimpleJSONDB

db = SimpleJSONDB()
historical_data = db.get_historical_data(days=30)
print(f"Analyzed {historical_data['total_responses']} responses in last 30 days")
```

## Configuration

### Brand Configuration

When running the application, you'll be prompted to configure:

- **Brand Name**: Your company or product name
- **Keywords**: Related terms to monitor (e.g., product names, industry terms)
- **Industry**: Your business sector (helps generate relevant queries)

### API Keys

- **OpenAI API Key**: Required for ChatGPT queries and LLM analysis
- **Google API Key**: Optional for Gemini queries (will fallback to OpenAI simulation)

## Reports

The tool generates comprehensive HTML reports including:

- **Key Metrics**: Total mentions, sentiment scores, mention rates
- **Platform Performance**: Breakdown by ChatGPT vs Gemini
- **Recent Mentions**: Sample mentions with context and sentiment
- **Optimization Recommendations**: AI-generated improvement suggestions

## Architecture

Built using the PocketFlow framework:

- **Nodes**: Individual processing units (query generation, analysis, etc.)
- **Flows**: Orchestrate nodes into workflows
- **Shared Store**: Data communication between nodes
- **Batch Processing**: Parallel execution across platforms

## Extending the Platform

### Adding New AI Platforms

1. Create platform interface in `utils/ai_platforms.py`
2. Update `MultiPlatformQueryNode` in `nodes.py`
3. Add platform to the platforms list

### Custom Analysis

1. Extend `analyze_brand_mentions()` in `utils/text_analysis.py`
2. Add new metrics to the analysis output
3. Update report templates in `utils/report_generator.py`

## Troubleshooting

### Common Issues

1. **API Key Errors**: Ensure environment variables are set correctly
2. **Rate Limits**: Add delays between API calls if needed
3. **No Mentions Found**: Try broader keywords or different query types

### Debug Mode

Set environment variable for verbose logging:

```bash
export DEBUG=1
python main.py
```

## License

This project is built using PocketFlow (100-line minimalist LLM framework) and is intended for educational and commercial use.