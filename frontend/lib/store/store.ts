import { configureStore } from "@reduxjs/toolkit";
import userReducer from "@/lib/store/slices/userSlice";

export const makeStore = () =>{
    return  configureStore({
    reducer: {
        auth: userReducer,
    },
});
}

export type AppStore = ReturnType<typeof makeStore>;
export type RootState = ReturnType<AppStore["getState"]>;
export type AppDispatch = AppStore["dispatch"];
