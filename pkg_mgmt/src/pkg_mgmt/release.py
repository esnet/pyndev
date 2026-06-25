#!/usr/bin/env python3
import argparse
import os
import sys
from dataclasses import dataclass
from urllib.parse import quote

import requests

from .utils import run


@dataclass
class Config:
    """Type for gitlab config variables"""

    api_url: str
    commit_branch: str
    project_id: str
    project_url: str
    token: str

    def __post_init__(self):
        self.headers = {"PRIVATE-TOKEN": self.token}
        self._setup_git_auth()

    def _setup_git_auth(self):
        """Configure git to use token authentication."""
        host = self.project_url.split("/")[2]

        run("git config --global credential.helper store")
        run(f"git config --global user.email 'release-bot@{host}'")
        run("git config --global user.name 'Release Bot'")

        auth_url = self.project_url.replace("https://", f"https://oauth2:{self.token}@")
        run(f"git remote set-url origin {auth_url}.git")
        run("git fetch origin --tags")


def get_gitlab_config():
    """Collect GitLab environment"""
    required = [
        "CI_API_V4_URL",
        "CI_COMMIT_BRANCH",
        "CI_PROJECT_ID",
        "CI_PROJECT_URL",
        "RELEASE_TOKEN",
    ]
    missing = [var for var in required if not os.environ.get(var)]

    if missing:
        print(f"ERROR: Missing required environment variables: {', '.join(missing)}")
        sys.exit(1)

    return Config(
        os.environ["CI_API_V4_URL"],
        os.environ["CI_COMMIT_BRANCH"],
        os.environ["CI_PROJECT_ID"],
        os.environ["CI_PROJECT_URL"],
        os.environ["RELEASE_TOKEN"],
    )


def branch_exists(conf: Config, branch: str) -> bool:
    """Test if a branch exists in the project"""
    encoded_branch = quote(branch, safe="")
    response = requests.get(
        f"{conf.api_url}/projects/{conf.project_id}/repository/branches/{encoded_branch}",
        headers=conf.headers,
    )
    return response.status_code == 200


def merge_request(
    conf: Config, source: str, target: str, title: str, remove_source: bool = False, squash: bool = False
) -> None:
    """Merge source branch into target using git CLI."""
    if not branch_exists(conf, source):
        print(f"Source branch '{source}' does not exist, skipping")
        return

    print(f"\n{title}")
    print(f"Merging {source} → {target}")

    run(f"git checkout {target}")
    run(f"git pull origin {target}")

    if squash:
        run(f"git merge origin/{source} --squash -m '{title}'")
        run(f"git commit -m '{title}'")
    else:
        run(f"git merge origin/{source} -m '{title}'")

    run(f"git push origin {target}")

    if remove_source:
        run(f"git push origin --delete {source}")
        print(f"Deleted branch {source}")

    print(f"Merged {source} into {target}")


def create_tag(conf: Config, tag: str, ref: str) -> None:
    """Create a simple git tag, git tag -a {tag} -m {tag}"""
    response = requests.post(
        f"{conf.api_url}/projects/{conf.project_id}/repository/tags",
        headers=conf.headers,
        json={
            "tag_name": tag,
            "ref": ref,
            "message": tag,
        },
    )

    if response.status_code != 201:
        print(f"ERROR: Failed to create tag {tag}")
        print(f"Response: {response.text}")
        sys.exit(1)

    print(f"Created tag {tag}")


def get_latest_tag(conf: Config) -> str | None:
    """Fetch the most recent tag by semver order"""
    response = requests.get(
        f"{conf.api_url}/projects/{conf.project_id}/repository/tags",
        headers=conf.headers,
        params={"order_by": "version", "per_page": 1},
    )

    if response.status_code != 200 or not response.json():
        return None

    return response.json()[0]["name"]


def bump(version: str, bump_type: str) -> str:
    """Bump version string where bump_type is minor or patch"""
    major, minor, patch = map(int, version.split("."))

    match bump_type:
        case "minor":
            return f"{major}.{minor + 1}.0"
        case "patch":
            return f"{major}.{minor}.{patch + 1}"
        case _:
            raise ValueError(f"Unknown bump type: {bump_type}")


def release(
    release_type: str,
    notes_branch: str | None = None,
    explicit_version: str | None = None,
) -> None:
    """The release process"""
    config = get_gitlab_config()
    current_version = get_latest_tag(config)
    if explicit_version:
        release_version = explicit_version
    elif release_type == "hotfix":
        release_version = bump(current_version, "patch")
    else:
        release_version = bump(current_version, "minor")

    if branch_exists(config, notes_branch):
        merge_request(
            config,
            notes_branch,
            config.commit_branch,
            f"release notes {release_version}",
            remove_source=True,
            squash=True,
        )

    # per gitflow-workflow hotfixes and long running release branches
    # merge into both main and develop, we can prevent some edge case
    # conflicts with a pure main -> develop merge
    if config.commit_branch != "develop":
        # non develop branches are pruned
        merge_request(
            config,
            config.commit_branch,
            "main",
            f"Hotfix: {release_version}",
            remove_source=True,
            squash=True,
        )
        merge_request(
            config,
            "main",
            "develop",
            f"Hotfix: {release_version}",
        )
    else:
        merge_request(config, config.commit_branch, "main", f"Release: {release_version}")

    create_tag(config, release_version, "main")
    print(f"\nRelease {release_version} complete!")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Automated GitLab release process",
    )
    parser.add_argument(
        "--release-type",
        type=str,
        choices=["standard", "hotfix"],
        default="standard",
        help="Signal this is a hotfix release",
    )
    parser.add_argument(
        "--notes-branch",
        type=str,
        help="Specify a release notes branch name to auto merge at release",
    )
    parser.add_argument(
        "--explicit-version",
        type=str,
        help="Specify an explicit version for the release tag",
    )
    args = parser.parse_args()
    release(args.release_type, args.notes_branch, args.explicit_version)


if __name__ == "__main__":
    main()
