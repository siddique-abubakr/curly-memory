#!/usr/bin/env python3
"""
Simple test script to verify GitHub client functionality.
Run this to test if the GitHub API client is working properly.
"""

import os
from clients.github import GithubClient


def test_github_client():
    print("Testing GitHub Client...")

    # Check if GitHub token is set
    if not os.getenv("GITHUB_TOKEN"):
        print("❌ GITHUB_TOKEN environment variable not set")
        return

    client = GithubClient()

    # Test basic repository info
    print("\n🔍 Testing repository info...")
    repo = client.get_repository()
    if repo:
        print(f"✅ Repository: {repo.full_name}")
        print(f"   Description: {repo.description or 'No description'}")
        print(f"   Stars: {repo.stargazers_count}")
        print(f"   Language: {repo.language or 'Unknown'}")
        print(f"   Created: {repo.created_at}")
        print(f"   Private: {repo.private}")
    else:
        print("❌ Failed to get repository info")
        return

    # Test commits (limit to 5 for testing)
    print("\n🔍 Testing commits...")
    commits = client.get_commits(params={"per_page": 5})
    if commits:
        print(f"✅ Retrieved {len(commits)} recent commits")
        for commit in commits[:3]:  # Show first 3
            message = commit.commit.message.split("\n")[0][:50]
            author = commit.commit.author.name
            print(f"   - {message} by {author}")
            print(f"     SHA: {commit.sha}")
    else:
        print("❌ Failed to get commits")

    # Test pull requests
    print("\n🔍 Testing pull requests...")
    prs = client.get_pull_requests(params={"state": "all", "per_page": 5})
    if prs:
        print(f"✅ Retrieved {len(prs)} pull requests")
        for pr in prs[:2]:  # Show first 2
            print(f"   - #{pr.number}: {pr.title} ({pr.state})")
            print(f"     Author: {pr.user.login}")
            print(f"     Created: {pr.created_at}")
    else:
        print("❌ Failed to get pull requests")

    # Test issues
    print("\n🔍 Testing issues...")
    issues = client.get_issues(params={"state": "all", "per_page": 3})
    if issues:
        print(f"✅ Retrieved {len(issues)} issues")
        for issue in issues[:2]:  # Show first 2
            print(f"   - #{issue.number}: {issue.title} ({issue.state})")
            print(f"     Labels: {[label.name for label in issue.labels]}")
    else:
        print("❌ Failed to get issues")

    # Test contributors
    print("\n🔍 Testing contributors...")
    contributors = client.get_contributors(params={"per_page": 5})
    if contributors:
        print(f"✅ Retrieved {len(contributors)} contributors")
        for contributor in contributors[:3]:  # Show first 3
            print(
                f"   - {contributor.login}: {contributor.contributions} contributions"
            )
    else:
        print("❌ Failed to get contributors")

    # Test branches
    print("\n🔍 Testing branches...")
    branches = client.get_branches(params={"per_page": 5})
    if branches:
        print(f"✅ Retrieved {len(branches)} branches")
        for branch in branches[:3]:  # Show first 3
            print(f"   - {branch.name} (protected: {branch.protected})")
    else:
        print("❌ Failed to get branches")

    # Test releases
    print("\n🔍 Testing releases...")
    releases = client.get_releases(params={"per_page": 3})
    if releases:
        print(f"✅ Retrieved {len(releases)} releases")
        for release in releases[:2]:  # Show first 2
            print(f"   - {release.tag_name}: {release.name or 'No title'}")
            print(f"     Published: {release.published_at}")
    else:
        print("❌ Failed to get releases")

    # Test singleton pattern
    print("\n🔍 Testing singleton pattern...")
    client2 = GithubClient()
    if client is client2:
        print("✅ Singleton pattern working - same instance returned")
    else:
        print("❌ Singleton pattern failed - different instances")

    print("\n🎉 GitHub client test completed!")


if __name__ == "__main__":
    test_github_client()
