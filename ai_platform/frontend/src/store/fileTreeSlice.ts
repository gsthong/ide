import { StateCreator } from 'zustand';

export interface FileNode {
    id: string;
    name: string;
    isFolder: boolean;
    children?: FileNode[];
    content?: string;
    isOpen?: boolean;
}

export interface FileTreeSlice {
    files: FileNode[];
    activeFileId: string | null;
    openFiles: string[]; // List of file IDs currently open in editor tabs

    setFiles: (files: FileNode[]) => void;
    setActiveFile: (id: string) => void;
    addOpenFile: (id: string) => void;
    removeOpenFile: (id: string) => void;
    updateFileContent: (id: string, content: string) => void;
    toggleFolder: (id: string) => void;
}

const initialFiles: FileNode[] = [
    {
        id: '1',
        name: 'src',
        isFolder: true,
        isOpen: true,
        children: [
            {
                id: '2',
                name: 'main.cpp',
                isFolder: false,
                content: '#include <iostream>\nusing namespace std;\n\nint main() {\n    int n;\n    if (cin >> n) {\n        cout << 5 << endl;\n    }\n    return 0;\n}\n'
            },
            {
                id: '3',
                name: 'utils.cpp',
                isFolder: false,
                content: '// Utility functions\n'
            }
        ]
    },
    {
        id: '4',
        name: 'README.md',
        isFolder: false,
        content: '# AI Coding Challenge\n\nSolve the problem defined in the prompt.\n'
    }
];

export const createFileTreeSlice: StateCreator<FileTreeSlice> = (set, get) => ({
    files: initialFiles,
    activeFileId: '2',
    openFiles: ['2'],

    setFiles: (files) => set({ files }),

    setActiveFile: (id) => {
        const { openFiles } = get();
        if (!openFiles.includes(id)) {
            set({ openFiles: [...openFiles, id], activeFileId: id });
        } else {
            set({ activeFileId: id });
        }
    },

    addOpenFile: (id) => {
        const { openFiles } = get();
        if (!openFiles.includes(id)) {
            set({ openFiles: [...openFiles, id] });
        }
    },

    removeOpenFile: (id) => {
        const { openFiles, activeFileId } = get();
        const newOpenFiles = openFiles.filter(fid => fid !== id);
        let newActiveFileId = activeFileId;

        if (activeFileId === id) {
            newActiveFileId = newOpenFiles.length > 0 ? newOpenFiles[0] : null;
        }

        set({ openFiles: newOpenFiles, activeFileId: newActiveFileId });
    },

    updateFileContent: (id, content) => {
        set((state) => {
            // Helper to recursively update file content
            const updateFileContentRecursive = (nodes: FileNode[]): FileNode[] => {
                return nodes.map(node => {
                    if (node.id === id && !node.isFolder) {
                        return { ...node, content };
                    }
                    if (node.isFolder && node.children) {
                        return { ...node, children: updateFileContentRecursive(node.children) };
                    }
                    return node;
                });
            };

            return { files: updateFileContentRecursive(state.files) };
        });
    },

    toggleFolder: (id) => {
        set((state) => {
            const toggleFolderRecursive = (nodes: FileNode[]): FileNode[] => {
                return nodes.map(node => {
                    if (node.id === id && node.isFolder) {
                        return { ...node, isOpen: !node.isOpen };
                    }
                    if (node.isFolder && node.children) {
                        return { ...node, children: toggleFolderRecursive(node.children) };
                    }
                    return node;
                });
            };

            return { files: toggleFolderRecursive(state.files) };
        });
    }
});
