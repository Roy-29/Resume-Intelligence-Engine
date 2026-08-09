"""
AI Core: NLP Extraction
Provides 3-Layer Skill Extraction system.
"""
import re
from candidate.data import TECHNICAL_SKILLS, SOFT_SKILLS

class SkillExtractor:
    def __init__(self):
        self.skills_db = {s.lower() for s in TECHNICAL_SKILLS | SOFT_SKILLS}
        
        # Ontology mapping for Layer 2
        self.ontology_map = {
            'js': 'javascript',
            'reactjs': 'react',
            'react.js': 'react',
            'node': 'node.js',
            'ts': 'typescript',
            'ml': 'machine learning',
            'ai': 'artificial intelligence',
            'dl': 'deep learning',
            'nlp': 'natural language processing',
            'aws': 'amazon web services',
            'gcp': 'google cloud',
            'k8s': 'kubernetes',
            'vuejs': 'vue',
        }

    def _layer_1_keyword(self, text: str) -> set:
        """Exact keyword matching with boundaries."""
        found = set()
        text_lower = text.lower()
        for skill in self.skills_db:
            if re.search(r'(?<![a-z])' + re.escape(skill) + r'(?![a-z])', text_lower):
                found.add(skill)
        return found

    def _layer_2_ontology(self, text: str) -> set:
        """Normalize common abbreviations."""
        found = set()
        text_lower = text.lower()
        for variant, canonical in self.ontology_map.items():
            if re.search(r'(?<![a-z])' + re.escape(variant) + r'(?![a-z])', text_lower):
                found.add(canonical)
        return found

    def _layer_3_semantic(self, text: str) -> set:
        """
        Semantic Skill Extraction using Sentence-BERT.
        Finds skills that are semantically implied but not explicitly mentioned.
        E.g. 'built RESTful microservices' → 'REST API', 'Microservices'
        """
        try:
            from sentence_transformers import SentenceTransformer, util
            import numpy as np
        except ImportError:
            return set()

        # Only process if text is substantial
        if len(text) < 100:
            return set()

        try:
            import os
            model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'ml_models', 'fine_tuned_bert')
            if os.path.exists(model_path):
                model = SentenceTransformer(model_path)
            else:
                model = SentenceTransformer('all-MiniLM-L6-v2')

            # Take sentences from resume (limit for performance)
            sentences = [s.strip() for s in text.split('.') if len(s.strip()) > 20][:60]
            if not sentences:
                return set()

            # Skills NOT found by Layer 1 and 2 (avoid duplicates)
            l1 = self._layer_1_keyword(text)
            l2 = self._layer_2_ontology(text)
            already_found = l1 | l2

            # Candidate skills to check semantically
            candidate_skills = [s for s in self.skills_db if s not in already_found]
            if not candidate_skills:
                return set()

            # No artificial cap — process all remaining skills for completeness

            # Encode
            sentence_embeddings = model.encode(sentences, convert_to_tensor=True)
            skill_embeddings = model.encode(candidate_skills, convert_to_tensor=True)

            # Compute similarity
            similarity = util.cos_sim(skill_embeddings, sentence_embeddings)

            found = set()
            for i, skill in enumerate(candidate_skills):
                max_sim = float(similarity[i].max())
                if max_sim >= 0.55:  # threshold for semantic match
                    found.add(skill)

            return found

        except Exception:
            return set()

    def extract(self, text: str) -> dict:
        """Execute all 3 extraction layers."""
        l1 = self._layer_1_keyword(text)
        l2 = self._layer_2_ontology(text)
        l3 = self._layer_3_semantic(text)
        
        # Merge all found skills
        combined = l1.union(l2).union(l3)
        
        # Title case them for display
        normalized = sorted([s.title() if len(s) > 3 else s.upper() for s in combined])
        if 'Node.js' in normalized: pass
        
        return {
            'layer1_count': len(l1),
            'layer2_count': len(l2),
            'layer3_count': len(l3),
            'all': normalized
        }
