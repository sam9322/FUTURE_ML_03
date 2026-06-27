import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import re

print(\)

# Load cleaned resumes
df = pd.read_csv('data/processed/resumes_cleaned.csv')
print(f\)
print(f\)

# Load sentence transformer model
print(\)
model = SentenceTransformer('all-MiniLM-L6-v2')
print(\)

# Test embedding dimension
test_embedding = model.encode([\

# Encode all resumes
print(\)


# Define test job descriptions
job_descriptions = {
    \: \\,
    ,
    ,
    ,
    ,
    ,
    ,
    \,
    
    \: \\,
    ,
    ,
    ,
    ,
    ,
    ,
    \,
    
    \: \\,
    ,
    ,
    ,
    ,
    ,
    ,
    \,
    
    \: \\,
    ,
    ,
    ,
    ,
    ,
    ,
    \
}

print(f\)
for title in job_descriptions.keys():
    print(f\)



# Define skill patterns and weights
SKILL_PATTERNS = {
    'python': r'\bpython\b',
    'machine learning': r'\b(machine learning|ml)\b',
    'tensorflow': r'\btensorflow\b',
    'pytorch': r'\bpytorch\b',
    'sql': r'\bsql\b',
    'data analysis': r'\bdata analysis\b',
    'excel': r'\bexcel\b',
    'tableau': r'\btableau\b',
    'aws': r'\baws\b',
    'docker': r'\bdocker\b',
    'kubernetes': r'\bkubernetes\b',
    'communication': r'\bcommunication\b',
    'leadership': r'\bleadership\b'
}

SKILL_WEIGHTS = {
    'python': 3,
    'machine learning': 3,
    'tensorflow': 3,
    'pytorch': 3,
    'sql': 2,
    'data analysis': 2,
    'tableau': 2,
    'aws': 2,
    'docker': 2,
    'kubernetes': 2,
    'excel': 1,
    'communication': 1,
    'leadership': 1
}

def extract_skills(text):
    \\\
    text_lower = text.lower()


def calculate_hybrid_score(job_description, resume_text, semantic_score):
    \\\
    # Handle empty or NaN resume text
    if not isinstance(resume_text, str) or pd.isna(resume_text):


def rank_resumes_hybrid(job_description, resume_embeddings, resume_df, model):
    \\\


def precision_at_k_hybrid(ranked_df, expected_category, k):
    \\\
    top_k = ranked_df.head(k)


def rank_resumes_multistage(job_description, resume_embeddings, resume_df, model):
    \\,
    ,
    ,
    ,
    \


# Save the Sentence Transformer model (required for API)
model.save('models/sentence_transformer_model')

print(\)

import qrcode

# Your live GitHub Pages URL
url = \

# Generate QR code
qr = qrcode.make(url)

# Save as image file
qr.save(\)

print(\)
print(f\)
print(\)

