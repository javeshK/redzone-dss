import { Routes, Route, NavLink } from 'react-router-dom';
import Overview from './pages/Overview';
import RiskMap from './pages/RiskMap';
import HabitationPanel from './pages/HabitationPanel';
import RelocationPlanner from './pages/RelocationPlanner';
import { AppProvider } from './context/AppContext';
import ErrorBoundary from './components/ErrorBoundary';
import GlobalBanners from './components/GlobalBanners';

export default function App() {
  return (
    <AppProvider>
      <div className="app-shell">
        <header className="app-header">
          <div className="header-brand">
            <h1>RedZone DSS</h1>
            <span className="header-subtitle">
              AI-assisted, explainable GIS decision-support — Rudraprayag
            </span>
          </div>
          <nav className="app-nav">
            <NavLink to="/" end>Overview</NavLink>
            <NavLink to="/map">Risk Map</NavLink>
            <NavLink to="/habitation">Habitation</NavLink>
            <NavLink to="/planner">Relocation Planner</NavLink>
          </nav>
        </header>
        <GlobalBanners />
        <main className="app-main">
          <ErrorBoundary>
            <Routes>
              <Route path="/" element={<Overview />} />
              <Route path="/map" element={<RiskMap />} />
              <Route path="/habitation" element={<HabitationPanel />} />
              <Route path="/habitation/:id" element={<HabitationPanel />} />
              <Route path="/planner" element={<RelocationPlanner />} />
              <Route path="/planner/:id" element={<RelocationPlanner />} />
            </Routes>
          </ErrorBoundary>
        </main>
        <footer className="app-footer">
          Derived scores are not official government hazard zonation.
          Capacity is first-order physical screening capacity, not statutory capacity.
        </footer>
      </div>
    </AppProvider>
  );
}
