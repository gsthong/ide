from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from schemas.analysis import AnalysisRequest, AnalysisResponse
from services.llm_service import get_llm_service, LLMServiceBase
from core.docker_sandbox import execute_code
import time

app = FastAPI(title="AI Coding Platform API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_submission(
    request: AnalysisRequest, 
    llm: LLMServiceBase = Depends(get_llm_service)
):
    """
    1. Runs the student code in the Docker sandbox.
    2. Gathers execution results (stdout, stderr, timeout).
    3. Calls the LLM to analyze the logic.
    """
    execution_result = await execute_code(request.student_code, language=request.language)
    
    # Offload the prompt formatting and inference to the chosen LLM provider
    start_time = time.time()
    try:
        # Request strict JSON as per schema requirements
        analysis = await llm.analyze_code(
            problem_description=request.problem_description,
            constraints=request.constraints,
            student_code=request.student_code,
            execution_output=execution_result["output"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    return analysis
