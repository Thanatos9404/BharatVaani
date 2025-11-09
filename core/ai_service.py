# BharatVaani/core/ai_service.py

"""
AI Service Module for What-If Scenarios
Supports multiple AI models with fallback mechanisms
"""

import logging
import requests
import os
from typing import Dict, Optional
import re

# Get API keys from environment
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
HUGGINGFACE_API_KEY = os.getenv('HUGGINGFACE_API_KEY', '')  # Optional


class AIService:
    """
    Handles AI model interactions for What-If scenarios
    Supports both Gemini and Hugging Face models with fallback
    """
    
    def __init__(self):
        self.gemini_key = GEMINI_API_KEY
        self.hf_key = HUGGINGFACE_API_KEY
        
    def generate_whatif_scenario(
        self,
        context: str,
        hypothetical_change: str,
        model_option: str,
        model_config: Dict
    ) -> Dict:
        """
        Generate a What-If scenario using specified AI model
        
        Args:
            context: Current situation/context
            hypothetical_change: Hypothetical change/event
            model_option: User-selected option (e.g., "Detailed & Comprehensive")
            model_config: Configuration for the selected model option
            
        Returns:
            Dict with 'headline' and 'article' or 'error'
        """
        # Try Gemini first (most reliable)
        if self.gemini_key:
            result = self._generate_with_gemini(
                context, hypothetical_change, model_option, model_config
            )
            if not result.get('error'):
                return result
            logging.warning(f"Gemini failed: {result.get('error')}, trying Hugging Face...")
        
        # Fallback to Hugging Face if Gemini fails or not configured
        if self.hf_key:
            result = self._generate_with_huggingface(
                context, hypothetical_change, model_option, model_config
            )
            if not result.get('error'):
                return result
            logging.error(f"Hugging Face also failed: {result.get('error')}")
        
        # If both fail, return helpful error
        error_msg = "Unable to generate scenario. "
        if not self.gemini_key and not self.hf_key:
            error_msg += "No API keys configured. Please add GEMINI_API_KEY to your .env file. Get one free at: https://makersuite.google.com/app/apikey"
        elif not self.gemini_key:
            error_msg += "Gemini API key not found. Add GEMINI_API_KEY to .env"
        else:
            error_msg += "API request failed. Check your internet connection and API key validity."
        
        return {
            "error": error_msg
        }
    
    def _generate_with_gemini(
        self,
        context: str,
        hypothetical_change: str,
        model_option: str,
        model_config: Dict
    ) -> Dict:
        """Generate scenario using Google Gemini API"""
        try:
            model_name = "gemini-1.5-flash"  # Using stable model
            
            # Build prompt based on model option
            style_hints = {
                "Detailed & Comprehensive": "Provide an in-depth, thorough analysis with comprehensive explanations covering multiple angles and implications.",
                "Crisp & Concise": "Be brief and to-the-point. Use short sentences and focus only on key facts.",
                "Creative & Imaginative": "Think outside the box. Explore unusual angles and creative possibilities that others might miss.",
                "Balanced & Neutral": "Present an objective, unbiased analysis. Stick to facts and avoid speculation.",
                "Technical & Data-Driven": "Focus on technical details, statistics, and data-backed insights. Be precise and factual."
            }
            
            style_instruction = style_hints.get(model_option, "Provide a balanced analysis.")
            
            prompt = f"""You are an expert news analyst. {style_instruction}

Current Situation:
{context}

Hypothetical Change:
{hypothetical_change}

Generate ONE plausible future news HEADLINE and ONE NEWS ARTICLE (3-5 sentences) describing the immediate implications.

Format your response EXACTLY as:
HEADLINE: [Your headline here]
ARTICLE: [Your article here]"""
            
            api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={self.gemini_key}"
            
            payload = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }],
                "generationConfig": {
                    "maxOutputTokens": model_config.get('max_tokens', 400),
                    "temperature": model_config.get('temperature', 0.7),
                    "topP": 0.95,
                    "topK": 40
                }
            }
            
            response = requests.post(
                api_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('candidates') and result['candidates'][0].get('content'):
                generated_text = result['candidates'][0]['content']['parts'][0]['text'].strip()
                return self._parse_response(generated_text)
            else:
                return {"error": f"Unexpected Gemini API response: {result}"}
                
        except requests.exceptions.Timeout:
            return {"error": "Request timed out. Please try again."}
        except requests.exceptions.RequestException as e:
            return {"error": f"Network error: {str(e)}"}
        except Exception as e:
            logging.error(f"Gemini API error: {e}", exc_info=True)
            return {"error": f"Gemini API error: {str(e)}"}
    
    def _generate_with_huggingface(
        self,
        context: str,
        hypothetical_change: str,
        model_option: str,
        model_config: Dict
    ) -> Dict:
        """Generate scenario using Hugging Face Inference API"""
        try:
            model_name = model_config.get('model', 'mistralai/Mistral-7B-Instruct-v0.2')
            
            prompt = f"""<s>[INST] You are a news analyst. Generate a news headline and article for this scenario:

Current Situation: {context}
Hypothetical Change: {hypothetical_change}

Format:
HEADLINE: [headline]
ARTICLE: [article]
[/INST]"""
            
            api_url = f"https://api-inference.huggingface.co/models/{model_name}"
            
            headers = {
                "Authorization": f"Bearer {self.hf_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": model_config.get('max_tokens', 400),
                    "temperature": model_config.get('temperature', 0.7),
                    "top_p": 0.95,
                    "do_sample": True,
                    "return_full_text": False
                },
                "options": {
                    "wait_for_model": True,
                    "use_cache": False
                }
            }
            
            response = requests.post(
                api_url,
                json=payload,
                headers=headers,
                timeout=60  # HF can be slower
            )
            response.raise_for_status()
            
            result = response.json()
            
            if isinstance(result, list) and len(result) > 0:
                generated_text = result[0].get('generated_text', '')
                return self._parse_response(generated_text)
            else:
                return {"error": f"Unexpected Hugging Face response: {result}"}
                
        except requests.exceptions.Timeout:
            return {"error": "Model loading timed out. Try a different option or wait a moment."}
        except requests.exceptions.RequestException as e:
            return {"error": f"Hugging Face API error: {str(e)}"}
        except Exception as e:
            logging.error(f"Hugging Face error: {e}", exc_info=True)
            return {"error": f"Hugging Face error: {str(e)}"}
    
    def _parse_response(self, generated_text: str) -> Dict:
        """Parse the generated text to extract headline and article"""
        try:
            # Try to extract HEADLINE: and ARTICLE: sections
            headline_match = re.search(r"HEADLINE:\s*(.*?)(?:\n|ARTICLE:|$)", generated_text, re.IGNORECASE | re.DOTALL)
            article_match = re.search(r"ARTICLE:\s*(.*?)(?:$|\n\n)", generated_text, re.IGNORECASE | re.DOTALL)
            
            headline = headline_match.group(1).strip() if headline_match else None
            article = article_match.group(1).strip() if article_match else None
            
            # Fallback: if format not found, try to split by lines
            if not headline or not article:
                lines = [line.strip() for line in generated_text.split('\n') if line.strip()]
                if len(lines) >= 2:
                    headline = lines[0]
                    article = ' '.join(lines[1:])
                else:
                    # Last resort: use first sentence as headline
                    sentences = generated_text.split('. ')
                    headline = sentences[0] if sentences else "Scenario Generated"
                    article = '. '.join(sentences[1:]) if len(sentences) > 1 else generated_text
            
            # Clean up
            headline = headline.replace('HEADLINE:', '').replace('**', '').strip()
            article = article.replace('ARTICLE:', '').replace('**', '').strip()
            
            # Ensure we have valid content
            if not headline or len(headline) < 10:
                headline = "Future Scenario: Implications of Recent Changes"
            if not article or len(article) < 20:
                article = generated_text[:500]  # Use raw text if parsing failed
            
            return {
                "headline": headline,
                "article": article
            }
            
        except Exception as e:
            logging.error(f"Error parsing AI response: {e}")
            return {
                "headline": "Scenario Analysis",
                "article": generated_text[:500] if generated_text else "Unable to generate scenario."
            }


# Global AI service instance
_ai_service = None


def get_ai_service() -> AIService:
    """Get or create the global AI service instance"""
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service
