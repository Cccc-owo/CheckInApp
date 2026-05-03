export type Tone = 'neutral' | 'success' | 'warning' | 'danger' | 'info'

export const buttonBase =
  'inline-flex items-center justify-center gap-2 rounded-md border px-3 py-2 text-sm font-medium transition active:translate-y-px disabled:cursor-not-allowed disabled:opacity-50'

export const buttonTone = {
  primary: 'border-zinc-900 bg-zinc-900 text-white hover:bg-zinc-800',
  secondary: 'border-zinc-200 bg-white text-zinc-900 hover:bg-zinc-50',
  ghost: 'border-transparent bg-transparent text-zinc-700 hover:bg-zinc-100',
  danger: 'border-rose-200 bg-rose-50 text-rose-700 hover:bg-rose-100',
}

export const inputClass =
  'w-full rounded-md border border-zinc-200 bg-white px-3 py-2 text-sm text-zinc-900 outline-none transition placeholder:text-zinc-400 focus:border-zinc-900 focus:ring-2 focus:ring-zinc-900/10'

export const textareaClass = `${inputClass} min-h-24 resize-y font-mono text-xs leading-5`

export const cardClass = 'rounded-lg border border-zinc-200 bg-white shadow-sm'

export const labelClass = 'text-xs font-semibold uppercase tracking-normal text-zinc-500'

export const mutedText = 'text-sm text-zinc-500'

export function toneClass(tone: Tone) {
  const tones: Record<Tone, string> = {
    neutral: 'border-zinc-200 bg-zinc-50 text-zinc-700',
    success: 'border-emerald-200 bg-emerald-50 text-emerald-700',
    warning: 'border-amber-200 bg-amber-50 text-amber-700',
    danger: 'border-rose-200 bg-rose-50 text-rose-700',
    info: 'border-sky-200 bg-sky-50 text-sky-700',
  }
  return `inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium ${tones[tone]}`
}
