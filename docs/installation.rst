Installation
============

Requirements
------------

* Python 3.13 or higher
* Poetry (for dependency management)
* Jira instance with API access

Installation Steps
-----------------

1. **Clone the repository**

   .. code-block:: bash

      git clone <repository-url>
      cd curly-memory

2. **Install dependencies**

   .. code-block:: bash

      poetry install

3. **Set up environment variables**

   Copy the environment template and configure your Jira credentials:

   .. code-block:: bash

      cp .env.dist .env

   Edit `.env` with your Jira configuration:

   .. code-block:: env

      JIRA_SERVER=https://your-domain.atlassian.net
      JIRA_EMAIL=your-email@company.com
      JIRA_API_TOKEN=your-api-token

4. **Configure projects and boards**

   Edit `src/core/constants.py` to specify your projects and boards:

   .. code-block:: python

      PROJECTS_TO_INCLUDE = ["10001", "10006"]  # Your project keys
      SCRUM_BOARDS = [2, 6]                     # Your board IDs

5. **Verify installation**

   .. code-block:: bash

      poetry run python src/main.py

Development Installation
-----------------------

For development, install with development dependencies:

.. code-block:: bash

   poetry install --extras dev

This includes:

* **pytest**: Testing framework
* **black**: Code formatting
* **flake8**: Linting
* **sphinx**: Documentation generation
* **sphinx-rtd-theme**: Documentation theme
* **sphinx-autodoc-typehints**: Type hints documentation
* **myst-parser**: Markdown support

Generating Documentation
-----------------------

.. code-block:: bash

   # Build documentation
   cd docs
   make html

   # View documentation
   open _build/html/index.html

Running Tests
------------

.. code-block:: bash

   # Run all tests
   poetry run pytest src/tests/

   # Run with coverage
   poetry run pytest --cov=src src/tests/

   # Run specific test file
   poetry run pytest src/tests/test_board_service.py 