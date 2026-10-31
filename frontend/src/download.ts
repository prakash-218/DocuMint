// Downloading a file the server makes from several records (a ZIP of PDFs, a CSV): an ordinary form post with their
// ids, so the browser saves the answer itself and the page stays where it is.

export function download(action: string, ids: string[]) {
  const form = document.createElement('form');
  form.method = 'post';
  form.action = action;
  form.hidden = true;
  for (const id of ids) {
    const input = document.createElement('input');
    input.type = 'hidden';
    input.name = 'ids';
    input.value = id;
    form.appendChild(input);
  }
  document.body.appendChild(form);
  form.submit();
  form.remove();
}
