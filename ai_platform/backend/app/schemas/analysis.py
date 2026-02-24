from pydantic import BaseModel, ConfigDict
from typing import List, Literal, Optional

class TestCase(BaseModel):
    type: Literal["normal", "edge", "boundary", "stress"]
    input: str
    expected_output: str
    why_this_case_matters: str

class ErrorAnalysis(BaseModel):
    error_type: Literal["syntax_error", "logic_error", "edge_case_missing", "infinite_loop", "time_limit_exceeded", "correct_solution"]
    confidence: float
    reasoning: str

class ComplexityAnalysis(BaseModel):
    predicted_time_complexity: str
    space_complexity: str
    dominant_operation: str
    reasoning: str

class Hints(BaseModel):
    hint_level_1: str
    hint_level_2: str
    hint_level_3: str
    common_mistake: str
    recommended_pattern: str

class AnalysisResponse(BaseModel):
    """
    Root JSON Schema strictly enforcing the requested response structure from the Analyzer.
    """
    model_config = ConfigDict(extra='forbid')
    
    error_analysis: ErrorAnalysis
    complexity_analysis: ComplexityAnalysis
    hints: Hints
    test_cases: List[TestCase]

class AnalysisRequest(BaseModel):
    problem_description: str
    constraints: str
    student_code: str
    language: str = "python"
