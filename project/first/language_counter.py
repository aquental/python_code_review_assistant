from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict


@dataclass
class CodeFile:
    file_path: str
    content: str
    language: str
    last_updated: datetime
    file_size: int


# Create a list of at least 5 CodeFile instances with different languages
code_files = [
    CodeFile(
        file_path="src/main.py",
        content="def main():\n    print('Hello, Python!')",
        language="python",
        last_updated=datetime.now(),
        file_size=50
    ),
    CodeFile(
        file_path="src/app.js",
        content="console.log('Hello, JavaScript!');",
        language="javascript",
        last_updated=datetime.now(),
        file_size=30
    ),
    CodeFile(
        file_path="src/Main.java",
        content="public class Main {\n    public static void main(String[] args) {\n        System.out.println('Hello, Java!');\n    }\n}",
        language="java",
        last_updated=datetime.now(),
        file_size=100
    ),
    CodeFile(
        file_path="src/styles.css",
        content="body { background-color: #f0f0f0; }",
        language="css",
        last_updated=datetime.now(),
        file_size=40
    ),
    CodeFile(
        file_path="src/index.html",
        content="<!DOCTYPE html><html><body>Hello, HTML!</body></html>",
        language="html",
        last_updated=datetime.now(),
        file_size=60
    )
]

# Create a dictionary to store the count of files per language
language_counts = {}

# Write a loop to count files by language
for code_file in code_files:
    language = code_file.language
    language_counts[language] = language_counts.get(language, 0) + 1

# Display the counts in a readable format
print("Language File Count Summary:")
print("-" * 30)
for language, count in sorted(language_counts.items()):
    print(f"{language.capitalize()}: {count} file{'s' if count != 1 else ''}")
print("-" * 30)
print(f"Total files: {len(code_files)}")

if __name__ == "__main__":
    pass
