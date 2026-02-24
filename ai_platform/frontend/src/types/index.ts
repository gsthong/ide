// types/index.ts
export interface AttemptResult {
    test_case_id: string;
    passed: boolean;
    status: string;
    execution_time_ms: number | null;
    error_message: string | null;
}

export interface TestCaseOutput {
    type: "normal" | "edge" | "boundary" | "stress";
    input: string;
    expected_output: string;
    why_this_case_matters: string;
}

export interface ErrorAnalysisOutput {
    error_type: "syntax_error" | "logic_error" | "edge_case_missing" | "infinite_loop" | "time_limit_exceeded" | "correct_solution" | "memory_limit_exceeded";
    confidence: number;
    reasoning: string;
}

export interface ComplexityAnalysisOutput {
    predicted_time_complexity: string;
    space_complexity: string;
    dominant_operation: string;
    reasoning: string;
}

export interface HintsOutput {
    hint_level_1: string;
    hint_level_2: string;
    hint_level_3: string;
    common_mistake: string;
    recommended_pattern: string;
}

export interface AIAnalysisResponse {
    error_analysis: ErrorAnalysisOutput;
    complexity_analysis: ComplexityAnalysisOutput;
    hints: HintsOutput;
    test_cases: TestCaseOutput[];
}

export interface SubmissionResultResponse {
    submission_id: number;
    status: string;
    score: number;
    time_taken_ms: number | null;
    memory_used_mb: number | null;
    attempts: AttemptResult[];
    ai_analysis: AIAnalysisResponse | null;
}
