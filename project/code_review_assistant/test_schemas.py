import pytest
from pydantic import ValidationError
from schemas import FileChangeRequest, ChangesetRequest

def test_file_change_request_valid():
    data = {
        "file_path": "src/main.py",
        "diff_content": "@@ -1,5 +1,7 @@\n+def new_function():\n+    return True\n def existing_function():\n     return False"
    }
    file_change = FileChangeRequest(**data)
    assert file_change.file_path == data["file_path"]
    assert file_change.diff_content == data["diff_content"]

def test_file_change_request_invalid():
    # Missing required field
    with pytest.raises(ValidationError):
        FileChangeRequest(diff_content="some diff")
    
    # Wrong type
    with pytest.raises(ValidationError):
        FileChangeRequest(file_path=123, diff_content="some diff")

def test_changeset_request_valid():
    data = {
        "title": "Add new feature",
        "author": "developer@example.com",
        "files": [
            {
                "file_path": "src/main.py",
                "diff_content": "@@ -1,5 +1,7 @@\n+def new_function():\n+    return True"
            }
        ]
    }
    changeset = ChangesetRequest(**data)
    assert changeset.title == data["title"]
    assert changeset.description is None
    assert changeset.author == data["author"]
    assert len(changeset.files) == 1
    assert changeset.files[0].file_path == data["files"][0]["file_path"]

def test_changeset_request_with_description():
    data = {
        "title": "Add new feature",
        "description": "This adds a new function to handle user requests",
        "author": "developer@example.com",
        "files": [
            {
                "file_path": "src/main.py",
                "diff_content": "@@ -1,5 +1,7 @@\n+def new_function():\n+    return True"
            }
        ]
    }
    changeset = ChangesetRequest(**data)
    assert changeset.description == data["description"]

def test_changeset_request_invalid():
    # Missing required field
    with pytest.raises(ValidationError):
        ChangesetRequest(
            description="Some description",
            author="developer@example.com",
            files=[]
        )
    
    # Invalid files format
    with pytest.raises(ValidationError):
        ChangesetRequest(
            title="Add feature",
            author="developer@example.com",
            files="not a list"
        )
    
    # Empty files list is valid, but each file must be valid
    with pytest.raises(ValidationError):
        ChangesetRequest(
            title="Add feature",
            author="developer@example.com",
            files=[{"file_path": "src/main.py"}]  # missing diff_content
        )
