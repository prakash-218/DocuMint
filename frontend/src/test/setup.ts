import '@testing-library/jest-dom/vitest';
import { cleanup } from '@testing-library/react';
import { afterEach } from 'vitest';

afterEach(cleanup);        // without vitest globals, Testing Library doesn't unmount between tests by itself
