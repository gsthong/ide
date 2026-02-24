// store/submissionSlice.ts
import { StateCreator } from 'zustand';
import { SubmissionResultResponse, AIAnalysisResponse } from '@/types';

export interface SubmissionSlice {
    currentTaskId: string | null;
    submissionStatus: 'idle' | 'submitting' | 'polling' | 'completed' | 'error';
    lastResult: SubmissionResultResponse | null;
    aiAnalysis: AIAnalysisResponse | null;

    setSubmissionState: (taskId: string, status: 'submitting' | 'polling') => void;
    setSubmissionResult: (result: SubmissionResultResponse) => void;
    setSubmissionError: () => void;
    resetSubmission: () => void;
}

export const createSubmissionSlice: StateCreator<SubmissionSlice> = (set) => ({
    currentTaskId: null,
    submissionStatus: 'idle',
    lastResult: null,
    aiAnalysis: null,

    setSubmissionState: (taskId, status) => set({
        currentTaskId: taskId,
        submissionStatus: status
    }),

    setSubmissionResult: (result) => set({
        lastResult: result,
        submissionStatus: 'completed',
        aiAnalysis: result.ai_analysis,
        currentTaskId: null
    }),

    setSubmissionError: () => set({
        submissionStatus: 'error',
        currentTaskId: null
    }),

    resetSubmission: () => set({
        submissionStatus: 'idle',
        lastResult: null,
        aiAnalysis: null,
        currentTaskId: null
    }),
});
