import requests
from bs4 import BeautifulSoup
from pathlib import Path
from .base_agent import BaseAgent
import os

class CollectorAgent(BaseAgent):
    """Agent odpowiedzialny za pobieranie danych z API."""
    
    def __init__(self):
        super().__init__(name="CollectorAgent")
        self.data_dir = Path("data/content")
        self.downloads_dir = Path("data/downloads")
        
        # Utwórz strukturę katalogów
        for dir_name in ["images", "audio", "text"]:
            (self.downloads_dir / dir_name).mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
    def process(self):
        """Główna metoda przetwarzająca - pobiera i zapisuje dane."""
        self.log_info("Sprawdzam istniejące dane...")
        
        # Sprawdź czy dane już istnieją
        if self._check_existing_data():
            user_input = input("Znaleziono istniejące dane. Chcesz je nadpisać? (t/n): ")
            if user_input.lower() != 't':
                self.log_info("Używam istniejących danych")
                return self._load_existing_data()
        
        self.log_info("Rozpoczynam pobieranie danych...")
        
        # Pobierz klucz API ze zmiennych środowiskowych
        api_key = os.getenv('AGENTS_API_KEY')
        if not api_key:
            self.handle_error(Exception("Brak klucza API w zmiennych środowiskowych"))
            return None

        try:
            # Pobierz artykuł
            article_url = os.getenv('CENTRALA_URL') + os.getenv('PUBLIC_DATA_PATH') + '/arxiv-draft.html'
            self.log_info(f"Pobieram artykuł z: {article_url}")
            article_data = self.download_article(article_url)
            
            # Pobierz pytania
            questions_url = os.getenv('CENTRALA_URL') + os.getenv('DATA_API_KEY_PATH') + '/arxiv.txt'
            questions_url = questions_url.replace('AGENTS_API_KEY', api_key)
            self.log_info(f"Pobieram pytania z: {questions_url}")
            questions = self.download_questions(questions_url)
            
            # Zapisz dane
            result = self.save_raw_data({
                'article': article_data,
                'questions': questions
            })
            
            self.log_info(f"Zapisano {len(article_data['images'])} obrazów")
            for img_path in article_data['images']:
                self.log_info(f"- Obraz: {img_path}")
                
            self.log_info(f"Zapisano {len(article_data['audio'])} plików audio")
            for audio_path in article_data['audio']:
                self.log_info(f"- Audio: {audio_path}")
                
            self.log_info("Dane zostały zapisane w katalogu data/content/")
            return result
            
        except Exception as e:
            self.handle_error(e, "Błąd podczas pobierania danych")
            return None
    
    def download_article(self, url):
        """Pobiera artykuł z API."""
        self.log_info(f"Pobieram artykuł z: {url}")
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Pobierz tekst artykułu
            article_text = soup.get_text()  # lub inna metoda, aby wyodrębnić tekst
            
            # Zbieranie obrazów - dodaj PUBLIC_DATA_PATH do URLi
            images = []
            for img in soup.find_all('img'):
                if 'src' in img.attrs:
                    img_url = img['src']
                    if not img_url.startswith(('http://', 'https://')):
                        img_url = os.getenv('CENTRALA_URL') + os.getenv('PUBLIC_DATA_PATH') + '/' + img_url.lstrip('/')
                    
                    # Znajdź opis obrazu
                    img_description = ""
                    # Sprawdź czy jest podpis pod obrazem (zazwyczaj w elemencie figcaption)
                    if img.parent.find('figcaption'):
                        img_description = img.parent.find('figcaption').get_text().strip()
                    # Sprawdź czy jest opis w atrybucie alt
                    elif 'alt' in img.attrs:
                        img_description = img['alt'].strip()
                    
                    images.append({
                        'url': img_url,
                        'description': img_description
                    })
            
            # Zbieranie plików audio - dodaj PUBLIC_DATA_PATH do URLi
            audio = []
            # Szukamy elementów audio
            for a in soup.find_all('audio'):
                if 'src' in a.attrs:
                    audio_url = a['src']
                    if not audio_url.startswith(('http://', 'https://')):
                        audio_url = os.getenv('CENTRALA_URL') + os.getenv('PUBLIC_DATA_PATH') + '/' + audio_url.lstrip('/')
                    audio.append(audio_url)
                    
            # Szukamy linków do plików .mp3
            for a in soup.find_all('a'):
                if 'href' in a.attrs and a['href'].lower().endswith('.mp3'):
                    audio_url = a['href']
                    if not audio_url.startswith(('http://', 'https://')):
                        audio_url = os.getenv('CENTRALA_URL') + os.getenv('PUBLIC_DATA_PATH') + '/' + audio_url.lstrip('/')
                    audio.append(audio_url)
            
            return {
                'text': article_text,  # Upewnij się, że klucz 'text' jest obecny
                'html': response.text,
                'images': images,
                'audio': audio
            }
            
        except Exception as e:
            self.handle_error(e, "Błąd podczas pobierania artykułu")
            return None
    
    def download_questions(self, url):
        """Pobiera pytania z API.
        
        Returns:
            list: Lista pytań
        """
        self.log_info(f"Pobieram pytania z: {url}")
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.text.strip().split('\n')
            
        except Exception as e:
            self.handle_error(e, "Błąd podczas pobierania pytań")
    
    def save_raw_data(self, data):
        """Zapisuje pobrane dane do plików."""
        try:
            # Zapisz tekst artykułu
            with open(self.downloads_dir / "text" / "article.txt", "w", encoding="utf-8") as f:
                f.write(data['article']['text'])
            self.log_info("Zapisano tekst artykułu")
            
            # Zapisz HTML artykułu
            with open(self.downloads_dir / "text" / "article.html", "w", encoding="utf-8") as f:
                f.write(data['article']['html'])
            self.log_info("Zapisano HTML artykułu")
            
            # Zapisz pytania
            with open(self.downloads_dir / "text" / "questions.txt", "w", encoding="utf-8") as f:
                f.write("\n".join(data['questions']))
            self.log_info("Zapisano pytania")
            
            # Zapisz obrazy zachowując oryginalne nazwy
            for img_data in data['article']['images']:
                # Pobierz URL z nowej struktury danych
                img_url = img_data['url']
                img_filename = Path(img_url).name
                if not img_filename:
                    continue
                    
                # Dodaj bazowy URL jeśli brakuje
                if not img_url.startswith(('http://', 'https://')):
                    img_url = os.getenv('CENTRALA_URL') + '/' + img_url.lstrip('/')
                
                try:
                    self.log_info(f"Pobieram obraz: {img_url}")
                    img_path = self.downloads_dir / "images" / img_filename
                    response = requests.get(img_url)
                    response.raise_for_status()
                    with open(img_path, "wb") as f:
                        f.write(response.content)
                    self.log_info(f"Zapisano obraz: {img_path}")
                    
                    # Zapisz opis obrazu jeśli istnieje
                    if img_data['description']:
                        desc_path = self.downloads_dir / "images" / f"{img_filename}_description.txt"
                        with open(desc_path, "w", encoding="utf-8") as f:
                            f.write(img_data['description'])
                        self.log_info(f"Zapisano opis obrazu: {desc_path}")
                    
                except requests.exceptions.RequestException as e:
                    self.log_info(f"Nie udało się pobrać obrazu {img_url}: {e}")
                    continue
            
            return data
            
        except Exception as e:
            self.handle_error(e, "Błąd podczas zapisywania danych")
            return None 
    
    def _check_existing_data(self):
        """Sprawdza czy istnieją już pobrane dane."""
        required_files = [
            self.downloads_dir / "text" / "article.txt",
            self.downloads_dir / "text" / "article.html",
            self.downloads_dir / "text" / "questions.txt"
        ]
        return all(f.exists() for f in required_files)
    
    def _load_existing_data(self):
        """Wczytuje istniejące dane."""
        try:
            with open(self.downloads_dir / "text" / "article.txt", "r", encoding="utf-8") as f:
                text = f.read()
            with open(self.downloads_dir / "text" / "article.html", "r", encoding="utf-8") as f:
                html = f.read()
            with open(self.downloads_dir / "text" / "questions.txt", "r", encoding="utf-8") as f:
                questions = f.read().strip().split('\n')
            
            return {
                'article': {
                    'text': text,
                    'html': html,
                    'images': list(self.downloads_dir.glob("images/*")),
                    'audio': list(self.downloads_dir.glob("audio/*"))
                },
                'questions': questions
            }
        except Exception as e:
            self.handle_error(e, "Błąd podczas wczytywania istniejących danych")