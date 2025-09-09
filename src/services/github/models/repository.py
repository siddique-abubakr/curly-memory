"""
GitHub repository models for the /repos endpoints.

These models represent repository data returned by GitHub's REST API.
"""

from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl
from enum import Enum

from .base import GitHubUser


class RepositoryVisibility(str, Enum):
    """Repository visibility options"""

    PUBLIC = "public"
    PRIVATE = "private"
    INTERNAL = "internal"


class SecurityStatus(str, Enum):
    """Security feature status options"""

    ENABLED = "enabled"
    DISABLED = "disabled"


class RepositoryOwner(GitHubUser):
    """
    Repository owner (extends GitHubUser with additional repository-specific fields)"""

    pass


class RepositoryPermissions(BaseModel):
    """Repository permissions for the authenticated user"""

    admin: bool = Field(description="Whether user has admin permissions")
    maintain: bool | None = Field(
        default=None, description="Whether user has maintain permissions"
    )
    push: bool = Field(description="Whether user has push permissions")
    triage: bool | None = Field(
        default=None, description="Whether user has triage permissions"
    )
    pull: bool = Field(description="Whether user has pull permissions")


class AdvancedSecurity(BaseModel):
    """Advanced security settings"""

    status: SecurityStatus = Field(description="Advanced security status")


class SecretScanning(BaseModel):
    """Secret scanning settings"""

    status: SecurityStatus = Field(description="Secret scanning status")


class SecretScanningPushProtection(BaseModel):
    """Secret scanning push protection settings"""

    status: SecurityStatus = Field(description="Push protection status")


class DependencyReview(BaseModel):
    """Dependency review settings"""

    status: SecurityStatus = Field(description="Dependency review status")


class SecurityAnalysis(BaseModel):
    """Repository security and analysis settings"""

    advanced_security: AdvancedSecurity | None = Field(
        default=None, description="Advanced security settings"
    )
    secret_scanning: SecretScanning | None = Field(
        default=None, description="Secret scanning settings"
    )
    secret_scanning_push_protection: SecretScanningPushProtection | None = Field(
        default=None, description="Secret scanning push protection settings"
    )
    dependabot_security_updates: dict[str, str] | None = Field(
        default=None, description="Dependabot security updates settings"
    )
    dependency_review: DependencyReview | None = Field(
        default=None, description="Dependency review settings"
    )


