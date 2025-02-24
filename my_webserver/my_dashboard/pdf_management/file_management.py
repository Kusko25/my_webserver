from pathlib import Path
import logging
import my_dashboard.pdf_management.models as models

from typing import List


def detect_new_files() -> List[Path]:
    """Detect new files in the base directory."""
    new_files = []
    known_files = set([doc.file_path for doc in models.Document.objects.all()])
    for file in BASE_DIR.glob('**/*'):
        if file.is_file() and str(file) not in known_files:
            new_files.append(file)
    return new_files