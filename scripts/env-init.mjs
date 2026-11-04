import { ensureRootEnv, ENV_PATH } from './lib/env.mjs';
ensureRootEnv();
console.log(`Configuration ready: ${ENV_PATH}`);
