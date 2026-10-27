export function ProgressRing({ value, label }: { value: number; label: string }) {
  return <div className="progress-ring" style={{ '--progress': `${value * 3.6}deg` } as React.CSSProperties}><div className="progress-ring-inner"><strong>{value}%</strong><span>{label}</span></div></div>
}
