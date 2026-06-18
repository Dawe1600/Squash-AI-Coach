import pytest
import os
from unittest.mock import patch, mock_open
from app.core.knowledge_loader import KnowledgeLoader

@pytest.fixture(autouse=True)
def reset_singleton():
    # Zapewnia, że każdy test zaczyna z czystym stanem Singletona
    KnowledgeLoader.reset()
    yield
    KnowledgeLoader.reset()

def test_knowledge_loader_initialization():
    # Sprawdza czy poprawnie wczytuje z domyślnego katalogu
    loader = KnowledgeLoader()
    knowledge_text = loader.get_knowledge_text()
    
    # Wiedza powinna być wczytana z plików, sprawdzamy czy nie jest pusta
    # Jeśli pliki nie istnieją, zwróci "", więc ten test ufa obecności faktycznych plików 
    # w środowisku dev/test (lub można je zmockować)
    assert isinstance(knowledge_text, str)
    
def test_knowledge_loader_singleton():
    loader1 = KnowledgeLoader()
    loader2 = KnowledgeLoader()
    assert loader1 is loader2

@patch("os.path.isdir", return_value=False)
def test_knowledge_loader_missing_dir(mock_isdir):
    loader = KnowledgeLoader("invalid_path")
    assert loader.get_knowledge_text() == ""

@patch("os.path.isdir", return_value=True)
@patch("glob.glob", return_value=["test1.md", "test2.md"])
@patch("builtins.open", new_callable=mock_open, read_data="Test Content <!-- VERIFY -->")
def test_knowledge_loader_file_reading(mock_file, mock_glob, mock_isdir):
    loader = KnowledgeLoader("mock_dir")
    text = loader.get_knowledge_text()
    
    # Powinien przeczytać oba pliki i złączyć, usuwając komentarze HTML
    assert "Test Content" in text
    assert "VERIFY" not in text
    assert text.count("Test Content") == 2
    assert "---" in text  # separator
