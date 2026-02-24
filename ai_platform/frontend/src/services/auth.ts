import { UserResponse } from '../types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1';

export const login = async (username: string, password: string): Promise<{ access_token: string, token_type: string }> => {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    const response = await fetch(`${API_URL}/auth/login`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData.toString(),
        credentials: 'include',
    });

    if (!response.ok) {
        throw new Error('Login failed');
    }

    return response.json();
};

export const register = async (username: string, email: string, password: string): Promise<UserResponse> => {
    const response = await fetch(`${API_URL}/auth/register`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, email, password }),
        credentials: 'include',
    });

    if (!response.ok) {
        throw new Error('Registration failed');
    }

    return response.json();
};

export const logout = async (): Promise<void> => {
    await fetch(`${API_URL}/auth/logout`, {
        method: 'POST',
        credentials: 'include',
    });
};
