# Jira Performance Review Metrics

Automated Python scripts to generate performance review metrics from Jira data using the `jira` package.

## 📊 Features

- Extract individual contributor metrics from Jira
- Generate sprint performance reports
- Calculate velocity and completion rates
- Export data to CSV/JSON formats for review discussions
- Customizable date ranges and project filters
- Support for multiple Jira projects and boards

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Jira account with API access
- Jira API token ([How to create](https://support.atlassian.com/atlassian-account/docs/manage-api-tokens-for-your-atlassian-account/))

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/jira-performance-metrics
cd jira-performance-metrics

# Install dependencies using Poetry (recommended)
poetry install
poetry shell

# Or using pip
pip install -r requirements.txt
```

### Configuration

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` with your Jira credentials:
```env
JIRA_SERVER=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=your-api-token-here
JIRA_PROJECT_KEY=PROJ
```

## 📋 Available Metrics

### Individual Performance Metrics
- **Issues Completed**: Total tickets resolved in date range
- **Story Points Delivered**: Sum of story points for completed work
- **Average Cycle Time**: Time from In Progress to Done
- **Bug Fix Rate**: Percentage of bugs vs features worked on
- **Code Review Participation**: Comments and approvals on PRs/tickets

### Sprint Metrics
- **Sprint Velocity**: Story points completed per sprint
- **Commitment Accuracy**: Planned vs delivered work
- **Sprint Goal Achievement**: Percentage of sprint goals met
- **Carry-over Rate**: Work moved between sprints

### Quality Metrics
- **Bug Creation vs Resolution**: Bugs reported vs fixed
- **Rework Rate**: Issues reopened after completion
- **First-time Resolution**: Tickets completed without reopening

## 🛠️ Usage

### Basic Usage

```bash
# Generate metrics for current user (last 3 months)
python -m jira_metrics.main

# Generate metrics for specific user
python -m jira_metrics.main --user john.doe@company.com

# Custom date range
python -m jira_metrics.main --start-date 2024-01-01 --end-date 2024-03-31
```

### Advanced Options

```bash
# Multiple projects
python -m jira_metrics.main --projects PROJ1,PROJ2,PROJ3

# Specific metric categories
python -m jira_metrics.main --metrics velocity,quality,individual

# Export to different formats
python -m jira_metrics.main --output-format csv
python -m jira_metrics.main --output-format json

# Team-wide report
python -m jira_metrics.main --team-report --output team_metrics.csv
```

### Example Output

```
Performance Metrics Report
==========================
Period: 2024-01-01 to 2024-03-31
User: john.doe@company.com

📈 Productivity Metrics:
- Issues Completed: 45
- Story Points Delivered: 123
- Average Cycle Time: 4.2 days
- Velocity (per sprint): 41 points

🐛 Quality Metrics:
- Bug Fix Ratio: 15% (7 bugs, 38 features)
- Rework Rate: 8% (4 reopened issues)
- First-time Resolution: 92%

🎯 Sprint Performance:
- Sprint Commitment Accuracy: 94%
- Goals Achieved: 8/10 sprints
- Average Carry-over: 12%
```

## 📂 Project Structure

```
jira-performance-metrics/
├── jira_metrics/
│   ├── __init__.py
│   ├── main.py              # Main CLI interface
│   ├── client.py            # Jira API client wrapper
│   ├── collectors/          # Data collection modules
│   │   ├── individual.py    # Individual metrics
│   │   ├── sprint.py        # Sprint-based metrics
│   │   └── quality.py       # Quality metrics
│   ├── processors/          # Data processing utilities
│   │   ├── calculator.py    # Metric calculations
│   │   └── formatter.py     # Output formatting
│   └── exporters/           # Export functionality
│       ├── csv_exporter.py
│       └── json_exporter.py
├── tests/
├── examples/
│   └── sample_report.py     # Example usage
├── .env.example
├── pyproject.toml
├── requirements.txt
└── README.md
```

## 🔧 Configuration Options

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `JIRA_SERVER` | Your Jira instance URL | Yes | - |
| `JIRA_EMAIL` | Your Jira email | Yes | - |
| `JIRA_API_TOKEN` | Your API token | Yes | - |
| `JIRA_PROJECT_KEY` | Default project key | No | - |
| `DEFAULT_DATE_RANGE` | Default lookback period | No | 90 |

### Custom Metrics Configuration

Create a `metrics_config.yaml` file to customize which metrics to collect:

```yaml
individual_metrics:
  - issues_completed
  - story_points_delivered
  - cycle_time
  - bug_ratio

sprint_metrics:
  - velocity
  - commitment_accuracy
  - goal_achievement

quality_metrics:
  - rework_rate
  - first_time_resolution
  - bug_creation_rate
```

## 📊 Sample Scripts

### Generate Monthly Report
```python
from jira_metrics import MetricsCollector
from datetime import datetime, timedelta

collector = MetricsCollector()
end_date = datetime.now()
start_date = end_date - timedelta(days=30)

metrics = collector.collect_user_metrics(
    user_email="john.doe@company.com",
    start_date=start_date,
    end_date=end_date
)

print(f"Issues completed: {metrics['issues_completed']}")
print(f"Story points: {metrics['story_points']}")
```

### Team Comparison Report
```python
team_emails = [
    "alice@company.com",
    "bob@company.com", 
    "charlie@company.com"
]

for email in team_emails:
    metrics = collector.collect_user_metrics(user_email=email)
    print(f"{email}: {metrics['velocity']} avg velocity")
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-metric`)
3. Make your changes and add tests
4. Run tests: `poetry run pytest`
5. Submit a pull request

### Development Setup

```bash
# Install development dependencies
poetry install --with dev

# Run tests
poetry run pytest

# Format code
poetry run black .

# Lint
poetry run flake8
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Important Notes

- **Privacy**: Be mindful of privacy when sharing performance data
- **Rate Limits**: Jira API has rate limits; large datasets may take time
- **Permissions**: Ensure your API token has access to required projects
- **Data Accuracy**: Metrics are based on Jira data quality and workflow setup

## 🔗 Useful Links

- [Jira Python Package Documentation](https://jira.readthedocs.io/)
- [Jira REST API Reference](https://developer.atlassian.com/cloud/jira/platform/rest/v3/)
- [Creating Jira API Tokens](https://support.atlassian.com/atlassian-account/docs/manage-api-tokens-for-your-atlassian-account/)

## 📞 Support

If you encounter issues or have questions:

1. Check the [Issues](https://github.com/yourusername/jira-performance-metrics/issues) page
2. Create a new issue with:
   - Error message/logs
   - Steps to reproduce
   - Your environment details

---

**Disclaimer**: This tool is designed to provide objective metrics for performance discussions. Use responsibly and in accordance with your company's performance review policies.