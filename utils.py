# utils.py
import os
import yaml
import json
import csv
from datetime import datetime


def load_prompt(filename):
    """Load a prompt from a YAML file."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    prompt_path = os.path.join(script_dir, "prompts", filename)

    try:
        with open(prompt_path, "r", encoding="utf-8") as file:
            prompt_data = yaml.safe_load(file)
            return prompt_data.get("instructions", "")
    except (FileNotFoundError, yaml.YAMLError) as e:
        print(f"Error loading prompt file {filename}: {e}")
        return ""


def get_history_path():
    """Get file path for chat history data (single user assumed)."""
    base_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "data", "history"
    )
    os.makedirs(base_dir, exist_ok=True)
    return os.path.join(base_dir, "history.json")


def load_previous_history(context=None):
    """Load summary JSON (single user)."""
    path = get_history_path()
    if not os.path.exists(path):
        return "There is no previous conversation data."

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return "Failed to load previous conversation data."


def save_history(context, summary: dict):
    """Save summary JSON (single user)."""
    path = get_history_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving chat history: {e}")


def append_request_log(detail: str):
    """Append a request entry to CSV."""
    base_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "data", "requests"
    )
    os.makedirs(base_dir, exist_ok=True)
    csv_path = os.path.join(base_dir, "requests.csv")

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        write_header = not os.path.exists(csv_path)
        with open(csv_path, "a", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            if write_header:
                writer.writerow(["timestamp", "detail"])
            writer.writerow([now, detail])
    except Exception as e:
        print(f"Error writing request log: {e}")
