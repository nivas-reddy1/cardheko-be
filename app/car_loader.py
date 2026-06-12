import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
file_path = os.path.join(BASE_DIR, "data", "cars.json")

with open(file_path, "r", encoding="utf-8") as f:
    CAR_DATASET = json.load(f)