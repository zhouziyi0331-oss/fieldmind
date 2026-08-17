import { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useProjectStore } from './stores/projectStore';
import Sidebar from './components/Sidebar';
import Topbar from './components/Topbar';
import DataTicker from './components/DataTicker';
import Overview from './pages/Overview';
import MaterialImport from './pages/MaterialImport';
import KeywordUnlock from './pages/KeywordUnlock';
import BusinessAnalysis from './pages/BusinessAnalysis';
import Visualization from './pages/Visualization';
import ThinkingModel from './pages/ThinkingModel';
import SkillEcosystem from './pages/SkillEcosystem';
import './styles/globals.css';

function App() {
  const { fetchProjects, currentProject } = useProjectStore();

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  if (!currentProject) {
    return (
      <div className="loading-screen">
        <div className="loading-spinner"></div>
        <p>加载中...</p>
      </div>
    );
  }

  return (
    <BrowserRouter>
      <div className="app-container">
        <Sidebar />
        <div className="main-content">
          <Topbar />
          <DataTicker />
          <div className="page-content">
            <Routes>
              <Route path="/" element={<Navigate to="/overview" replace />} />
              <Route path="/overview" element={<Overview />} />
              <Route path="/materials" element={<MaterialImport />} />
              <Route path="/keywords" element={<KeywordUnlock />} />
              <Route path="/business" element={<BusinessAnalysis />} />
              <Route path="/visualization" element={<Visualization />} />
              <Route path="/thinking" element={<ThinkingModel />} />
              <Route path="/skills" element={<SkillEcosystem />} />
            </Routes>
          </div>
        </div>
        <div className="scan-line"></div>
      </div>
    </BrowserRouter>
  );
}

export default App;
