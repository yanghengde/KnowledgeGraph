import { lazy, Suspense } from "react";
import { Spin } from "antd";
import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "./components/AppShell";

const OverviewPage = lazy(() => import("./pages/OverviewPage").then((module) => ({ default: module.OverviewPage })));
const QueryLibraryPage = lazy(() => import("./pages/QueryLibraryPage").then((module) => ({ default: module.QueryLibraryPage })));
const AssistantPage = lazy(() => import("./pages/AssistantPage").then((module) => ({ default: module.AssistantPage })));

export default function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<Navigate to="overview" replace />} />
        <Route path="overview" element={<Suspense fallback={<Spin fullscreen />}><OverviewPage /></Suspense>} />
        <Route path="queries" element={<Suspense fallback={<Spin fullscreen />}><QueryLibraryPage /></Suspense>} />
        <Route path="assistant" element={<Suspense fallback={<Spin fullscreen />}><AssistantPage /></Suspense>} />
      </Route>
      <Route path="*" element={<Navigate to="overview" replace />} />
    </Routes>
  );
}
