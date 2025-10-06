#!/usr/bin/env python3
"""
GitHub API Client Usage Examples

This file demonstrates how to use the GitHub client with Pydantic models
for type-safe API interactions and data validation.
"""

import os
from datetime import datetime, timezone, timedelta

from clients.github import GithubClient
from clients.github_params import (
    CommitParams,
    PullRequestParams,
    PullRequestState,
    PullRequestSort,
    IssueParams,
    IssueState,
    IssueSort,
    ContributorParams,
    ReleaseParams,
)
from services.github.models import (
    Repository,
    Commit,
    PullRequest,
    Issue,
    Contributor,
    Release,
)


def example_repository_info():
    """Example: Get repository information with type safety"""
    print("=" * 50)
    print("Repository Information Example")
    print("=" * 50)

    client = GithubClient()
    repo: Repository | None = client.get_repository()

    if repo:
        print(f"📁 Repository: {repo.full_name}")
        print(f"📝 Description: {repo.description or 'No description'}")
        print(f"⭐ Stars: {repo.stargazers_count}")
        print(f"🍴 Forks: {repo.forks_count}")
        print(f"📊 Language: {repo.language or 'Multiple/Unknown'}")
        print(f"🔒 Private: {repo.private}")
        print(f"📅 Created: {repo.created_at.strftime('%Y-%m-%d')}")
        print(f"📈 Open Issues: {repo.open_issues_count}")

        # Access owner information
        print(f"👤 Owner: {repo.owner.login} ({repo.owner.type})")

        # Check features
        features = []
        if repo.has_issues:
            features.append("Issues")
        if repo.has_wiki:
            features.append("Wiki")
        if repo.has_pages:
            features.append("Pages")
        if repo.has_projects:
            features.append("Projects")
        print(f"🔧 Features: {', '.join(features) if features else 'None'}")
    else:
        print("❌ Failed to retrieve repository information")


def example_commit_analysis():
    """Example: Analyze recent commits with filtering"""
    print("\n" + "=" * 50)
    print("Recent Commits Analysis")
    print("=" * 50)

    client = GithubClient()

    # Get commits from the last 30 days
    since_date = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()

    params = CommitParams(since=since_date, per_page=20)

    commits: list[Commit] = client.get_commits(params)

    if commits:
        print(f"📊 Found {len(commits)} commits in the last 30 days")
        print()

        # Analyze commit authors
        authors = {}
        for commit in commits:
            if commit.author:  # GitHub user exists
                author_name = commit.author.login
                authors[author_name] = authors.get(author_name, 0) + 1
            else:  # Use git author name
                author_name = commit.commit.author.name
                authors[author_name] = authors.get(author_name, 0) + 1

        print("👥 Top Contributors:")
        for author, count in sorted(authors.items(), key=lambda x: x[1], reverse=True)[
            :5
        ]:
            print(f"   {author}: {count} commits")

        print("\n📝 Recent Commits:")
        for commit in commits[:5]:
            message = commit.commit.message.split("\n")[0][:60]
            author = commit.author.login if commit.author else commit.commit.author.name
            date = commit.commit.author.date.strftime("%m-%d %H:%M")
            print(f"   {date} | {author}: {message}")
    else:
        print("❌ No commits found")


