import { registerHooks } from "node:module";

const shim = new URL("./dompurify-node.mjs", import.meta.url).href;

registerHooks({
  resolve(specifier, context, nextResolve) {
    if (
      specifier === "dompurify" &&
      context.parentURL &&
      !context.parentURL.includes("dompurify-node.mjs")
    ) {
      return {
        shortCircuit: true,
        url: shim,
      };
    }
    return nextResolve(specifier, context);
  },
});
