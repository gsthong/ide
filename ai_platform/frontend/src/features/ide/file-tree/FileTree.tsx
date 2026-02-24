import React from 'react';
import { useStore } from '@/store';
import { FileNode } from '@/store/fileTreeSlice';
import { ChevronRight, ChevronDown, File as FileIcon, FileCode2, Search, Plus, Trash2, Folder as FolderIcon, LucideIcon } from 'lucide-react';

export default function FileTree() {
    const { files, activeFileId, setActiveFile, toggleFolder } = useStore();

    // Utility to pick icon based on file extension
    const getFileIcon = (name: string): LucideIcon => {
        if (name.endsWith('.cpp') || name.endsWith('.h')) return FileCode2;
        if (name.endsWith('.md')) return FileIcon; // Markdown context
        return FileIcon;
    };

    const renderNode = (node: FileNode, level: number = 0) => {
        const isSelected = activeFileId === node.id;
        const indent = level * 16 + 8; // 16px per level, 8px base padding

        if (node.isFolder) {
            return (
                <div key={node.id} className="w-full flex flex-col">
                    <button
                        onClick={() => toggleFolder(node.id)}
                        className={`flex items-center w-full hover:bg-[#2a2d2e] py-1 text-sm text-gray-300 transition-colors group ${isSelected ? 'bg-[#37373d] text-white' : ''}`}
                        style={{ paddingLeft: `${indent}px` }}
                    >
                        <span className="w-4 h-4 flex items-center justify-center mr-1 text-gray-400 group-hover:text-gray-300">
                            {node.isOpen ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
                        </span>
                        <FolderIcon className="w-4 h-4 mr-2 text-blue-400" />
                        <span className="truncate">{node.name}</span>
                    </button>
                    {node.isOpen && node.children && (
                        <div className="flex flex-col">
                            {node.children.map(child => renderNode(child, level + 1))}
                        </div>
                    )}
                </div>
            );
        } else {
            const Icon = getFileIcon(node.name);
            return (
                <button
                    key={node.id}
                    onClick={() => setActiveFile(node.id)}
                    className={`flex items-center w-full hover:bg-[#2a2d2e] py-1 text-sm transition-colors group ${isSelected ? 'bg-[#37373d] text-white' : 'text-gray-300'}`}
                    style={{ paddingLeft: `${indent + 20}px` }} // +20px for alignment with folder chevons
                >
                    <Icon className={`w-4 h-4 mr-2 ${node.name.endsWith('.cpp') ? 'text-green-500' : 'text-gray-400'} shrink-0`} />
                    <span className="truncate">{node.name}</span>
                </button>
            );
        }
    };

    return (
        <div className="flex flex-col h-full bg-[#1e1e1e] border-r border-gray-800 shrink-0">
            {/* Explorer Header */}
            <div className="flex items-center justify-between px-4 py-2 text-xs font-semibold text-gray-400 uppercase tracking-wider">
                <span>Explorer</span>
                <div className="flex space-x-1">
                    <button className="p-1 hover:bg-[#2d2d2d] rounded transition-colors text-gray-400 hover:text-white" title="New File">
                        <Plus className="w-4 h-4" />
                    </button>
                    <button className="p-1 hover:bg-[#2d2d2d] rounded transition-colors text-gray-400 hover:text-white" title="Search">
                        <Search className="w-4 h-4" />
                    </button>
                </div>
            </div>

            {/* File List */}
            <div className="flex-1 overflow-y-auto py-2">
                {files.map(file => renderNode(file, 0))}
            </div>
        </div>
    );
}