def example_pull_request_analysis():
    """Example: Analyze pull requests with type-safe filtering"""
    print("\n" + "=" * 50)
    print("Pull Request Analysis")
    print("=" * 50)

    client = GithubClient()

    # Get all pull requests, sorted by update date
    params = PullRequestParams(
        state=PullRequestState.ALL, sort=PullRequestSort.UPDATED, per_page=30
    )

    pull_requests: list[PullRequest] = client.get_pull_requests(params)

    if pull_requests:
        open_prs = [pr for pr in pull_requests if pr.state == PullRequestState.OPEN]
        closed_prs = [pr for pr in pull_requests if pr.state == PullRequestState.CLOSED]

        print("📊 Pull Request Summary:")
        print(f"   Open: {len(open_prs)}")
        print(f"   Closed: {len(closed_prs)}")
        print(f"   Total analyzed: {len(pull_requests)}")

        if open_prs:
            print("\n🔥 Open Pull Requests:")
            for pr in open_prs[:5]:
                print(f"   #{pr.number}: {pr.title}")
                print(f"      👤 Author: {pr.user.login}")
                print(f"      📅 Created: {pr.created_at.strftime('%Y-%m-%d')}")
                print(f"      🏷️  Labels: {[label.name for label in pr.labels]}")

        # Analyze recent merges
        merged_prs = [pr for pr in closed_prs if pr.merged_at]
        if merged_prs:
            print("\n✅ Recently Merged PRs:")
            for pr in sorted(merged_prs, key=lambda x: x.merged_at, reverse=True)[:3]:
                print(f"   #{pr.number}: {pr.title}")
                print(f"      🔀 Merged: {pr.merged_at.strftime('%Y-%m-%d %H:%M')}")
    else:
        print("❌ No pull requests found")


def example_issue_tracking():
    """Example: Issue tracking and analysis"""
    print("\n" + "=" * 50)
    print("Issue Tracking Analysis")
    print("=" * 50)

    client = GithubClient()

    # Get all issues, sorted by update date
    params = IssueParams(state=IssueState.ALL, sort=IssueSort.UPDATED, per_page=25)

    issues: list[Issue] = client.get_issues(params)

    if issues:
        # Filter out pull requests (issues endpoint includes PRs)
        actual_issues = [issue for issue in issues if not issue.pull_request]

        open_issues = [
            issue for issue in actual_issues if issue.state == IssueState.OPEN
        ]
        closed_issues = [
            issue for issue in actual_issues if issue.state == IssueState.CLOSED
        ]

        print("📊 Issue Summary:")
        print(f"   Open Issues: {len(open_issues)}")
        print(f"   Closed Issues: {len(closed_issues)}")
        print(f"   Total Issues: {len(actual_issues)}")

        # Analyze labels
        all_labels = {}
        for issue in actual_issues:
            for label in issue.labels:
                all_labels[label.name] = all_labels.get(label.name, 0) + 1

        if all_labels:
            print("\n🏷️  Most Common Labels:")
            for label, count in sorted(
                all_labels.items(), key=lambda x: x[1], reverse=True
            )[:5]:
                print(f"   {label}: {count} issues")

        if open_issues:
            print("\n🔥 Recent Open Issues:")
            for issue in sorted(open_issues, key=lambda x: x.updated_at, reverse=True)[
                :3
            ]:
                print(f"   #{issue.number}: {issue.title}")
                print(f"      👤 Author: {issue.user.login}")
                print(f"      📅 Updated: {issue.updated_at.strftime('%Y-%m-%d')}")
                print(f"      💬 Comments: {issue.comments}")
    else:
        print("❌ No issues found")


def example_contributor_analysis():
    """Example: Analyze repository contributors"""
    print("\n" + "=" * 50)
    print("Contributor Analysis")
    print("=" * 50)

    client = GithubClient()

    params = ContributorParams(per_page=50)
    contributors: list[Contributor] = client.get_contributors(params)

    if contributors:
        total_contributions = sum(c.contributions for c in contributors)

        print("📊 Contributor Summary:")
        print(f"   Total Contributors: {len(contributors)}")
        print(f"   Total Contributions: {total_contributions}")

        print("\n🌟 Top Contributors:")
        for contributor in contributors[:10]:
            percentage = (contributor.contributions / total_contributions) * 100
            print(
                f"   {contributor.login}: {contributor.contributions}"
                f" contributions ({percentage:.1f}%)"
            )
    else:
        print("❌ No contributors found")


