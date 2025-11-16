import { createContext, useContext } from "react";

export const AppContext = createContext();

export const useAppContext = () => {
    const context = useContext(AppContext);
    return context;
};