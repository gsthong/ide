import json
import logging
import tempfile
from typing import Dict, Any, List
from core.docker_sandbox import execute_code_secure
from infrastructure.docker.cpp_sandbox import compile_cpp_secure, run_cpp_secure, cleanup_cpp_secure
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
        
        # --- Language Specific Optimization ---
        # For compiled languages like C++, we MUST compile once. 
        # Compiling dynamically per-test-case is incredibly slow (~1s per test)
        volume_name = None
        
        if language == "cpp":
            compile_results = await compile_cpp_secure(student_code)
            volume_name = compile_results.get("volume_name")
            
            if compile_results["error"]:
                # Fast fail if compilation breaks
                await cleanup_cpp_secure(volume_name)
                return {
                    "status": "Compilation Error",
                    "score": 0.0,
                    "time_taken_ms": 0,
                    "memory_used_mb": 0.0,
                    "attempts": [{
                        "test_case_id": case["id"],
                        "passed": False,
                        "execution_time_ms": 0,
                        "memory_used_mb": 0.0,
                        "error_message": compile_results["output"],
                        "status": "Compilation Error"
                    } for case in all_tests]
                }
        
        try:
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
                # Execute execution efficiently depending on language
                if language == "cpp":
                    execution = await run_cpp_secure(
                        volume_name=volume_name,
                        stdin_data=str(case['input']),
                        timeout_seconds=max(1, time_limit_ms // 1000),
                        memory_limit_mb=memory_limit_mb
                    )
                else:
                    execution = await execute_code_secure(
                        code=driver_code if language == "python" else student_code, 
                        language=language, 
                        timeout_seconds=max(1, time_limit_ms // 1000),
                        memory_limit_mb=memory_limit_mb
                    )
                
                # Actual Assertions: compare execution['output'].strip() against case['expected'].strip()
                passed = not execution["error"] and not execution["tle"]
                
                actual_output = execution.get("output", "")
                expected_output = str(case.get("expected", ""))
                
                if passed:
                    # Strip whitespace to be forgiving with trailing newlines/spaces
                    if actual_output.strip() == expected_output.strip():
                        earned_score += weight
                    else:
                        passed = False
                        all_passed = False
                        execution["status"] = "Wrong Answer"
                else:
                    all_passed = False
                    
                time_ms = execution.get("time_taken_ms", 0)
                mem_mb = execution.get("memory_used_mb", 0.0)
                
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
                
                
        finally:
            if language == "cpp" and volume_name:
                await cleanup_cpp_secure(volume_name)

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
