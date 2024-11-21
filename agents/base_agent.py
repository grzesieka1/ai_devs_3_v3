from abc import ABC, abstractmethod
import os
import logging
from dotenv import load_dotenv
from openai import OpenAI

class BaseAgent(ABC):
    """Bazowa klasa dla wszystkich agentów w systemie."""
    
    def __init__(self, name="BaseAgent"):
        """Inicjalizacja agenta.
        
        Args:
            name (str): Nazwa agenta do logowania
        """
        # Konfiguracja podstawowa
        load_dotenv()
        self.name = name
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Konfiguracja loggera
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def _create_embeddings(self, texts):
        """Tworzy embeddingi dla tekstów."""
        self.log_info("Tworzę embeddingi...")
        embeddings = []
        
        for text in texts:
            try:
                response = self.client.embeddings.create(
                    model=os.getenv('EMBEDDING_MODEL'),
                    input=text
                )
                embeddings.append(response.data[0].embedding)
            except Exception as e:
                self.handle_error(e, f"Błąd podczas tworzenia embeddingu")
                
        return embeddings
    
    @abstractmethod
    def process(self, data):
        """Abstrakcyjna metoda do przetwarzania danych.
        
        Args:
            data: Dane wejściowe do przetworzenia
            
        Returns:
            Przetworzone dane
        """
        pass
    
    def handle_error(self, error, context=""):
        """Obsługa błędów z logowaniem.
        
        Args:
            error: Wystąpiony błąd
            context (str): Kontekst wystąpienia błędu
        """
        error_msg = f"{context}: {str(error)}" if context else str(error)
        self.logger.error(error_msg)
        raise Exception(f"{self.name} error: {error_msg}")
    
    def log_info(self, message):
        """Logowanie informacji.
        
        Args:
            message (str): Wiadomość do zalogowania
        """
        self.logger.info(message)
    
    def log_error(self, message):
        """Logowanie błędów.
        
        Args:
            message (str): Wiadomość do zalogowania
        """
        self.logger.error(message)