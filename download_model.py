from transformers import AutoTokenizer, AutoModelForSequenceClassification
import os

MODEL_NAME = "google-bert/bert-base-uncased"
SAVE_PATH = "models/genre_model"

def download_and_save():
    print(f"Starting download of {MODEL_NAME}...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, use_fast=False)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
    
    if not os.path.exists(SAVE_PATH):
        os.makedirs(SAVE_PATH)
        
    tokenizer.save_pretrained(SAVE_PATH)
    model.save_pretrained(SAVE_PATH)
    print(f"Model saved successfully to {SAVE_PATH}")

if __name__ == "__main__":
    download_and_save()
