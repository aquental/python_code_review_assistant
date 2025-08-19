from models import CodeFile, Commit
from database import get_session, init_database
from repository_scanner import RepositoryScanner
from git_extractor import GitHistoryExtractor


def populate_database(repo_path, session):
    """
    Populate the database with code files and commits from a repository.

    Args:
        repo_path: Path to the repository
        session: SQLAlchemy database session
    """
    scanner = RepositoryScanner()
    # TODO: Create an instance of GitHistoryExtractor
    git_extractor = GitHistoryExtractor()

    # Store files
    print("Scanning repository for code files...")
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
    print(f"Stored {len(files)} code files in the database.")

    # Store commits
    print("Extracting commit history...")
    # Extract commits from the repository using the git_extractor
    commits = git_extractor.extract_commits(repo_path)

    # Loop through each commit and create a Commit model instance
    for commit_data in commits:
        db_commit = Commit(
            hash=commit_data.hash,
            author=commit_data.author,
            message=commit_data.message,
            date=commit_data.date
        )
        session.merge(db_commit)

    # Commit the changes to the database
    session.commit()

    print("Database populated successfully!")


if __name__ == "__main__":
    init_database()
    session = get_session()
    populate_database('.', session)
