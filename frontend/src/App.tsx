import { useState } from 'react';
import { Routes, Route, NavLink } from 'react-router-dom';
import Overview from './pages/Overview';
import RiskMap from './pages/RiskMap';
import HabitationPanel from './pages/HabitationPanel';
import RelocationPlanner from './pages/RelocationPlanner';
import { AppProvider } from './context/AppContext';
import ErrorBoundary from './components/ErrorBoundary';
import GlobalBanners from './components/GlobalBanners';
import { t, setLang, getLang } from './i18n';

export default function App() {
  const [lang, setLangState] = useState(getLang());

  const toggleLang = () => {
    const next = lang === 'en' ? 'hi' : 'en';
    setLang(next);
    setLangState(next);
  };

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
            <NavLink to="/" end>{t('nav.overview')}</NavLink>
            <NavLink to="/map">{t('nav.map')}</NavLink>
            <NavLink to="/habitation">{t('nav.habitation')}</NavLink>
            <NavLink to="/planner">{t('nav.planner')}</NavLink>
            <button className="lang-toggle" onClick={toggleLang} title="Toggle Hindi/English">
              {lang === 'en' ? 'हिं' : 'EN'}
            </button>
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
          {t('disclaimer.derived')}
          {' '}
          {t('disclaimer.capacity')}
        </footer>
      </div>
    </AppProvider>
  );
}
