import { useState, useEffect, useCallback } from 'react';
import type { ViewMode, HealthResponse } from './types';
import { ApiClient } from './api/client';
import { Shell } from './components/layout/Shell';
import { OverviewView } from './views/OverviewView';
import { VideoAnalysisView } from './views/VideoAnalysisView';
import { EventReviewView } from './views/EventReviewView';
import { GisOperationsView } from './views/GisOperationsView';
import { IncidentsView } from './views/IncidentsView';
import { ReportsAuditView } from './views/ReportsAuditView';

export function App() {
  const [currentView, setCurrentView] = useState<ViewMode>('overview');
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchHealth = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await ApiClient.getHealth();
      setHealth(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
      setHealth(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchHealth();
    // Poll health every 30 seconds
    const interval = setInterval(fetchHealth, 30000);
    return () => clearInterval(interval);
  }, [fetchHealth]);

  const renderView = () => {
    switch (currentView) {
      case 'overview':
        return (
          <OverviewView
            health={health}
            loading={loading}
            error={error}
            onRefreshHealth={fetchHealth}
            onNavigate={setCurrentView}
          />
        );
      case 'video_analysis':
        return <VideoAnalysisView />;
      case 'event_review':
        return <EventReviewView />;
      case 'gis_operations':
        return <GisOperationsView />;
      case 'incidents':
        return <IncidentsView onNavigateToGis={() => setCurrentView('gis_operations')} />;
      case 'reports_audit':
        return <ReportsAuditView />;
      default:
        return (
          <OverviewView
            health={health}
            loading={loading}
            error={error}
            onRefreshHealth={fetchHealth}
            onNavigate={setCurrentView}
          />
        );
    }
  };

  return (
    <Shell
      currentView={currentView}
      onNavigate={setCurrentView}
      health={health}
    >
      {renderView()}
    </Shell>
  );
}

export default App;
