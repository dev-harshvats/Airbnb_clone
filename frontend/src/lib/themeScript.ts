/**
 * Runs in <head> before first paint (so there's no flash): a saved choice wins, otherwise the
 * browser's colour-scheme preference decides. Kept apart from lib/theme.ts because the root layout
 * (a server component) needs this string while that file uses client-only hooks.
 */
export const THEME_INIT_SCRIPT = `try{var t=localStorage.getItem("airbnb:theme");if(t!=="light"&&t!=="dark"){t=matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light"}document.documentElement.dataset.theme=t}catch(e){}`;
