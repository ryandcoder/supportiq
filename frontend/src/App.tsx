import { Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import { AppStateProvider } from "./context/AppState";
import Breakdowns from "./pages/Breakdowns";
import DataQuality from "./pages/DataQuality";
import InsightsPage from "./pages/InsightsPage";
import Overview from "./pages/Overview";
import Report from "./pages/Report";
import Team from "./pages/Team";
import Tickets from "./pages/Tickets";
import Upload from "./pages/Upload";

export default function App() {
  return (
    <AppStateProvider>
      <Routes>
        <Route path="/report" element={<Report />} />
        <Route element={<Layout />}>
          <Route path="/" element={<Overview />} />
          <Route path="/breakdowns" element={<Breakdowns />} />
          <Route path="/insights" element={<InsightsPage />} />
          <Route path="/team" element={<Team />} />
          <Route path="/tickets" element={<Tickets />} />
          <Route path="/data-quality" element={<DataQuality />} />
          <Route path="/upload" element={<Upload />} />
        </Route>
      </Routes>
    </AppStateProvider>
  );
}
