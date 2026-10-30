import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { Mantine } from '../mantine/Mantine';
import { App } from './App';
import { readBoot } from './boot';

/** Draw the app over the frame and grey shapes the server page put in #app. */
export function start(el: HTMLElement) {
  createRoot(el).render(
    <StrictMode>
      <Mantine>
        <App boot={readBoot()} />
      </Mantine>
    </StrictMode>,
  );
}
