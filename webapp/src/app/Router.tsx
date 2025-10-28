import { createBrowserRouter, RouterProvider, Navigate } from "react-router-dom";
import Layout from "./Layout";
import Dashboard from "@/components/Dashboard/Dashboard";
import SmartTrade from "@/components/SmartTrade/SmartTrade";
import Bots from "@/components/Bots/Bots";
import BotDetail from "@/components/Bots/BotDetail";
import Lab from "@/components/Lab/Lab";
import { StrategyLab } from "@/components/Lab/StrategyLab/StrategyLab";
import { RunResults } from "@/components/Lab/StrategyLab/RunResults";
import { CompareRuns } from "@/components/Lab/StrategyLab/CompareRuns";
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
            { path: "lab/strategy", element: <StrategyLab /> },
            { path: "lab/results/:runId", element: <RunResults /> },
            { path: "lab/compare", element: <CompareRuns /> },
            { path: "data", element: <Data /> },
            { path: "reports", element: <Reports /> },
            { path: "settings", element: <Settings /> },
        ]
    }
]);

export function Router() {
    return <RouterProvider router={router} />;
}