import { BrowserRouter, Routes, Route } from "react-router-dom";

import ProjectsPage from "./pages/projects/ProjectsPage";
import ProjectPage from "./pages/projects/ProjectPage";
import RunPage from "./pages/run/RunPage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<ProjectsPage />} />

        <Route
          path="/projects/:projectId"
          element={<ProjectPage />}
        />
        <Route
  path="/projects/:projectId/runs/:runId"
  element={<RunPage />}
/>
      </Routes>
    </BrowserRouter>
  );
}