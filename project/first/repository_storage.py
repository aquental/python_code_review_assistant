from models import CodeFile
from database import get_session, init_database
from repository_scanner import RepositoryScanner


def store_code_files(files, session):
    """
    Store a list of code files in the database.

    Args:
        files: List of file objects with file_path, content, language, and last_updated attributes
        session: SQLAlchemy database session

    Returns:
        int: Number of files stored in the database
    """
    count = 0

    for file_data in files:
        # Create a new CodeFile object with attributes from file_data
        code_file = CodeFile(
            file_path=file_data.file_path,
            content=file_data.content,
            language=file_data.language,
            last_updated=file_data.last_updated
        )

        # Add the file to the session using merge to handle duplicates
        session.merge(code_file)

        count += 1

    # Commit the changes to the database
    session.commit()

    return count


if __name__ == "__main__":
    # Initialize the database
    init_database()

    # Get a database session
    session = get_session()

    # Scan the repository for files
    scanner = RepositoryScanner()
    files = scanner.scan_repository('.')

    # Store the files in the database
    num_stored = store_code_files(files, session)

    print(f"Successfully stored {num_stored} files in the database.")
