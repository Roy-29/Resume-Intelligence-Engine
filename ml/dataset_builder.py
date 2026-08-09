"""
Dataset Builder
===============
Collects training data from the Kaggle CSV and optionally from
analyzed CentralizedResume / CandidateAnalysis records in the database.
"""
import os
import re
import pandas as pd
import logging

logger = logging.getLogger(__name__)


def clean_text(text: str) -> str:
    """Strip HTML, URLs, special chars from resume text."""
    text = re.sub(r'http\S+', ' ', text)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'[^a-zA-Z0-9\s.,-]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def load_kaggle_dataset(csv_path: str = None) -> pd.DataFrame:
    """
    Load the Kaggle resume dataset.
    Tries UpdatedResumeDataSet.csv first, falls back to Resume.csv.
    Returns DataFrame with columns: text, category
    """
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    kaggle_dir = os.path.join(base, 'ml_models', 'kaggle_data')
    
    # Try both CSV files
    csv_files = []
    if csv_path:
        csv_files = [csv_path]
    else:
        for fname in ['UpdatedResumeDataSet.csv', 'Resume.csv']:
            fpath = os.path.join(kaggle_dir, fname)
            if os.path.exists(fpath):
                csv_files.append(fpath)

    if not csv_files:
        raise FileNotFoundError(f"No Kaggle CSV files found in {kaggle_dir}")

    all_dfs = []
    for fpath in csv_files:
        try:
            df = pd.read_csv(fpath)
            cols_lower = {c: c.strip().lower() for c in df.columns}

            # Find the text column
            text_col = None
            for orig, lc in cols_lower.items():
                if lc in ('resume', 'resume_str', 'resume_text', 'content', 'resume_html'):
                    text_col = orig
                    break
            
            # Find the category column
            cat_col = None
            for orig, lc in cols_lower.items():
                if lc in ('category', 'label', 'class', 'resume_category'):
                    cat_col = orig
                    break
            
            if text_col and cat_col:
                result = pd.DataFrame({
                    'text': df[text_col].astype(str).apply(clean_text),
                    'category': df[cat_col].astype(str)
                })
                result = result[result['text'].str.len() > 50].reset_index(drop=True)
                logger.info(f"Loaded {len(result)} resumes from {os.path.basename(fpath)} with {result['category'].nunique()} categories")
                all_dfs.append(result)
            elif 'career_objective' in cols_lower.values() and 'job_position_name' in cols_lower.values():
                # Parsed CSV format (e.g. UpdatedResumeDataSet.csv with structured columns)
                logger.info(f"Detected parsed CSV format in {os.path.basename(fpath)}, synthesizing text...")
                # Find original column names
                rev = {v: k for k, v in cols_lower.items()}
                cat_orig = rev.get('job_position_name')
                text_parts = ['career_objective', 'skills', 'degree_names', 'major_field_of_studies', 'responsibilities']
                
                def combine_row(row):
                    parts = []
                    for col_lc in text_parts:
                        orig = rev.get(col_lc)
                        if orig and pd.notna(row.get(orig)):
                            parts.append(str(row[orig]))
                    return " ".join(parts)
                
                df['_text'] = df.apply(combine_row, axis=1).apply(clean_text)
                df['_cat'] = df[cat_orig].fillna('Unknown').astype(str)
                result = pd.DataFrame({'text': df['_text'], 'category': df['_cat']})
                result = result[result['text'].str.len() > 50].reset_index(drop=True)
                logger.info(f"Loaded {len(result)} resumes from {os.path.basename(fpath)} (parsed format)")
                all_dfs.append(result)
            else:
                logger.warning(f"Skipping {os.path.basename(fpath)}: could not find text/category columns. Found: {list(df.columns)}")
        except Exception as e:
            logger.warning(f"Error reading {fpath}: {e}")
    
    if not all_dfs:
        raise ValueError(f"Could not parse any CSV files in {kaggle_dir}")
    
    combined = pd.concat(all_dfs, ignore_index=True)
    combined = combined.drop_duplicates(subset=['text']).reset_index(drop=True)
    logger.info(f"Total Kaggle dataset: {len(combined)} resumes, {combined['category'].nunique()} categories")
    return combined


def load_db_resumes() -> pd.DataFrame:
    """
    Load analyzed resumes from the database (CentralizedResume + CandidateAnalysis).
    Returns DataFrame with columns: text, category
    """
    rows = []

    try:
        from api.models import CentralizedResume
        for cv in CentralizedResume.objects.filter(status='Analyzed').exclude(extracted_text__isnull=True):
            if cv.extracted_text and len(cv.extracted_text.strip()) > 50:
                rows.append({
                    'text': clean_text(cv.extracted_text),
                    'category': cv.fit_level or 'Unknown'
                })
    except Exception as e:
        logger.warning(f"Could not load CentralizedResumes: {e}")

    try:
        from candidate.models import CandidateAnalysis
        for ca in CandidateAnalysis.objects.exclude(full_text__isnull=True):
            if ca.full_text and len(ca.full_text.strip()) > 50:
                rows.append({
                    'text': clean_text(ca.full_text),
                    'category': ca.resume_category or 'Unknown'
                })
    except Exception as e:
        logger.warning(f"Could not load CandidateAnalysis: {e}")

    if rows:
        logger.info(f"Loaded {len(rows)} resumes from database")
        return pd.DataFrame(rows)
    else:
        return pd.DataFrame(columns=['text', 'category'])


def build_training_dataset(csv_path: str = None, include_db: bool = True) -> pd.DataFrame:
    """
    Build the combined training dataset from Kaggle + database.
    """
    df = load_kaggle_dataset(csv_path)

    if include_db:
        db_df = load_db_resumes()
        if not db_df.empty:
            df = pd.concat([df, db_df], ignore_index=True)
            logger.info(f"Combined dataset size: {len(df)}")

    return df
