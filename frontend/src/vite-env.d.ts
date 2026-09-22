/// <reference types="vite/client" />

declare module 'vuetify/styles';

// eslint-disable-next-line no-unused-vars
interface ImportMetaEnv {
  readonly VITE_EVENT_SERVICE_HOST: string
  readonly VITE_EVENT_SERVICE_PORT: string
  readonly VITE_SEARCHSPACE_EDITOR_HOST: string
  readonly VITE_SEARCHSPACE_EDITOR_PORT: string
  readonly VITE_WAFFLE_HOST: string
  readonly VITE_WAFFLE_PORT: string
}