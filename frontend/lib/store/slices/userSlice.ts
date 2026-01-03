import { createSlice, PayloadAction } from "@reduxjs/toolkit";

interface User {
    id: string;
    name: string;
    email: string;
    token: string;
    created_at?: string;
    updated_at?: string;
    is_verified?: boolean;
    current_subscription?: string | null;
    profile_picture?: string | null;
    stripe_customer_id?: string | null;
}

interface UserState {
    user: User | null;
    isLoading: boolean;
    error: string | null;
}

// load initial state from local storage
const loadUserFromStorage = (): User | null => {
    if (typeof window === 'undefined') return null;
    try {
        const storedUser = localStorage.getItem('vidinie_user');
        if (storedUser) {
            return JSON.parse(storedUser);
        }
    } catch (error) {
        console.error('error loading user from local storage:', error);
    }
    return null;
};

const initialState: UserState = {
    user: loadUserFromStorage(),
    isLoading: false,
    error: null,
};

const userSlice = createSlice({
    name: "auth",
    initialState,
    reducers: {
        setUser: (state, action: PayloadAction<User>) => {
            state.user = action.payload;
            // persist to local storage
            if (typeof window !== 'undefined') {
                try {
                    localStorage.setItem('vidinie_user', JSON.stringify(action.payload));
                } catch (error) {
                    console.error('error saving user to local storage:', error);
                }
            }
        },
        clearUser: (state) => {
            state.user = null;
            // clear from local storage
            if (typeof window !== 'undefined') {
                try {
                    localStorage.removeItem('vidinie_user');
                } catch (error) {
                    console.error('error removing user from local storage:', error);
                }
            }
        },
    },
})

export const { setUser, clearUser } = userSlice.actions;
export default userSlice.reducer;
