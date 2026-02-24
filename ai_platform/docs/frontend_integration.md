# Frontend Integration Guide (Production)

## Architecture Overview
The frontend communicates directly with the robust backend APIs. Long-running executions (the LLM + Sandboxes) are handled asynchronously via Celery. The frontend must **Poll** or utilize **WebSockets**.

## Contract Flow for `/submit`
1. **User Submits Code:**  
   POST `{"problem_id": 1, "code": "def solve():...", "language": "python"}` to `/api/v1/submit`.
2. **Backend Responds immediately:**  
   `{"message": "success", "task_id": "uuid..."}`
3. **Frontend Polls (or listens via SS/WS):**  
   GET `/api/v1/attempts/{task_id}` every 2 seconds.
4. **Processing Completion:**  
   Once the payload returns `status != 'Pending'`, execution is finished.
   If `results.score != 100`, the `ai_analysis` key will contain the strictly validated JSON matching your required schema.

## Strict AI Parsing Implementation (React/Monaco Example)
Because the backend implements a Fault-Tolerant auto-repair loop, the frontend no longer needs to worry about parsing broken JSON from the LLM. 

```tsx
// Once you receive the payload:
const attemptData = await response.json();

if (attemptData.ai_analysis) {
  const hints = attemptData.ai_analysis.hints;
  const metrics = attemptData.ai_analysis.complexity_analysis;

  // Render Time Complexity accurately based off strict object rules:
  renderStats(metrics.predicted_time_complexity, metrics.space_complexity);

  // Push Hint Level 1 into UI state progressively:
  expandHint(hints.hint_level_1);
}
```
