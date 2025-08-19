from models import CodeFile
from database import get_session, init_database
from repository_scanner import RepositoryScanner
from datetime import datetime


def sync_repository_files(repo_path, session):
    """
    Synchronize files from the repository with the database.

    This function:
    1. Scans the repository for current files
    2. Updates existing files in the database if their content has changed
    3. Adds new files that don't exist in the database
    4. Optionally handles files that have been deleted from the repository

    Args:
        repo_path: Path to the repository
        session: SQLAlchemy database session

    Returns:
        dict: Statistics about files added, updated, and deleted
    """
    # Initialize statistics
    stats = {
        'added': 0,
        'updated': 0,
        'deleted': 0
    }

    # Scan repository for current files
    scanner = RepositoryScanner()
    current_files = scanner.scan_repository(repo_path)

    # Query the database to get all existing files
    db_files = session.query(CodeFile).all()

    # Create a dictionary mapping file paths to database objects for quick lookup
    db_files_map = {db_file.file_path: db_file for db_file in db_files}

    # Create a set to track which file paths we've processed in this scan
    processed_paths = set()

    # Process each file from the current scan
    for file_data in current_files:
        # Add this file path to the set of processed paths
        processed_paths.add(file_data.file_path)

        # Check if the file already exists in the database
        if file_data.file_path in db_files_map:
            # If file exists, check if its content has changed
            db_file = db_files_map[file_data.file_path]
            if db_file.content != file_data.content:
                # If content has changed, update the database record and increment stats['updated']
                db_file.content = file_data.content
                db_file.language = file_data.language
                db_file.last_updated = file_data.last_updated
                session.merge(db_file)
                stats['updated'] += 1
        else:
            # If file doesn't exist in the database, create a new record and increment stats['added']
            new_file = CodeFile(
                file_path=file_data.file_path,
                content=file_data.content,
                language=file_data.language,
                last_updated=file_data.last_updated
            )
            session.add(new_file)
            stats['added'] += 1

    # Check for files that have been deleted from the repository
    # (files that exist in the database but weren't in the current scan)
    for db_file in db_files:
        if db_file.file_path not in processed_paths:
            session.delete(db_file)
            stats['deleted'] += 1

    # Commit all changes to the database
    session.commit()

    return stats


if __name__ == "__main__":
    # Set up the database with initial data
    from db_setup import setup_database
    setup_database()

    # Get a database session
    session = get_session()

    # Synchronize repository files with the database
    stats = sync_repository_files('.', session)

    # Print statistics
    print(f"Files added: {stats['added']}")
    print(f"Files updated: {stats['updated']}")
    print(f"Files deleted: {stats['deleted']}")
    print(
        f"Total files processed: {stats['added'] + stats['updated'] + stats['deleted']}")
