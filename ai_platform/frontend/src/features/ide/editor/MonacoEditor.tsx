'use client';

import React from 'react';
import Editor, { useMonaco, Monaco } from '@monaco-editor/react';
import { useStore } from '@/store';

export default function MonacoEditor() {
    const monaco = useMonaco();
    const { language, theme, setCode } = useStore();
    const { files, activeFileId, updateFileContent } = useStore();

    // Helper to find active file
    const findActiveFile = (nodes: any[]): any | null => {
        for (const node of nodes) {
            if (node.id === activeFileId) return node;
            if (node.children) {
                const found = findActiveFile(node.children);
                if (found) return found;
            }
        }
        return null;
    };

    const activeFile = findActiveFile(files);
    const content = activeFile ? activeFile.content : '';

    // Custom configurations for C++ context
    React.useEffect(() => {
        if (monaco) {
            // We can inject custom snippets for competitive programming here later
        }
    }, [monaco]);

    const handleEditorChange = (value: string | undefined) => {
        if (value !== undefined && activeFileId) {
            updateFileContent(activeFileId, value);
            setCode(value); // Keep code in sync for submission
        }
    };

    return (
        <div className="w-full h-full border border-gray-700 rounded overflow-hidden">
            <Editor
                height="100%"
                language={language}
                theme={theme}
                value={content}
                onChange={handleEditorChange}
                options={{
                    minimap: { enabled: true },
                    fontSize: 14,
                    fontFamily: 'Consolas, "Courier New", monospace',
                    wordWrap: 'on',
                    automaticLayout: true,
                    scrollBeyondLastLine: false,
                    smoothScrolling: true,
                    cursorBlinking: 'smooth',
                    cursorSmoothCaretAnimation: 'on',
                    formatOnPaste: true,
                }}
                loading={<div className="text-gray-400 p-4">Loading Editor...</div>}
            />
        </div>
    );
}
