import argparse
import os
import sys
from scanner import RepositoryScanner
from git_extractor import GitHistoryExtractor

# Import specific git exceptions or define them if GitPython is not available
try:
    from git import InvalidGitRepositoryError, NoSuchPathError
except ImportError:
    class InvalidGitRepositoryError(Exception):
        pass

    class NoSuchPathError(Exception):
        pass


class CodebaseAnalyzer:
    def __init__(self):
        self.scanner = RepositoryScanner()
        self.git_extractor = GitHistoryExtractor()

    def analyze_repository(self, repo_path):
        print("Starting analysis...")

        # Validate the repository path
        if not os.path.exists(repo_path):
            print(f"Error: Repository path '{repo_path}' does not exist")
            return False
        if not os.path.isdir(repo_path):
            print(f"Error: '{repo_path}' is not a directory")
            return False
        if not os.access(repo_path, os.R_OK):
            print(f"Error: No read permissions for '{repo_path}'")
            return False

        # Scan files with error handling
        files = []
        try:
            files = self.scanner.scan_repository(repo_path)
        except PermissionError as e:
            print(
                f"Error: Permission denied while scanning repository: {str(e)}")
            return False
        except Exception as e:
            print(f"Error: Failed to scan repository: {str(e)}")
            return False

        # Extract git history with error handling
        commits = []
        try:
            commits = self.git_extractor.extract_commits(repo_path)
        except (InvalidGitRepositoryError, NoSuchPathError) as e:
            print(f"Warning: Invalid git repository or path: {str(e)}")
            print("Continuing analysis without git history...")
        except Exception as e:
            print(f"Warning: Failed to extract git history: {str(e)}")
            print("Continuing analysis without git history...")

        # Show results
        print(f"\nResults:")
        print(f"Files: {len(files)}")
        print(f"Commits: {len(commits)}")
        print(
            f"File changes: {len(getattr(self.git_extractor, 'file_changes', []))}")

        # Language stats
        languages = {}
        for file in files:
            lang = getattr(file, 'language', 'Unknown')
            if lang:
                languages[lang] = languages.get(lang, 0) + 1
        print(f"Languages: {languages or 'No language data available'}")

        return True


def main():
    parser = argparse.ArgumentParser(description="Analyze code repositories")
    parser.add_argument('--repo', default='.', help='Repository path')
    args = parser.parse_args()

    # Create analyzer and call analyze_repository
    analyzer = CodebaseAnalyzer()

    # Call analyze_repository and handle the return status
    success = analyzer.analyze_repository(args.repo)

    # Exit with appropriate exit code based on success/failure
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
