"""
# Notebook 02: Resume Preprocessing

## Objective
Clean resume text and apply lemmatization for better skill matching.

## Why Lemmatization Matters
Resumes use past tense: "developed" → "develop", "managed" → "manage"
This ensures "develop" matches "developed" in job descriptions.
"""

import pandas as pd
import re
import nltk
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords

# Download required NLTK data
nltk.download('wordnet')
nltk.download('omw-1.4')
nltk.download('stopwords')

print("Libraries imported and NLTK data downloaded successfully.")


# Load raw data
df = pd.read_csv('data/raw/Resume.csv')

print(f"Loaded {len(df)} resumes")
print(f"Columns: {df.columns.tolist()}")
print(f"\nFirst row preview:\n{df['Resume_str'].iloc[0][:300]}")

"""
## Text Cleaning Function

### Steps:
1. Lowercase
2. Remove URLs, emails, phone numbers
3. Remove special characters (keep only letters and spaces)
4. Remove extra whitespace
5. Lemmatization (convert "developed" → "develop")
"""



# Initialize lemmatizer
lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))

def clean_and_lemmatize(text):
    """
    Clean resume text and apply lemmatization.
    """
    if not isinstance(text, str):
        text = str(text)
    
    # Lowercase
    text = text.lower()
    
    # Remove URLs
    text = re.sub(r'http\S+|www\S+|https\S+', ' ', text)
    
    # Remove emails
    text = re.sub(r'\S+@\S+', ' ', text)
    
    # Remove phone numbers (10+ digits)
    text = re.sub(r'\b\d{10,}\b', ' ', text)
    
    # Remove special characters (keep only letters and spaces)
    text = re.sub(r'[^a-z\s]', ' ', text)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Tokenize and lemmatize
    words = text.split()
    words = [lemmatizer.lemmatize(word) for word in words if word not in stop_words]
    
    return ' '.join(words)

# Test on first resume
sample = df['Resume_str'].iloc[0]
cleaned = clean_and_lemmatize(sample)

print("=== CLEANING TEST ===\n")
print(f"Original length: {len(sample)} characters")
print(f"Cleaned length: {len(cleaned)} characters")
print(f"\nCleaned preview (first 500 chars):\n")
print(cleaned[:500])

"""
## Apply Cleaning to All Resumes

Process all 2,484 resumes and save the cleaned dataset.
"""

# Apply cleaning to all resumes
df['cleaned_text'] = df['Resume_str'].apply(clean_and_lemmatize)

# Add cleaned text length
df['cleaned_length'] = df['cleaned_text'].str.len()

print("=== PROCESSING COMPLETE ===\n")
print(f"Total resumes: {len(df)}")
print(f"Original avg length: {df['Resume_str'].str.len().mean():.0f} chars")
print(f"Cleaned avg length: {df['cleaned_length'].mean():.0f} chars")
print(f"Average reduction: {(1 - df['cleaned_length'].mean() / df['Resume_str'].str.len().mean()) * 100:.1f}%")

# Preview cleaned data
print("\n=== PREVIEW CLEANED DATA ===\n")
print(df[['Category', 'cleaned_text']].head(2))

"""
## Save Cleaned Dataset

Save the processed resumes to the processed data folder for use in Notebook 03.
"""

import os

# Create processed directory if it doesn't exist
os.makedirs('data/processed', exist_ok=True)

# Save cleaned dataset
df.to_csv('data/processed/resumes_cleaned.csv', index=False)

print("✅ Cleaned dataset saved to: data/processed/resumes_cleaned.csv")
print(f"   Shape: {df.shape}")
print(f"   Columns: {df.columns.tolist()}")

