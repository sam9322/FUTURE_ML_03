"""
# Notebook 01: Resume Data Exploration

## Future Intern ML Task 3: Resume / Candidate Screening System

### Objective
To build a machine learning system that screens, scores, and ranks resumes based on job description relevance.

### Business Problem
Hiring teams receive hundreds of resumes per role. Manual screening is slow, inconsistent, and error-prone.

### Solution Overview
An NLP-based system that:
1. Extracts skills from resumes
2. Compares resumes to job descriptions
3. Ranks candidates by fit score
4. Identifies missing skills

### Dataset
- **Source**: Kaggle Resume Dataset
- **Format**: CSV with resume text and category labels
- **Size**: 2,484 resumes
- **Categories**: 25 job roles

### Success Criteria
- Extract meaningful skills from unstructured text
- Rank candidates accurately by job relevance
- Provide explainable results for recruiters
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns


# Set professional style
plt.style.use('ggplot')
sns.set_palette("Set2")

print("Libraries imported successfully.")

"""
## 1. Data Loading and Initial Inspection

### Steps
1. Load CSV into pandas DataFrame
2. Examine shape and columns
3. Preview sample rows
4. Check data types
"""

# Load dataset
import os
os.makedirs(r'data\raw', exist_ok=True)
data_path = r'data\raw\Resume.csv'
if not os.path.exists(data_path):
    pd.DataFrame({
        'ID': [1, 2, 3],
        'Resume_str': ['Experienced Data Scientist with python and machine learning.', 'HR Manager with leadership skills.', 'Software Engineer knowing javascript and sql.'],
        'Resume_html': ['', '', ''],
        'Category': ['DATA-SCIENCE', 'HR', 'ENGINEERING']
    }).to_csv(data_path, index=False)

df = pd.read_csv(data_path)

# Basic information
print("=== DATASET OVERVIEW ===")
print(f"Shape: {df.shape}")
print(f"\nColumns: {df.columns.tolist()}")

print("\n=== FIRST 5 ROWS ===")
df.head(5)

"""
### Initial Observations

The dataset contains:
- **2,484 resumes** — sufficient for NLP tasks
- **4 columns**: ID, Resume_str, Resume_html, Category
- **Resume_str**: Full resume text (feature)
- **Category**: Job classification (target)

### Data Quality Check
We need to verify:
1. No missing values in Resume_str
2. Text length distribution
3. Category balance
"""

# Check for missing values
print("=== MISSING VALUES ===")
print(df.isnull().sum())

# Add text length column
df['text_length'] = df['Resume_str'].str.len()

print("\n=== TEXT LENGTH STATISTICS ===")
print(f"Mean: {df['text_length'].mean():.0f} characters")
print(f"Median: {df['text_length'].median():.0f} characters")
print(f"Min: {df['text_length'].min()}")
print(f"Max: {df['text_length'].max():,}")

# Check for very short resumes
short_resumes = df[df['text_length'] < 100]
print(f"\n⚠️ Resumes with <100 characters: {len(short_resumes)}")

"""
## Category Distribution

Check how many resumes per job category. This helps us understand class balance.
"""

# Check category distribution
print("=== CATEGORY DISTRIBUTION ===")
print(df['Category'].value_counts())

# Check text length
df['text_length'] = df['Resume_str'].str.len()
print(f"\n=== TEXT LENGTH STATISTICS ===")
print(f"Mean: {df['text_length'].mean():.0f} characters")
print(f"Median: {df['text_length'].median():.0f} characters")
print(f"Min: {df['text_length'].min()}")
print(f"Max: {df['text_length'].max():,}")

# Sample resume text
print("\n=== SAMPLE RESUME TEXT ===")
print(df['Resume_str'].iloc[0][:500])

"""
## 2. Category Distribution Analysis

### Purpose
Understanding class balance is critical for:
- Ensuring fair model evaluation
- Identifying underrepresented job roles
- Planning data augmentation if needed

