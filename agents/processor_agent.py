import os
from pathlib import Path
import json
from .base_agent import BaseAgent

class ProcessorAgent(BaseAgent):
    """Agent odpowiedzialny za przetwarzanie danych i tworzenie bazy wiedzy."""
    
    def __init__(self):
        super().__init__(name="ProcessorAgent")
        self.data_dir = Path("data/content")
        self.processed_dir = Path("data/processed")
        self.downloads_dir = Path("data/downloads")
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
    def process(self, data=None):
        """Główna metoda przetwarzająca dane."""
        try:
            self.log_info("Sprawdzam istniejące przetworzone dane...")
            
            # Sprawdź czy istnieją przetworzone dane
            if self._check_existing_processed_data():
                user_input = input("Znaleziono przetworzone dane. Chcesz je przetworzyć ponownie? (t/n): ")
                if user_input.lower() != 't':
                    self.log_info("Używam istniejących przetworzonych danych")
                    return self._load_processed_data()
            
            self.log_info("Rozpoczynam przetwarzanie danych...")
            
            # Wczytaj zebrane dane
            raw_data = self._load_raw_data()
            processed_data = {'text': {}, 'images': {}, 'audio': {}}
            
            # Przetwarzanie tekstu
            text_input = input("Czy chcesz przetworzyć tekst artykułu? (t/n): ")
            if text_input.lower() == 't':
                self.log_info("Przetwarzam tekst artykułu...")
                text_chunks = self._process_text(raw_data['text'])
                embeddings_input = input("Czy chcesz utworzyć embeddingi dla tekstu? (t/n): ")
                if embeddings_input.lower() == 't':
                    text_embeddings = self._create_embeddings([chunk for chunk in text_chunks])
                    self.log_info(f"Utworzono {len(text_embeddings)} embeddingów tekstu")
                    processed_data['text'] = {
                        'chunks': text_chunks,
                        'embeddings': text_embeddings
                    }
                else:
                    processed_data['text'] = {
                        'chunks': text_chunks,
                        'embeddings': []
                    }
            
            # Przetwarzanie obrazów
            images_input = input("Czy chcesz przetworzyć obrazy? (t/n): ")
            if images_input.lower() == 't':
                self.log_info("Przetwarzam obrazy...")
                images_result = self._process_images(raw_data['images'])
                embeddings_input = input("Czy chcesz utworzyć embeddingi dla opisów obrazów? (t/n): ")
                if embeddings_input.lower() == 't':
                    processed_data['images'] = images_result
                else:
                    processed_data['images'] = {
                        'descriptions': images_result['descriptions'],
                        'embeddings': []
                    }
            
            # Przetwarzanie audio
            audio_input = input("Czy chcesz przetworzyć pliki audio? (t/n): ")
            if audio_input.lower() == 't':
                self.log_info("Przetwarzam pliki audio...")
                audio_transcripts = self._process_audio(raw_data['audio'])
                embeddings_input = input("Czy chcesz utworzyć embeddingi dla transkrypcji audio? (t/n): ")
                if embeddings_input.lower() == 't':
                    audio_embeddings = self._create_embeddings([t['transcript'] for t in audio_transcripts])
                    processed_data['audio'] = {
                        'transcripts': audio_transcripts,
                        'embeddings': audio_embeddings
                    }
                else:
                    processed_data['audio'] = {
                        'transcripts': audio_transcripts,
                        'embeddings': []
                    }
            
            # Zapisz przetworzone dane
            self._save_processed_data(processed_data)
            
            return processed_data
            
        except Exception as e:
            import traceback
            self.log_error(f"Błąd podczas przetwarzania danych: {str(e)}")
            self.log_error(f"Traceback: {traceback.format_exc()}")
            self.handle_error(e, "Błąd podczas przetwarzania danych")
    
    def _load_raw_data(self):
        """Wczytuje surowe dane z plików."""
        try:
            with open(self.data_dir / "article.txt", "r", encoding="utf-8") as f:
                text = f.read()
                
            with open(self.data_dir / "article.html", "r", encoding="utf-8") as f:
                html = f.read()
                
            return {
                'text': text,
                'html': html,
                'images': self._get_image_paths(),
                'audio': self._get_audio_paths()
            }
        except Exception as e:
            self.handle_error(e, "Błąd podczas wczytywania danych")
    
    def _process_text(self, text, chunk_size=1000):
        """Dzieli tekst na mniejsze fragmenty do analizy."""
        self.log_info("Przetwarzam tekst...")
        chunks = []
        current_chunk = ""
        current_length = 0
        
        # Dzielimy tekst na zdania (prosta implementacja)
        sentences = text.replace(".", ". ").replace("!", "! ").replace("?", "? ").split()
        
        for word in sentences:
            # Sprawdź, czy dodanie nowego słowa nie przekroczy limitu
            if current_length + len(word) + 1 > chunk_size:
                if current_chunk:  # Zapisz aktualny fragment
                    chunks.append(current_chunk.strip())
                current_chunk = word
                current_length = len(word)
            else:
                current_chunk = current_chunk + " " + word if current_chunk else word
                current_length += len(word) + 1
        
        # Dodaj ostatni fragment jeśli istnieje
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        # Dodatkowe sprawdzenie długości
        chunks = [chunk[:chunk_size] for chunk in chunks]
        
        return chunks
    
    def _process_images(self, image_paths):
        """Analizuje obrazy używając modelu wizyjnego."""
        self.log_info("Przetwarzam obrazy...")
        descriptions = []
        embeddings = []
        
        for image_path in image_paths:
            try:
                # Konwertuj ścieżkę na string
                image_path_str = str(image_path)
                image_filename = Path(image_path_str).name
                
                # Wczytaj oryginalny opis z pliku txt
                desc_path = self.downloads_dir / "images" / f"{image_filename}_description.txt"
                original_description = ""
                if desc_path.exists():
                    with open(desc_path, "r", encoding="utf-8") as f:
                        original_description = f.read().strip()
                
                # Wczytaj obraz jako base64
                with open(image_path, "rb") as image_file:
                    import base64
                    image_data = base64.b64encode(image_file.read()).decode('utf-8')
                    # Format wymagany przez API
                    image_url = f"data:image/jpeg;base64,{image_data}"
                
                # Przygotuj prompt z kontekstem
                prompt = f"""Przeanalizuj dokładnie to zdjęcie w kontekście eksperymentów z podróżą w czasie i transportem materii.
                
                Oryginalny opis tego zdjęcia to: {original_description}
                
                Opisz szczegółowo co widzisz na zdjęciu, zwracając szczególną uwagę na:
                1. czy widać owoc lub jedzenie
                2. czy widać fragmenty miasta? jakie to może być miasto?
                3. sprawdaj co widzisz na zdjęciu z oryginalnym opisem
                4. opisz kroki step by step swojego rozumowania"""
                
                # Wywołaj model GPT-4 Vision
                response = self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": image_url
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=300
                )
                
                enhanced_description = response.choices[0].message.content.strip()
                self.log_info(f"Wygenerowano rozszerzony opis: {enhanced_description}")
                
                # Dodaj do listy opisów
                descriptions.append({
                    "file": image_path_str,
                    "original_description": original_description,
                    "description": enhanced_description
                })
                
                # Twórz embedding dla rozszerzonego opisu
                if enhanced_description:
                    self.log_info("Tworzę embeddingi...")
                    embedding = self._create_embeddings([enhanced_description])[0]
                    embeddings.append(embedding)
                
                self.log_info(f"Wygenerowano opis dla: {image_path_str}")
                
            except Exception as e:
                import traceback
                self.log_error(f"Błąd podczas przetwarzania obrazu: {str(e)}")
                self.log_error(f"Traceback: {traceback.format_exc()}")
                self.handle_error(e, f"Błąd podczas przetwarzania obrazu: {image_path_str}")
                
        return {
            "descriptions": descriptions,
            "embeddings": embeddings
        }
    
    def _process_audio(self, audio_paths):
        """Transkrybuje pliki audio."""
        self.log_info("Przetwarzam pliki audio...")
        transcripts = []
        
        audio_model = os.getenv('AUDIO_MODEL')
        if not audio_model:
            self.handle_error(Exception("Brak zdefiniowanego AUDIO_MODEL w .env"))
            return []
        
        for audio_path in audio_paths:
            try:
                if not Path(audio_path).exists():
                    self.log_info(f"Pominięto nieistniejący plik: {audio_path}")
                    continue
                
                self.log_info(f"Transkrybuję plik: {audio_path}")
                
                with open(audio_path, "rb") as audio_file:
                    response = self.client.audio.transcriptions.create(
                        model=audio_model,
                        file=audio_file,
                        response_format="text"
                    )
                
                transcripts.append({
                    "file": str(audio_path),
                    "transcript": response
                })
                
                self.log_info(f"Wygenerowano transkrypcję dla: {audio_path}")
                
            except Exception as e:
                self.handle_error(e, f"Błąd podczas transkrypcji pliku: {audio_path}")
        
        return transcripts
    
    def _save_processed_data(self, data):
        """Zapisuje przetworzone dane."""
        try:
            self.log_info("Rozpoczynam zapisywanie danych...")
            
            # Przygotuj dane do zapisu (bez embeddingów)
            save_data = {
                'text': {
                    'chunks': data['text']['chunks']
                },
                'images': {
                    'descriptions': [item['description'] for item in data['images']['descriptions']]
                },
                'audio': {
                    'transcripts': [item['transcript'] for item in data['audio']['transcripts']]
                }
            }
            
            self.log_info("Struktura save_data:")
            self.log_info(f"- text: {list(save_data['text'].keys())}")
            self.log_info(f"- images: {list(save_data['images'].keys())}")
            self.log_info(f"- audio: {list(save_data['audio'].keys())}")
            
            # Zapisz główne dane
            with open(self.processed_dir / "processed_data.json", "w", encoding="utf-8") as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            self.log_info("Zapisano przetworzone dane")
            
            # Zapisz embeddingi osobno
            embeddings_data = {
                'text_embeddings': data['text']['embeddings'],
                'image_embeddings': data['images']['embeddings'],
                'audio_embeddings': self._create_embeddings([t['transcript'] for t in data['audio']['transcripts']])
            }
            
            self.log_info("Struktura embeddings_data:")
            self.log_info(f"- text_embeddings: {len(embeddings_data['text_embeddings'])}")
            self.log_info(f"- image_embeddings: {len(embeddings_data['image_embeddings'])}")
            self.log_info(f"- audio_embeddings: {len(embeddings_data['audio_embeddings'])}")
            
            with open(self.processed_dir / "embeddings.json", "w", encoding="utf-8") as f:
                json.dump(embeddings_data, f)
            self.log_info("Zapisano embeddingi")
            
        except Exception as e:
            import traceback
            self.log_error(f"Błąd podczas zapisywania danych: {str(e)}")
            self.log_error(f"Traceback: {traceback.format_exc()}")
            self.handle_error(e, "Błąd podczas zapisywania przetworzonych danych")
    
    def _get_image_paths(self):
        """Zwraca ścieżki do obrazów."""
        downloads_dir = Path("data/downloads/images")
        return list(downloads_dir.glob("*.png")) + list(downloads_dir.glob("*.jpg"))
    
    def _get_audio_paths(self):
        """Zwraca ścieżki do plików audio."""
        downloads_dir = Path("data/downloads/audio")
        return list(downloads_dir.glob("*.mp3"))
    
    def _load_questions(self):
        """Wczytuje pytania z pliku."""
        questions_path = self.downloads_dir / "text" / "questions.txt"
        try:
            with open(questions_path, "r", encoding="utf-8") as f:
                return [line.strip() for line in f if line.strip()]
        except Exception as e:
            self.handle_error(e, f"Błąd podczas wczytywania pytań z {questions_path}") 
    
    def _check_existing_processed_data(self):
        """Sprawdza czy istnieją przetworzone dane."""
        required_files = [
            self.processed_dir / "processed_data.json",
            self.processed_dir / "embeddings.json"
        ]
        return all(f.exists() for f in required_files)
    
    def _load_processed_data(self):
        """Wczytuje istniejące przetworzone dane."""
        try:
            with open(self.processed_dir / "processed_data.json", "r", encoding="utf-8") as f:
                processed_data = json.load(f)
            with open(self.processed_dir / "embeddings.json", "r", encoding="utf-8") as f:
                embeddings = json.load(f)
                
            # Połącz dane z embeddingami w odpowiedniej strukturze
            return {
                'text': {
                    'chunks': processed_data['text']['chunks'],
                    'embeddings': embeddings['text_embeddings']
                },
                'images': {
                    'descriptions': processed_data['images']['descriptions'],
                    'embeddings': embeddings['image_embeddings']
                },
                'audio': {
                    'transcripts': processed_data['audio']['transcripts'],
                    'embeddings': embeddings['audio_embeddings']
                }
            }
            
        except Exception as e:
            self.handle_error(e, "Błąd podczas wczytywania przetworzonych danych") 