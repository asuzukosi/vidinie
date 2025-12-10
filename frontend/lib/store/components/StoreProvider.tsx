'use client';

import { Provider } from "react-redux";
import { useMemo, useRef } from "react";
import { AppStore, makeStore } from "@/lib/store/store";

export const StoreProvider = ({ children }: { children: React.ReactNode }) => {
    const storeRef = useRef<AppStore | null>(null);
    const store = useMemo(() => {
        if (!storeRef.current) {
            storeRef.current = makeStore();
        }
        return storeRef.current;
    }, []);
    return <Provider store={store}>{children}</Provider>;
}