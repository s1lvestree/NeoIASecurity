import { BrowserRouter, Routes, Route, useLocation } from 'react-router';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { Dashboard } from './pages/Dashboard';
import { TechnicalCopilotPage } from './pages/TechnicalCopilotPage';
import { GovernancePage } from './pages/GovernancePage';

function AppContent() {
  const location = useLocation();
  const showHeader = location.pathname === '/';
  const isFullHeight = location.pathname === '/technical';

  return (
    <div className="size-full flex bg-background dark">
      <Sidebar />

      <main className={`min-h-0 min-w-0 flex-1 ${isFullHeight ? 'overflow-hidden' : 'overflow-auto'}`}>
        {showHeader && <Header />}
        <div className={isFullHeight ? "h-full min-h-0" : (showHeader ? "p-8" : "")}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/technical" element={<TechnicalCopilotPage />} />
            <Route path="/governance" element={<GovernancePage />} />
            <Route path="/settings" element={
              <div className="text-center py-20">
                <h2 className="text-2xl font-bold text-foreground mb-2">Configurações</h2>
                <p className="text-muted-foreground">Em breve...</p>
              </div>
            } />
          </Routes>
        </div>
      </main>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  );
}
