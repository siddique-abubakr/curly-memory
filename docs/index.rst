Curly Memory Documentation
==========================

Advanced Jira analytics and performance metrics automation for Arbisoft.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   api/services
   api/models
   api/clients
   api/core

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

Overview
--------

Curly Memory is a comprehensive Jira analytics tool that provides detailed insights into sprint performance, bug resolution metrics, and team productivity. Built with a modular architecture, it offers configurable sprint filtering, priority analysis, and resolution time tracking.

Key Features
------------

* **Sprint Performance Analysis**: Track sprint completion rates and issue distribution
* **Bug Resolution Metrics**: Calculate average, min, max resolution times per sprint
* **Priority Classification**: Automatic categorization of bugs by priority (Critical/Major/Minor)
* **Configurable Filtering**: Filter sprints by date ranges, states, and specific IDs
* **Modular Architecture**: Service-oriented design with clear separation of concerns
* **Comprehensive Reporting**: Detailed reports with priority distribution and resolution metrics

Quick Start
-----------

.. code-block:: python

   from services.jira_analyzer import JiraAnalyzer
   from clients.jira import jira
   from services.jira.models import Issue, Board

   # Initialize analyzer
   analyzer = JiraAnalyzer(jira)
   
   # Analyze project
   results = analyzer.analyze_project("PROJ", [BOARD_ID])
   
   # Generate report
   report = analyzer.generate_report(results)
   print(report)
   
   # Work with Pydantic models
   for issue_data in results['issues']:
       issue = Issue(**issue_data)
       print(f"Issue {issue.key}: {issue.resolution_time_days} days") 