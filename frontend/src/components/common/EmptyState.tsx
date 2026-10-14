import React from 'react';

interface EmptyStateProps {
  title: string;
  phaseTag: string;
  description: string;
  requirements?: string[];
  plannedFeatures?: string[];
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  phaseTag,
  description,
  requirements = [],
  plannedFeatures = [],
}) => {
  return (
    <div style={{
      border: 'var(--border-hairline)',
      backgroundColor: 'var(--color-carbon-lift)',
      padding: 'var(--space-8)',
      borderRadius: 'var(--radius-xs)',
      display: 'flex',
      flexDirection: 'column',
      gap: 'var(--space-4)',
      maxWidth: '780px',
      margin: 'var(--space-4) auto',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span className="mono-caption" style={{
          backgroundColor: '#262220',
          padding: '2px 8px',
          borderRadius: 'var(--radius-xs)',
          border: '1px solid var(--color-ash-stroke)',
          color: 'var(--color-signal-orange)',
        }}>
          {phaseTag}
        </span>
        <span className="mono-caption">CONTROLS INERT // SCHEDULED INCREMENT</span>
      </div>

      <div>
        <h2 style={{ fontSize: '18px', fontWeight: 500, letterSpacing: '-0.02em', marginBottom: 'var(--space-2)' }}>
          {title}
        </h2>
        <p style={{ color: 'var(--color-pale-stone)', fontSize: '13px', lineHeight: 1.6 }}>
          {description}
        </p>
      </div>

      {plannedFeatures.length > 0 && (
        <div style={{
          backgroundColor: 'var(--color-obsidian-canvas)',
          padding: 'var(--space-4)',
          borderRadius: 'var(--radius-xs)',
          border: '1px solid #23201e',
        }}>
          <div className="mono-caption" style={{ marginBottom: 'var(--space-2)' }}>
            PLANNED OPERATIONAL CAPABILITIES
          </div>
          <ul style={{
            listStyleType: 'square',
            paddingLeft: 'var(--space-4)',
            color: 'var(--color-warm-granite)',
            fontSize: '13px',
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--space-1)',
          }}>
            {plannedFeatures.map((feat, idx) => (
              <li key={idx} style={{ color: 'var(--color-pale-stone)' }}>{feat}</li>
            ))}
          </ul>
        </div>
      )}

      {requirements.length > 0 && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', flexWrap: 'wrap' }}>
          <span className="mono-caption">TRACEABLE REQUIREMENTS:</span>
          {requirements.map((req) => (
            <span
              key={req}
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: '11px',
                padding: '1px 6px',
                backgroundColor: '#161413',
                border: '1px solid var(--color-ash-stroke)',
                color: 'var(--color-bone)',
              }}
            >
              {req}
            </span>
          ))}
        </div>
      )}
    </div>
  );
};
