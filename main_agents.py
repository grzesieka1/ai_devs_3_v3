import os
import importlib
import re
import sys

print(f"Używany interpreter Python: {sys.executable}")

def get_available_tasks():
    """Znajduje wszystkie dostępne zadania w katalogu tasks"""
    tasks = []
    tasks_dir = 'tasks'
    
    for filename in os.listdir(tasks_dir):
        if filename.startswith('task') and filename.endswith('.py'):
            match = re.match(r'task(S\d+E\d+)\.py', filename)
            if match:
                task_id = match.group(1)
                module_name = filename[:-3]
                
                try:
                    module = importlib.import_module(f'tasks.{module_name}')
                    description = module.__doc__.strip() if module.__doc__ else "Brak opisu"
                    
                    tasks.append({
                        'id': task_id,
                        'description': description,
                        'module': module_name
                    })
                except ImportError as e:
                    print(f"Nie można załadować modułu {module_name}: {e}")
    
    return sorted(tasks, key=lambda x: x['id'])

def display_tasks(tasks):
    """Wyświetla listę dostępnych zadań"""
    print("\nDostępne zadania (wersja z agentami):")
    print("-" * 50)
    for i, task in enumerate(tasks, 1):
        print(f"{i}. --{task['id']}-- {task['description']}")
    print("-" * 50)

def main():
    tasks = get_available_tasks()
    
    while True:
        display_tasks(tasks)
        choice = input("\nWybierz numer zadania (q aby wyjść): ").strip()
        
        if choice.lower() == 'q':
            print("Do widzenia!")
            break
            
        try:
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(tasks):
                task = tasks[choice_idx]
                print(f"\nUruchamiam zadanie {task['id']} z wykorzystaniem agentów...")
                try:
                    module = importlib.import_module(f"tasks.{task['module']}")
                    if hasattr(module, 'initialize_agents'):
                        module.initialize_agents()
                    module.solve_task()
                except Exception as e:
                    print(f"Błąd podczas wykonywania zadania: {e}")
                    import traceback
                    print(traceback.format_exc())
            else:
                print(f"\nNieznane zadanie: {choice}")
        except ValueError:
            print(f"\nNieprawidłowy wybór: {choice}")

if __name__ == "__main__":
    main() 