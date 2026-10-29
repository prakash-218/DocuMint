import '@testing-library/jest-dom/vitest';
import { cleanup, configure } from '@testing-library/react';
import { afterEach } from 'vitest';

afterEach(cleanup);        // without vitest globals, Testing Library doesn't unmount between tests by itself
// The screens load lazily; side by side with the other test files that can take more than findBy's usual second
configure({ asyncUtilTimeout: 5000 });
