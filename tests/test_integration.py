import unittest
import sys
from pathlib import Path
import os
import json
import shutil
from unittest.mock import patch, Mock, MagicMock

# Dodaj ścieżkę główną projektu do sys.path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from agents.collector_agent import CollectorAgent
from agents.processor_agent import ProcessorAgent
from agents.responder_agent import ResponderAgent

class TestIntegration(unittest.TestCase):
    """Testy integracyjne sprawdzające współpracę agentów."""
    
    def setUp(self):
        """Przygotowanie środowiska testowego."""
        # Ustaw testowy klucz API
        os.environ['OPENAI_API_KEY'] = 'test_key'
        
        # Utwórz katalogi testowe
        self.test_data_dir = Path("data/content")
        self.test_processed_dir = Path("data/processed")
        
        # Wyczyść istniejące katalogi
        for dir_path in [self.test_data_dir, self.test_processed_dir]:
            if dir_path.exists():
                shutil.rmtree(dir_path)
            dir_path.mkdir(parents=True)
        
        # Przygotuj testowe dane
        self.test_questions = [
            "ID-pytania-01 Pierwsze pytanie?",
            "ID-pytania-02 Drugie pytanie?"
        ]
        
        # Zapisz testowe pliki
        with open(self.test_data_dir / "questions.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(self.test_questions))
        
        with open(self.test_data_dir / "article.txt", "w", encoding="utf-8") as f:
            f.write("Testowy artykuł")
        
        with open(self.test_data_dir / "article.html", "w", encoding="utf-8") as f:
            f.write("<html>Testowy artykuł</html>")
    
    @patch('openai.OpenAI')
    def test_full_pipeline(self, mock_openai_class):
        """Test pełnego procesu: pobranie -> przetworzenie -> odpowiedzi."""
        # Przygotuj mock dla klienta OpenAI
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        # Mock dla embeddings
        mock_embedding_response = MagicMock()
        mock_embedding_response.data = [MagicMock(embedding=[0.1, 0.2, 0.3])]
        mock_client.embeddings.create.return_value = mock_embedding_response
        
        # Mock dla chat completions
        mock_chat_response = MagicMock()
        mock_chat_response.choices = [MagicMock(message=MagicMock(content="Testowa odpowiedź"))]
        mock_client.chat.completions.create.return_value = mock_chat_response
        
        # Inicjalizacja agentów
        self.processor = ProcessorAgent()
        self.processor.client = mock_client  # Podmiana klienta na mocka
        
        self.responder = ResponderAgent()
        self.responder.client = mock_client  # Podmiana klienta na mocka
        
        # Wykonaj pipeline
        processed_data = self.processor.process()
        self.assertIsNotNone(processed_data)
        
        answers = self.responder.process()
        self.assertIsNotNone(answers)
        
        # Sprawdź format odpowiedzi
        for question_id, answer in answers.items():
            self.assertTrue(question_id.startswith("ID-pytania-"))
            self.assertIsInstance(answer, str)
    
    @patch('openai.OpenAI')
    def test_error_handling(self, mock_openai_class):
        """Test obsługi błędów."""
        # Przygotuj mock dla klienta OpenAI
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        # Symuluj błąd API
        mock_client.embeddings.create.side_effect = Exception("API Error")
        
        # Inicjalizacja agenta z mockiem
        self.processor = ProcessorAgent()
        self.processor.client = mock_client  # Podmiana klienta na mocka
        
        with self.assertRaises(Exception) as context:
            self.processor.process()
        
        self.assertIn("API Error", str(context.exception))
    
    def test_data_consistency(self):
        """Test spójności danych."""
        # Zapisz testowe odpowiedzi
        test_answers = {
            "ID-pytania-01": "Odpowiedź 1",
            "ID-pytania-02": "Odpowiedź 2"
        }
        os.makedirs(self.test_processed_dir, exist_ok=True)
        with open(self.test_processed_dir / "answers.json", "w", encoding="utf-8") as f:
            json.dump(test_answers, f)
        
        # Sprawdź spójność
        with open(self.test_data_dir / "questions.txt", "r", encoding="utf-8") as f:
            questions = f.read().strip().split('\n')
        
        with open(self.test_processed_dir / "answers.json", "r", encoding="utf-8") as f:
            answers_data = json.load(f)
        
        self.assertEqual(len(questions), len(answers_data))
    
    def tearDown(self):
        """Czyszczenie po testach."""
        # Przywróć oryginalne zmienne środowiskowe
        if 'OPENAI_API_KEY' in os.environ:
            del os.environ['OPENAI_API_KEY']
        
        # Wyczyść katalogi testowe
        for dir_path in [self.test_data_dir, self.test_processed_dir]:
            if dir_path.exists():
                shutil.rmtree(dir_path)

if __name__ == '__main__':
    unittest.main() 