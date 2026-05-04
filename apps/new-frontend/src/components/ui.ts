export type Tone = 'neutral' | 'success' | 'warning' | 'danger' | 'info'

export const buttonBase =
  'inline-flex min-h-9 items-center justify-center gap-2 rounded-md border px-3 py-2 text-sm font-medium shadow-sm transition duration-200 ease-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/50 active:translate-y-px disabled:cursor-not-allowed disabled:opacity-50'

export const buttonTone = {
  primary: 'border-primary bg-primary text-primary-foreground hover:bg-primary/90',
  secondary:
    'border-border bg-background text-foreground hover:bg-accent hover:text-accent-foreground',
  ghost:
    'border-transparent bg-transparent text-muted-foreground shadow-none hover:bg-accent hover:text-accent-foreground',
  danger:
    'border-destructive/30 bg-destructive/10 text-destructive hover:border-destructive/40 hover:bg-destructive/15',
  admin:
    'border-[var(--tone-info-strong)] bg-[var(--tone-info-strong)] text-white hover:bg-[var(--tone-info-strong-hover)]',
}

export const inputClass =
  'w-full min-h-9 rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground shadow-sm outline-none transition placeholder:text-muted-foreground focus:border-ring focus:ring-2 focus:ring-ring/15 disabled:cursor-not-allowed disabled:bg-muted disabled:text-muted-foreground'

export const textareaClass = `${inputClass} min-h-24 resize-y font-mono text-xs leading-5`

export const cardClass =
  'rounded-xl border border-border bg-card text-card-foreground shadow-[0_12px_28px_-24px_rgba(24,24,27,0.42)] dark:shadow-none'

export const sectionHeaderClass =
  'grid gap-2 border-b border-border bg-muted/55 px-4 py-3 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center'

export const actionBarClass =
  'grid gap-2 border-b border-border bg-muted/55 px-4 py-3 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center'

export const labelClass = 'text-xs font-semibold uppercase tracking-normal text-muted-foreground'

export const mutedText = 'text-sm text-muted-foreground'

export const alertClass = {
  info: 'rounded-lg border border-[var(--tone-info-border)] bg-[var(--tone-info-bg)] px-3 py-2 text-sm leading-5 text-[var(--tone-info-fg)]',
  success:
    'rounded-lg border border-[var(--tone-success-border)] bg-[var(--tone-success-bg)] px-3 py-2 text-sm leading-5 text-[var(--tone-success-fg)]',
  warning:
    'rounded-lg border border-[var(--tone-warning-border)] bg-[var(--tone-warning-bg)] px-3 py-2 text-sm leading-5 text-[var(--tone-warning-fg)]',
  danger:
    'rounded-lg border border-[var(--tone-danger-border)] bg-[var(--tone-danger-bg)] px-3 py-2 text-sm leading-5 text-[var(--tone-danger-fg)]',
}

export function toneClass(tone: Tone) {
  const tones: Record<Tone, string> = {
    neutral: 'border-border bg-muted text-muted-foreground',
    success:
      'border-[var(--tone-success-border)] bg-[var(--tone-success-bg)] text-[var(--tone-success-fg)]',
    warning:
      'border-[var(--tone-warning-border)] bg-[var(--tone-warning-bg)] text-[var(--tone-warning-fg)]',
    danger:
      'border-[var(--tone-danger-border)] bg-[var(--tone-danger-bg)] text-[var(--tone-danger-fg)]',
    info: 'border-[var(--tone-info-border)] bg-[var(--tone-info-bg)] text-[var(--tone-info-fg)]',
  }
  return `inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium ${tones[tone]}`
}
