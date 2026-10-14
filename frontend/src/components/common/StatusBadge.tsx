import React from 'react';

interface StatusBadgeProps {
  status: 'healthy' | 'degraded' | 'offline' | 'active' | 'pending' | 'blocked';
  label?: string;
  size?: 'sm' | 'md';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, label, size = 'sm' }) => {
  const getPulseClass = () => {
    switch (status) {
      case 'healthy':
      case 'active':
        return 'pulse-green';
      case 'degraded':
      case 'pending':
        return 'pulse-orange';
      case 'offline':
      case 'blocked':
      default:
        return 'pulse-red';
    }
  };

  const displayLabel = label || status.toUpperCase();

  return (
    <span style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: '6px',
      fontSize: size === 'sm' ? '11px' : '12px',
      fontFamily: 'var(--font-mono)',
      color: 'var(--color-bone)',
      letterSpacing: '0.04em',
    }}>
      <span className={`pulse-indicator ${getPulseClass()}`} />
      <span>{displayLabel}</span>
    </span>
  );
};
