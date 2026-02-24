// store/editorSlice.ts
import { StateCreator } from 'zustand';

export interface EditorSlice {
    code: string;
    language: string;
    theme: 'vs-dark' | 'light';
    isDirty: boolean;
    setCode: (code: string) => void;
    setLanguage: (lang: string) => void;
    setTheme: (theme: 'vs-dark' | 'light') => void;
    markClean: () => void;
}

const DEFAULT_CPP_CODE = `#include <iostream>
#include <vector>

using namespace std;

// Start coding here...
int main() {
    cout << "Ready for compilation!" << endl;
    return 0;
}
`;

export const createEditorSlice: StateCreator<EditorSlice> = (set) => ({
    code: DEFAULT_CPP_CODE,
    language: 'cpp',
    theme: 'vs-dark',
    isDirty: false,
    setCode: (code) => set({ code, isDirty: true }),
    setLanguage: (language) => set({ language }),
    setTheme: (theme) => set({ theme }),
    markClean: () => set({ isDirty: false }),
});
