from pydantic import BaseModel
from typing import List, Optional


class FileChangeRequest(BaseModel):
    file_path: str
    diff_content: str


class ChangesetRequest(BaseModel):
    title: str
    description: Optional[str] = None
    author: str
    files: List[FileChangeRequest]
