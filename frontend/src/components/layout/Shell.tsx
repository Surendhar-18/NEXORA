import React, { useState, useEffect } from 'react';
import type { ViewMode, HealthResponse, UserProfile } from '../../types';
import { StatusBadge } from '../common/StatusBadge';
import { ApiClient } from '../../api/client';

interface ShellProps {
  currentView: ViewMode;
  onNavigate: (view: ViewMode) => void;
  health: HealthResponse | null;
  children: React.ReactNode;
}

export const Shell: React.FC<ShellProps> = ({
  currentView,
  onNavigate,
  health,
  children,
}) => {
  const [currentUser, setCurrentUser] = useState<UserProfile | null>(null);
  const [showLoginModal, setShowLoginModal] = useState<boolean>(false);
  const [usernameInput, setUsernameInput] = useState<string>('');
  const [passwordInput, setPasswordInput] = useState<string>('');
  const [loginError, setLoginError] = useState<string | null>(null);
  const [loginLoading, setLoginLoading] = useState<boolean>(false);

  useEffect(() => {
    const fetchUser = async () => {
      try {
        const token = ApiClient.getAuthToken();
        if (token) {
          const user = await ApiClient.getCurrentUser();
          setCurrentUser(user);
        }
      } catch {
        // Token expired or invalid
        ApiClient.setAuthToken(null);
        setCurrentUser(null);
      }
    };
    fetchUser();
  }, []);

  const handleLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!usernameInput || !passwordInput) return;
    setLoginLoading(true);
    setLoginError(null);
    try {
      const res = await ApiClient.login({
        username: usernameInput,
        password: passwordInput,
      });
      setCurrentUser(res.user);
      setShowLoginModal(false);
      setUsernameInput('');
      setPasswordInput('');
    } catch (err: unknown) {
      if (err instanceof Error) {
        setLoginError(err.message.replace(/^API error \d+:\s*/, ''));
      } else {
        setLoginError('Authentication failed.');
      }
    } finally {
      setLoginLoading(false);
    }
  };

  const handleLogout = () => {
    ApiClient.logout();
    setCurrentUser(null);
  };

  const navItems: { id: ViewMode; label: string; badge?: string }[] = [
    { id: 'overview', label: 'Overview' },
    { id: 'video_analysis', label: 'Video Analysis', badge: 'P2' },
    { id: 'event_review', label: 'Event Review', badge: 'P4' },
    { id: 'gis_operations', label: 'GIS Operations', badge: 'P5' },
    { id: 'incidents', label: 'Incidents', badge: 'P7' },
    { id: 'reports_audit', label: 'Reports & Audit', badge: 'LIVE' },
  ];

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      minHeight: '100vh',
      backgroundColor: 'var(--color-obsidian-canvas)',
    }}>
      {/* Top Header / Control Surface */}
      <header style={{
        borderBottom: 'var(--border-hairline)',
        backgroundColor: 'var(--color-carbon-lift)',
        padding: '0 var(--space-6)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        height: '52px',
        position: 'sticky',
        top: 0,
        zIndex: 100,
      }}>
        {/* Brand */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-4)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
            <span style={{
              fontWeight: 600,
              fontSize: '15px',
              letterSpacing: '-0.03em',
              color: 'var(--color-bone)',
            }}>
              NEXORA
            </span>
            <span className="mono-caption" style={{
              backgroundColor: '#161413',
              padding: '2px 6px',
              borderRadius: 'var(--radius-xs)',
              border: '1px solid var(--color-ash-stroke)',
              color: 'var(--color-signal-orange)',
            }}>
              SECURE
            </span>
          </div>

          <div style={{ height: '16px', width: '1px', backgroundColor: 'var(--color-ash-stroke)' }} />

          <div className="mono-caption" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span>VENUE:</span>
            <span style={{ color: 'var(--color-bone)' }}>GRAND CULTURAL ARENA</span>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav style={{ display: 'flex', gap: 'var(--space-1)' }}>
          {navItems.map((item) => {
            const isActive = currentView === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onNavigate(item.id)}
                style={{
                  background: isActive ? 'var(--color-obsidian-canvas)' : 'transparent',
                  color: isActive ? 'var(--color-chalk)' : 'var(--color-warm-granite)',
                  border: 'none',
                  borderBottom: isActive ? '2px solid var(--color-signal-orange)' : '2px solid transparent',
                  padding: '14px 14px',
                  fontFamily: 'var(--font-sans)',
                  fontSize: '13px',
                  fontWeight: isActive ? 500 : 400,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  transition: 'color 0.1s ease',
                }}
              >
                <span>{item.label}</span>
                {item.badge && (
                  <span style={{
                    fontFamily: 'var(--font-mono)',
                    fontSize: '9px',
                    padding: '0 4px',
                    borderRadius: '2px',
                    backgroundColor: item.badge === 'LIVE' ? '#1c2818' : '#262220',
                    color: item.badge === 'LIVE' ? 'var(--color-metric-green)' : 'var(--color-warm-granite)',
                    border: '1px solid var(--color-ash-stroke)',
                  }}>
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        {/* Right Status & Operator Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-4)' }}>
          <StatusBadge
            status={health?.status === 'healthy' ? 'healthy' : health ? 'degraded' : 'offline'}
            label={health ? `API: ${health.status.toUpperCase()}` : 'API: OFFLINE'}
          />

          <div style={{ height: '16px', width: '1px', backgroundColor: 'var(--color-ash-stroke)' }} />

          {currentUser ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
              <span className="mono-caption" style={{
                color: 'var(--color-bone)',
                backgroundColor: '#161413',
                padding: '3px 8px',
                borderRadius: 'var(--radius-xs)',
                border: '1px solid var(--color-ash-stroke)',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}>
                <span>OP:</span>
                <strong style={{ color: 'var(--color-signal-orange)' }}>{currentUser.username}</strong>
                <span style={{
                  fontSize: '9px',
                  color: currentUser.role === 'admin' ? 'var(--color-signal-orange)' : 'var(--color-metric-green)',
                  borderLeft: '1px solid var(--color-ash-stroke)',
                  paddingLeft: '4px'
                }}>
                  {currentUser.role.toUpperCase()}
                </span>
              </span>
              <button
                onClick={handleLogout}
                className="mono-caption"
                style={{
                  background: 'transparent',
                  border: '1px solid var(--color-ash-stroke)',
                  color: 'var(--color-warm-granite)',
                  padding: '3px 8px',
                  borderRadius: 'var(--radius-xs)',
                  cursor: 'pointer',
                }}
              >
                LOGOUT
              </button>
            </div>
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
              <span className="mono-caption" style={{ color: 'var(--color-warm-granite)' }}>
                OP: DEMO (DEV)
              </span>
              <button
                onClick={() => setShowLoginModal(true)}
                className="mono-caption"
                style={{
                  background: '#161413',
                  border: '1px solid var(--color-signal-orange)',
                  color: 'var(--color-signal-orange)',
                  padding: '3px 8px',
                  borderRadius: 'var(--radius-xs)',
                  cursor: 'pointer',
                  fontWeight: 600
                }}
              >
                LOGIN
              </button>
            </div>
          )}
        </div>
      </header>

      {/* Login Dialog Modal */}
      {showLoginModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.75)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
        }}>
          <div style={{
            backgroundColor: 'var(--color-carbon-lift)',
            border: '1px solid var(--color-ash-stroke)',
            borderRadius: 'var(--radius-sm)',
            width: '380px',
            padding: 'var(--space-6)',
            boxShadow: '0 8px 24px rgba(0,0,0,0.8)',
          }}>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              borderBottom: 'var(--border-hairline)',
              paddingBottom: 'var(--space-3)',
              marginBottom: 'var(--space-4)'
            }}>
              <span className="mono-caption" style={{ color: 'var(--color-signal-orange)', fontWeight: 600 }}>
                NEXORA OPERATOR AUTHENTICATION
              </span>
              <button
                onClick={() => { setShowLoginModal(false); setLoginError(null); }}
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'var(--color-warm-granite)',
                  cursor: 'pointer',
                  fontSize: '14px'
                }}
              >
                ✕
              </button>
            </div>

            {loginError && (
              <div style={{
                backgroundColor: '#261210',
                border: '1px solid #7f1d1d',
                color: '#f87171',
                padding: 'var(--space-2) var(--space-3)',
                borderRadius: 'var(--radius-xs)',
                fontFamily: 'var(--font-mono)',
                fontSize: '11px',
                marginBottom: 'var(--space-4)'
              }}>
                {loginError}
              </div>
            )}

            <form onSubmit={handleLoginSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
              <div>
                <label className="mono-caption" style={{ display: 'block', marginBottom: '4px' }}>
                  OPERATOR USERNAME
                </label>
                <input
                  type="text"
                  value={usernameInput}
                  onChange={(e) => setUsernameInput(e.target.value)}
                  placeholder="e.g. sys_admin"
                  required
                  autoFocus
                  style={{
                    width: '100%',
                    backgroundColor: 'var(--color-obsidian-canvas)',
                    border: '1px solid var(--color-ash-stroke)',
                    color: 'var(--color-bone)',
                    padding: '8px 10px',
                    fontFamily: 'var(--font-mono)',
                    fontSize: '12px',
                    borderRadius: 'var(--radius-xs)',
                    outline: 'none',
                    boxSizing: 'border-box'
                  }}
                />
              </div>

              <div>
                <label className="mono-caption" style={{ display: 'block', marginBottom: '4px' }}>
                  PASSWORD
                </label>
                <input
                  type="password"
                  value={passwordInput}
                  onChange={(e) => setPasswordInput(e.target.value)}
                  placeholder="••••••••••••"
                  required
                  style={{
                    width: '100%',
                    backgroundColor: 'var(--color-obsidian-canvas)',
                    border: '1px solid var(--color-ash-stroke)',
                    color: 'var(--color-bone)',
                    padding: '8px 10px',
                    fontFamily: 'var(--font-mono)',
                    fontSize: '12px',
                    borderRadius: 'var(--radius-xs)',
                    outline: 'none',
                    boxSizing: 'border-box'
                  }}
                />
              </div>

              <div style={{
                display: 'flex',
                justifyContent: 'flex-end',
                gap: 'var(--space-2)',
                marginTop: 'var(--space-2)'
              }}>
                <button
                  type="button"
                  onClick={() => { setShowLoginModal(false); setLoginError(null); }}
                  style={{
                    backgroundColor: 'transparent',
                    border: '1px solid var(--color-ash-stroke)',
                    color: 'var(--color-warm-granite)',
                    padding: '6px 12px',
                    fontFamily: 'var(--font-mono)',
                    fontSize: '11px',
                    borderRadius: 'var(--radius-xs)',
                    cursor: 'pointer'
                  }}
                >
                  CANCEL
                </button>
                <button
                  type="submit"
                  disabled={loginLoading}
                  style={{
                    backgroundColor: 'var(--color-signal-orange)',
                    border: 'none',
                    color: '#ffffff',
                    padding: '6px 16px',
                    fontFamily: 'var(--font-mono)',
                    fontSize: '11px',
                    fontWeight: 600,
                    borderRadius: 'var(--radius-xs)',
                    cursor: loginLoading ? 'wait' : 'pointer'
                  }}
                >
                  {loginLoading ? 'AUTHENTICATING...' : 'SIGN IN'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Main Workspace Canvas */}
      <main style={{
        flex: 1,
        maxWidth: '1280px',
        width: '100%',
        margin: '0 auto',
        padding: 'var(--space-6)',
      }}>
        {children}
      </main>

      {/* Footer Status Bar */}
      <footer style={{
        borderTop: 'var(--border-hairline)',
        backgroundColor: '#0c0c0c',
        padding: 'var(--space-2) var(--space-6)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        fontFamily: 'var(--font-mono)',
        fontSize: '11px',
        color: 'var(--color-warm-granite)',
      }}>
        <div style={{ display: 'flex', gap: 'var(--space-4)' }}>
          <span>CORE: FASTAPI 0.115 + REACT 18</span>
          <span>STORAGE: SQLITE (WAL)</span>
          <span>AUTH: JWT (NATIVE BCRYPT)</span>
          <span>PORT: 8000 / 5173</span>
        </div>
        <div style={{ display: 'flex', gap: 'var(--space-4)' }}>
          <span style={{ color: 'var(--color-metric-green)' }}>PHASE 10 HARDENED (RBAC & CSP)</span>
          <span>FACTORY THEME (DARK)</span>
        </div>
      </footer>
    </div>
  );
};
