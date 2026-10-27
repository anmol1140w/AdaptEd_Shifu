import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode, SelectHTMLAttributes } from 'react'
import { Link } from 'react-router-dom'
import { ArrowRight, Check, ChevronDown, CircleAlert, Info, LoaderCircle } from 'lucide-react'
import type { Difficulty, MasteryStatus } from '../types'

export function Button({ variant = 'primary', size = 'md', children, className = '', ...props }: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: 'primary' | 'secondary' | 'ghost' | 'danger'; size?: 'sm' | 'md' | 'lg' }) {
  return <button className={`button button-${variant} button-${size} ${className}`} {...props}>{children}</button>
}

export function IconButton({ label, children, className = '', ...props }: ButtonHTMLAttributes<HTMLButtonElement> & { label: string }) {
  return <button className={`icon-button ${className}`} aria-label={label} title={label} {...props}>{children}</button>
}

export function Input({ className = '', ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return <input className={`input ${className}`} {...props} />
}

export function Select({ className = '', children, ...props }: SelectHTMLAttributes<HTMLSelectElement>) {
  return <span className={`select-wrap ${className}`}><select className="select" {...props}>{children}</select><ChevronDown size={15} /></span>
}

export function Card({ children, className = '', padding = true, ...props }: { children: ReactNode; className?: string; padding?: boolean; id?: string }) {
  return <section className={`card ${padding ? 'card-padded' : ''} ${className}`} {...props}>{children}</section>
}

export function PageHeader({ eyebrow, title, description, actions }: { eyebrow?: string; title: string; description?: string; actions?: ReactNode }) {
  return <div className="page-header"><div><div className="eyebrow">{eyebrow}</div><h1>{title}</h1>{description && <p>{description}</p>}</div>{actions && <div className="page-actions">{actions}</div>}</div>
}

export function Badge({ children, tone = 'neutral' }: { children: ReactNode; tone?: 'neutral' | 'green' | 'amber' | 'red' | 'blue' }) {
  return <span className={`badge badge-${tone}`}>{children}</span>
}

export function DifficultyBadge({ difficulty }: { difficulty: Difficulty }) {
  return <Badge tone={difficulty === 'Easy' ? 'green' : difficulty === 'Medium' ? 'amber' : 'red'}>{difficulty}</Badge>
}

export function MasteryBadge({ status }: { status: MasteryStatus }) {
  const tone = status === 'Mastered' ? 'green' : status === 'Proficient' ? 'blue' : status === 'Developing' ? 'amber' : 'red'
  return <Badge tone={tone}>{status}</Badge>
}

export function ProgressBar({ value, color = 'green', height = 6 }: { value: number; color?: 'green' | 'amber' | 'red' | 'blue'; height?: number }) {
  return <div className="progress-track" style={{ height }}><div className={`progress-fill progress-${color}`} style={{ width: `${Math.max(0, Math.min(100, value))}%` }} /></div>
}

export function Metric({ label, value, detail, tone = 'default' }: { label: string; value: string | number; detail?: string; tone?: 'default' | 'green' | 'amber' | 'red' }) {
  return <div className={`metric metric-${tone}`}><div className="metric-label">{label}</div><div className="metric-value">{value}</div>{detail && <div className="metric-detail">{detail}</div>}</div>
}

export function EmptyState({ icon = <Info size={18} />, title, description, action }: { icon?: ReactNode; title: string; description: string; action?: ReactNode }) {
  return <div className="empty-state"><div className="empty-icon">{icon}</div><strong>{title}</strong><p>{description}</p>{action}</div>
}

export function LoadingState() {
  return <div className="loading-state"><LoaderCircle size={20} className="spin" /> Loading demo data…</div>
}

export function LinkButton({ to, children, className = '' }: { to: string; children: ReactNode; className?: string }) {
  return <Link className={`button button-secondary button-md ${className}`} to={to}>{children}<ArrowRight size={15} /></Link>
}

export function SectionHeading({ title, description, action }: { title: string; description?: string; action?: ReactNode }) {
  return <div className="section-heading"><div><h2>{title}</h2>{description && <p>{description}</p>}</div>{action}</div>
}

export function CheckRow({ checked, children, onClick }: { checked: boolean; children: ReactNode; onClick?: () => void }) {
  return <button className={`check-row ${checked ? 'is-checked' : ''}`} onClick={onClick} aria-pressed={checked}><span className="check-box">{checked && <Check size={13} />}</span><span>{children}</span></button>
}

export function Notice({ children, tone = 'info' }: { children: ReactNode; tone?: 'info' | 'warning' | 'success' }) {
  return <div className={`notice notice-${tone}`}>{tone === 'warning' ? <CircleAlert size={16} /> : <Info size={16} />}<span>{children}</span></div>
}
