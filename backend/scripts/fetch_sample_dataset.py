import os
import requests
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
DATA_DIR.mkdir(parents=True, exist_ok=True)

def fetch_sample_dataset(url: str = "https://raw.githubusercontent.com/jbrownlee/Datasets/master/daily-min-temperatures.csv",
                       filename: str = "sample_temperature.csv") -> Path:
    """Download a public CSV dataset and store it under `data/raw/`.

    Returns the absolute path of the saved file.
    """
    target_path = DATA_DIR / filename
    # Simple GET request – raise for HTTP errors.
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    with open(target_path, "wb") as f:
        f.write(response.content)
    return target_path

if __name__ == "__main__":
    path = fetch_sample_dataset()
    print(f"Dataset saved to {path}")
