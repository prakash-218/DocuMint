// The app's dropdown: Mantine's Select (src/mantine/), for every choice a screen offers. It works as the browser's
// <select> did in the app's forms: with a name, a hidden input carries the value when the form posts; required stops
// a form that has nothing picked; a choice may be '' ("All customers", "Not in a project"). A choice can carry a
// second line (sub) or a colour dot. In a <dialog> its list is drawn inside the dialog, above the page.
import { useLayoutEffect, useRef, useState, type CSSProperties } from 'react';
import { ColorSwatch, Group, Select, Text, type ComboboxItem } from '@mantine/core';

export interface Choice {
  value: string;
  label: string;
  /** A second line under the label */
  sub?: string;
  /** A colour dot before the label (a status) */
  dot?: string;
  disabled?: boolean;
}

export interface ChoiceGroup {
  group: string;
  items: Choice[];
}

/** Choices from [value, label] pairs, or from strings that are both */
export const choices = (pairs: readonly (readonly [string, string] | string)[]): Choice[] =>
  pairs.map((p) => (typeof p === 'string' ? { value: p, label: p } : { value: p[0], label: p[1] }));

const NONE = '__none__';            // the '' choice: Mantine's own "nothing picked" is null
const toMantine = (v: string) => (v === '' ? NONE : v);
const fromMantine = (v: string | null) => (v === null || v === NONE ? '' : v);

interface Props {
  data: (Choice | ChoiceGroup)[];
  id?: string;
  /** Posted with its form (a hidden input) */
  name?: string;
  /** The id of the form it belongs to, when it isn't inside it */
  form?: string;
  'aria-label'?: string;
  value?: string;
  defaultValue?: string;
  onChange?: (value: string) => void;
  /** Shown while nothing is picked */
  placeholder?: string;
  required?: boolean;
  /** Typing filters the choices; on by default when there are more than 8 */
  searchable?: boolean;
  /** xs: in a row of other small controls (a contact's row, a team member's) */
  size?: 'xs' | 'sm';
  /** Post its form as soon as something is picked */
  submitOnChange?: boolean;
  disabled?: boolean;
  onFocus?: () => void;
  className?: string;
  style?: CSSProperties;
}

export function Dropdown({ data, id, name, form, value, defaultValue, onChange, placeholder, required, searchable, size = 'sm',
                           submitOnChange, disabled, onFocus, className, style, ...aria }: Props) {
  const root = useRef<HTMLDivElement>(null);
  const field = useRef<HTMLInputElement>(null);
  const [dialog, setDialog] = useState<HTMLElement | null>(null);
  const [own, setOwn] = useState(defaultValue ?? '');
  const current = value ?? own;

  useLayoutEffect(() => setDialog(root.current?.closest('dialog') ?? null), []);

  const flat = data.flatMap((d) => ('group' in d ? d.items : [d]));
  const info = new Map(flat.map((c) => [toMantine(c.value), c]));
  const item = (c: Choice): ComboboxItem => ({ value: toMantine(c.value), label: c.label, disabled: c.disabled });
  const items = data.map((d) => ('group' in d ? { group: d.group, items: d.items.map(item) } : item(d)));
  const picked = current === '' && !info.has(NONE) ? null : toMantine(current);
  const rich = flat.some((c) => c.sub || c.dot);
  const dot = info.get(picked ?? '')?.dot;

  function change(next: string | null) {
    if (next === null) return;
    const v = fromMantine(next);
    setOwn(v);
    onChange?.(v);
    if (submitOnChange) {
      // once the hidden input holds the new value
      setTimeout(() => (root.current?.querySelector<HTMLInputElement>('input[type="hidden"]')?.form ?? null)?.requestSubmit());
    }
  }

  return (
    <div ref={root} className={`dm-dropdown${className ? ` ${className}` : ''}`} style={style}>
      <Select ref={field} id={id} data={items} value={picked} onChange={change} allowDeselect={false} disabled={disabled}
              placeholder={placeholder} size={size} searchable={searchable ?? flat.length > 8} maxDropdownHeight={300}
              nothingFoundMessage="Nothing matches" onFocus={onFocus} aria-label={aria['aria-label']}
              leftSection={dot ? <ColorSwatch color={dot} size={10} withShadow={false} /> : undefined}
              comboboxProps={dialog ? { withinPortal: true, portalProps: { target: dialog }, floatingStrategy: 'fixed' } : undefined}
              renderOption={rich ? ({ option }) => {
                const c = info.get(option.value);
                return (
                  <Group gap="xs" wrap="nowrap">
                    {c?.dot && <ColorSwatch color={c.dot} size={10} withShadow={false} />}
                    <div style={{ minWidth: 0 }}>
                      <Text size="sm">{option.label}</Text>
                      {c?.sub && <Text size="xs" c="dimmed">{c.sub}</Text>}
                    </div>
                  </Group>
                );
              } : undefined} />
      {name && <input type="hidden" name={name} form={form} value={current} />}
      {required && (
        // the browser's "pick one" check, on a stand-in for the hidden value; it hands focus to the dropdown
        <input className="dm-dropdown-required" tabIndex={-1} aria-hidden="true" required form={form} value={current}
               onChange={() => undefined} onFocus={() => field.current?.focus()} />
      )}
    </div>
  );
}
