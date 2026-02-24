import json
import logging
from typing import List, Dict, Any
from core.docker_sandbox import execute_code_secure
from core.metrics import SUBMISSION_VERDICTS, SANDBOX_RUNTIME_SECONDS, SANDBOX_MEMORY_MB

logger = logging.getLogger(__name__)

class ScoringEngine:
    """
    Evaluates submitted code against both public and hidden test cases.
    Computes time, memory, partial scores, and aggregates results.
    """
    
    @staticmethod
    async def evaluate_submission(student_code: str, language: str, test_cases_json: dict, time_limit_ms: int, memory_limit_mb: int) -> Dict[str, Any]:
        """
        `test_cases_json` format: 
        {
          "public": [{"id": "p1", "input": "...", "expected": "...", "weight": 1.0}],
          "hidden": [{"id": "h1", "input": "...", "expected": "...", "weight": 2.0}]
        }
        """
        results_breakdown = []
        total_possible_score = 0.0
        earned_score = 0.0
        
        max_time_ms = 0
        peak_memory_mb = 0.0
        all_passed = True
        
        all_tests = test_cases_json.get("public", []) + test_cases_json.get("hidden", [])
        
        for case in all_tests:
            weight = float(case.get("weight", 1.0))
            total_possible_score += weight
            
            # Wrap standard code with driver block to inject stdin & read stdout
            # For Python, we just append a runner.
            driver_code = f"""
import sys

def solve():
{chr(10).join(['    ' + line for line in student_code.strip().split(chr(10))])}

if __name__ == '__main__':
    # Inject input artificially or override sys.stdin for real I/O
    # Real implementation would route case['input'] to sys.stdin optimally.
    input_data = {repr(case['input'])}
    # Mocking standard logic ...
    pass
"""
            # For this architectural blueprint we will execute the raw isolated string, 
            # normally we'd mount input files and pass stdin.
            # To execute efficiently per test case in isolation:
            execution = await execute_code_secure(
                code=student_code, 
                language=language, 
                timeout_seconds=max(1, time_limit_ms // 1000),
                memory_limit_mb=memory_limit_mb
            )
            
            # Simulating assertions for the blueprint.
            # In production: compare execution['output'].strip() against case['expected'].strip()
            # If matching exactly, passed = True.
            passed = not execution["error"] and not execution["tle"]
            
            time_ms = execution["time_taken_ms"]
            mem_mb = execution["memory_used_mb"]
            
            if passed:
                earned_score += weight
            else:
                all_passed = False
                
            max_time_ms = max(max_time_ms, time_ms)
            peak_memory_mb = max(peak_memory_mb, mem_mb)
            
            results_breakdown.append({
                "test_case_id": case["id"],
                "passed": passed,
                "execution_time_ms": time_ms,
                "memory_used_mb": mem_mb,
                "error_message": execution["output"] if not passed else None,
                "status": execution.get("status", "System Error")
            })
            
        final_score = (earned_score / total_possible_score * 100) if total_possible_score > 0 else 0.0
        
        # Aggregate the final verdict status based on all attempts
        # Priority of failure: Compilation Error > Runtime Error/SegFault > TLE/MLE > Wrong Answer
        status = "Accepted" if all_passed else "Wrong Answer"
        
        # Find highest priority error
        for r in results_breakdown:
            if r["status"] == "Compilation Error":
                status = "Compilation Error"
                break
            elif "Runtime Error" in r["status"] or "Segmentation Fault" in r["status"]:
                status = r["status"]
            elif "Time Limit Exceeded" in r["status"] and status not in ["Compilation Error", "Runtime Error", "Segmentation Fault"]:
                status = "Time Limit Exceeded"
            elif "Memory Limit Exceeded" in r["status"] and status not in ["Compilation Error", "Runtime Error", "Segmentation Fault", "Time Limit Exceeded"]:
                status = "Memory Limit Exceeded"
        
        if final_score == 0 and status == "Wrong Answer":
            status = "Failed"

        # Export Metrics to Prometheus
        SUBMISSION_VERDICTS.labels(status=status).inc()
        SANDBOX_RUNTIME_SECONDS.labels(language=language).observe(max_time_ms / 1000.0)
        SANDBOX_MEMORY_MB.labels(language=language).observe(peak_memory_mb)

        return {
            "status": status,
            "score": round(final_score, 2),
            "time_taken_ms": max_time_ms,
            "memory_used_mb": peak_memory_mb,
            "attempts": results_breakdown
        }
