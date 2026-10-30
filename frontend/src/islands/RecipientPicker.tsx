// Who an email goes to (EmailComposer's To and Cc): the customer's contacts and the addresses found in their emails,
// picked from a list that shows who each one is, or typed and pasted (several at once). Mantine's Combobox and
// PillsInput, in the app's look (src/mantine/).
import { useState, type ClipboardEvent, type KeyboardEvent } from 'react';
import { Avatar, Combobox, Group, Highlight, Pill, PillsInput, Text, Tooltip, useCombobox } from '@mantine/core';
import { IN_DIALOG } from '../mantine/Mantine';
import type { Person } from './EmailComposer';

export const EMAIL = /^[^@\s,;<>"]+@[^@\s,;<>"]+\.[^@\s,;<>"]+$/;
const GETS: Record<string, string> = { all: 'gets everything', billing: 'proformas and invoices only', none: 'not on this project' };
const COLORS = ['docu', 'teal', 'orange', 'blue', 'grape', 'cyan'];

export function initials(name: string): string {
  const words = name.replace(/^(mr|ms|mrs|dr)\.?\s+/i, '').split(/\s+/).filter((w) => /^[a-z]/i.test(w));
  return ((words[0]?.[0] ?? '') + (words.length > 1 ? words[words.length - 1][0] : '')).toUpperCase() || '@';
}

const colorOf = (email: string) => COLORS[[...email].reduce((n, c) => n + c.charCodeAt(0), 0) % COLORS.length];

interface Props {
  id: string;
  label: string;
  value: string[];
  onChange: (value: string[]) => void;
  /** The project's (or customer's) contacts */
  people: Person[];
  /** Addresses found in the customer's emails, not contacts yet */
  found: Person[];
}

export function RecipientPicker({ id, label, value, onChange, people, found }: Props) {
  const combobox = useCombobox({
    onDropdownClose: () => combobox.resetSelectedOption(),
    onDropdownOpen: () => combobox.updateSelectedOptionIndex('active'),
  });
  const [search, setSearch] = useState('');
  const [problem, setProblem] = useState('');
  const known = (email: string) => people.find((p) => p.email === email) ?? found.find((p) => p.email === email);

  const q = search.trim().toLowerCase();
  const matches = (p: Person) => !value.includes(p.email) && (!q || [p.name, p.email, p.role ?? ''].some((s) => s.toLowerCase().includes(q)));
  const contacts = people.filter(matches);
  const fromMail = found.filter(matches);
  const typed = q && !known(q) && !value.includes(q) ? q : '';

  /** Add what was typed or pasted: one address or several (commas, semicolons, spaces between) */
  function add(raw: string) {
    const parts = raw.split(/[,;\s]+/).map((s) => s.trim().toLowerCase().replace(/^<|>$/g, '')).filter(Boolean);
    const bad = parts.filter((p) => !EMAIL.test(p));
    const good = parts.filter((p, i) => EMAIL.test(p) && !value.includes(p) && parts.indexOf(p) === i);
    if (good.length) onChange([...value, ...good]);
    setProblem(bad.length ? `${bad.map((b) => `"${b}"`).join(', ')} ${bad.length === 1 ? "isn't an email address" : "aren't email addresses"}.` : '');
    setSearch(bad.join(' '));
  }

  function pick(email: string) {
    if (email === '__typed') {
      add(search);
    } else {
      onChange([...value, email]);
      setSearch('');
      setProblem('');
    }
    combobox.updateSelectedOptionIndex();
  }

  function onKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    const picking = combobox.dropdownOpened && combobox.getSelectedOptionIndex() >= 0;
    if (e.key === 'Enter' && !picking) {
      e.preventDefault();                       // never sends the email
      if (search.trim()) add(search);
    } else if ((e.key === ',' || e.key === ';') && search.trim()) {
      e.preventDefault();
      add(search);
    } else if (e.key === 'Backspace' && !search && value.length) {
      e.preventDefault();
      onChange(value.slice(0, -1));
    }
  }

  function onPaste(e: ClipboardEvent<HTMLInputElement>) {
    const text = e.clipboardData.getData('text');
    if (/[,;\s]/.test(text.trim())) {           // several addresses at once
      e.preventDefault();
      add(text);
    }
  }

  const option = (p: Person) => (
    <Combobox.Option value={p.email} key={p.email}>
      <Group gap="sm" wrap="nowrap">
        <Avatar size={30} radius="xl" color={colorOf(p.email)} variant={people.includes(p) ? 'light' : 'outline'}>{initials(p.name)}</Avatar>
        <div style={{ minWidth: 0 }}>
          <Group gap={6} wrap="nowrap">
            <Highlight highlight={q} color="docu" size="sm" fw={500} truncate>{p.name}</Highlight>
            {p.role && <Text size="xs" c="dimmed" truncate>· {p.role}</Text>}
          </Group>
          <Highlight highlight={q} color="docu" size="xs" c="dimmed" truncate>
            {p.gets && GETS[p.gets] ? `${p.email} · ${GETS[p.gets]}` : p.email}
          </Highlight>
        </div>
      </Group>
    </Combobox.Option>
  );

  return (
    <div className="dm-field">
      <label htmlFor={id} className="dm-field-label">{label}</label>
      <div style={{ minWidth: 0 }}>
        <Combobox store={combobox} onOptionSubmit={pick} {...IN_DIALOG}>
          <Combobox.DropdownTarget>
            <PillsInput id={id} onClick={() => combobox.openDropdown()} error={!!problem}
                        rightSection={value.length > 1 ? <Text size="xs" c="dimmed" pr={6}>{value.length}</Text> : null}>
              <Pill.Group>
                {value.map((email) => {
                  const p = known(email);
                  return (
                    <Tooltip key={email} label={email} openDelay={300} withinPortal={false}>
                      <Pill withRemoveButton className="dm-recipient" onRemove={() => onChange(value.filter((v) => v !== email))}
                            removeButtonProps={{ 'aria-label': `Remove ${p?.name ?? email}`, 'aria-hidden': false, tabIndex: 0 }}>
                        <Avatar size={18} radius="xl" color={colorOf(email)} variant="filled">{initials(p?.name ?? email)}</Avatar>
                        {p ? p.name : email}
                      </Pill>
                    </Tooltip>
                  );
                })}
                <Combobox.EventsTarget>
                  <PillsInput.Field value={search} placeholder={value.length ? '' : 'Name, role or email'}
                                    onFocus={() => combobox.openDropdown()}
                                    onBlur={() => { combobox.closeDropdown(); if (EMAIL.test(search.trim())) add(search); }}
                                    onChange={(e) => {
                                      combobox.openDropdown();
                                      combobox.updateSelectedOptionIndex();
                                      setSearch(e.currentTarget.value);
                                      setProblem('');
                                    }}
                                    onKeyDown={onKeyDown} onPaste={onPaste} />
                </Combobox.EventsTarget>
              </Pill.Group>
            </PillsInput>
          </Combobox.DropdownTarget>
          <Combobox.Dropdown>
            <Combobox.Options mah={300} style={{ overflowY: 'auto' }}>
              {contacts.length > 0 && <Combobox.Group label="Their contacts">{contacts.map(option)}</Combobox.Group>}
              {fromMail.length > 0 && <Combobox.Group label="Found in their emails">{fromMail.map(option)}</Combobox.Group>}
              {typed && EMAIL.test(typed) && <Combobox.Option value="__typed"><Text size="sm">Add <b>{typed}</b></Text></Combobox.Option>}
              {typed && !EMAIL.test(typed) && !contacts.length && !fromMail.length && (
                <Combobox.Empty>Nobody matches. Keep typing their email address.</Combobox.Empty>
              )}
              {!q && !contacts.length && !fromMail.length && <Combobox.Empty>Type an email address to add it.</Combobox.Empty>}
            </Combobox.Options>
          </Combobox.Dropdown>
        </Combobox>
        {problem && <span className="dm-error-inline" role="alert">{problem}</span>}
      </div>
    </div>
  );
}
