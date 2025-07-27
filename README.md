# Curly Memory

Advanced Jira analytics and performance metrics automation for Arbisoft

## Overview

Curly Memory is a comprehensive Jira analytics tool that provides detailed insights into sprint performance, bug resolution metrics, and team productivity. Built with a modular architecture, it offers configurable sprint filtering, priority analysis, and resolution time tracking.

## Features

### 🎯 **Core Analytics**
- **Sprint Performance Analysis**: Track sprint completion rates and issue distribution
- **Bug Resolution Metrics**: Calculate average, min, max resolution times per sprint
- **Priority Classification**: Automatic categorization of bugs by priority (Critical/Major/Minor)
- **Longest Resolution Tracking**: Identify the most time-consuming issues in each sprint

### ⚙️ **Configurable Filtering**
- **Date Range Filtering**: Analyze sprints within specific time periods (e.g., since April 2024)
- **Sprint State Filtering**: Filter by active, closed, or future sprints
- **Specific Sprint Selection**: Target individual sprints by ID
- **Multi-Project Support**: Analyze multiple projects simultaneously

### 🏗️ **Modular Architecture**
- **Service-Oriented Design**: Separate services for boards, sprints, and issues
- **Singleton Jira Client**: Thread-safe API access with automatic pagination
- **Comprehensive Logging**: Detailed logging with configurable levels
- **Error Handling**: Robust error handling with graceful degradation

### 📊 **Advanced Reporting**
- **Detailed Sprint Reports**: Priority distribution, resolution metrics, and issue details
- **Board-Level Aggregation**: Consolidated metrics across multiple boards
- **Project-Level Insights**: Overall performance metrics and trends
- **Formatted Output**: Clean, readable reports with structured data

## Project Structure

```
curly-memory/
├── src/
│   ├── clients/
│   │   ├── __init__.py
│   │   └── jira_client.py          # Singleton Jira API client
│   ├── core/
│   │   ├── __init__.py
│   │   ├── constants.py            # Configuration constants
│   │   ├── enums.py               # Project and board enums
│   │   └── logger.py              # Centralized logging
│   ├── services/
│   │   ├── __init__.py
│   │   ├── board_service.py       # Board management
│   │   ├── sprint_service.py      # Sprint filtering and analysis
│   │   ├── issue_service.py       # Issue metrics and classification
│   │   └── jira_analyzer.py       # Main orchestrator
│   ├── tests/
│   │   └── __init__.py
│   └── main.py                    # Application entry point
├── logs/                          # Application logs
├── .env.dist                      # Environment template
├── pyproject.toml                 # Poetry configuration
└── README.md
```

## Getting Started

### 1. Install Dependencies

```sh
poetry install
```

### 2. Configure Environment

Copy `.env.dist` to `.env` and configure your Jira credentials:

```env
JIRA_SERVER=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=your-api-token
```

### 3. Configure Projects and Boards

Edit `src/core/constants.py` to specify your projects and boards:

```python
PROJECTS_TO_INCLUDE = ["10001", "10006"]  # Your project keys
SCRUM_BOARDS = [2, 6]                     # Your board IDs
```

### 4. Configure Sprint Filtering

Set up sprint filtering in `src/core/constants.py`:

```python
SPRINT_FILTER_CONFIG = {
    'date_range': {
        'start_date': datetime(2024, 4, 1, tzinfo=timezone.utc),
        'end_date': datetime.now(timezone.utc),
        'enabled': True
    },
    'sprint_states': ['active', 'closed', 'future'],
    'specific_sprint_ids': [],
    'include_no_end_date': True
}
```

### 5. Run the Analysis

```sh
poetry run python src/main.py
```

## Usage Examples

### Basic Analysis

```python
from services import JiraAnalyzer
from clients.jira_client import jira

analyzer = JiraAnalyzer(jira)
results = analyzer.analyze_project("PROJECT_KEY", [BOARD_ID])
report = analyzer.generate_report(results)
print(report)
```

