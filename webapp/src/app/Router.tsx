import { createBrowserRouter, RouterProvider, Navigate } from "react-router-dom";
import Layout from "./Layout";
import Dashboard from "@/components/Dashboard/Dashboard";
import SmartTrade from "@/components/SmartTrade/SmartTrade";
import Bots from "@/components/Bots/Bots";
import BotDetail from "@/components/Bots/BotDetail";
import Lab from "@/components/Lab/Lab";
import Data from "@/components/Data/Data";
import Reports from "@/components/Reports/Reports";
import Settings from "@/components/Settings/Settings";

const router = createBrowserRouter([
    {
        path: "/",
        element: <Layout />,
        children: [
            { path: "/", element: <Navigate to="/dashboard" replace /> },
            { path: "dashboard", element: <Dashboard /> },
            { path: "smart", element: <SmartTrade /> },
            { path: "bots", element: <Bots /> },
            { path: "bots/:botId", element: <BotDetail /> },
            { path: "lab", element: <Lab /> },
            { path: "data", element: <Data /> },
            { path: "reports", element: <Reports /> },
            { path: "settings", element: <Settings /> },
        ]
    }
]);

export function Router() {
    return <RouterProvider router={router} />;
}
