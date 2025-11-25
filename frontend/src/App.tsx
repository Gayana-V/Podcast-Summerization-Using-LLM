import { Route, Routes } from "react-router-dom";

import HomePage from "./pages/HomePage";
import StatusPage from "./pages/StatusPage";
import ResultsPage from "./pages/ResultsPage";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/status/:jobId" element={<StatusPage />} />
      <Route path="/results/:jobId" element={<ResultsPage />} />
    </Routes>
  );
}


