// On every page. The React app's page (templates/spa.html) has <div id="app">: the app draws the whole page there.
// A server page loads React only when it has a React screen on it: <div data-island="name" data-props='{...}'>
// (the island macro in templates/_macros.html).
const app = document.getElementById('app');
if (app) {
  import('./app/start').then(({ start }) => start(app));
} else {
  const elements = document.querySelectorAll<HTMLElement>('[data-island]');
  if (elements.length) {
    import('./mount').then(({ mountAll }) => mountAll(elements));
  }
}
