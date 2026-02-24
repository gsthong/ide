from celery import Celery
import os
import asyncio
from services.scoring_engine import ScoringEngine
from services.llm_service import get_llm_service

# Redis used as both broker and result backend for Celery
redis_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "ai_platform",
    broker=redis_url,
    backend=redis_url
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_time_limit=30,      # Absolute killer
    task_soft_time_limit=25  # Throw exception gracefully before hard kill
)

@celery_app.task(bind=True, max_retries=3)
def process_submission_task(self, submission_id: int, student_code: str, language: str, test_cases: dict, time_limit_ms: int, memory_limit_mb: int, problem_description: str, constraints: str):
    """
    Background worker that:
    1. Runs the code securely.
    2. Calls LLM if the code failed/TLE'd.
    3. Triggers DB update (skipped in raw Celery to avoid async DB conflicts, handled via REST callback normally).
    """
    loop = asyncio.get_event_loop()
    
    # Run scoring
    results = loop.run_until_complete(ScoringEngine.evaluate_submission(
        student_code, language, test_cases, time_limit_ms, memory_limit_mb
    ))
    
    ai_analysis = None
    if results["score"] < 100.0 or results["status"] != "Accepted":
        llm = get_llm_service()
        try:
            # We pick the first failed attempt's output to give the LLM context of the crash.
            crash_logs = next((attempt["error_message"] for attempt in results["attempts"] if not attempt["passed"]), "No crash logs.")
            
            analysis_obj = loop.run_until_complete(llm.analyze_code(
                problem_description=problem_description,
                constraints=constraints,
                student_code=student_code,
                execution_output=crash_logs
            ))
            # Pydantic dump for serialization
            ai_analysis = analysis_obj.model_dump()
        except Exception as e:
            ai_analysis = {"error": f"LLM Generation failed: {str(e)}"}
            
    return {
        "submission_id": submission_id,
        "results": results,
        "ai_analysis": ai_analysis
    }
