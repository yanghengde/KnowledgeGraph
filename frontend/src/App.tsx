import { lazy, Suspense } from "react";
import { Spin } from "antd";
import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "./components/layout/AppShell";

const ObjectExplorerPage = lazy(() => import("./pages/ObjectExplorerPage").then((module) => ({ default: module.ObjectExplorerPage })));
const OverviewPage = lazy(() => import("./pages/OverviewPage").then((module) => ({ default: module.OverviewPage })));
const QueryLibraryPage = lazy(() => import("./pages/QueryLibraryPage").then((module) => ({ default: module.QueryLibraryPage })));
const AssistantPage = lazy(() => import("./pages/AssistantPage").then((module) => ({ default: module.AssistantPage })));
const ConnectionsPage = lazy(() => import("./pages/ConnectionsPage").then((module) => ({ default: module.ConnectionsPage })));
const PublishManagementPage = lazy(() => import("./pages/PublishManagementPage").then((module) => ({ default: module.PublishManagementPage })));
const SemanticModelPage = lazy(() => import("./pages/SemanticModelPage").then((module) => ({ default: module.SemanticModelPage })));
const DataSynchronizationPage = lazy(() => import("./pages/DataSynchronizationPage").then((module) => ({ default: module.DataSynchronizationPage })));

export default function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<Navigate to="overview" replace />} />
        <Route path="overview" element={<Suspense fallback={<Spin fullscreen />}><OverviewPage /></Suspense>} />
        <Route path="queries" element={<Suspense fallback={<Spin fullscreen />}><QueryLibraryPage /></Suspense>} />
        <Route path="assistant" element={<Suspense fallback={<Spin fullscreen />}><AssistantPage /></Suspense>} />
        <Route path="connections" element={<Suspense fallback={<Spin fullscreen />}><ConnectionsPage /></Suspense>} />
        <Route path="data-sync" element={<Suspense fallback={<Spin fullscreen />}><DataSynchronizationPage /></Suspense>} />
        <Route path="publish" element={<Suspense fallback={<Spin fullscreen />}><PublishManagementPage /></Suspense>} />
        <Route path="object-explorer" element={<Suspense fallback={<Spin fullscreen />}><ObjectExplorerPage /></Suspense>} />
        <Route path="ontology-model" element={<Suspense fallback={<Spin fullscreen />}><SemanticModelPage /></Suspense>} />
        <Route path="ontology-governance" element={<Navigate to="../ontology-model" replace />} />
      </Route>
      <Route path="*" element={<Navigate to="overview" replace />} />
    </Routes>
  );
}
