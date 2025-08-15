from git import Repo
from datetime import datetime
import os
from collections import Counter

# Minimal dataclasses for continuity with the outline
from dataclasses import dataclass


@dataclass
class GitCommit:
    hash: str
    message: str
    author: str
    date: datetime


@dataclass
class FileChange:
    file_path: str
    commit_hash: str
    diff_content: str


class GitHistoryExtractor:
    def __init__(self):
        self.commits = []
        self.file_changes = []

    def extract_commits(self, repo_path, max_commits=50):
        print(f"Extracting git history: {repo_path}")
        repo = Repo(repo_path)

        for commit in repo.iter_commits(max_count=max_commits):
            git_commit = GitCommit(
                hash=commit.hexsha,
                message=commit.message.strip(),
                author=f"{commit.author.name} <{commit.author.email}>",
                date=commit.committed_datetime
            )
            self.commits.append(git_commit)

            # Extract file changes
            if commit.parents:
                parent = commit.parents[0]
                for diff in parent.diff(commit, create_patch=True):
                    if diff.b_path:
                        file_change = FileChange(
                            file_path=diff.b_path,
                            commit_hash=commit.hexsha,
                            diff_content=diff.diff.decode(
                                'utf-8', errors='ignore')
                        )
                        self.file_changes.append(file_change)

        print(
            f"Found {len(self.commits)} commits, {len(self.file_changes)} changes")
        return self.commits

    def generate_commit_summary(self):
        if not self.commits:
            return {
                "total_commits": 0,
                "unique_authors": 0,
                "most_active_author": None,
                "most_changed_file": None,
                "date_range": None
            }

        # Calculate total commits
        total_commits = len(self.commits)

        # Calculate unique authors
        authors = {commit.author for commit in self.commits}
        unique_authors = len(authors)

        # Find most active author
        author_counts = Counter(commit.author for commit in self.commits)
        most_active_author = author_counts.most_common(
            1)[0][0] if author_counts else None

        # Find most changed file
        file_counts = Counter(change.file_path for change in self.file_changes)
        most_changed_file = file_counts.most_common(
            1)[0][0] if file_counts else None

        # Calculate date range
        dates = [commit.date for commit in self.commits]
        date_range = (
            min(dates).strftime("%Y-%m-%d %H:%M:%S"),
            max(dates).strftime("%Y-%m-%d %H:%M:%S")
        ) if dates else None

        return {
            "total_commits": total_commits,
            "unique_authors": unique_authors,
            "most_active_author": most_active_author,
            "most_changed_file": most_changed_file,
            "date_range": date_range
        }


def main():
    extractor = GitHistoryExtractor()

    # Use current directory as the git repository
    repo_path = "./sample-ecommerce-api"

    # Check if we're in a git repository
    if not os.path.exists(os.path.join(repo_path, ".git")):
        print("Not a git repository. Initializing a sample repo...")
        print("GitHistoryExtractor initialized successfully!")
        return

    try:
        commits = extractor.extract_commits(repo_path, max_commits=10)

        # Display first few commits
        print("\nRecent commits:")
        for i, commit in enumerate(commits[:3]):
            print(f"{i+1}. {commit.hash[:8]} - {commit.message[:50]}...")
            print(f"   Author: {commit.author}")
            print(f"   Date: {commit.date}")
            print()

        # Call the generate_commit_summary method and store the result
        summary = extractor.generate_commit_summary()

        # Display the summary information with appropriate formatting
        print("\nRepository Summary:")
        print(f"Total Commits: {summary['total_commits']}")
        print(f"Unique Authors: {summary['unique_authors']}")
        print(f"Most Active Author: {summary['most_active_author'] or 'N/A'}")
        print(f"Most Changed File: {summary['most_changed_file'] or 'N/A'}")
        if summary['date_range']:
            print(
                f"Date Range: {summary['date_range'][0]} to {summary['date_range'][1]}")
        else:
            print("Date Range: N/A")

    except Exception as e:
        print(f"Error extracting git history: {e}")


if __name__ == "__main__":
    main()
