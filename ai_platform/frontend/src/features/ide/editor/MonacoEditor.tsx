'use client';

import React from 'react';
import Editor, { useMonaco, Monaco } from '@monaco-editor/react';
import { useStore } from '@/store';

export default function MonacoEditor() {
    const monaco = useMonaco();
    const { code, language, theme, setCode } = useStore();

    // Custom configurations for C++ context
    React.useEffect(() => {
        if (monaco) {
            monaco.languages.typescript.javascriptDefaults.setEagerModelSync(true);
            // We can inject custom snippets for competitive programming here later
        }
    }, [monaco]);

    const handleEditorChange = (value: string | undefined) => {
        if (value !== undefined) {
            setCode(value);
        }
    };

    return (
        <div className="w-full h-full border border-gray-700 rounded overflow-hidden">
            <Editor
                height="100%"
                language={language}
                theme={theme}
                value={code}
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
