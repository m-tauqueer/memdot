import createDOMPurify from "dompurify";
import { JSDOM } from "jsdom";

const window = new JSDOM("<!DOCTYPE html><html><body></body></html>", {
  url: "https://memdot.local/",
}).window;

const purify = createDOMPurify(window);

export default purify;
export const sanitize = purify.sanitize.bind(purify);
export const addHook = purify.addHook.bind(purify);
export const removeHook = purify.removeHook.bind(purify);
export const removeHooks = purify.removeHooks.bind(purify);
export const removeAllHooks = purify.removeAllHooks.bind(purify);
export const setConfig = purify.setConfig.bind(purify);
export const clearConfig = purify.clearConfig.bind(purify);
export const isValidAttribute = purify.isValidAttribute.bind(purify);
export const isSupported = purify.isSupported;
export const version = purify.version;
export const removed = purify.removed;
