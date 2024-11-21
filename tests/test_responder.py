import unittest
import sys
from pathlib import Path
import os
import json

# Dodaj ścieżkę główną projektu do sys.path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from agents.responder_agent import ResponderAgent

class TestResponderAgent(unittest.TestCase):
    def setUp(self):
        self.agent = ResponderAgent()
        self.data_dir = Path("data/content")
        self.processed_dir = Path("data/processed")
        
    def test_extract_question_id(self):
        question = "ID-pytania-01 Jaka jest główna teza artykułu?"
        question_id = self.agent._extract_question_id(question)
        self.assertEqual(question_id, "ID-pytania-01")
        
    def test_find_relevant_chunks(self):
        # Przygotuj testowe embeddingi
        self.agent.knowledge_base = {
            'text': {
                'chunks': ['Test chunk 1', 'Test chunk 2'],
                'embeddings': [[1.0, 0.0], [0.0, 1.0]]
            },
            'images': {'descriptions': [], 'embeddings': []},
            'audio': {'transcripts': [], 'embeddings': []}
        }
        
        question_embedding = [1.0, 0.0]
        chunks = self.agent._find_relevant_chunks(question_embedding)
        self.assertTrue(len(chunks) > 0)
        
    def test_process(self):
        result = self.agent.process()
        self.assertTrue(isinstance(result, dict))
        self.assertTrue(len(result) > 0)
        self.assertTrue((self.processed_dir / "answers.json").exists())

if __name__ == '__main__':
    unittest.main() 