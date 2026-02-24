import os
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from prompts.analyzer_prompt import ANALYZER_SYSTEM_PROMPT
from schemas.domain import AIAnalysisResponse
from pydantic import ValidationError
import httpx
import asyncio
import time
from core.metrics import LLM_LATENCY_SECONDS, LLM_RETRIES, LLM_TOKENS_USED

logger = logging.getLogger(__name__)

class LLMServiceBase(ABC):
    @abstractmethod
    async def analyze_code(self, problem_description: str, constraints: str, student_code: str, execution_output: str) -> AIAnalysisResponse:
        pass

class FaultTolerantLLMService(LLMServiceBase):
    """
    Robust wrapper that handles dynamic providers, retries, and strict JSON validation 
    with an auto-repair prompt loop backing off up to 2 times.
    """
    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "ollama").lower()
        self.api_key = os.environ.get("LLM_API_KEY", "")
        self.max_retries = int(os.getenv("LLM_MAX_RETRIES", "2"))
        
        # Select endpoint dynamically
        if self.provider == "groq":
            self.endpoint = "https://api.groq.com/openai/v1/chat/completions"
            self.model = os.getenv("GROQ_MODEL", "llama3-70b-8192")
            self.headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        elif self.provider == "together":
            self.endpoint = "https://api.together.xyz/v1/chat/completions"
            self.model = os.getenv("TOGETHER_MODEL", "deepseek-coder-33b-instruct")
            self.headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        else:
            host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
            self.endpoint = f"{host}/api/generate"
            self.model = os.getenv("OLLAMA_MODEL", "deepseek-coder:latest")
            self.headers = {"Content-Type": "application/json"}

    async def _call_inference(self, prompt: str) -> str:
        """Raw inference call abstraction over provider differences."""
        payload = {}
        if self.provider in ["groq", "together"]:
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are a senior C++ engineer. Always output strict JSON matching the requested schema. Never output markdown outside of the JSON."},
                    {"role": "user", "content": prompt}
                ],
                "response_format": {"type": "json_object"},
                "temperature": float(os.getenv("LLM_TEMPERATURE", "0.1")),
                "seed": 42 # Deterministic mode
            }
        else:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "options": {
                    "temperature": float(os.getenv("LLM_TEMPERATURE", "0.1")),
                    "seed": 42
                }
            }
            
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(self.endpoint, json=payload, headers=self.headers, timeout=45.0)
                resp.raise_for_status()
                data = resp.json()
                if self.provider in ["groq", "together"]:
                    return data["choices"][0]["message"]["content"]
                else:
                    return data["response"]
            except httpx.HTTPError as e:
                logger.error(f"HTTP Provider Error [{self.provider}]: {str(e)}")
                raise

    async def analyze_code(self, problem_description: str, constraints: str, student_code: str, execution_output: str) -> AIAnalysisResponse:
        """
        Executes analysis with built-in auto-repair loop for JSON validation.
        """
        base_prompt = ANALYZER_SYSTEM_PROMPT.format(
            problem_description=problem_description,
            constraints=constraints,
            student_code=student_code,
            execution_output=execution_output
        )
        
        current_prompt = base_prompt
        last_error = None
        
        start_time = time.time()
        
        for attempt in range(self.max_retries + 1):
            try:
                # Add jittered backoff on retries (Circuit break prevention)
                if attempt > 0:
                    LLM_RETRIES.labels(provider=self.provider).inc()
                    await asyncio.sleep(2 ** attempt)
                    
                raw_json_str = await self._call_inference(current_prompt)
                
                # Sanitize block wrappers if LLM still spits markdown ```json
                raw_json_str = raw_json_str.strip()
                if raw_json_str.startswith("```json"):
                    raw_json_str = raw_json_str[7:-3].strip()
                elif raw_json_str.startswith("```"):
                    raw_json_str = raw_json_str[3:-3].strip()
                
                parsed_data = json.loads(raw_json_str)
                
                # Enforce strict Pydantic rules
                validated_model = AIAnalysisResponse(**parsed_data)
                
                # Simple heuristic token usage tracking for blueprint
                estimated_tokens = len(current_prompt) // 4 + len(raw_json_str) // 4
                LLM_TOKENS_USED.labels(provider=self.provider).inc(estimated_tokens)
                
                LLM_LATENCY_SECONDS.labels(provider=self.provider).observe(time.time() - start_time)
                
                return validated_model
                
            except json.JSONDecodeError as e:
                last_error = f"Invalid JSON generated: {e.msg} at line {e.lineno}"
                logger.warning(f"Attempt {attempt + 1}: {last_error}")
                # Auto-repair injection
                current_prompt = base_prompt + f"\n\nERROR IN PREVIOUS OUTPUT:\n{last_error}\nYou MUST return a valid JSON object matching the exact schema."
                
            except ValidationError as e:
                last_error = f"JSON Schema Validation Error: {e.errors()}"
                logger.warning(f"Attempt {attempt + 1}: {last_error}")
                current_prompt = base_prompt + f"\n\nSCHEMA ERROR IN PREVIOUS OUTPUT:\n{last_error}\nYou MUST correct these fields to match the required properties."
                
            except httpx.HTTPError as e:
                last_error = f"Network/Provider Error: {str(e)}"
                logger.error(f"Attempt {attempt + 1} failed due to network: {last_error}")
                if attempt == self.max_retries:
                    raise # Drop to circuit breaker upper level
        
        LLM_LATENCY_SECONDS.labels(provider=self.provider).observe(time.time() - start_time)
        # Fallback if unrecoverable
        raise Exception(f"Failed to generate valid analysis after {self.max_retries} retries. Last error: {last_error}")

def get_llm_service() -> LLMServiceBase:
    return FaultTolerantLLMService()
