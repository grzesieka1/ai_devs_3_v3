class TaskS02E04:
    """Zadanie: Analiza plików z fabryki i kategoryzacja według zawartości"""
    
    def __init__(self):
        self.collector = CollectorAgent()
        self.processor = ProcessorAgent()
        self.categorizer = CategorizerAgent()  # Nowy agent do kategoryzacji
        
    def solve_task(self):
        try:
            # 1. Pobieranie danych
            self.log_info("1️⃣ Uruchamiam CollectorAgent...")
            collector_result = self._run_collector()
            
            # 2. Przetwarzanie plików
            self.log_info("2️⃣ Uruchamiam ProcessorAgent...")
            processed_data = self._run_processor(collector_result)
            
            # 3. Kategoryzacja
            self.log_info("3️⃣ Uruchamiam CategorizerAgent...")
            categories = self._run_categorizer(processed_data)
            
            # 4. Wysłanie odpowiedzi
            response = {
                "people": sorted(categories.get("people", [])),
                "hardware": sorted(categories.get("hardware", []))
            }
            
            return self._send_answer(response)
            
        except Exception as e:
            self.handle_error(e, "Błąd podczas rozwiązywania zadania") 