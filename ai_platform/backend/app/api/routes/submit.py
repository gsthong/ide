from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.schemas.domain import SubmitCodeRequest, SubmissionResultResponse, AIAnalysisResponse
from app.api.dependencies import get_current_user_id, rate_limit, get_db_session
from app.core.celery_app import process_submission_task
from celery.result import AsyncResult

from app.db.models import Submission, Problem

router = APIRouter()

@router.post("/submit", dependencies=[Depends(rate_limit(15))])
async def submit_code(
    request: SubmitCodeRequest, 
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Ingests the submission. Validates code size limit handled by Pydantic.
    Pushes work to Celery Worker cluster to avoid blocking API threads.
    """
    # Verify Problem Exists (or mock for blueprint)
    stmt = select(Problem).where(Problem.id == request.problem_id)
    result = await db.execute(stmt)
    problem = result.scalar_one_or_none()
    
    if not problem:
        # Mock problem for blueprint purposes if empty DB
        mock_problem_desc = "Compute the Nth Fibonacci number."
        mock_constraints = "1 <= N <= 30"
        mock_tests = {
            "public": [{"id": "p1", "input": "5", "expected": "5", "weight": 1.0}],
            "hidden": [{"id": "h1", "input": "10", "expected": "55", "weight": 2.0}]
        }
    else:
        mock_problem_desc = problem.description
        mock_constraints = problem.constraints
        mock_tests = {
            "public": problem.public_test_cases,
            "hidden": problem.hidden_test_cases
        }

    # Create Submission Record
    new_submission = Submission(
        user_id=user_id,
        problem_id=request.problem_id if problem else None, # Allow null for blueprint mocked execution
        code=request.code,
        language=request.language,
        status="Pending"
    )
    db.add(new_submission)
    await db.commit()
    await db.refresh(new_submission)
    
    # 1. Dispatch background job
    task = process_submission_task.delay(
        submission_id=new_submission.id,
        student_code=request.code,
        language=request.language,
        test_cases=mock_tests,
        time_limit_ms=2000,
        memory_limit_mb=128,
        problem_description=mock_problem_desc,
        constraints=mock_constraints
    )
    
    return {"message": "Code submitted successfully.", "task_id": task.id, "submission_id": new_submission.id}

@router.get("/attempts/{task_id}", response_model=SubmissionResultResponse)
async def get_attempt_status(task_id: str):
    """
    Polling endpoint for Frontend to retrieve status. 
    In modern stacks, WebSockets would push this.
    """
    res = AsyncResult(task_id)
    if not res.ready():
        # Keep same rigid polling struct
        return SubmissionResultResponse(
            submission_id=-1, status="Pending", score=0.0, time_taken_ms=0, memory_used_mb=0.0, attempts=[], ai_analysis=None
        )
    
    data = res.get()
    
    # Cast ai_analysis back to strict Schema class
    analysis_obj = None
    if data["ai_analysis"] and "error" not in data["ai_analysis"]:
        analysis_obj = AIAnalysisResponse(**data["ai_analysis"])
        
    return SubmissionResultResponse(
        submission_id=data["submission_id"],
        status=data["results"]["status"],
        score=data["results"]["score"],
        time_taken_ms=data["results"]["time_taken_ms"],
        memory_used_mb=data["results"]["memory_used_mb"],
        attempts=data["results"]["attempts"],
        ai_analysis=analysis_obj
    )
