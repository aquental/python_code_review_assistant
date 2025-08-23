from typing import List, Dict
from mock_data import Session, CodeFile


def get_file_context(session: Session, file_path: str, max_lines=50) -> str:
    """Get current file content as context"""
    file_record = session.query(CodeFile).filter_by(
        file_path=file_path).first()
    if not file_record:
        return ""

    if not file_record.content:
        return ""

    lines = file_record.content.split('\n')
    if len(lines) <= max_lines:
        return file_record.content

    # Return first part of file with truncation notice
    truncated = '\n'.join(lines[:max_lines])
    return f"{truncated}\n... [truncated after {max_lines} lines]"


def get_recent_changes(session: Session, file_path: str, limit=3) -> List[Dict]:
    """Get recent changes to the file"""
    file_record = session.query(CodeFile).filter_by(
        file_path=file_path).first()
    if not file_record:
        return []

    # This is a stub for demonstration; in a real scenario, this would query commits
    # Here we return a mock list
    return [
        {
            'hash': 'abc12345',
            'message': 'Initial commit',
            'author': 'Alice',
            'date': '2024-06-01'
        },
        {
            'hash': 'def67890',
            'message': 'Refactor code',
            'author': 'Bob',
            'date': '2024-06-02'
        },
        {
            'hash': 'ghi54321',
            'message': 'Fix bug in main function',
            'author': 'Charlie',
            'date': '2024-06-03'
        }
    ][:limit]


def find_related_files(session: Session, file_path: str) -> List[str]:
    """Find files that might be related based on imports"""
    # Check if file exists in the session
    file_record = session.query(CodeFile).filter_by(
        file_path=file_path).first()
    if not file_record:
        return []

    # Simple heuristic: find files imported in this file
    related = []
    content = file_record.content

    # Loop through each line in the content
    for line in content.split('\n'):
        # Check if the line starts with 'from' or 'import'
        if line.strip().startswith(('from ', 'import ')):
            # For lines with imports, extract module names that contain dots
            parts = line.strip().split()
            for part in parts:
                if '.' in part:
                    # Convert module names to file paths (replace dots with slashes, add .py)
                    module_path = part.replace('.', '/') + '.py'
                    # Check if the file exists in the session and add it to related files
                    if session.query(CodeFile).filter_by(file_path=module_path).first():
                        if module_path not in related:  # Avoid duplicates
                            related.append(module_path)

    # Return the list of related files, limited to 3 maximum
    return related[:3]