def example_release_tracking():
    """Example: Track repository releases"""
    print("\n" + "=" * 50)
    print("Release Tracking")
    print("=" * 50)

    client = GithubClient()

    params = ReleaseParams(per_page=10)
    releases: list[Release] = client.get_releases(params)

    if releases:
        print(f"📊 Found {len(releases)} releases")

        latest_release = releases[0] if releases else None
        if latest_release:
            print("\n🚀 Latest Release:")
            print(f"   Tag: {latest_release.tag_name}")
            print(f"   Name: {latest_release.name or 'No title'}")
            print(f"   Published: {latest_release.published_at}")
            print(f"   Draft: {latest_release.draft}")
            print(f"   Prerelease: {latest_release.prerelease}")
            print(f"   Assets: {len(latest_release.assets)}")

            if latest_release.body:
                preview = latest_release.body[:200].replace("\n", " ")
                print(f"   Description: {preview}...")

        print("\n📋 Recent Releases:")
        for release in releases[:5]:
            status = (
                "🚧 Draft"
                if release.draft
                else ("🧪 Pre-release" if release.prerelease else "✅ Release")
            )
            published = (
                release.published_at.strftime("%Y-%m-%d")
                if release.published_at
                else "Not published"
            )
            print(
                f"   {release.tag_name}: {release.name or 'No title'}"
                f" | {status} | {published}"
            )
    else:
        print("❌ No releases found")


def example_single_resource_access():
    """Example: Access individual resources with detailed information"""
    print("\n" + "=" * 50)
    print("Single Resource Access Examples")
    print("=" * 50)

    client = GithubClient()

    # Get commits to find a specific one
    commits = client.get_commits(params={"per_page": 5})
    if commits:
        # Get detailed information about the latest commit
        latest_commit_sha = commits[0].sha
        detailed_commit = client.get_commit(latest_commit_sha)

        if detailed_commit:
            print("📝 Detailed Commit Information:")
            print(f"   SHA: {detailed_commit.sha}")
            print(f"   Author: {detailed_commit.commit.author.name}")
            print(f"   Message: {detailed_commit.commit.message.split(chr(10))[0]}")
            print(f"   Date: {detailed_commit.commit.author.date}")

            if detailed_commit.stats:
                print(
                    f"   📊 Stats: +{detailed_commit.stats.additions} -"
                    f"{detailed_commit.stats.deletions}"
                )

            if detailed_commit.files:
                print(f"   📁 Files changed: {len(detailed_commit.files)}")
                for file in detailed_commit.files[:3]:  # Show first 3 files
                    print(f"      {file.filename}: +{file.additions} -{file.deletions}")

    # Get pull requests to find a specific one
    prs = client.get_pull_requests(params={"per_page": 3})
    if prs:
        pr_number = prs[0].number
        detailed_pr = client.get_pull_request(pr_number)

        if detailed_pr:
            print("\n🔀 Detailed Pull Request Information:")
            print(f"   #{detailed_pr.number}: {detailed_pr.title}")
            print(f"   State: {detailed_pr.state}")
            print(f"   Author: {detailed_pr.user.login}")
            print(f"   Mergeable: {detailed_pr.mergeable}")
            print(f"   Commits: {detailed_pr.commits}")
            print(f"   Additions: {detailed_pr.additions}")
            print(f"   Deletions: {detailed_pr.deletions}")
            print(f"   Changed Files: {detailed_pr.changed_files}")


def main():
    """Run all examples"""
    print("🚀 GitHub API Client Examples")
    print("Using Pydantic models for type-safe API interactions")

    try:
        # Check if GitHub token is set
        if not os.getenv("GITHUB_TOKEN"):
            print("\n❌ GITHUB_TOKEN environment variable not set")
            print("Please set your GitHub personal access token to run these examples.")
            return

        example_repository_info()
        example_commit_analysis()
        example_pull_request_analysis()
        example_issue_tracking()
        example_contributor_analysis()
        example_release_tracking()
        example_single_resource_access()

        print("\n🎉 All examples completed successfully!")

    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
