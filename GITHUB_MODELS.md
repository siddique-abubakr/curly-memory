# GitHub API Response Models

This document describes the Pydantic models created for GitHub API responses, providing type safety and validation for all GitHub REST API interactions.

## Overview

The GitHub models are located in `src/clients/github_models/` and provide comprehensive coverage of GitHub's REST API v3 responses. All models use Pydantic v2 for validation and type safety.

## Model Structure

### Base Models (`base.py`)
- **GitHubUser**: Core user model used across all endpoints
- **GitHubLabel**: Label model for issues and pull requests
- **GitHubMilestone**: Milestone model with full metadata
- **GitHubBranch**: Branch reference model

### Repository Models (`repository.py`)
- **Repository**: Complete repository information
- **RepositoryOwner**: Repository owner details
- **RepositoryPermissions**: User permissions on repository
- **SecurityAnalysis**: Security and analysis settings

### Commit Models (`commit.py`)
- **Commit**: Basic commit information (list endpoint)
- **CommitDetails**: Extended commit with stats and files (single endpoint)
- **GitCommit**: Git-level commit data
- **CommitVerification**: Signature verification information
- **CommitAuthor**: Author/committer information

### Pull Request Models (`pull_request.py`)
- **PullRequest**: Complete pull request information
- **PullRequestHead/Base**: Branch references
- **PullRequestReview**: Review information
- **AutoMerge**: Auto-merge configuration

### Issue Models (`issue.py`)
- **Issue**: Complete issue information
- **IssuePullRequest**: Pull request reference in issues
- **IssueReactions**: Reaction counts
- **IssueComment**: Issue comment model

### Contributor Models (`contributor.py`)
- **Contributor**: Repository contributor information
- **Branch**: Branch information with protection status

### Release Models (`release.py`)
- **Release**: Release information
- **ReleaseAsset**: Release asset details
- **ReleaseReactions**: Release reaction counts

## Key Features

### Type Safety
All models provide complete type safety with proper field types:
```python
repo: Repository = client.get_repository()
print(repo.stargazers_count)  # Type: int
print(repo.created_at)        # Type: datetime
print(repo.private)           # Type: bool
```

### Validation
Pydantic automatically validates all API responses:
```python
# Invalid data will raise ValidationError
try:
    commits = client.get_commits()
    for commit in commits:
        # commit.sha is guaranteed to be a string
        # commit.commit.author.date is guaranteed to be a datetime
        print(f"{commit.sha}: {commit.commit.author.date}")
except ValidationError as e:
    print(f"API response validation failed: {e}")
```

### Computed Fields
Some models include computed properties:
```python
# Repository model includes computed fields
repo = client.get_repository()
# Access all standard fields plus computed ones
```

### Enum Support
Models use enums for consistent values:
```python
from clients.github_params import PullRequestState

params = PullRequestParams(state=PullRequestState.OPEN)
prs = client.get_pull_requests(params)
```

## Usage Examples

### Basic Repository Information
```python
from clients.github import GithubClient

client = GithubClient()
repo = client.get_repository()

if repo:
    print(f"Repository: {repo.full_name}")
    print(f"Stars: {repo.stargazers_count}")
    print(f"Language: {repo.language}")
    print(f"Created: {repo.created_at}")
    print(f"Owner: {repo.owner.login} ({repo.owner.type})")
```

### Working with Commits
```python
from clients.github_params import CommitParams

# Type-safe parameters
params = CommitParams(
    since="2024-01-01T00:00:00Z",
    per_page=50
)

commits = client.get_commits(params)
for commit in commits:
    print(f"SHA: {commit.sha}")
    print(f"Author: {commit.commit.author.name}")
    print(f"Message: {commit.commit.message}")
    print(f"Date: {commit.commit.author.date}")
```

### Pull Request Analysis
```python
from clients.github_params import PullRequestParams, PullRequestState

params = PullRequestParams(
    state=PullRequestState.ALL,
    per_page=20
)

prs = client.get_pull_requests(params)
for pr in prs:
    print(f"#{pr.number}: {pr.title}")
    print(f"State: {pr.state}")
    print(f"Author: {pr.user.login}")
    print(f"Labels: {[label.name for label in pr.labels]}")
```

### Issue Tracking
```python
issues = client.get_issues()
for issue in issues:
    print(f"#{issue.number}: {issue.title}")
    print(f"State: {issue.state}")
    print(f"Comments: {issue.comments}")
    print(f"Labels: {[label.name for label in issue.labels]}")
    
    # Check if it's actually a pull request
    if issue.pull_request:
        print("This is a pull request, not an issue")
```

## Error Handling

All client methods return typed objects or None:
```python
repo = client.get_repository()
if repo is None:
    print("Failed to get repository information")
else:
    # repo is guaranteed to be a Repository object
    print(f"Repository: {repo.full_name}")
```

List methods return empty lists on failure:
```python
commits = client.get_commits()
if not commits:
    print("No commits found or request failed")
else:
    # commits is guaranteed to be List[Commit]
    for commit in commits:
        print(commit.sha)
```

## Testing

Run the test suite to verify GitHub integration:
```bash
# Set your GitHub token
export GITHUB_TOKEN="your_github_token"

# Run the test
python src/tests/test_github_client.py

# Run comprehensive examples
python src/examples/github_usage_examples.py
```

## Benefits

1. **Type Safety**: IDE autocompletion and type checking
2. **Validation**: Automatic validation of API responses
3. **Documentation**: Self-documenting code with clear field types
4. **Consistency**: Standardized access patterns across all endpoints
5. **Maintainability**: Easy to update when GitHub API changes
6. **Performance**: Efficient parsing with Pydantic's optimized validation

## Compatibility

- **GitHub REST API**: v3 (2022-11-28)
- **Python**: 3.13+
- **Pydantic**: v2.11.7+
- **Requests**: 2.32.4+

All models are designed to match GitHub's current API response schemas and will be updated as the GitHub API evolves.