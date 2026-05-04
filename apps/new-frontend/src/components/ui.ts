export type Tone = 'neutral' | 'success' | 'warning' | 'danger' | 'info'

export const buttonBase =
  'inline-flex min-h-9 items-center justify-center gap-2 rounded-md border px-3 py-2 text-sm font-medium shadow-sm transition duration-200 ease-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-700/20 active:translate-y-px disabled:cursor-not-allowed disabled:opacity-50 dark:focus-visible:ring-emerald-400/30'

export const buttonTone = {
  primary:
    'border-emerald-700 bg-emerald-700 text-white hover:bg-emerald-800 dark:border-emerald-500 dark:bg-emerald-600 dark:hover:bg-emerald-500',
  secondary:
    'border-zinc-200 bg-white text-zinc-900 hover:border-zinc-300 hover:bg-zinc-50 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100 dark:hover:border-zinc-600 dark:hover:bg-zinc-800',
  ghost:
    'border-transparent bg-transparent text-zinc-700 shadow-none hover:bg-zinc-100 dark:text-zinc-300 dark:hover:bg-zinc-800',
  danger:
    'border-rose-200 bg-rose-50 text-rose-700 hover:border-rose-300 hover:bg-rose-100 dark:border-rose-900/70 dark:bg-rose-950/50 dark:text-rose-300 dark:hover:border-rose-800 dark:hover:bg-rose-900/40',
  admin:
    'border-sky-700 bg-sky-700 text-white hover:bg-sky-800 dark:border-sky-500 dark:bg-sky-600 dark:hover:bg-sky-500',
}

export const inputClass =
  'w-full min-h-9 rounded-md border border-zinc-200 bg-white px-3 py-2 text-sm text-zinc-900 shadow-sm outline-none transition placeholder:text-zinc-400 focus:border-emerald-700 focus:ring-2 focus:ring-emerald-700/10 disabled:cursor-not-allowed disabled:bg-zinc-100 disabled:text-zinc-500 dark:border-zinc-700 dark:bg-zinc-950 dark:text-zinc-100 dark:placeholder:text-zinc-500 dark:focus:border-emerald-500 dark:focus:ring-emerald-400/10 dark:disabled:bg-zinc-900 dark:disabled:text-zinc-500'

export const textareaClass = `${inputClass} min-h-24 resize-y font-mono text-xs leading-5`

export const cardClass =
  'rounded-lg border border-zinc-200/80 bg-white shadow-[0_14px_32px_-28px_rgba(24,24,27,0.45)] dark:border-zinc-800 dark:bg-zinc-900 dark:shadow-none'

export const sectionHeaderClass =
  'flex flex-wrap items-start justify-between gap-3 border-b border-zinc-200 bg-zinc-50/70 px-4 py-3 dark:border-zinc-800 dark:bg-zinc-950/50'

export const actionBarClass =
  'flex flex-wrap items-center gap-2 border-b border-zinc-200 bg-zinc-50/70 p-4 dark:border-zinc-800 dark:bg-zinc-950/50'

export const labelClass =
  'text-xs font-semibold uppercase tracking-normal text-zinc-500 dark:text-zinc-400'

export const mutedText = 'text-sm text-zinc-500 dark:text-zinc-400'

export const alertClass = {
  info: 'rounded-md border border-sky-200 bg-sky-50 px-3 py-2 text-sm text-sky-800 dark:border-sky-900/70 dark:bg-sky-950/50 dark:text-sky-200',
  success:
    'rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-800 dark:border-emerald-900/70 dark:bg-emerald-950/50 dark:text-emerald-200',
  warning:
    'rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800 dark:border-amber-900/70 dark:bg-amber-950/50 dark:text-amber-200',
  danger:
    'rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-800 dark:border-rose-900/70 dark:bg-rose-950/50 dark:text-rose-200',
}

export function toneClass(tone: Tone) {
  const tones: Record<Tone, string> = {
    neutral:
      'border-zinc-200 bg-zinc-50 text-zinc-700 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-300',
    success:
      'border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-900/70 dark:bg-emerald-950/50 dark:text-emerald-300',
    warning:
      'border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-900/70 dark:bg-amber-950/50 dark:text-amber-300',
    danger:
      'border-rose-200 bg-rose-50 text-rose-700 dark:border-rose-900/70 dark:bg-rose-950/50 dark:text-rose-300',
    info: 'border-sky-200 bg-sky-50 text-sky-700 dark:border-sky-900/70 dark:bg-sky-950/50 dark:text-sky-300',
  }
  return `inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium ${tones[tone]}`
}
