import { Spin } from "antd";
import { lazy,Suspense } from "react";
import { Navigate,Route,Routes } from "react-router-dom";
import { AppShell } from "./components/layout/AppShell";

const ObjectExplorerPage = lazy(() => import("./features/modeling/pages/ObjectExplorerPage").then((module) => ({ default: module.ObjectExplorerPage })));
const OverviewPage = lazy(() => import("./features/overview/pages/OverviewPage").then((module) => ({ default: module.OverviewPage })));
const QueryLibraryPage = lazy(() => import("./features/query/pages/QueryLibraryPage").then((module) => ({ default: module.QueryLibraryPage })));
const AssistantPage = lazy(() => import("./features/query/pages/AssistantPage").then((module) => ({ default: module.AssistantPage })));
const ConnectionsPage = lazy(() => import("./features/connections/pages/ConnectionsPage").then((module) => ({ default: module.ConnectionsPage })));
const PublishManagementPage = lazy(() => import("./features/publishing/pages/PublishManagementPage").then((module) => ({ default: module.PublishManagementPage })));
const SemanticModelPage = lazy(() => import("./features/modeling/pages/SemanticModelPage").then((module) => ({ default: module.SemanticModelPage })));
const DataSynchronizationPage = lazy(() => import("./features/sync/pages/DataSynchronizationPage").then((module) => ({ default: module.DataSynchronizationPage })));

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
