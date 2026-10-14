import React from 'react';

interface CardProps {
  title?: string;
  subtitle?: string;
  badge?: React.ReactNode;
  children: React.ReactNode;
  variant?: 'dark' | 'light';
  style?: React.CSSProperties;
}

export const Card: React.FC<CardProps> = ({
  title,
  subtitle,
  badge,
  children,
  variant = 'dark',
  style,
}) => {
  return (
    <div
      className={variant === 'light' ? 'card-light' : 'card-surface'}
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--space-3)',
        ...style,
      }}
    >
      {(title || subtitle || badge) && (
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          borderBottom: variant === 'dark' ? '1px solid #23201e' : '1px solid #ddd',
          paddingBottom: 'var(--space-2)',
        }}>
          <div>
            {subtitle && (
              <div className="mono-caption" style={{ marginBottom: '2px' }}>
                {subtitle}
              </div>
            )}
            {title && (
              <h3 style={{
                fontSize: '15px',
                fontWeight: 500,
                color: variant === 'dark' ? 'var(--color-bone)' : 'var(--color-obsidian-canvas)',
                letterSpacing: '-0.02em',
              }}>
                {title}
              </h3>
            )}
          </div>
          {badge && <div>{badge}</div>}
        </div>
      )}
      <div>{children}</div>
    </div>
  );
};
