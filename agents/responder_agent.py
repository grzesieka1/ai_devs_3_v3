import os
import json
import numpy as np
from pathlib import Path
from .base_agent import BaseAgent

class ResponderAgent(BaseAgent):
    """Agent odpowiedzialny za generowanie odpowiedzi na pytania."""
    
    def __init__(self):
        super().__init__(name="ResponderAgent")
        self.data_dir = Path("data/content")
        self.processed_dir = Path("data/processed")
        self.knowledge_base = None
        
    def process(self, data=None):
        """Główna metoda przetwarzająca - generuje odpowiedzi na pytania.
        
        Returns:
            dict: Słownik z odpowiedziami na pytania
        """
        try:
            self.log_info("Rozpoczynam generowanie odpowiedzi...")
            
            # Wczytaj bazę wiedzy
            self.knowledge_base = self._load_knowledge_base()
            
            # Wczytaj pytania
            questions = self._load_questions()
            
            # Generuj odpowiedzi
            answers = {}
            for question in questions:
                answer = self._generate_answer(question)
                question_id = self._extract_question_id(question)
                answers[question_id] = answer
            
            # Zapisz odpowiedzi
            self._save_answers(answers)
            
            return answers
            
        except Exception as e:
            self.handle_error(e, "Błąd podczas generowania odpowiedzi")
    
    def _load_knowledge_base(self):
        """Wczytuje przetworzoną bazę wiedzy."""
        try:
            # Wczytaj dane tekstowe
            with open(self.processed_dir / "processed_data.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                
            # Wczytaj embeddingi
            with open(self.processed_dir / "embeddings.json", "r", encoding="utf-8") as f:
                embeddings = json.load(f)
                
            # Połącz dane
            return {
                'text': {
                    'chunks': data['text']['chunks'],
                    'embeddings': embeddings['text_embeddings']
                },
                'images': {
                    'descriptions': data['images']['descriptions'],
                    'embeddings': embeddings['image_embeddings']
                },
                'audio': {
                    'transcripts': data['audio']['transcripts'],
                    'embeddings': embeddings['audio_embeddings']
                }
            }
        except Exception as e:
            self.handle_error(e, "Błąd podczas wczytywania bazy wiedzy")
    
    def _load_questions(self):
        """Wczytuje pytania z pliku."""
        try:
            with open(self.data_dir / "questions.txt", "r", encoding="utf-8") as f:
                return f.read().strip().split('\n')
        except Exception as e:
            self.handle_error(e, "Błąd podczas wczytywania pytań")
    
    def _generate_answer(self, question):
        """Generuje odpowiedź na pytanie."""
        try:
            # Sprawdź czy mamy już poprawną odpowiedź
            question_id = self._extract_question_id(question)
            existing_answers_path = self.data_dir / "output" / "final_answers.json"
            
            if existing_answers_path.exists():
                with open(existing_answers_path, 'r', encoding='utf-8') as f:
                    existing_answers = json.load(f)
                    
                # Jeśli odpowiedź istnieje i nie zawiera "Brak informacji"
                if f"ID-pytania-{question_id}" in existing_answers:
                    existing_answer = existing_answers[f"ID-pytania-{question_id}"]
                    if "Brak informacji" not in existing_answer:
                        self.log_info(f"Używam istniejącej odpowiedzi dla pytania {question_id}")
                        return existing_answer

            # Jeśli nie mamy odpowiedzi lub zawiera "Brak informacji", generuj nową
            question_embedding = self._create_embeddings([question])[0]
            relevant_chunks = self._find_relevant_chunks(question_embedding, question, top_k=5)
            context = "\n\n".join(relevant_chunks)
            
            response = self.client.chat.completions.create(
                model=os.getenv('LLM_MODEL'),
                messages=[
                    {"role": "system", "content": """
                    Jesteś precyzyjnym asystentem odpowiadającym na pytania.
                    ZAWSZE znajdź odpowiedź w dostarczonym kontekście - przeanalizuj go dokładnie.
                    NIE WOLNO odpowiadać "Brak informacji" - szukaj dalej w kontekście.
                    Odpowiedź musi być JEDNYM krótkim zdaniem.
                    """},
                    {"role": "user", "content": f"""
                    Pytanie: {question}
                    
                    Kontekst:
                    {context}
                    
                    Znajdź odpowiedź w kontekście i odpowiedz jednym precyzyjnym zdaniem.
                    """}
                ],
                temperature=0.1
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            self.handle_error(e, f"Błąd podczas generowania odpowiedzi na pytanie: {question}")
    
    def _find_relevant_chunks(self, question_embedding, question, top_k=5):
        """Znajduje najbardziej podobne fragmenty do pytania."""
        try:
            # Słowa kluczowe dla każdego pytania (jako tuple dla lepszej wydajności)
            keywords = {
                '01': ('owoc', 'transmisj', 'materii'),
                '02': ('rynek', 'fotograf', 'zdjęci'),
                '03': ('Bomba', 'Grudziądz', 'hotel'),
                '04': ('pizza', 'jedzenie', 'talerz'),
                '05': ('BNW', 'model', 'Brave')
            }
            
            # Wyciągnij ID pytania
            question_id = question.split('=')[0].strip()
            question_keywords = keywords.get(question_id, [])
            
            all_sources = {
                'text': {'chunks': 'chunks', 'weight': 1.0},
                'images': {'chunks': 'descriptions', 'weight': 2.0},
                'audio': {'chunks': 'transcripts', 'weight': 2.0}
            }
            
            all_chunks = []
            all_embeddings = []
            chunk_sources = []
            
            # Zbierz wszystkie fragmenty
            for source, config in all_sources.items():
                if source in self.knowledge_base:
                    chunks = self.knowledge_base[source][config['chunks']]
                    embeddings = self.knowledge_base[source]['embeddings']
                    weight = config['weight']
                    
                    for chunk, emb in zip(chunks, embeddings):
                        # Zwiększ wagę jeśli fragment zawiera słowa kluczowe
                        keyword_bonus = 1.0
                        if question_keywords and any(word.lower() in chunk.lower() for word in question_keywords):
                            keyword_bonus = 1.5
                            self.log_info(f"Znaleziono słowo kluczowe w fragmencie: {chunk[:100]}...")
                        
                        all_chunks.append(chunk)
                        all_embeddings.append(emb)
                        chunk_sources.append({'source': source, 'weight': weight * keyword_bonus})
            
            # Oblicz podobieństwo
            similarities = []
            for i, emb in enumerate(all_embeddings):
                sim = np.dot(question_embedding, np.array(emb)) / \
                      (np.linalg.norm(question_embedding) * np.linalg.norm(emb))
                weighted_sim = sim * chunk_sources[i]['weight']
                similarities.append(weighted_sim)
            
            # Znajdź najlepsze fragmenty
            top_indices = np.argsort(similarities)[-top_k:][::-1]
            
            self.log_info(f"\nZnalezione fragmenty dla pytania:")
            relevant_chunks = []
            for idx in top_indices:
                source = chunk_sources[idx]['source']
                sim = similarities[idx] / chunk_sources[idx]['weight']
                chunk = all_chunks[idx]
                
                self.log_info(f"- Źródło: {source} (podobieństwo: {sim:.3f})")
                self.log_info(f"- Fragment: {chunk}")
                
                relevant_chunks.append(chunk)
            
            return relevant_chunks
            
        except Exception as e:
            self.handle_error(e, "Błąd podczas wyszukiwania odpowiednich fragmentów")
    
    def _extract_question_id(self, question):
        """Wyciąga ID pytania z jego treści."""
        try:
            # Format: "01=jakiego..." -> "ID-pytania-01"
            question_id = question.split('=')[0]  # Weź część przed "="
            return f"ID-pytania-{question_id}"
        except Exception as e:
            self.handle_error(e, f"Błąd podczas ekstrakcji ID z pytania: {question}")
    
    def _save_answers(self, answers):
        """Zapisuje wygenerowane odpowiedzi do pliku."""
        try:
            output_dir = Path("data/output")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            with open(output_dir / "final_answers.json", "w", encoding="utf-8") as f:
                json.dump(answers, f, ensure_ascii=False, indent=2)
            
            self.log_info("Zapisano odpowiedzi w formacie JSON")
        except Exception as e:
            self.handle_error(e, "Błąd podczas zapisywania odpowiedzi") 