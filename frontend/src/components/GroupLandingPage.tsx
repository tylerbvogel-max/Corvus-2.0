import type { ReactNode } from 'react';

interface LandingItem {
  key: string;
  label: string;
  description: string;
}

interface GroupLandingProps {
  title: string;
  icon: ReactNode;
  description: string;
  items: LandingItem[];
  onNavigate: (key: string) => void;
}

export default function GroupLandingPage({ title, icon, description, items, onNavigate }: GroupLandingProps) {
  return (
    <div className="group-landing">
      <div className="group-landing-header">
        <span className="group-landing-icon">{icon}</span>
        <h1 className="group-landing-title">{title}</h1>
        <p className="group-landing-desc">{description}</p>
      </div>
      <div className="group-landing-grid">
        {items.map(item => (
          <button
            key={item.key}
            className="group-landing-card"
            onClick={() => onNavigate(item.key)}
          >
            <span className="group-landing-card-label">{item.label}</span>
            <span className="group-landing-card-desc">{item.description}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
