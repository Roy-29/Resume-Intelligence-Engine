"""
Fine-tuning Script for Sentence-BERT (all-MiniLM-L6-v2)
=====================================================
This script allows you to specialize the semantic matching model 
on your specific resume and job description pairs.
"""
import os
import torch
from sentence_transformers import SentenceTransformer, InputExample, losses
from torch.utils.data import DataLoader

# 1. Initialize the base model
print("Loading base model: all-MiniLM-L6-v2...")
model = SentenceTransformer('all-MiniLM-L6-v2')

# 2. Define your training data
# Labels: 1.0 = Perfect Match, 0.0 = Totally Irrelevant
training_examples = [
    InputExample(
        texts=["Expert in React, Node.js, and Cloud Architecture with 5 years exp.", 
               "Looking for a Senior Fullstack Engineer with React and Node experience."], 
        label=0.95
    ),
    InputExample(
        texts=["Professional accountant with CPA and 10 years in tax auditing.", 
               "Hiring a Tax Manager for a large corporate accounting firm."], 
        label=0.9
    ),
    InputExample(
        texts=["Recent graduate with a degree in Marketing and social media internship.", 
               "Entry-level Social Media Coordinator to manage Instagram and Twitter."], 
        label=0.85
    ),
    InputExample(
        texts=["Data Scientist specializing in Python, PyTorch, and Computer Vision.", 
               "Senior Software Engineer specializing in Java and Spring Boot."], 
        label=0.2  # Unrelated pair
    ),
    # TODO: Add more resume/job pairs here from your historical database!
]

# 3. Create a DataLoader
train_dataloader = DataLoader(training_examples, shuffle=True, batch_size=16)

# 4. Choose a loss function (CosineSimilarityLoss is standard for matching)
train_loss = losses.CosineSimilarityLoss(model=model)

# 5. Fine-tune the model
print("Starting fine-tuning...")
model.fit(
    train_objectives=[(train_dataloader, train_loss)],
    epochs=1,  # Start with 1-3 epochs to avoid overfitting on small data
    warmup_steps=100,
    output_path='./ml_models/fine_tuned_bert'
)

print("\nSuccess! The fine-tuned model is saved at: ./ml_models/fine_tuned_bert")
print("To use this model in the project, update 'ai_core/matching.py' to load this path.")
