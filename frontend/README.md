# Report Scheduler Frontend

Vue 3 + TypeScript + Vuetify frontend application.

## Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── components/       # Reusable Vue components
│   ├── views/            # Page components (ReportsView, SchedulesView, GalleryView)
│   ├── stores/           # Pinia state management
│   ├── composables/      # Composition API reusable logic
│   ├── services/         # API client functions
│   ├── router/           # Vue Router configuration
│   ├── types/            # TypeScript type definitions
│   └── App.vue           # Root component
├── public/               # Static assets
└── vite.config.ts        # Vite configuration
```

## Development

```bash
# Run tests
npm run test

# Run E2E tests
npm run test:e2e

# Type checking
npm run type-check

# Linting
npm run lint

# Format code
npm run format
```

## Features

- **Reports Management**: Create, edit, view report definitions
- **Scheduling**: Visual cron builder with timezone support
- **Email Delivery**: Optional email notifications on report completion
- **Artifact Gallery**: Browse, download, and share generated reports
- **Execution History**: Track report runs with status and duration

## Tech Stack

- Vue 3 with Composition API (`<script setup>`)
- TypeScript for type safety
- Pinia for state management
- VueQuery for server state and caching
- VeeValidate + Zod for form validation
- Vuetify 3 for Material Design UI components
- Vite for fast builds and HMR
