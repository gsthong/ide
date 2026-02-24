import { StateCreator } from 'zustand';
import { UserResponse } from '@/types';
import { login, register, logout } from '@/services/auth';

export interface AuthSlice {
    user: UserResponse | null;
    isAuthenticated: boolean;
    authLoading: boolean;
    loginAction: (username: string, password: string) => Promise<void>;
    registerAction: (username: string, email: string, password: string) => Promise<void>;
    logoutAction: () => Promise<void>;
}

export const createAuthSlice: StateCreator<AuthSlice> = (set) => ({
    user: null,
    isAuthenticated: false,
    authLoading: false,

    loginAction: async (username, password) => {
        set({ authLoading: true });
        try {
            const res = await login(username, password);
            // In a real app we'd fetch the user profile with the token or parse it
            set({
                user: { id: 1, username, email: "", is_active: true },
                isAuthenticated: true
            });
        } finally {
            set({ authLoading: false });
        }
    },

    registerAction: async (username, email, password) => {
        set({ authLoading: true });
        try {
            const user = await register(username, email, password);
            set({ user, isAuthenticated: true });
        } finally {
            set({ authLoading: false });
        }
    },

    logoutAction: async () => {
        set({ authLoading: true });
        try {
            await logout();
            set({ user: null, isAuthenticated: false });
        } finally {
            set({ authLoading: false });
        }
    }
});
