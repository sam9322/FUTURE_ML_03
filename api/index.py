from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime
import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import base64
import io
import json
import spacy
import traceback
import sys
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# PDF and DOCX support
try:
    import PyPDF2
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

try:
    import docx
    DOCX_SUPPORT = True
except ImportError:
    DOCX_SUPPORT = False

# Pyresparser support
try:
    from pyresparser import ResumeParser
    PYRESPARSER_SUPPORT = True
except ImportError:
    PYRESPARSER_SUPPORT = False

# Setup NLTK data directory for Vercel Serverless (read-only filesystem workaround)
import os
os.makedirs('/tmp/nltk_data', exist_ok=True)
nltk.data.path.append('/tmp/nltk_data')

# Download NLTK data to /tmp
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', download_dir='/tmp/nltk_data')
try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet', download_dir='/tmp/nltk_data')
try:
    nltk.data.find('corpora/omw-1.4')
except LookupError:
    nltk.download('omw-1.4', download_dir='/tmp/nltk_data')

# Initialize NLTK components
lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))

# Removing SentenceTransformer to fit Vercel Serverless Limits
# semantic_model will be computed via TF-IDF at request time

# ============================================================
# PROFESSIONAL SKILL EXTRACTOR (No Hardcoded Lists)
# ============================================================

class SkillExtractor:
    def __init__(self):
        """Initialize skill extractor with NLP capabilities."""
        try:
            import en_core_web_sm
            self.nlp = en_core_web_sm.load()
            print("spaCy model loaded from direct import")
        except:
            try:
                self.nlp = spacy.load("en_core_web_sm")
                print("spaCy model loaded")
            except:
                # Fallback to empty model for Vercel if install fails
                self.nlp = spacy.blank("en")
                print("Fallback: Using blank spaCy model")
    
    def extract(self, text):
        """Extract skills from job description using multiple NLP methods."""
        skills = set()
        text_lower = text.lower()
        
        skill_indicators = [
            'experience in', 'knowledge of', 'proficient in', 'skilled in',
            'expertise in', 'familiar with', 'strong', 'hands-on', 'competent in',
            'ability to', 'background in', 'trained in', 'certified in'
        ]
        
        doc = self.nlp(text_lower)
        
        for indicator in skill_indicators:
            if indicator in text_lower:
                parts = text_lower.split(indicator)
                for part in parts[1:]:
                    end_chars = ['.', ',', ';', 'and', 'or']
                    extracted = part
                    for end in end_chars:
                        if end in extracted:
                            extracted = extracted.split(end)[0]
                            break
                    potential = re.split(r',|\sand\s', extracted[:100])
                    for skill in potential[:5]:
                        cleaned = skill.strip()
                        if 3 <= len(cleaned) <= 30 and cleaned not in stop_words:
                            skills.add(cleaned)
        
        for chunk in doc.noun_chunks:
            chunk_text = chunk.text.strip()
            if 3 <= len(chunk_text) <= 30 and chunk_text not in stop_words:
                if any(word in chunk_text for word in ['experience', 'knowledge', 'skill', 'proficient', 'expert']):
                    skills.add(chunk_text)
        
        try:
            vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words='english', max_features=20)
            tfidf_matrix = vectorizer.fit_transform([text_lower])
            feature_names = vectorizer.get_feature_names_out()
            scores = tfidf_matrix.toarray()[0]
            top_indices = np.argsort(scores)[-15:][::-1]
            for idx in top_indices:
                term = feature_names[idx]
                if 3 <= len(term) <= 30 and term not in stop_words:
                    skills.add(term)
        except:
            pass
        
        capitalized = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        for cap in capitalized[:10]:
            if 3 <= len(cap) <= 30:
                skills.add(cap.lower())
        
        stopwords_list = {'the', 'a', 'an', 'and', 'or', 'of', 'to', 'in', 'for', 'on', 'with', 
                          'by', 'at', 'from', 'as', 'is', 'was', 'are', 'were', 'be', 'been', 
                          'have', 'has', 'had', 'do', 'does', 'did', 'but', 'so', 'if', 'then', 
                          'else', 'when', 'where', 'which', 'while', 'using', 'including', 'such'}
        
        filtered_skills = [s for s in skills if s not in stopwords_list and len(s) > 2]
        
        return list(set(filtered_skills))[:15]

skill_extractor = SkillExtractor()

# ============================================================
# PDF/DOCX PARSING FUNCTIONS
# ============================================================

