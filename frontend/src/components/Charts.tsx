import { useMemo } from 'react'

export function Sparkline({ values, color = '#65b985', height = 44 }: { values: number[]; color?: string; height?: number }) {
  const points = useMemo(() => {
    const max = Math.max(...values)
    const min = Math.min(...values)
    const range = max - min || 1
    return values.map((value, index) => `${(index / (values.length - 1 || 1)) * 100},${height - 7 - ((value - min) / range) * (height - 14)}`).join(' ')
  }, [height, values])
  return <svg className="sparkline" viewBox={`0 0 100 ${height}`} preserveAspectRatio="none" aria-hidden="true"><polyline points={points} fill="none" stroke={color} strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" /></svg>
}

export function BarChart({ data, color = '#65b985' }: { data: { label: string; value: number; secondary?: number }[]; color?: string }) {
  const max = Math.max(...data.map((item) => item.value), 1)
  return <div className="bar-chart">{data.map((item) => <div className="bar-col" key={item.label}><div className="bar-value">{item.value}%</div><div className="bar-track"><div className="bar-fill" style={{ height: `${(item.value / max) * 100}%`, background: color }} />{item.secondary !== undefined && <div className="bar-marker" style={{ bottom: `${(item.secondary / max) * 100}%` }} />}</div><div className="bar-label">{item.label}</div></div>)}</div>
}

export function Donut({ value, label, color = '#65b985' }: { value: number; label: string; color?: string }) {
  return <div className="donut-wrap"><div className="donut" style={{ '--value': `${value * 3.6}deg`, '--donut-color': color } as React.CSSProperties}><div className="donut-inner"><strong>{value}%</strong><span>{label}</span></div></div></div>
}
