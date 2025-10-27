import { Route, Routes } from 'react-router-dom';
import { Suspense } from 'react';
import { AppLayout } from '../components/Shared/AppLayout';
import { SmartTradePage } from '../components/SmartTrade/SmartTradePage';
import { LabPage } from '../components/Lab/LabPage';
import { DataPage } from '../components/Data/DataPage';
import { ReportsPage } from '../components/Reports/ReportsPage';
import { SettingsPage } from '../components/Settings/SettingsPage';
import { BotsPage } from '../components/SmartTrade/BotsPage';

const App = (): JSX.Element => (
  <AppLayout>
    <Suspense fallback={<div className="p-6 text-slate-400">Loading...</div>}>
      <Routes>
        <Route path="/" element={<SmartTradePage />} />
        <Route path="/smart" element={<SmartTradePage />} />
        <Route path="/bots" element={<BotsPage />} />
        <Route path="/lab" element={<LabPage />} />
        <Route path="/data" element={<DataPage />} />
        <Route path="/reports" element={<ReportsPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="*" element={<SmartTradePage />} />
      </Routes>
    </Suspense>
  </AppLayout>
);

export default App;
