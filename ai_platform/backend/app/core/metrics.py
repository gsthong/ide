from prometheus_client import Counter, Histogram, Gauge

# Sandbox Execution Metrics
SANDBOX_RUNTIME_SECONDS = Histogram(
    'sandbox_runtime_seconds',
    'Time spent executing code in the docker sandbox',
    ['language']
)

SANDBOX_MEMORY_MB = Histogram(
    'sandbox_memory_mb',
    'Peak memory used by code execution in the docker sandbox',
    ['language']
)

# Verdict Distribution
SUBMISSION_VERDICTS = Counter(
    'submission_verdicts_total',
    'Count of submission verdicts',
    ['status']
)

# LLM Intelligence Metrics
LLM_LATENCY_SECONDS = Histogram(
    'llm_latency_seconds',
    'Latency of LLM API calls for AI Tutor',
    ['provider']
)

LLM_RETRIES = Counter(
    'llm_retries_total',
    'Number of retries when parsing strict JSON from LLM',
    ['provider']
)

LLM_TOKENS_USED = Counter(
    'llm_tokens_total',
    'Total LLM tokens consumed',
    ['provider']
)

# Celery Queue Depth
CELERY_QUEUE_DEPTH = Gauge(
    'celery_queue_depth',
    'Number of pending tasks in the celery submission queue' 
)
