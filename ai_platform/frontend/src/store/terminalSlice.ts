// store/terminalSlice.ts
import { StateCreator } from 'zustand';

export interface TerminalSlice {
    output: string;
    isExecuting: boolean;
    appendOutput: (text: string) => void;
    clearOutput: () => void;
    setExecuting: (executing: boolean) => void;
}

export const createTerminalSlice: StateCreator<TerminalSlice> = (set) => ({
    output: 'Terminal ready.\n> ',
    isExecuting: false,
    appendOutput: (text) => set((state) => ({ output: state.output + text })),
    clearOutput: () => set({ output: '' }),
    setExecuting: (isExecuting) => set({ isExecuting }),
});
