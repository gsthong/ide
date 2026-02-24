import { SubmissionResultResponse } from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export const submitCode = async (problemId: number, code: string, language: string) => {
    const response = await fetch(`${API_BASE_URL}/submit`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            problem_id: problemId,
            code,
            language,
        }),
        credentials: 'include',
    });

    if (!response.ok) {
        throw new Error('Failed to submit code');
    }

    return response.json(); // { message, task_id }
};

export const pollSubmissionStatus = async (taskId: string): Promise<SubmissionResultResponse> => {
    const response = await fetch(`${API_BASE_URL}/attempts/${taskId}`, {
        credentials: 'include',
    });

    if (!response.ok) {
        throw new Error('Failed to fetch status');
    }

    return response.json();
};
