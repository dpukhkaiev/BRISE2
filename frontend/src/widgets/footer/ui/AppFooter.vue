<script setup lang="ts">
const year = new Date().getFullYear()
</script>

<template>
  <v-divider />
  <v-footer
    color="surface"
    class="d-flex flex-column flex-md-row justify-space-between pa-4"
  >
    <div class="footer-about">
      <span class="text-accent font-weight-bold">BRISE</span>
      <p class="text-body-2 text-medium-emphasis mb-1">
        BRISE is a Software Product Line (SPL) for Expensive Blackbox Optimization. It covers a wide
        spectrum of use cases, in particular hyperparameter optimization, simulation-based optimization,
        and parameter control.
        <a
          href="https://github.com/dpukhkaiev/BRISE2"
          target="_blank"
          class="text-primary"
        >About</a>
      </p>
      <p class="text-caption text-primary mb-0">
        TU Dresden {{ year }}
      </p>
    </div>

    <div class="d-flex flex-column ga-1">
      <a
        href="https://goo.gl/maps/29CadiPEe5ATHG4Y8"
        target="_blank"
        class="footer-link"
      >
        <v-avatar
          size="21"
          color="primary"
        >
          <v-icon
            icon="mdi-map-marker"
            size="14"
            color="white"
          />
        </v-avatar>
        Nöthnitzer Str. 46, 01187 Dresden
      </a>
      <a
        href="mailto:dmytro.pukhkaiev@tu-dresden.de"
        class="footer-link"
      >
        <v-avatar
          size="21"
          color="primary"
        >
          <v-icon
            icon="mdi-email"
            size="14"
            color="white"
          />
        </v-avatar>
        dmytro.pukhkaiev@tu-dresden.de
      </a>
      <a
        href="https://github.com/dpukhkaiev/BRISE2"
        target="_blank"
        class="footer-link"
      >
        <v-avatar
          size="21"
          color="primary"
        >
          <v-icon
            icon="mdi-github"
            size="14"
            color="white"
          />
        </v-avatar>
        github.com/dpukhkaiev/BRISE2
      </a>
    </div>
  </v-footer>
</template>

<style scoped>
.footer-about {
  max-width: 600px;
}

.footer-link {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 12px;
  color: rgba(var(--v-theme-on-surface), var(--v-medium-emphasis-opacity));
  text-decoration: none;
}

.footer-link:hover {
  color: rgb(var(--v-theme-primary));
}
</style>
