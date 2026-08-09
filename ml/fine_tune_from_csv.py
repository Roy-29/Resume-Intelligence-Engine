import os
import pandas as pd
import torch
from sentence_transformers import SentenceTransformer, InputExample, losses
from torch.utils.data import DataLoader

def fine_tune_bert_from_csv():
    """
    Fine-tuning Script for Sentence-BERT (all-MiniLM-L6-v2) 
    using a custom CSV dataset downloaded from Kaggle/HuggingFace.
    """
    print("Loading base model: all-MiniLM-L6-v2...")
    model = SentenceTransformer('all-MiniLM-L6-v2')

    # 1. Load your dataset
    # We assume you downloaded a CSV file with these columns:
    # ['resume_text', 'job_description', 'score'] (where score is 0.0 to 1.0)
    csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'ml_models', 'training_data', 'sbert_training_pairs.csv')
    
    if not os.path.exists(csv_path):
        print(f"Error: Dataset not found at {csv_path}")
        print("Please run ml/download_dataset.py first, or place your Kaggle CSV there.")
        return

    print(f"Loading dataset from: {csv_path}")
    df = pd.read_csv(csv_path)

    # 2. Convert rows into SBERT InputExamples
    training_examples = []
    
    # We take the first 1000 rows just for speed in this example
    for index, row in df.head(1000).iterrows():
        try:
            # SBERT needs text pairs (resume vs job) and a float label (0.0 to 1.0)
            resume_text = str(row['resume_text'])
            job_desc = str(row['job_description'])
            match_score = float(row['score']) 
            
            example = InputExample(texts=[resume_text, job_desc], label=match_score)
            training_examples.append(example)
        except KeyError:
            print("Error: Your CSV must have columns named 'resume_text', 'job_description', and 'score'")
            return
        except Exception as e:
            continue # Skip bad rows

    print(f"Loaded {len(training_examples)} valid training examples.")

    # 3. Create DataLoader and Loss Function
    train_dataloader = DataLoader(training_examples, shuffle=True, batch_size=16)
    train_loss = losses.CosineSimilarityLoss(model=model)

    # 4. Fine-Tune
    output_model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'ml_models', 'fine_tuned_bert')
    os.makedirs(output_model_path, exist_ok=True)
    
    print("Starting fine-tuning sequence (this will take time)...")
    model.fit(
        train_objectives=[(train_dataloader, train_loss)],
        epochs=1,  # 1-3 epochs is usually enough
        warmup_steps=100,
        output_path=output_model_path
    )

    print(f"\nTraining Complete! Model saved to: {output_model_path}")
    print("Update 'ai_core/matching.py' to use this new local path!")

if __name__ == "__main__":
    fine_tune_bert_from_csv()