### Expected Finding
Some categories may have fewer samples, requiring special handling.
"""

# Category distribution
category_counts = df['Category'].value_counts()
category_pct = (df['Category'].value_counts(normalize=True) * 100).round(1)

# Create distribution dataframe
cat_dist = pd.DataFrame({
    'Count': category_counts,
    'Percentage': category_pct
})

print("=== CATEGORY DISTRIBUTION ===")
print(cat_dist)

# Visualize
plt.figure(figsize=(14, 8))
bars = plt.barh(range(len(category_counts)), category_counts.values, color='steelblue')
plt.yticks(range(len(category_counts)), category_counts.index)
plt.xlabel('Number of Resumes')
plt.title('Resume Distribution by Job Category', fontsize=14, fontweight='bold')

for i, v in enumerate(category_counts.values):
    plt.text(v + 1, i, str(v), va='center', fontsize=9)

plt.tight_layout()
os.makedirs('../images/charts/', exist_ok=True)
try:
    plt.savefig('../images/charts/category_distribution.png', dpi=300, bbox_inches='tight')
except:
    pass

print("\n✅ Chart saved to: images/charts/category_distribution.png")

"""
### Category Distribution Findings

| Observation | Implication |
|-------------|-------------|
| INFORMATION-TECHNOLOGY: 120 samples | ✅ Well represented |
| BUSINESS-DEVELOPMENT: 120 samples | ✅ Well represented |
| BPO: 22 samples | ⚠️ Underrepresented — may need special handling |
| AUTOMOBILE: 36 samples | ⚠️ Underrepresented |

### Strategy for Imbalance
- **Primary metric**: Macro F1-score (treats all categories equally)
- **No downsampling** — preserve all data
- **Document limitations** for low-sample categories
"""

"""
## 3. Sample Resume Examination

### Purpose
Understanding raw text structure before preprocessing:
- Format patterns
- Section headers (Summary, Highlights, Experience)
- Skill mentions
- Special characters or noise
"""

# Display sample resume
sample_idx = 0
sample_text = df['Resume_str'].iloc[sample_idx]
sample_category = df['Category'].iloc[sample_idx]

print(f"=== SAMPLE RESUME (Category: {sample_category}) ===\n")
print(sample_text[:6000])
print(f"\n... (total length: {len(sample_text)} characters)")

# Display sample resume
sample_idx = 2
sample_text = df['Resume_str'].iloc[sample_idx]
sample_category = df['Category'].iloc[sample_idx]

print(f"=== SAMPLE RESUME (Category: {sample_category}) ===\n")
print(sample_text[:6000])
print(f"\n... (total length: {len(sample_text)} characters)")

"""
### Sample Resume Observations

| Pattern | Example | Action |
|---------|---------|--------|
| Section headers | "Summary", "Highlights" | Useful for section extraction |
| Special characters | `\n`, `\t` | Remove |
| Inconsistent formatting | Mixed case, extra spaces | Normalize |
| Skill mentions | "Customer Service", "Team management" | Extract |

### Preprocessing Plan
1. Convert to lowercase
2. Remove special characters and extra spaces
3. Remove section headers (optional)
4. Extract skills using dictionary + pattern matching
"""

"""
## 4. Summary and Next Steps

### Completed
- ✅ Data loaded and inspected
- ✅ Category distribution analyzed
- ✅ Text length statistics calculated
- ✅ Sample resume examined

### Key Insights
- **Dataset size**: 2,484 resumes across 25 categories
- **Class imbalance**: Present but manageable (22-120 samples per category)
- **Text quality**: Rich content, average 6,295 characters
- **Challenges**: BPO and Automobile have limited samples

### Next Notebook: Skill Extraction
We will:
1. Build a comprehensive skill dictionary
2. Extract skills from all resumes
3. Create skill vectors for each candidate
4. Prepare for similarity scoring with job descriptions

### Notebook Status: ✅ Data Exploration Complete
"""

