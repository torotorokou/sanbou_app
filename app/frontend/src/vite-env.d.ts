/// <reference types="vite/client" />

declare module "*.module.css" {
  const classes: { readonly [key: string]: string };
  export default classes;
}

// Vite worker import typing (e.g., '...?.worker')
// (Optional) If using Vite ?worker imports, declare above. Not used currently.
