// On every page. Each kind of page has its own root, and only its part of the app loads:
//   #app     the staff app's page (templates/spa.html): the app draws the whole page there
//   #public  a page outside the app (templates/public.html): signing in, registering, choosing an organization
//   #portal  the customer portal (templates/portal.html)
const app = document.getElementById('app');
const outside = document.getElementById('public');
const portal = document.getElementById('portal');
if (app) {
  import('./app/start').then(({ start }) => start(app));
} else if (outside) {
  import('./public/start').then(({ start }) => start(outside));
} else if (portal) {
  import('./portal/start').then(({ start }) => start(portal));
}
