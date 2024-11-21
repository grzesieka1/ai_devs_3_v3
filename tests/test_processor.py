import unittest
import sys
from pathlib import Path
import os

# Dodaj ścieżkę główną projektu do sys.path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from agents.processor_agent import ProcessorAgent


class TestProcessorAgent(unittest.TestCase):
    def setUp(self):
        self.agent = ProcessorAgent()
        self.data_dir = Path("data/content")
        self.processed_dir = Path("data/processed")
        
    def test_process_text(self):
        sample_text = "To jest przykładowy tekst " * 100
        chunks = self.agent._process_text(sample_text)
        self.assertTrue(len(chunks) > 0)
        for chunk in chunks:
            self.assertTrue(len(chunk) <= 1000)
            
    def test_create_embeddings(self):
        texts = ["To jest przykładowy tekst", "To jest drugi tekst"]
        embeddings = self.agent._create_embeddings(texts)
        self.assertEqual(len(embeddings), len(texts))
        self.assertTrue(all(isinstance(emb, list) for emb in embeddings))
        
    def test_process(self):
        result = self.agent.process()
        self.assertIn('text', result)
        self.assertIn('images', result)
        self.assertIn('audio', result)
        self.assertTrue((self.processed_dir / "processed_data.json").exists())

if __name__ == '__main__':
    unittest.main() 