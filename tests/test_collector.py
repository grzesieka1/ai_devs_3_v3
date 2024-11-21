"""Testy dla CollectorAgent"""

import unittest
from agents.collector_agent import CollectorAgent
from pathlib import Path

class TestCollectorAgent(unittest.TestCase):
    def setUp(self):
        self.agent = CollectorAgent()
        self.data_dir = Path("data/content")

    def test_process(self):
        # Uruchom agenta
        result = self.agent.process()
        
        # Sprawdź czy mamy wszystkie klucze
        self.assertIn('article', result)
        self.assertIn('questions', result)
        
        # Sprawdź czy są dane artykułu
        article = result['article']
        self.assertIn('html', article)
        self.assertIn('text', article)
        self.assertIn('images', article)
        self.assertIn('audio', article)
        
        # Sprawdź czy pliki zostały utworzone
        self.assertTrue((self.data_dir / "article.html").exists())
        self.assertTrue((self.data_dir / "article.txt").exists())
        self.assertTrue((self.data_dir / "questions.txt").exists())

if __name__ == '__main__':
    unittest.main() 