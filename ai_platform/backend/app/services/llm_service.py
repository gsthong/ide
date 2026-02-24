import os
import json
from abc import ABC, abstractmethod
from typing import Dict, Any
from prompts.analyzer_prompt import ANALYZER_SYSTEM_PROMPT
import httpx

class LLMServiceBase(ABC):
    @abstractmethod
    async def analyze_code(self, problem_description: str, constraints: str, student_code: str, execution_output: str) -> Dict[str, Any]:
        pass

class GroqLLMService(LLMServiceBase):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.endpoint = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "llama3-70b-8192"

    async def analyze_code(self, problem_description: str, constraints: str, student_code: str, execution_output: str) -> Dict[str, Any]:
        prompt = ANALYZER_SYSTEM_PROMPT.format(
            problem_description=problem_description,
            constraints=constraints,
            student_code=student_code,
            execution_output=execution_output
        )
        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": prompt}],
            "response_format": {"type": "json_object"},
            "temperature": 0.1
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            resp = await client.post(self.endpoint, json=payload, headers=headers, timeout=30.0)
            resp.raise_for_status()
            data = resp.json()
            return json.loads(data["choices"][0]["message"]["content"])

class OllamaLLMService(LLMServiceBase):
    def __init__(self, host: str = "http://localhost:11434"):
        self.endpoint = f"{host}/api/generate"
        self.model = "deepseek-coder:latest"

    async def analyze_code(self, problem_description: str, constraints: str, student_code: str, execution_output: str) -> Dict[str, Any]:
        prompt = ANALYZER_SYSTEM_PROMPT.format(
            problem_description=problem_description,
            constraints=constraints,
            student_code=student_code,
            execution_output=execution_output
        )
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json"
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(self.endpoint, json=payload, timeout=60.0)
            resp.raise_for_status()
            return json.loads(resp.json()["response"])

# Factory pattern to load LLM dynamically
def get_llm_service() -> LLMServiceBase:
    provider = os.getenv("LLM_PROVIDER", "ollama").lower()
    if provider == "groq":
        return GroqLLMService(api_key=os.environ["GROQ_API_KEY"])
    elif provider == "together":
        # Implementation for Together AI via OpenAI compatible routes
        return GroqLLMService(api_key=os.environ.get("TOGETHER_API_KEY")) 
    else:
        return OllamaLLMService(host=os.getenv("OLLAMA_HOST", "http://localhost:11434"))