def extract_text_from_pdf(file_content: bytes) -> str:
    if not PDF_SUPPORT:
        raise ImportError("PyPDF2 not installed")
    text = ""
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    except Exception as e:
        logger.warning(f"PyPDF2 failed: {e}. Trying pdfminer fallback.")
        try:
            from pdfminer.high_level import extract_text as extract_text_pdfminer
            text = extract_text_pdfminer(io.BytesIO(file_content))
        except ImportError:
            logger.error("pdfminer not installed for fallback.")
            raise ValueError(f"Failed to parse PDF: {str(e)} (fallback unavailable)")
        except Exception as fallback_e:
            logger.error(f"Fallback pdfminer also failed: {fallback_e}")
            raise ValueError(f"Failed to parse PDF: {str(e)}. Fallback failed: {str(fallback_e)}")
            
    if not text.strip():
        raise ValueError("PDF contains no extractable text")
    return text

def extract_text_from_docx(file_content: bytes) -> str:
    if not DOCX_SUPPORT:
        raise ImportError("python-docx not installed")
    text = ""
    try:
        doc = docx.Document(io.BytesIO(file_content))
        for paragraph in doc.paragraphs:
            if paragraph.text:
                text += paragraph.text + "\n"
    except Exception as e:
        raise ValueError(f"Failed to parse DOCX: {str(e)}")
    return text

def extract_text_from_file(file_content: bytes, filename: str) -> str:
    ext = filename.lower().split('.')[-1]
    if ext == 'pdf':
        return extract_text_from_pdf(file_content)
    elif ext == 'docx':
        return extract_text_from_docx(file_content)
    elif ext == 'txt':
        return file_content.decode('utf-8', errors='ignore')
    else:
        raise ValueError(f"Unsupported file format: {ext}. Supported: pdf, docx, txt")

# ============================================================
# TEXT PROCESSING FUNCTIONS
# ============================================================

