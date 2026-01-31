import json
import os

def load_schema(filename="schema.json"):
    """
    Loads a JSON schema file from the same directory as this script.
    Returns the dict or None if file is missing/invalid.
    """
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
        file_path = os.path.join(base_dir, filename)
        
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
            
    except FileNotFoundError:
        print(f"Warning: Could not find '{filename}' at {file_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error: '{filename}' contains invalid JSON. \nDetails: {e}")
        return None