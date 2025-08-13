from dataclasses import dataclass
from datetime import datetime
from typing import List
import os.path


@dataclass
class CodeFile:
    file_path: str
    content: str
    language: str
    last_updated: datetime

    def get_file_extension(self) -> str:
        """Extracts and returns the file extension from file_path.
        Returns an empty string if no extension is found."""
        extension = os.path.splitext(self.file_path)[1]
        # Remove leading dot or return empty string
        return extension[1:] if extension else ""


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


if __name__ == "__main__":
    # Create sample CodeFile instances with different file paths
    python_file = CodeFile(
        file_path="src/main.py",
        content="print('Hello, world!')",
        language="python",
        last_updated=datetime.now()
    )

    javascript_file = CodeFile(
        file_path="web/script.js",
        content="console.log('Hello, world!');",
        language="javascript",
        last_updated=datetime.now()
    )

    readme_file = CodeFile(
        file_path="README",
        content="# Project Documentation",
        language="markdown",
        last_updated=datetime.now()
    )

    dockerfile = CodeFile(
        file_path="Dockerfile",
        content="FROM python:3.9-slim",
        language="dockerfile",
        last_updated=datetime.now()
    )

    # Call the get_file_extension method on each CodeFile instance and print the results
    files = [python_file, javascript_file, readme_file, dockerfile]
    print("File Extensions:")
    print("-" * 30)
    for file in files:
        print(
            f"File: {file.file_path:<20} Extension: {file.get_file_extension()}")
    print("-" * 30)

    print("Project setup complete. Ready to build components!")
