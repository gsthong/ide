'use client';

import React from 'react';
import { Panel, Group as PanelGroup, Separator as PanelResizeHandle } from 'react-resizable-panels';
import MonacoEditor from '@/features/ide/editor/MonacoEditor';
import TerminalPanel from '@/features/ide/terminal/TerminalPanel';
import AIAnalysisPanel from '@/features/ide/ai-panel/AIAnalysisPanel';
import AuthModal from '@/features/auth/AuthModal';
import { useStore } from '@/store';
import { Play, Loader2, UserCircle, LogOut } from 'lucide-react';
import { submitCode, pollSubmissionStatus } from '@/services/api';

export default function Home() {
  const {
    code,
    language,
    appendOutput,
    clearOutput,
    setExecuting,
    isExecuting,
    submissionStatus,
    setSubmissionState,
    setSubmissionResult,
    setSubmissionError,
    isAuthenticated,
    user,
    logoutAction
  } = useStore();

  const [isAuthModalOpen, setIsAuthModalOpen] = React.useState(false);

  const handleRunCode = async () => {
    if (isExecuting) return;

    clearOutput();
    setExecuting(true);
    appendOutput('Starting compilation...\r\n');
    setSubmissionState('pending', 'submitting');

    try {
      // 1. Submit Code
      const submitResponse = await submitCode(1, code, language);
      const taskId = submitResponse.task_id;
      appendOutput(`Task Queued: ${taskId}\r\n`);
      setSubmissionState(taskId, 'polling');

      // 2. Poll Status
      let attemptResult = null;
      let polling = true;
      while (polling) {
        await new Promise(resolve => setTimeout(resolve, 1000));
        const statusResponse = await pollSubmissionStatus(taskId);

        if (statusResponse.status !== 'Processing' && statusResponse.status !== 'Pending') {
          attemptResult = statusResponse;
          polling = false;
        } else {
          appendOutput('.');
        }
      }

      // 3. Render Results
      if (attemptResult) {
        setSubmissionResult(attemptResult);
        appendOutput('\r\n\r\n=== Execution Report ===\r\n');
        appendOutput(`Status: ${attemptResult.status}\r\n`);
        appendOutput(`Score: ${attemptResult.score}\r\n`);

        if (attemptResult.time_taken_ms) appendOutput(`Time: ${attemptResult.time_taken_ms}ms\r\n`);
        if (attemptResult.memory_used_mb) appendOutput(`Memory: ${attemptResult.memory_used_mb}MB\r\n`);

        if (attemptResult.attempts && attemptResult.attempts.length > 0) {
          appendOutput('\r\nTest Cases:\r\n');
          attemptResult.attempts.forEach((a: any, i: number) => {
            appendOutput(`[Test ${i + 1}] ${a.passed ? 'PASS' : 'FAIL'} - ${a.status} (${a.execution_time_ms}ms)\r\n`);
            if (a.error_message) {
              appendOutput(`  -> ${a.error_message}\r\n`);
            }
          });
        }
      }

    } catch (error) {
      appendOutput(`\r\nError: ${String(error)}\r\n`);
      setSubmissionError();
    } finally {
      setExecuting(false);
    }
  };

  return (
    <div className="h-screen w-screen bg-[#111111] text-white flex flex-col font-sans overflow-hidden">

      {/* Top Navigation Bar */}
      <header className="h-14 border-b border-gray-800 bg-[#181818] flex items-center justify-between px-6 shrink-0 z-10">
        <div className="flex items-center space-x-4">
          <div className="w-8 h-8 bg-blue-600 rounded flex items-center justify-center font-bold text-lg">C++</div>
          <h1 className="font-semibold tracking-wide flex items-center">
            AI Coding Platform
            <span className="ml-3 px-2 py-0.5 text-xs bg-gray-800 rounded text-gray-400 border border-gray-700">Enterprise</span>
          </h1>
        </div>

        <div className="flex items-center space-x-4">
          {isAuthenticated ? (
            <div className="flex items-center space-x-3 text-sm border-r border-gray-700 pr-4 mr-1">
              <UserCircle className="w-5 h-5 text-gray-400" />
              <span className="font-medium text-gray-200">{user?.username}</span>
              <button onClick={() => logoutAction()} className="text-gray-500 hover:text-red-400 transition-colors" title="Logout">
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <button
              onClick={() => setIsAuthModalOpen(true)}
              className="text-sm font-medium text-gray-300 hover:text-white border-r border-gray-700 pr-4 mr-1 transition-colors"
            >
              Sign In
            </button>
          )}

          <button
            onClick={handleRunCode}
            disabled={isExecuting || submissionStatus === 'submitting' || submissionStatus === 'polling'}
            className="flex items-center space-x-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-900/50 disabled:cursor-not-allowed text-white px-4 py-1.5 rounded text-sm font-medium transition-colors border border-blue-500 disabled:border-blue-900/50"
          >
            {isExecuting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
            <span>{isExecuting ? 'Running...' : 'Run Code'}</span>
          </button>
        </div>
      </header>

      {/* Main IDE Layout */}
      <main className="flex-1 h-[calc(100vh-3.5rem)]">
        <PanelGroup orientation="horizontal">

          {/* Left Column: Editor & Terminal */}
          <Panel defaultSize={70} minSize={30}>
            <PanelGroup orientation="vertical">
              <Panel defaultSize={70} minSize={20}>
                <div className="h-full border-r border-b border-gray-800 bg-[#1e1e1e]">
                  <MonacoEditor />
                </div>
              </Panel>

              <PanelResizeHandle className="h-2 bg-[#252526] hover:bg-blue-600 transition-colors cursor-row-resize flex items-center justify-center border-r border-gray-800">
                <div className="w-16 h-1 bg-gray-600 rounded-full" />
              </PanelResizeHandle>

              <Panel defaultSize={30} minSize={10}>
                <div className="h-full border-r border-gray-800">
                  <TerminalPanel />
                </div>
              </Panel>
            </PanelGroup>
          </Panel>

          <PanelResizeHandle className="w-2 bg-[#252526] hover:bg-blue-600 transition-colors cursor-col-resize flex flex-col items-center justify-center">
            <div className="h-16 w-1 bg-gray-600 rounded-full" />
          </PanelResizeHandle>

          {/* Right Column: AI Tutor Panel */}
          <Panel defaultSize={30} minSize={20}>
            <div className="h-full border-l border-gray-800">
              <AIAnalysisPanel />
            </div>
          </Panel>

        </PanelGroup>
      </main>

      {/* Auth Modal Overlay */}
      <AuthModal isOpen={isAuthModalOpen} onClose={() => setIsAuthModalOpen(false)} />
    </div>
  );
}
