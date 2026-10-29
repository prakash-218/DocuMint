// Numbers and dates the way the pages print them: ₹4,95,600 (lakh grouping), 24 Oct, today 14:05.

export function money(amount: number | null | undefined, currency: string | null = 'INR'): string {
  const code = (currency || 'INR').toUpperCase();
  try {
    return new Intl.NumberFormat(code === 'INR' ? 'en-IN' : 'en-US', {
      style: 'currency', currency: code, maximumFractionDigits: 0,
    }).format(amount ?? 0);
  } catch {
    return `${code} ${Math.round(amount ?? 0)}`;
  }
}

export function day(iso: string | null | undefined): string {
  if (!iso) return '';
  const d = new Date(iso.length === 10 ? `${iso}T00:00:00` : iso);
  return Number.isNaN(d.getTime()) ? '' : d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short' });
}

/** 'just now', '12 min ago', 'today 14:05', 'yesterday', '12 Oct' */
export function when(iso: string | null | undefined, now: Date = new Date()): string {
  if (!iso) return '';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '';
  const minutes = (now.getTime() - d.getTime()) / 60000;
  if (minutes >= 0 && minutes < 1) return 'just now';
  if (minutes >= 0 && minutes < 60) return `${Math.floor(minutes)} min ago`;
  const sameDay = d.toDateString() === now.toDateString();
  if (sameDay) return `today ${d.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })}`;
  const yesterday = new Date(now);
  yesterday.setDate(now.getDate() - 1);
  if (d.toDateString() === yesterday.toDateString()) return 'yesterday';
  return day(iso);
}
