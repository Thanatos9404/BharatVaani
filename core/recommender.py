# BharatVaani/core/recommender.py

"""
Recommendation System for BharatVaani
Provides content-based filtering for suggesting similar articles based on user's bookmarks
"""

import logging
from typing import List, Dict, Set
from collections import Counter
import re
from datetime import datetime


class ArticleRecommender:
    """
    Content-based recommendation system that suggests articles similar to user's bookmarks.
    Uses multiple features: categories, keywords, sentiment, and entities.
    """
    
    def __init__(self):
        self.stop_words = {
            'the', 'is', 'at', 'which', 'on', 'a', 'an', 'and', 'or', 'but',
            'in', 'with', 'to', 'for', 'of', 'as', 'by', 'that', 'this',
            'are', 'was', 'were', 'been', 'be', 'have', 'has', 'had', 'do',
            'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might'
        }
    
    def extract_keywords(self, text: str, top_n: int = 10) -> List[str]:
        """
        Extract important keywords from text.
        Removes stop words and returns most frequent meaningful words.
        """
        if not text:
            return []
        
        # Convert to lowercase and extract words
        words = re.findall(r'\b[a-z]{3,}\b', text.lower())
        
        # Remove stop words
        filtered_words = [w for w in words if w not in self.stop_words]
        
        # Count frequency
        word_freq = Counter(filtered_words)
        
        # Return top N keywords
        return [word for word, _ in word_freq.most_common(top_n)]
    
    def extract_entities(self, text: str) -> Set[str]:
        """
        Extract named entities (capitalized phrases) from text.
        """
        if not text:
            return set()
        
        # Find capitalized words/phrases (simple NER)
        entities = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        return set(entities)
    
    def calculate_similarity(self, article1: Dict, article2: Dict) -> float:
        """
        Calculate similarity score between two articles based on multiple features.
        Returns a score between 0 and 1.
        """
        score = 0.0
        
        # 1. Category similarity (30% weight)
        if article1.get('category') == article2.get('category'):
            score += 0.30
        
        # 2. Keyword overlap (35% weight)
        text1 = f"{article1.get('title', '')} {article1.get('summary', '')}"
        text2 = f"{article2.get('title', '')} {article2.get('summary', '')}"
        
        keywords1 = set(self.extract_keywords(text1))
        keywords2 = set(self.extract_keywords(text2))
        
        if keywords1 and keywords2:
            keyword_overlap = len(keywords1 & keywords2) / len(keywords1 | keywords2)
            score += 0.35 * keyword_overlap
        
        # 3. Entity overlap (20% weight)
        entities1 = self.extract_entities(text1)
        entities2 = self.extract_entities(text2)
        
        if entities1 and entities2:
            entity_overlap = len(entities1 & entities2) / len(entities1 | entities2)
            score += 0.20 * entity_overlap
        
        # 4. Sentiment similarity (10% weight)
        sentiment1 = article1.get('sentiment_data', {}).get('label', 'Unknown')
        sentiment2 = article2.get('sentiment_data', {}).get('label', 'Unknown')
        
        if sentiment1 == sentiment2:
            score += 0.10
        
        # 5. Source similarity (5% weight)
        if article1.get('source') == article2.get('source'):
            score += 0.05
        
        return score
    
    def get_user_profile(self, bookmarked_articles: List[Dict]) -> Dict:
        """
        Build a user profile based on their bookmarked articles.
        Returns aggregated preferences.
        """
        if not bookmarked_articles:
            return {
                'preferred_categories': [],
                'preferred_keywords': [],
                'preferred_entities': [],
                'preferred_sentiment': 'Neutral',
                'preferred_sources': []
            }
        
        # Aggregate categories
        categories = [a.get('category', 'Uncategorized') for a in bookmarked_articles]
        category_counter = Counter(categories)
        
        # Aggregate keywords
        all_keywords = []
        for article in bookmarked_articles:
            text = f"{article.get('title', '')} {article.get('summary', '')}"
            all_keywords.extend(self.extract_keywords(text, top_n=5))
        keyword_counter = Counter(all_keywords)
        
        # Aggregate entities
        all_entities = []
        for article in bookmarked_articles:
            text = f"{article.get('title', '')} {article.get('summary', '')}"
            all_entities.extend(self.extract_entities(text))
        entity_counter = Counter(all_entities)
        
        # Aggregate sentiments
        sentiments = [a.get('sentiment_data', {}).get('label', 'Neutral') for a in bookmarked_articles]
        sentiment_counter = Counter(sentiments)
        
        # Aggregate sources
        sources = [a.get('source', 'Unknown') for a in bookmarked_articles]
        source_counter = Counter(sources)
        
        return {
            'preferred_categories': [cat for cat, _ in category_counter.most_common(3)],
            'preferred_keywords': [kw for kw, _ in keyword_counter.most_common(15)],
            'preferred_entities': [ent for ent, _ in entity_counter.most_common(10)],
            'preferred_sentiment': sentiment_counter.most_common(1)[0][0] if sentiment_counter else 'Neutral',
            'preferred_sources': [src for src, _ in source_counter.most_common(3)]
        }
    
    def recommend_articles(
        self,
        all_articles: List[Dict],
        bookmarked_articles: List[Dict],
        bookmarked_ids: Set[str],
        top_n: int = 10
    ) -> List[Dict]:
        """
        Recommend articles similar to user's bookmarks.
        
        Args:
            all_articles: All available articles
            bookmarked_articles: Articles the user has bookmarked
            bookmarked_ids: Set of bookmarked article IDs
            top_n: Number of recommendations to return
        
        Returns:
            List of recommended articles with similarity scores
        """
        if not bookmarked_articles:
            logging.info("No bookmarked articles. Cannot generate recommendations.")
            return []
        
        # Build user profile
        user_profile = self.get_user_profile(bookmarked_articles)
        logging.info(f"User Profile: Categories={user_profile['preferred_categories']}, "
                    f"Keywords={user_profile['preferred_keywords'][:5]}")
        
        # Calculate similarity scores for all non-bookmarked articles
        recommendations = []
        
        for article in all_articles:
            article_id = article.get('id')
            
            # Skip already bookmarked articles
            if article_id in bookmarked_ids:
                continue
            
            # Calculate average similarity with all bookmarked articles
            similarities = []
            for bookmarked in bookmarked_articles:
                sim = self.calculate_similarity(article, bookmarked)
                similarities.append(sim)
            
            if similarities:
                avg_similarity = sum(similarities) / len(similarities)
                
                # Boost score if article matches user profile
                boost = 0.0
                if article.get('category') in user_profile['preferred_categories']:
                    boost += 0.10
                
                article_text = f"{article.get('title', '')} {article.get('summary', '')}".lower()
                matching_keywords = sum(1 for kw in user_profile['preferred_keywords'] 
                                      if kw in article_text)
                boost += min(0.15, matching_keywords * 0.03)
                
                final_score = min(1.0, avg_similarity + boost)
                
                recommendations.append({
                    'article': article,
                    'score': final_score,
                    'reason': self._generate_recommendation_reason(article, user_profile)
                })
        
        # Sort by score and return top N
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        
        logging.info(f"Generated {len(recommendations)} recommendations. Returning top {top_n}.")
        return recommendations[:top_n]
    
    def _generate_recommendation_reason(self, article: Dict, user_profile: Dict) -> str:
        """
        Generate a human-readable reason for the recommendation.
        """
        reasons = []
        
        # Check category match
        if article.get('category') in user_profile['preferred_categories']:
            reasons.append(f"Similar category: {article.get('category')}")
        
        # Check keyword matches
        article_text = f"{article.get('title', '')} {article.get('summary', '')}".lower()
        matching_keywords = [kw for kw in user_profile['preferred_keywords'][:5] 
                           if kw in article_text]
        if matching_keywords:
            reasons.append(f"Matching interests: {', '.join(matching_keywords[:3])}")
        
        # Check entity matches
        article_entities = self.extract_entities(f"{article.get('title', '')} {article.get('summary', '')}")
        matching_entities = article_entities & set(user_profile['preferred_entities'])
        if matching_entities:
            reasons.append(f"Related to: {', '.join(list(matching_entities)[:2])}")
        
        if not reasons:
            return "Based on your reading preferences"
        
        return " | ".join(reasons[:2])


# Global recommender instance
_recommender_instance = None


def get_recommender() -> ArticleRecommender:
    """Get or create the global recommender instance."""
    global _recommender_instance
    if _recommender_instance is None:
        _recommender_instance = ArticleRecommender()
    return _recommender_instance
