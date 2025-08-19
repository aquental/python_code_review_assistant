from project.first.models import CodeFile, Commit
from database import get_session
from datetime import datetime

# Dummy implementations for demonstration purposes


class RepositoryScanner:
    def scan_repository(self, repo_path):
        # Return a list of dummy CodeFile-like objects
        from collections import namedtuple
        DummyFile = namedtuple(
            'DummyFile', ['file_path', 'content', 'language', 'last_updated'])
        return [
            DummyFile('main.py', 'print("Hello, World!")',
                      'Python', datetime.now())
        ]


class GitHistoryExtractor:
    def extract_commits(self, repo_path):
        # Return a list of dummy Commit-like objects
        from collections import namedtuple
        DummyCommit = namedtuple(
            'DummyCommit', ['hash', 'message', 'author', 'date'])
        return [
            DummyCommit('abc123', 'Initial commit',
                        'Alice <alice@example.com>', datetime.now())
        ]


def populate_database(repo_path, session):
    scanner = RepositoryScanner()
    git_extractor = GitHistoryExtractor()

    # Store files
    files = scanner.scan_repository(repo_path)
    for file_data in files:
        db_file = CodeFile(
            file_path=file_data.file_path,
            content=file_data.content,
            language=file_data.language,
            last_updated=file_data.last_updated
        )
        session.merge(db_file)
    session.commit()

    # Store commits
    commits = git_extractor.extract_commits(repo_path)
    for commit_data in commits:
        db_commit = Commit(
            hash=commit_data.hash,
            message=commit_data.message,
            author=commit_data.author,
            date=commit_data.date
        )
        session.merge(db_commit)
    session.commit()

    print("Database populated successfully!")


if __name__ == "__main__":
    from database import init_database
    init_database()
    session = get_session()
    populate_database('.', session)
