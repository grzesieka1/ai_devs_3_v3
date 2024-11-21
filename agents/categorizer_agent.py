class CategorizerAgent(BaseAgent):
    """Agent odpowiedzialny za kategoryzację plików według zawartości."""
    
    def __init__(self):
        super().__init__(name="CategorizerAgent")
        
    def process(self, data):
        """Kategoryzuje pliki na podstawie ich zawartości."""
        try:
            categories = {
                "people": [],
                "hardware": []
            }
            
            for file_data in data:
                file_name = file_data["name"]
                content = file_data["content"]
                
                # Pomiń pliki z katalogu facts
                if "facts" in file_name.lower():
                    continue
                
                # Przygotuj prompt dla kategoryzacji
                prompt = f"""Przeanalizuj poniższą treść i określ, czy zawiera informacje o:
                1. Schwytanych ludziach lub śladach ich obecności
                2. Naprawionych usterkach sprzętowych (hardware)
                
                Ignoruj informacje o:
                - Usterkach software'owych
                - Innych tematach
                
                Treść: {content}
                
                Odpowiedz w formacie JSON:
                {{
                    "category": "people|hardware|none",
                    "reason": "krótkie uzasadnienie"
                }}
                """
                
                # Użyj LLM do kategoryzacji
                response = self._categorize_content(prompt)
                
                # Dodaj plik do odpowiedniej kategorii
                if response["category"] == "people":
                    categories["people"].append(file_name)
                elif response["category"] == "hardware":
                    categories["hardware"].append(file_name)
                
            return categories
            
        except Exception as e:
            self.handle_error(e, "Błąd podczas kategoryzacji") 