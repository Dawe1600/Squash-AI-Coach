import os
import glob
from typing import Optional


class KnowledgeLoader:
    """
    Loads and caches expert squash knowledge from Markdown files
    in the knowledge/ directory. Knowledge is loaded once at initialization
    and served from memory for all subsequent requests.
    """

    _instance: Optional["KnowledgeLoader"] = None
    _knowledge_text: Optional[str] = None

    def __new__(cls, knowledge_dir: Optional[str] = None):
        """Singleton pattern — ensures knowledge is loaded only once."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, knowledge_dir: Optional[str] = None):
        if self._knowledge_text is not None:
            return  # Already loaded

        if knowledge_dir is None:
            # Default: knowledge/ directory next to this file
            knowledge_dir = os.path.join(os.path.dirname(__file__), "knowledge")

        self._knowledge_dir = knowledge_dir
        self._knowledge_text = self._load_all_files()
        print(f"[KnowledgeLoader] Loaded {len(self._knowledge_text)} characters of squash knowledge from {self._knowledge_dir}")

    def _load_all_files(self) -> str:
        """
        Reads all .md files from the knowledge directory, sorted by filename.
        Returns a single concatenated string with section headers.
        """
        if not os.path.isdir(self._knowledge_dir):
            print(f"[KnowledgeLoader] WARNING: Knowledge directory not found: {self._knowledge_dir}")
            return ""

        md_files = sorted(glob.glob(os.path.join(self._knowledge_dir, "*.md")))

        if not md_files:
            print(f"[KnowledgeLoader] WARNING: No .md files found in {self._knowledge_dir}")
            return ""

        sections = []
        for filepath in md_files:
            filename = os.path.basename(filepath)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                if content:
                    # Strip HTML comments (<!-- VERIFY --> tags) from the content
                    # sent to the model — they are for human review only
                    import re
                    content = re.sub(r"<!--.*?-->", "", content, flags=re.DOTALL).strip()
                    sections.append(content)
            except Exception as e:
                print(f"[KnowledgeLoader] Error reading {filename}: {e}")

        return "\n\n---\n\n".join(sections)

    def get_knowledge_text(self) -> str:
        """Returns the full cached knowledge text."""
        return self._knowledge_text or ""

    @classmethod
    def reset(cls):
        """Resets the singleton (useful for testing or hot-reload)."""
        cls._instance = None
        cls._knowledge_text = None
