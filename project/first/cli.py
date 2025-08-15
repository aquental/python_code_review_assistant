import argparse
from scanner import RepositoryScanner
from git_extractor import GitHistoryExtractor
import os


class CodebaseAnalyzer:
    def __init__(self):
        self.scanner = RepositoryScanner()
        self.git_extractor = GitHistoryExtractor()

    def analyze_repository(self, repo_path):
        print("Starting full analysis...")

        # Scan files
        files = self.scanner.scan_repository(repo_path)

        # Extract git history
        commits = self.git_extractor.extract_commits(repo_path)

        # Show results
        print(f"\nResults:")
        print(f"Files: {len(files)}")
        print(f"Commits: {len(commits)}")
        print(f"File changes: {len(self.git_extractor.file_changes)}")

        # Language stats
        languages = {}
        for file in files:
            languages[file.language] = languages.get(file.language, 0) + 1
        print(f"Languages: {languages}")

    def scan_only_mode(self, repo_path):
        print("Starting scan-only analysis...")

        # Scan files
        files = self.scanner.scan_repository(repo_path)

        # Count total lines of code
        total_lines = 0
        for file in files:
            try:
                # Construct full path using repo_path and relative file_path
                full_path = os.path.join(repo_path, file.file_path)
                with open(full_path, 'r', encoding='utf-8') as f:
                    total_lines += sum(1 for line in f)
            except (IOError, UnicodeDecodeError):
                continue  # Skip files that can't be read

        # Language stats
        languages = {}
        for file in files:
            languages[file.language] = languages.get(file.language, 0) + 1

        # Show results
        print(f"\nScan-Only Results:")
        print(f"Files: {len(files)}")
        print(f"Total Lines of Code: {total_lines}")
        print(f"Languages: {languages}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', default='.', help='Repository path')
    parser.add_argument('--scan-only', action='store_true',
                        help='Run in scan-only mode')
    args = parser.parse_args()

    analyzer = CodebaseAnalyzer()

    if args.scan_only:
        analyzer.scan_only_mode(args.repo)
    else:
        analyzer.analyze_repository(args.repo)


if __name__ == "__main__":
    main()
