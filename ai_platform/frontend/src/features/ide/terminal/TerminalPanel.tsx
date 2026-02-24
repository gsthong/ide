'use client';

import React, { useEffect, useRef } from 'react';
import { Terminal } from 'xterm';
import { FitAddon } from '@xterm/addon-fit';
import { useStore } from '@/store';
import 'xterm/css/xterm.css';

export default function TerminalPanel() {
    const terminalRef = useRef<HTMLDivElement>(null);
    const xtermRef = useRef<Terminal | null>(null);
    const fitAddonRef = useRef<FitAddon | null>(null);
    const { output } = useStore();

    useEffect(() => {
        if (!terminalRef.current) return;

        // Initialize xterm.js
        const term = new Terminal({
            theme: {
                background: '#1e1e1e',
                foreground: '#d4d4d4',
                cursor: '#ffffff',
                selectionBackground: '#5da5d533',
                black: '#000000',
                red: '#cd3131',
                green: '#0dbc79',
                yellow: '#e5e510',
                blue: '#2472c8',
                magenta: '#bc3fbc',
                cyan: '#11a8cd',
                white: '#e5e5e5',
                brightBlack: '#666666',
                brightRed: '#f14c4c',
                brightGreen: '#23d18b',
                brightYellow: '#f5f543',
                brightBlue: '#3b8eea',
                brightMagenta: '#d670d6',
                brightCyan: '#29b8db',
                brightWhite: '#e5e5e5'
            },
            fontFamily: 'Consolas, "Courier New", monospace',
            fontSize: 14,
            cursorBlink: true,
            disableStdin: true, // Output only for now
        });

        const fitAddon = new FitAddon();
        term.loadAddon(fitAddon);

        term.open(terminalRef.current);

        // Only fit initially if we have dimensions
        if (terminalRef.current.clientWidth > 0 && terminalRef.current.clientHeight > 0) {
            try {
                fitAddon.fit();
            } catch (e) {
                console.warn("Initial xterm fit error ignored", e);
            }
        }

        xtermRef.current = term;
        fitAddonRef.current = fitAddon;

        // Handle resize
        const resizeObserver = new ResizeObserver(() => {
            // Need a tiny delay to ensure container has dimensions before calculating
            setTimeout(() => {
                if (fitAddonRef.current && terminalRef.current && terminalRef.current.clientWidth > 0 && terminalRef.current.clientHeight > 0) {
                    try {
                        fitAddonRef.current.fit();
                    } catch (e) {
                        console.warn("xterm fit error ignored", e);
                    }
                }
            }, 10);
        });

        resizeObserver.observe(terminalRef.current);

        return () => {
            resizeObserver.disconnect();
            term.dispose();
        };
    }, []);

    // Sync Zustand output state strictly to xterm
    useEffect(() => {
        if (xtermRef.current) {
            xtermRef.current.clear();
            // Handle line endings for xterm
            const formattedOutput = output.replace(/\n/g, '\r\n');
            xtermRef.current.write(formattedOutput);
        }
    }, [output]);

    return (
        <div className="w-full h-full bg-[#1e1e1e] p-2 overflow-hidden flex flex-col">
            <div className="text-xs text-gray-400 mb-2 uppercase tracking-wider font-semibold border-b border-gray-700 pb-1">
                Execution Terminal
            </div>
            <div ref={terminalRef} className="flex-1 w-full h-full" />
        </div>
    );
}
