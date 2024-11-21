"""Zadanie: Analiza publikacji profesora Maja i odpowiedzi na pytania centrali"""

from agents.collector_agent import CollectorAgent
from agents.processor_agent import ProcessorAgent
from agents.responder_agent import ResponderAgent
import json
from pathlib import Path
import requests
import os
from dotenv import load_dotenv
import logging

# Na początku pliku, zaraz po importach
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_collector():
    """Uruchamia CollectorAgent do pobrania danych"""
    print("\n1️⃣ Uruchamiam CollectorAgent...")
    collector = CollectorAgent()
    try:
        result = collector.process()
        print("✅ Pobrano dane:")
        print(f"- Artykuł: {len(result['article']['text'])} znaków")
        print(f"- Obrazy: {len(result['article']['images'])}")
        print(f"- Audio: {len(result['article']['audio'])}")
        print(f"- Pytania: {len(result['questions'])}")
        return result
    except Exception as e:
        print(f"❌ Błąd podczas pobierania danych: {e}")
        return None

def run_processor():
    """Uruchamia ProcessorAgent do przetworzenia danych"""
    print("\n2️⃣ Uruchamiam ProcessorAgent...")
    processor = ProcessorAgent()
    try:
        result = processor.process()
        print("✅ Przetworzono dane:")
        print(f"- Fragmenty tekstu: {len(result['text']['chunks'])}")
        if 'images' in result:
            print(f"- Opisy obrazów: {len(result['images']['descriptions'])}")
        if 'audio' in result:
            print(f"- Transkrypcje audio: {len(result['audio']['transcripts'])}")
        return result
    except Exception as e:
        print(f"❌ Błąd podczas przetwarzania danych: {e}")
        return None

def run_responder():
    """Uruchamia ResponderAgent do generowania odpowiedzi"""
    print("\n3️⃣ Uruchamiam ResponderAgent...")
    responder = ResponderAgent()
    try:
        answers = responder.process()
        print("✅ Wygenerowano odpowiedzi:")
        print(f"- Liczba odpowiedzi: {len(answers)}")
        return answers
    except Exception as e:
        print(f"❌ Błąd podczas generowania odpowiedzi: {e}")
        return None

def save_answers(answers):
    """Zapisuje końcowe odpowiedzi do pliku"""
    if not answers:
        return False
        
    try:
        output_dir = Path("data/output")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / "final_answers.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(answers, f, ensure_ascii=False, indent=2)
            
        print(f"\n💾 Zapisano odpowiedzi do: {output_file}")
        return True
    except Exception as e:
        print(f"❌ Błąd podczas zapisywania odpowiedzi: {e}")
        return False

def send_answers_to_api(answers):
    """Wysyła odpowiedzi do API centrali"""
    try:
        api_key = os.getenv('AGENTS_API_KEY')
        if not api_key:
            print("❌ Nie znaleziono klucza API")
            return False
            
        # Debugowanie - sprawdź co wysyłamy
        print(f"\n🔍 Wysyłane odpowiedzi: {answers}")
        
        formatted_answers = {}
        for key, value in answers.items():
            question_id = key.split('-')[-1]  # Tu może być problem
            formatted_answers[question_id] = value
            
        data = {
            "answer": formatted_answers,
            "task": "arxiv",
            "apikey": api_key
        }
        
        # Debugowanie - sprawdź końcowy format
        print(f"\n🔍 Wysyłane dane: {data}")
        
        print("\n📤 Wysyłam odpowiedzi do centrali...")
        response = requests.post(
            'https://centrala.ag3nts.org/report',
            json=data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code != 200:
            print(f"❌ Błąd HTTP: {response.status_code}")
            print(f"Odpowiedź API: {response.text}")
            return False
            
        result = response.json()
        print(f"✅ Odpowiedź centrali: {result}")
        return True
        
    except Exception as e:
        print(f"❌ Błąd podczas wysyłania odpowiedzi: {str(e)}")
        if 'response' in locals():
            print(f"Odpowiedź API: {response.text}")
        return False

def solve_task():
    """Główna funkcja rozwiązująca zadanie"""
    print("\n🚀 Rozpoczynam rozwiązywanie zadania S02E05...")
    
    # 1. Pobierz dane
    collector_result = run_collector()
    if not collector_result:
        print("❌ Przerwano wykonywanie - błąd w CollectorAgent")
        return False
        
    # 2. Przetwórz dane
    processor_result = run_processor()
    if not processor_result:
        print("❌ Przerwano wykonywanie - błąd w ProcessorAgent")
        return False
        
    # 3. Wygeneruj odpowiedzi
    answers = run_responder()
    if not answers:
        print("❌ Przerwano wykonywanie - błąd w ResponderAgent")
        return False
        
    # 4. Zapisz wyniki lokalnie
    if not save_answers(answers):
        print("\n❌ Wystąpił błąd podczas zapisywania odpowiedzi")
        return False
        
    # 5. Wyślij odpowiedzi do centrali
    if send_answers_to_api(answers):
        print("\n✨ Zadanie wykonane pomyślnie!")
        print("📝 Sprawdź wygenerowane odpowiedzi w pliku: data/output/final_answers.json")
        return True
    else:
        print("\n❌ Wystąpił błąd podczas wysyłania odpowiedzi do centrali")
        return False

if __name__ == "__main__":
    solve_task()