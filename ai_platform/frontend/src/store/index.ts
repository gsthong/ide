// store/index.ts
import { create } from 'zustand';
import { createEditorSlice, EditorSlice } from './editorSlice';
import { createTerminalSlice, TerminalSlice } from './terminalSlice';
import { createSubmissionSlice, SubmissionSlice } from './submissionSlice';

type StoreState = EditorSlice & TerminalSlice & SubmissionSlice;

export const useStore = create<StoreState>()((...a) => ({
    ...createEditorSlice(...a),
    ...createTerminalSlice(...a),
    ...createSubmissionSlice(...a),
}));
