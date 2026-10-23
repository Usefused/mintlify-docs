import { registerHooks } from 'node:module';
registerHooks({
  // Replace only the hosted bindings; the real example logic and Zod schemas execute locally.
  resolve(specifier, context, nextResolve) {
    // Hosting registration is inert during a local contract test.
    if (specifier === '@fused/unified-app') {
      return { url: 'data:text/javascript,export const buildUnifiedApp = (config) => config;', shortCircuit: true };
    }
    // Tests inject provider fixtures explicitly; accidental real adapter calls must fail.
    if (specifier === '@fused/operations') {
      return { url: 'data:text/javascript,export const services = {};', shortCircuit: true };
    }
    return nextResolve(specifier, context);
  },
});
