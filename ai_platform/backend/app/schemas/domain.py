from pydantic import BaseModel, ConfigDict, Field
from typing import List, Literal, Optional, Dict
from datetime import datetime

# ==========================================
# Strict Schema for AI Output
# ==========================================
class TestCaseOutput(BaseModel):
    type: Literal["normal", "edge", "boundary", "stress"]
    input: str
    expected_output: str
    why_this_case_matters: str

class ErrorAnalysisOutput(BaseModel):
    error_type: Literal["syntax_error", "logic_error", "edge_case_missing", "infinite_loop", "time_limit_exceeded", "correct_solution", "memory_limit_exceeded"]
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str

class ComplexityAnalysisOutput(BaseModel):
    predicted_time_complexity: str
    space_complexity: str
    dominant_operation: str
    reasoning: str

class HintsOutput(BaseModel):
    hint_level_1: str
    hint_level_2: str
    hint_level_3: str
    common_mistake: str
    recommended_pattern: str

class AIAnalysisResponse(BaseModel):
    """
    Root JSON Schema strictly enforced for the LLM output.
    Used by the auto-repair loop.
    """
    model_config = ConfigDict(extra='forbid')
    
    error_analysis: ErrorAnalysisOutput
    complexity_analysis: ComplexityAnalysisOutput
    hints: HintsOutput
    test_cases: List[TestCaseOutput]

# ==========================================
# API Domain Schemas
# ==========================================
class SubmitCodeRequest(BaseModel):
    problem_id: int
    code: str = Field(..., max_length=50000) # Security: Input size limits
    language: Literal["python", "cpp", "java"] = "python"

class AttemptResult(BaseModel):
    test_case_id: str
    passed: bool
    status: str
    execution_time_ms: Optional[int]
    error_message: Optional[str]

class SubmissionResultResponse(BaseModel):
    submission_id: int
    status: str
    score: float
    time_taken_ms: Optional[int]
    memory_used_mb: Optional[float]
    attempts: List[AttemptResult]
    ai_analysis: Optional[AIAnalysisResponse] = None

class ProblemBase(BaseModel):
    title: str
    slug: str
    description: str
    constraints: str
    difficulty_level: int = Field(..., ge=1, le=10)
    time_limit_ms: int
    memory_limit_mb: int

class ProblemResponse(ProblemBase):
    id: int
    tags: List[str]
    model_config = ConfigDict(from_attributes=True)

class UserSkillResponse(BaseModel):
    elo_rating: float
    total_solved: int
    total_attempts: int
    weak_tags: Dict[str, float]
    model_config = ConfigDict(from_attributes=True)
