import os
import pandas as pd

def download_huggingface_dataset():
    """
    Downloads a popular resume-job matching dataset from HuggingFace
    and formats it for SBERT fine-tuning.
    """
    print("Initializing HuggingFace dataset download...")
    try:
        from datasets import load_dataset
    except ImportError:
        print("Error: The 'datasets' library is required.")
        print("Please run: pip install datasets")
        return

    # We use a public resume-to-job matching dataset
    # Dataset: jacob-hugging-face/job-descriptions (or similar SBERT training data)
    print("Downloading dataset (this may take a minute)...")
    
    try:
        # We use a public semantic similarity dataset (STSB from GLUE) as a proxy for resume-job matching.
        # This dataset teaches the model how to score semantic similarity.
        dataset = load_dataset("glue", "stsb", split="train[:1000]") 
        print(f"Successfully loaded {len(dataset)} examples.")
        
        # Create destination directory
        dest_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'ml_models', 'training_data')
        os.makedirs(dest_dir, exist_ok=True)
        csv_path = os.path.join(dest_dir, 'sbert_training_pairs.csv')

        # Convert to DataFrame
        df = pd.DataFrame(dataset)
        
        # NOTE: SBERT expects 3 columns: [text1, text2, label/score]
        # We rename the STSB columns to match what our script expects
        df = df.rename(columns={'sentence1': 'resume_text', 'sentence2': 'job_description', 'label': 'score'})
        
        # Normalize the GLUE STSB score (0.0 to 5.0) down to (0.0 to 1.0)
        df['score'] = df['score'] / 5.0
        
        df = df[['resume_text', 'job_description', 'score']]
        
        df.to_csv(csv_path, index=False)
        print(f"Dataset formatted and saved to: {csv_path}")
        print("You can now update 'ml/fine_tune_bert.py' to read from this CSV file!")

    except Exception as e:
        print(f"Failed to download dataset: {e}")

if __name__ == "__main__":
    download_huggingface_dataset()
