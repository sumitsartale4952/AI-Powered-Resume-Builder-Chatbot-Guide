import spacy
from spacy.matcher import Matcher
from typing import Dict, List
import logging
import re

class NLPProcessor:
    def __init__(self, model_name="en_core_web_lg"):
        try:
            self.nlp = spacy.load(model_name)
            self._add_custom_patterns()
        except OSError:
            logging.error(f"SpaCy model {model_name} not found. Installing...")
            spacy.cli.download(model_name)
            self.nlp = spacy.load(model_name)
            
        self.skill_pattern = self._create_skill_pattern()

    def _add_custom_patterns(self):
        # Add resume-specific entity recognition
        ruler = self.nlp.add_pipe("entity_ruler")
        patterns = [
            {"label": "DEGREE", "pattern": [{"LOWER": {"IN": ["bsc", "msc", "phd"]}}]},
            {"label": "COMPANY", "pattern": [{"ENT_TYPE": "ORG"}]}
        ]
        ruler.add_patterns(patterns)

    def _create_skill_pattern(self):
        matcher = Matcher(self.nlp.vocab)
        skills = ["machine learning", "project management", "data analysis"]
        for skill in skills:
            matcher.add(skill, [[{"LOWER": skill}]])
        return matcher

    def extract_entities(self, text: str) -> Dict:
        doc = self.nlp(text)
        return {
            "skills": self._extract_skills(doc),
            "companies": self._extract_companies(doc),
            "education": self._extract_education(doc)
        }

    def _extract_skills(self, doc):
        matches = self.skill_pattern(doc)
        return list(set(doc[start:end].text for _, start, end in matches))

    def _extract_companies(self, doc):
        return list(set(ent.text for ent in doc.ents if ent.label_ == "ORG"))

    def _extract_education(self, doc):
        return list(set(ent.text for ent in doc.ents if ent.label_ == "DEGREE"))

    def analyze_resume_text(self, text: str) -> Dict:
        doc = self.nlp(text)
        return {
            "readability_score": self._calculate_readability(doc),
            "keyword_density": self._calculate_keyword_density(doc),
            "action_verbs": self._find_action_verbs(doc)
        }

    def _calculate_readability(self, doc):
        # Simple Flesch-Kincaid approximation
        sentence_count = len(list(doc.sents))
        word_count = len(doc)
        return (206.835 - 1.015 * (word_count/sentence_count) - 84.6 * (len(doc)/(word_count or 1)))

    def _calculate_keyword_density(self, doc):
        keywords = ["develop", "manage", "improve", "create"]
        matches = [token.text.lower() for token in doc if token.text.lower() in keywords]
        return len(matches) / len(doc) if len(doc) > 0 else 0

    def _find_action_verbs(self, doc):
        return [token.lemma_ for token in doc if token.pos_ == "VERB" and token.dep_ == "ROOT"]