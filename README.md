# curly-memory

Jira scripts for automating Performance review metrics @Arbisoft

## Features

- Singleton-based Jira API client for easy and safe access to Jira.
- Environment-based configuration for credentials and server.
- Ready for extension with more API clients or scripts.
- Linting and formatting automation with Flake8 and Black.
- Example script for listing Jira projects.

## Project Structure

```
curly-memory/
├── src/
│   ├── clients/
│   │   ├── __init__.py
│   │   └── jira_client.py
│   ├── main.py
│   └── tests/
│       └── __init__.py
├── .env.dist
├── .flake8
├── .gitignore
├── LICENSE
├── pyproject.toml
├── poetry.lock
├── pytest.ini
├── README.md
```

## Getting Started

### 1. Install dependencies

```sh
poetry install
```

### 2. Set up environment variables

Copy `.env.dist` to `.env` and fill in your Jira credentials:
```
JIRA_SERVER=
JIRA_EMAIL=
JIRA_API_TOKEN=
```

### 3. Run the example script

```sh
poetry run python src/main.py
```

This will print the list of Jira projects accessible with your credentials.

## Usage

You can use the Jira client in your own scripts:

```python
from clients.jira_client import jira

# Use the jira object as you would with the official jira library
print(jira.projects())
```

## Development

### Linting

```sh
poetry run flake8 src
```

### Formatting

```sh
poetry run black src
```

### Testing

If you add tests, run them with:

```sh
poetry run pytest
```

## Dependencies

- [jira](https://pypi.org/project/jira/)
- [python-dotenv](https://pypi.org/project/python-dotenv/)
- [requests](https://pypi.org/project/requests/)
- [argparse](https://pypi.org/project/argparse/)
- [pytest](https://pypi.org/project/pytest/) (dev)
- [black](https://pypi.org/project/black/) (dev)
- [flake8](https://pypi.org/project/flake8/) (dev)

## License

BSD 3-Clause