class Repository(BaseModel):
    """GitHub repository model for API responses"""

    id: int = Field(description="Unique repository ID")
    node_id: str = Field(description="GraphQL node ID")
    name: str = Field(description="Repository name")
    full_name: str = Field(description="Full repository name (owner/repo)")
    owner: RepositoryOwner = Field(description="Repository owner")
    private: bool = Field(description="Whether repository is private")
    html_url: HttpUrl = Field(description="Repository URL on GitHub")
    description: str | None = Field(default=None, description="Repository description")
    fork: bool = Field(description="Whether repository is a fork")
    url: HttpUrl = Field(description="API URL for repository")
    archive_url: str = Field(description="Archive URL template")
    assignees_url: str = Field(description="Assignees URL template")
    blobs_url: str = Field(description="Blobs URL template")
    branches_url: str = Field(description="Branches URL template")
    collaborators_url: str = Field(description="Collaborators URL template")
    comments_url: str = Field(description="Comments URL template")
    commits_url: str = Field(description="Commits URL template")
    compare_url: str = Field(description="Compare URL template")
    contents_url: str = Field(description="Contents URL template")
    contributors_url: HttpUrl = Field(description="Contributors API URL")
    deployments_url: HttpUrl = Field(description="Deployments API URL")
    downloads_url: HttpUrl = Field(description="Downloads API URL")
    events_url: HttpUrl = Field(description="Events API URL")
    forks_url: HttpUrl = Field(description="Forks API URL")
    git_commits_url: str = Field(description="Git commits URL template")
    git_refs_url: str = Field(description="Git refs URL template")
    git_tags_url: str = Field(description="Git tags URL template")
    git_url: str = Field(description="Git clone URL")
    issue_comment_url: str = Field(description="Issue comment URL template")
    issue_events_url: str = Field(description="Issue events URL template")
    issues_url: str = Field(description="Issues URL template")
    keys_url: str = Field(description="Keys URL template")
    labels_url: str = Field(description="Labels URL template")
    languages_url: HttpUrl = Field(description="Languages API URL")
    merges_url: HttpUrl = Field(description="Merges API URL")
    milestones_url: str = Field(description="Milestones URL template")
    notifications_url: str = Field(description="Notifications URL template")
    pulls_url: str = Field(description="Pull requests URL template")
    releases_url: str = Field(description="Releases URL template")
    ssh_url: str = Field(description="SSH clone URL")
    stargazers_url: HttpUrl = Field(description="Stargazers API URL")
    statuses_url: str = Field(description="Statuses URL template")
    subscribers_url: HttpUrl = Field(description="Subscribers API URL")
    subscription_url: HttpUrl = Field(description="Subscription API URL")
    tags_url: HttpUrl = Field(description="Tags API URL")
    teams_url: HttpUrl = Field(description="Teams API URL")
    trees_url: str = Field(description="Trees URL template")
    clone_url: HttpUrl = Field(description="HTTPS clone URL")
    mirror_url: HttpUrl | None = Field(
        default=None, description="Mirror URL if repository is a mirror"
    )
    hooks_url: HttpUrl = Field(description="Hooks API URL")
    svn_url: HttpUrl = Field(description="SVN URL")
    homepage: str | None = Field(default=None, description="Repository homepage URL")
    language: str | None = Field(
        default=None, description="Primary programming language"
    )
    forks_count: int = Field(description="Number of forks")
    stargazers_count: int = Field(description="Number of stars")
    watchers_count: int = Field(description="Number of watchers")
    size: int = Field(description="Repository size in KB")
    default_branch: str = Field(description="Default branch name")
    open_issues_count: int = Field(
        description="Number of open issues and pull requests"
    )
    is_template: bool | None = Field(
        default=None, description="Whether repository is a template"
    )
    topics: list[str] | None = Field(default=None, description="Repository topics/tags")
    has_issues: bool = Field(description="Whether repository has issues enabled")
    has_projects: bool = Field(description="Whether repository has projects enabled")
    has_wiki: bool = Field(description="Whether repository has wiki enabled")
    has_pages: bool = Field(description="Whether repository has GitHub Pages enabled")
    has_downloads: bool = Field(description="Whether repository has downloads enabled")
    has_discussions: bool | None = Field(
        default=None, description="Whether repository has discussions enabled"
    )
    archived: bool = Field(description="Whether repository is archived")
    disabled: bool = Field(description="Whether repository is disabled")
    visibility: RepositoryVisibility | None = Field(
        default=None, description="Repository visibility"
    )
    pushed_at: datetime | None = Field(default=None, description="Last push date")
    created_at: datetime = Field(description="Repository creation date")
    updated_at: datetime = Field(description="Last repository update")
    permissions: RepositoryPermissions | None = Field(
        default=None, description="User permissions on repository"
    )
    allow_rebase_merge: bool | None = Field(
        default=None, description="Whether rebase merging is allowed"
    )
    template_repository: "Repository | None" = Field(
        default=None, description="Template repository if created from template"
    )
    temp_clone_token: str | None = Field(
        default=None, description="Temporary clone token"
    )
    allow_squash_merge: bool | None = Field(
        default=None, description="Whether squash merging is allowed"
    )
    allow_auto_merge: bool | None = Field(
        default=None, description="Whether auto-merge is allowed"
    )
    delete_branch_on_merge: bool | None = Field(
        default=None, description="Whether to delete head branches after merge"
    )
    allow_update_branch: bool | None = Field(
        default=None, description="Whether to allow updating branch with rebase"
    )
    use_squash_pr_title_as_default: bool | None = Field(
        default=None,
        description="Whether to use PR title as default squash commit message",
    )
    squash_merge_commit_title: str | None = Field(
        default=None, description="Default squash merge commit title"
    )
    squash_merge_commit_message: str | None = Field(
        default=None, description="Default squash merge commit message"
    )
    merge_commit_title: str | None = Field(
        default=None, description="Default merge commit title"
    )
    merge_commit_message: str | None = Field(
        default=None, description="Default merge commit message"
    )
    allow_merge_commit: bool | None = Field(
        default=None, description="Whether merge commits are allowed"
    )
    allow_forking: bool | None = Field(
        default=None, description="Whether forking is allowed"
    )
    web_commit_signoff_required: bool | None = Field(
        default=None, description="Whether web-based commits require signoff"
    )
    subscribers_count: int | None = Field(
        default=None, description="Number of subscribers"
    )
    network_count: int | None = Field(
        default=None, description="Number of repositories in the network"
    )
    license: dict[str, any] | None = Field(
        default=None, description="Repository license information"
    )
    organization: GitHubUser | None = Field(
        default=None, description="Organization that owns the repository"
    )
    parent: "Repository | None" = Field(
        default=None, description="Parent repository if this is a fork"
    )
    source: "Repository | None" = Field(
        default=None, description="Source repository if this is a fork"
    )
    security_and_analysis: SecurityAnalysis | None = Field(
        default=None, description="Security and analysis settings"
    )

    class Config:
        # Handle forward references
        arbitrary_types_allowed = True
