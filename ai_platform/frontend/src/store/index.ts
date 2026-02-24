// store/index.ts
import { create } from 'zustand';
import { createEditorSlice, EditorSlice } from './editorSlice';
import { createTerminalSlice, TerminalSlice } from './terminalSlice';
import { createSubmissionSlice, SubmissionSlice } from './submissionSlice';
import { createAuthSlice, AuthSlice } from './authSlice';
import { createFileTreeSlice, FileTreeSlice } from './fileTreeSlice';

type StoreState = EditorSlice & TerminalSlice & SubmissionSlice & AuthSlice & FileTreeSlice;

export const useStore = create<StoreState>()((...a) => ({
    ...createEditorSlice(...a),
    ...createTerminalSlice(...a),
    ...createSubmissionSlice(...a),
    ...createAuthSlice(...a),
    ...createFileTreeSlice(...a),
}));