### Custom Sprint Filtering

```python
from datetime import datetime, timezone

custom_filter = {
    'date_range': {
        'start_date': datetime(2024, 1, 1, tzinfo=timezone.utc),
        'end_date': datetime(2024, 12, 31, tzinfo=timezone.utc),
        'enabled': True
    },
    'sprint_states': ['closed'],
    'specific_sprint_ids': []
}

results = analyzer.analyze_project("PROJECT_KEY", [BOARD_ID], custom_filter)
```

## Sample Output

```
=== Jira Analysis Report for Project: 10001 ===
Total Issues Analyzed: 24
Filter Configuration:
  Date Range: 2024-04-01 to 2024-12-19
  Sprint States: active, closed, future
Average Resolution Time: 15.2 days
Max Resolution Time: 45 days
Min Resolution Time: 2 days

=== Board Details ===

Board: Development Board (ID: 2)
Total Issues: 24

  Sprint: Sprint 101 (closed) - 8 issues
    Priority Distribution:
      Critical: 3
      Major: 2
      Minor: 3
    Longest Resolution: PROJ-123 - 25 days
      Summary: Database connection timeout
      Priority: High
    Resolution Metrics:
      Average: 18.5 days
      Max: 25 days
      Min: 8 days
```

## Configuration Options

### Sprint Filtering

- **Date Range**: Filter sprints by start/end dates
- **Sprint States**: `active`, `closed`, `future`
- **Specific IDs**: Target individual sprints
- **No End Date**: Include sprints without end dates

### Priority Classification

- **Critical**: `highest`, `high`
- **Major**: `medium`
- **Minor**: `low`, `lowest`

### Logging

Configure log levels and output in `src/core/logger.py`:

```python
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

## Development

### Code Quality

```sh
# Linting
poetry run flake8 src

# Formatting
poetry run black src

# Testing
poetry run pytest
```

### Documentation

```sh
# Setup documentation (first time)
python setup_docs.py

# Generate documentation
python scripts/generate_docs.py

# Or manually
cd docs
make html
```

The documentation will be available at `docs/_build/html/index.html`

#### Updating Documentation

When you make changes to your code or docstrings, regenerate the documentation:

```sh
# Quick update
python scripts/generate_docs.py

# Or manually
cd docs
make clean
make html
```

**Note**: Documentation is auto-generated from your docstrings, so make sure to keep them up to date!

### GitHub Pages Deployment

The documentation is automatically deployed to GitHub Pages when you push to the main branch.

**Live Documentation**: https://your-username.github.io/curly-memory/

**Manual Deployment**:
```bash
# Build docs locally
cd docs
make html

# Deploy to gh-pages branch
git checkout gh-pages
cp -r _build/html/* ./
git add .
git commit -m "Update documentation"
git push origin gh-pages
git checkout main
```

### Adding New Features

1. **New Service**: Create a service class in `src/services/`
2. **Configuration**: Add constants to `src/core/constants.py`
3. **Integration**: Update `JiraAnalyzer` to use new service
4. **Testing**: Add tests in `src/tests/`

## Dependencies

### Core Dependencies
- **jira** (>=3.8.0): Jira API client
- **python-dotenv** (>=1.1.1): Environment management
- **requests** (>=2.32.4): HTTP client

### Development Dependencies
- **pytest**: Testing framework
- **black**: Code formatting
- **flake8**: Linting
- **sphinx**: Documentation generation
- **sphinx-rtd-theme**: Documentation theme
- **sphinx-autodoc-typehints**: Type hints documentation
- **myst-parser**: Markdown support

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run linting and formatting
6. Submit a pull request

## License

BSD 3-Clause License - see [LICENSE](LICENSE) for details.

## Support

For issues and questions:
- Create an issue in the repository
- Contact the development team at Arbisoft