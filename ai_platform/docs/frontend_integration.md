# Frontend Integration Guide (React + Monaco Editor)

## Architecture

We use React for the frontend and Microsoft's Monaco Editor for the web IDE environment.
When the user clicks "Run/Submit", the frontend fires a request to `/analyze`.

```tsx
import React, { useState } from 'react';
import Editor from '@monaco-editor/react';

function CodingPlatform() {
  const [code, setCode] = useState('def solve(nums):\\n    pass');
  const [hints, setHints] = useState(null);

  const handleAnalyze = async () => {
    const payload = {
      problem_description: "Find the sum of an array.",
      constraints: "1 <= len(nums) <= 10^5",
      student_code: code,
      language: "python"
    };

    const res = await fetch("http://localhost:8000/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    
    if (res.ok) {
        const analysis = await res.json();
        setHints(analysis.hints);
        console.log(analysis);
    }
  };

  return (
    <div style={{ display: 'flex', height: '100vh' }}>
      <div style={{ flex: 1, padding: '10px' }}>
        <h2>Problem Description</h2>
        <p>Find the sum of an array...</p>
        <button onClick={handleAnalyze}>Submit & Analyze</button>
        {hints && (
          <div className="hints-panel">
            <h4>Hints</h4>
            <p>1. {hints.hint_level_1}</p>
          </div>
        )}
      </div>
      <div style={{ flex: 1 }}>
        <Editor
          height="100vh"
          defaultLanguage="python"
          theme="vs-dark"
          value={code}
          onChange={(val) => setCode(val)}
        />
      </div>
    </div>
  );
}
```
