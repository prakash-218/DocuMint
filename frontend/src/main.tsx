// On every page. React itself only loads when the page has a React screen on it:
// <div data-island="name" data-props='{...}'> (the island macro in templates/_macros.html).
const elements = document.querySelectorAll<HTMLElement>('[data-island]');
if (elements.length) {
  import('./mount').then(({ mountAll }) => mountAll(elements));
}
