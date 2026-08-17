import type { Plugin } from 'vite';

/**
 * Vite plugin to remove console statements in production builds
 * Removes: console.log, console.debug, console.info
 * Keeps: console.warn, console.error (important for debugging production issues)
 *
 * Uses terser for safe AST-based removal instead of regex
 */
export default function removeConsolePlugin(): Plugin {
  return {
    name: 'remove-console',
    apply: 'build', // Only apply during production builds
    config() {
      return {
        build: {
          minify: 'terser',
          terserOptions: {
            compress: {
              drop_console: ['log', 'debug', 'info'],
              pure_funcs: ['console.log', 'console.debug', 'console.info']
            }
          }
        }
      };
    }
  };
}
