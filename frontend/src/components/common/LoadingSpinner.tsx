import React from 'react';

interface LoadingSpinnerProps {
  message?: string;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ message = 'INITIALIZING SYSTEM STREAM...' }) => {
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: 'var(--space-8)',
      gap: 'var(--space-3)',
      color: 'var(--color-warm-granite)',
      fontFamily: 'var(--font-mono)',
      fontSize: '12px',
      letterSpacing: '0.05em',
    }}>
      <span className="pulse-indicator pulse-orange" />
      <span>{message}</span>
    </div>
  );
};