def clean_and_lemmatize(text):
    if not isinstance(text, str):
        text = str(text)
    text = text.lower()
    text = re.sub(r'[^a-z\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    words = text.split()
    words = [lemmatizer.lemmatize(word) for word in words if word not in stop_words]
    return ' '.join(words)

def extract_skills_with_patterns(text, skill_patterns):
    text_lower = text.lower()
    found = []
    for skill, pattern in skill_patterns.items():
        if re.search(pattern, text_lower):
            found.append(skill)
    return found

def calculate_skill_score_with_weights(job_skills, resume_skills, skill_weights):
    total_weight = 0
    matched_weight = 0
    for skill in job_skills:
        weight = skill_weights.get(skill, 1)
        total_weight += weight
        if skill in resume_skills:
            matched_weight += weight
    return matched_weight / total_weight if total_weight > 0 else 0

def generate_recommendation(final_score, matched_count, total_required, missing_skills):
    if final_score >= 0.7:
        return f"Strong match ({final_score:.0%}). Candidate meets {matched_count}/{total_required} core requirements. Recommend interview."
    elif final_score >= 0.5:
        return f"Moderate match ({final_score:.0%}). Missing skills: {', '.join(missing_skills[:3])}. Consider further screening."
    else:
        return f"Low match ({final_score:.0%}). Significant skill gaps: {', '.join(missing_skills[:5])}. Not recommended."


def extract_contact_info(text, file_content=None, filename=None):
    # Regex fallback
    email = re.search(r'[\w\.-]+@[\w\.-]+', text)
    phone = re.search(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text)
    contact = {
        "email": email.group(0) if email else "N/A",
        "phone": phone.group(0) if phone else "N/A",
        "name": None,
        "designation": None,
        "skills": []
    }
    
    # Try pyresparser
    if PYRESPARSER_SUPPORT and file_content and filename:
        import tempfile
        import os
        ext = "." + filename.split('.')[-1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp:
            temp.write(file_content)
            temp_path = temp.name
            
        try:
            data = ResumeParser(temp_path).get_extracted_data()
            if data:
                if data.get('email') and contact['email'] == "N/A":
                    contact['email'] = data['email']
                if data.get('mobile_number') and contact['phone'] == "N/A":
                    contact['phone'] = data['mobile_number']
                contact['name'] = data.get('name')
                
                des = data.get('designation')
                if des:
                    contact['designation'] = des[0] if isinstance(des, list) else des
                    
                if data.get('skills'):
                    contact['skills'] = data['skills']
        except Exception:
            pass
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    return contact

def process_resume_text(job_description, resume_text, semantic_weight, skill_weight, skill_patterns, skill_weights, file_content=None, filename=None):
    if not isinstance(job_description, str): job_description = str(job_description)
    if not isinstance(resume_text, str): resume_text = str(resume_text)
    
    jd_clean = clean_and_lemmatize(job_description)
    resume_clean = clean_and_lemmatize(resume_text)
    
    try:
        tfidf_vec = TfidfVectorizer(stop_words='english')
        tfidf_matrix = tfidf_vec.fit_transform([jd_clean, resume_clean])
        semantic_score = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
    except Exception:
        semantic_score = 0.0
    
    job_skills = list(skill_patterns.keys())
    resume_skills = extract_skills_with_patterns(resume_text, skill_patterns)
    
    contact_info = extract_contact_info(resume_text, file_content, filename)
    
    # Merge skills from pyresparser if available
    if contact_info.get('skills'):
        for s in contact_info['skills']:
            sl = s.lower()
            if sl in skill_patterns and sl not in resume_skills:
                resume_skills.append(sl)
    
    skill_score = calculate_skill_score_with_weights(job_skills, resume_skills, skill_weights)
    final_score = (semantic_score * semantic_weight) + (skill_score * skill_weight)
    
    matched = list(set([s for s in resume_skills if s in job_skills]))
    missing = list(set([s for s in job_skills if s not in matched]))
    
    recommendation = generate_recommendation(final_score, len(matched), len(job_skills), missing)
    
    return {
        "semantic_score": float(semantic_score),
        "skill_score": float(skill_score),
        "composite_score": float(final_score),
        "matched_skills": matched,
        "missing_skills": missing,
        "recommendation": recommendation,
        "email": contact_info["email"],
        "phone": contact_info["phone"],
        "extracted_name": contact_info.get("name"),
        "designation": contact_info.get("designation")
    }

# ============================================================
# FASTAPI APP
# ============================================================

API_KEY = "sam9322-resumeiq-2026-secret-key"
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

async def get_api_key(api_key: str = Depends(api_key_header)):
    if api_key == API_KEY:
        return api_key
    raise HTTPException(status_code=403, detail="Could not validate credentials")

app = FastAPI(title="Resume Screening API", version="3.1.0", docs_url=None, redoc_url=None, openapi_url=None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    import os
    from fastapi.responses import FileResponse
    # Try to serve index.html from current dir or parent dir
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    elif os.path.exists("../index.html"):
        return FileResponse("../index.html")
    return {"message": "Resume Screening API", "version": "3.1.0"}

@app.get("/health")
def health():
    return {"status": "healthy", "model_loaded": True}

# ============================================================
# FORMDATA ENDPOINT (With Job Title Support)
# ============================================================


@app.post("/extract-text")
async def extract_text_endpoint(
    file: UploadFile = File(...),
    api_key: str = Depends(get_api_key)
):
    try:
        content = await file.read()
        filename = file.filename
        
        if filename.endswith('.pdf'):
            text = extract_text_from_pdf(content)
        elif filename.endswith('.docx'):
            text = extract_text_from_docx(content)
        elif filename.endswith('.txt'):
            text = content.decode('utf-8', errors='ignore')
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {filename}")
            
        skills = skill_extractor.extract(text)
        
        # Simple guess for job title: first non-empty line
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        title = lines[0] if lines else "Untitled"
        if len(title) > 50:
            title = title[:50] + "..."
            
        return {"text": text, "skills": skills, "filename": filename, "guessed_title": title}
    except Exception as e:
        logger.error(f"Error in extract-text for {file.filename}: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail={"error": "Analysis Failed", "message": str(e), "traceback": traceback.format_exc()})


@app.post("/screen-form")
async def screen_form(
    file: UploadFile = File(...),
    job_description: str = Form(...),
    semantic_weight: float = Form(0.7),
    skill_weight: float = Form(0.3),
    required_skills: str = Form("[]"),
    job_title: str = Form(""),
    api_key: str = Depends(get_api_key)
):
    """
    Screen a single resume using FormData.
    Auto-extracts skills from job description if none provided.
    Now accepts and returns job_title for better organization.
    """
    try:
        # Parse required skills from frontend
        frontend_skills = json.loads(required_skills)
        
        # If no skills provided, auto-extract from job description
        if not frontend_skills:
            frontend_skills = skill_extractor.extract(job_description)
            print(f"Auto-extracted skills: {frontend_skills}")
        
        # Build skill patterns and weights
        skill_patterns = {}
        skill_weights = {}
        
        for skill in frontend_skills:
            skill_lower = skill.lower()
            skill_patterns[skill_lower] = r'\b' + re.escape(skill_lower) + r'\b'
            skill_weights[skill_lower] = 2
        
        # Read the raw file bytes
        content = await file.read()
        filename = file.filename
        
        # Extract text based on file type
        if filename.endswith('.pdf'):
            resume_text = extract_text_from_pdf(content)
        elif filename.endswith('.docx'):
            resume_text = extract_text_from_docx(content)
        elif filename.endswith('.txt'):
            resume_text = content.decode('utf-8', errors='ignore')
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {filename}")
        
        # Process the resume
        result = process_resume_text(
            job_description, resume_text, 
            semantic_weight, skill_weight,
            skill_patterns, skill_weights,
            content, filename
        )
        
        # Extract candidate name from filename or pyresparser output
        candidate_name = result.get("extracted_name") or filename.replace('.pdf', '').replace('.docx', '').replace('.txt', '')
        
        return {
            "semantic_score": result["semantic_score"],
            "skill_score": result["skill_score"],
            "composite_score": result["composite_score"],
            "matched_skills": result["matched_skills"],
            "missing_skills": result["missing_skills"],
            "recommendation": result["recommendation"],
            "candidate_name": candidate_name,
            "category": "Extracted from resume",
            "job_title": job_title if job_title else "Untitled Position",
            "extracted_skills_from_jd": frontend_skills if not json.loads(required_skills) else [],
            "email": result.get("email", "N/A"),
            "phone": result.get("phone", "N/A")
        }
        
        
    except json.JSONDecodeError as e:
        logger.error(f"JSONDecodeError: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=400, detail={"error": "Invalid Format", "message": "Invalid required_skills format"})
    except Exception as e:
        logger.error(f"Error in screen-form for {file.filename}: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail={"error": "Analysis Failed", "message": str(e), "traceback": traceback.format_exc()})

# ============================================================
# BATCH ENDPOINT (With Job Title Support)
# ============================================================

@app.post("/screen-form-batch")
async def screen_form_batch(
    files: List[UploadFile] = File(...),
    job_description: str = Form(...),
    semantic_weight: float = Form(0.7),
    skill_weight: float = Form(0.3),
    required_skills: str = Form("[]"),
    job_title: str = Form(""),
    api_key: str = Depends(get_api_key)
):
    try:
        frontend_skills = json.loads(required_skills)
        
        if not frontend_skills:
            frontend_skills = skill_extractor.extract(job_description)
        
        skill_patterns = {}
        skill_weights = {}
        
        for skill in frontend_skills:
            skill_lower = skill.lower()
            skill_patterns[skill_lower] = r'\b' + re.escape(skill_lower) + r'\b'
            skill_weights[skill_lower] = 2
        
        results = []
        
        for file in files:
            try:
                content = await file.read()
                filename = file.filename
                
                if filename.endswith('.pdf'):
                    resume_text = extract_text_from_pdf(content)
                elif filename.endswith('.docx'):
                    resume_text = extract_text_from_docx(content)
                elif filename.endswith('.txt'):
                    resume_text = content.decode('utf-8', errors='ignore')
                else:
                    continue
                
                result = process_resume_text(
                    job_description, resume_text, 
                    semantic_weight, skill_weight,
                    skill_patterns, skill_weights,
                    content, filename
                )
                candidate_name = result.get("extracted_name") or filename.replace('.pdf', '').replace('.docx', '').replace('.txt', '')
                
                results.append({
                    "candidate_name": candidate_name,
                    "filename": filename,
                    **result
                })
                
            except Exception as e:
                candidate_name = file.filename.replace('.pdf', '').replace('.docx', '').replace('.txt', '')
                results.append({
                    "candidate_name": candidate_name,
                    "filename": file.filename,
                    "semantic_score": 0.0,
                    "skill_score": 0.0,
                    "composite_score": 0.0,
                    "matched_skills": [],
                    "missing_skills": [],
                    "recommendation": f"Error: {str(e)}"
                })
        
        results.sort(key=lambda x: x["composite_score"], reverse=True)
        for i, r in enumerate(results, 1):
            r["rank"] = i
        
        return {
            "total_candidates": len(results),
            "ranked_candidates": results,
            "job_title": job_title if job_title else "Untitled Position",
            "extracted_skills_from_jd": frontend_skills if not json.loads(required_skills) else [],
            "email": result.get("email", "N/A"),
            "phone": result.get("phone", "N/A")
        }
        
        
    except Exception as e:
        logger.error(f"Error in screen-form-batch: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail={"error": "Batch Analysis Failed", "message": str(e), "traceback": traceback.format_exc()})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)