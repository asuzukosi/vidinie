import { createSlice, PayloadAction } from "@reduxjs/toolkit";

interface User {
    id: string;
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

const isWindowDefined = () => {
    return typeof window !== 'undefined';
};

const loadUserFromStorage = (): User | null => {
    // check if window is defined
    if (!isWindowDefined()) {
        console.error('window is not defined');
        return null; // return null if window is not defined
    }
    // load initial state from local storage
    try {
        const storedUser = localStorage.getItem('vidinie_user');
        if (storedUser) {
            return JSON.parse(storedUser);
        }
    } catch (error) {
        console.error('error loading user from local storage:', error);
        return null;
    }
    return null;
};

const initialState: UserState = {
    user: loadUserFromStorage(),
    isLoading: false,
    error: null,
};

const authSlice = createSlice({
    name: "auth",
    initialState,
    reducers: {
        setUser: (state, action: PayloadAction<User>) => {
            state.user = action.payload;
            // persist to local storage
            if (isWindowDefined()) {
                // try to save to local storage
                try {
                    localStorage.setItem('vidinie_user', JSON.stringify(action.payload));
                } catch (error) {
                    console.error('error saving user to local storage:', error);
                }
            } else {
                console.error('window is not defined');
            }
        },
        clearUser: (state) => {
            state.user = null;
            // clear from local storage
            if (isWindowDefined()) {
                // try to remove from local storage
                try {
                    localStorage.removeItem('vidinie_user');
                } catch (error) {
                    console.error('error removing user from local storage:', error);
                }
            } else {
                console.error('window is not defined');
            }
        },
        updateSubscription: (state, action: PayloadAction<string>) => {
            if (state.user) {
                state.user.current_subscription = action.payload;
            }
        },
        setEmail: (state, action: PayloadAction<string>) => {
            if (state.user) {
                state.user.email = action.payload;
            }
        },
    },
})

export const { setUser, clearUser, updateSubscription, setEmail } = authSlice.actions;
export default authSlice.reducer;
