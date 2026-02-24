'use client';

import React from 'react';
import { useStore } from '@/store';
import { AlertCircle, BrainCircuit, Clock, Cpu, Lightbulb, Target } from 'lucide-react';

export default function AIAnalysisPanel() {
    const { aiAnalysis, submissionStatus } = useStore();

    if (submissionStatus === 'submitting' || submissionStatus === 'polling') {
        return (
            <div className="w-full h-full bg-[#1e1e1e] p-4 flex flex-col items-center justify-center text-gray-400">
                <BrainCircuit className="w-8 h-8 animate-pulse mb-3" />
                <p>Analyzing code execution...</p>
            </div>
        );
    }

    if (!aiAnalysis) {
        return (
            <div className="w-full h-full bg-[#1e1e1e] p-4 flex flex-col items-center justify-center text-gray-500">
                <Target className="w-8 h-8 mb-3 opacity-50" />
                <p className="text-center text-sm px-4">
                    Submit your code to receive AI-powered complexity analysis, error diagnosis, and progressive hints.
                </p>
            </div>
        );
    }

    const { error_analysis, complexity_analysis, hints } = aiAnalysis;

    return (
        <div className="w-full h-full bg-[#1e1e1e] p-4 overflow-y-auto text-sm text-gray-300 space-y-6">
            <div className="flex items-center space-x-2 border-b border-gray-700 pb-2">
                <BrainCircuit className="w-5 h-5 text-indigo-400" />
                <h2 className="font-semibold text-white uppercase tracking-wider text-xs">AI Tutor Analysis</h2>
            </div>

            {/* Error Diagnosis */}
            {error_analysis && (
                <div className="space-y-2">
                    <div className="flex items-center space-x-2">
                        <AlertCircle className={`w-4 h-4 ${error_analysis.error_type === 'correct_solution' ? 'text-green-400' : 'text-red-400'}`} />
                        <h3 className="font-medium text-white">Diagnosis</h3>
                        <span className="text-xs px-2 py-0.5 rounded-full bg-gray-800 text-gray-300 border border-gray-600">
                            Confidence: {Math.round(error_analysis.confidence * 100)}%
                        </span>
                    </div>
                    <div className="bg-[#2d2d2d] p-3 rounded-md border border-gray-700">
                        <span className="inline-block px-2 py-0.5 mb-2 text-xs font-semibold rounded bg-red-900/50 text-red-300 border border-red-800">
                            {error_analysis.error_type.replace(/_/g, ' ').toUpperCase()}
                        </span>
                        <p className="leading-relaxed text-gray-300">{error_analysis.reasoning}</p>
                    </div>
                </div>
            )}

            {/* Complexity Metrics */}
            {complexity_analysis && (
                <div className="space-y-2">
                    <h3 className="font-medium text-white flex items-center space-x-2">
                        <Cpu className="w-4 h-4 text-blue-400" />
                        <span>Complexity</span>
                    </h3>
                    <div className="grid grid-cols-2 gap-3">
                        <div className="bg-[#2d2d2d] p-3 rounded-md border border-gray-700 flex flex-col justify-center">
                            <span className="text-xs text-gray-400 uppercase font-semibold mb-1 flex items-center"><Clock className="w-3 h-3 mr-1" /> Time</span>
                            <span className="font-mono text-blue-300 font-bold text-lg">{complexity_analysis.predicted_time_complexity}</span>
                        </div>
                        <div className="bg-[#2d2d2d] p-3 rounded-md border border-gray-700 flex flex-col justify-center">
                            <span className="text-xs text-gray-400 uppercase font-semibold mb-1">Space</span>
                            <span className="font-mono text-purple-300 font-bold text-lg">{complexity_analysis.space_complexity}</span>
                        </div>
                    </div>
                    <p className="text-xs text-gray-400 italic">Dominant Op: {complexity_analysis.dominant_operation}</p>
                </div>
            )}

            {/* Progressive Hints */}
            {hints && (
                <div className="space-y-3 pt-2">
                    <h3 className="font-medium text-white flex items-center space-x-2">
                        <Lightbulb className="w-4 h-4 text-yellow-500" />
                        <span>Progressive Hints</span>
                    </h3>

                    <details className="bg-[#252526] border border-gray-700 rounded-md group">
                        <summary className="p-3 text-sm font-medium cursor-pointer flex justify-between items-center text-gray-200">
                            Hint 1: Conceptual
                            <span className="text-xs text-blue-400 group-open:hidden">Reveal</span>
                        </summary>
                        <div className="p-3 border-t border-gray-700 text-gray-300 leading-relaxed bg-[#1e1e1e]">
                            {hints.hint_level_1}
                        </div>
                    </details>

                    <details className="bg-[#252526] border border-gray-700 rounded-md group">
                        <summary className="p-3 text-sm font-medium cursor-pointer flex justify-between items-center text-gray-200">
                            Hint 2: Approach
                            <span className="text-xs text-blue-400 group-open:hidden">Reveal</span>
                        </summary>
                        <div className="p-3 border-t border-gray-700 text-gray-300 leading-relaxed bg-[#1e1e1e]">
                            {hints.hint_level_2}
                        </div>
                    </details>

                    <div className="bg-blue-900/20 border border-blue-900/50 p-3 rounded-md mt-4">
                        <h4 className="text-xs uppercase text-blue-400 font-semibold mb-1">Recommended Pattern</h4>
                        <p className="text-gray-300">{hints.recommended_pattern}</p>
                    </div>
                </div>
            )}

        </div>
    );
}
