# CryptoVault Frontend

Modern React-based frontend for the CryptoVault cryptocurrency trading platform.

## Tech Stack

- **React 18** with TypeScript
- **Vite 5** for fast development and building
- **Tailwind CSS** for styling
- **Radix UI** for accessible components
- **React Router** for navigation
- **React Query** for server state management
- **React Hook Form + Zod** for form validation

## Development

```bash
# Install dependencies
yarn install

# Start dev server (port 3000)
yarn dev

# Build for production
yarn build

# Preview production build
yarn preview
```

## Project Structure

```
src/
├── components/        # Reusable components
│   ├── ui/           # Shadcn/Radix UI components
│   └── ...           # Feature components
├── contexts/         # React contexts (Auth)
├── hooks/            # Custom hooks
├── lib/              # Utilities
│   ├── api.ts       # API client
│   ├── utils.ts     # Helper functions
│   └── validation.ts # Form validation schemas
├── pages/            # Page components (routes)
├── App.tsx           # Main app component
└── main.tsx          # Entry point
```

## Key Features

- 🔐 Authentication with JWT cookies
- 📊 Real-time cryptocurrency prices
- 💼 Portfolio management
- 📈 Trading interface
- 💳 Transaction history
- 🔒 Two-factor authentication
- 📝 Audit log viewer
- 🎨 Modern UI with dark mode support

## Environment Variables

```env
REACT_APP_BACKEND_URL=https://your-backend-url.com
WDS_SOCKET_PORT=443
ENABLE_HEALTH_CHECK=false
```

## Available Pages

- `/` - Landing page
- `/auth` - Sign in / Sign up
- `/markets` - Cryptocurrency market data
- `/trade` - Trading interface
- `/earn` - Staking/earning (placeholder)
- `/learn` - Educational content (placeholder)
- `/dashboard` - User dashboard (protected)
- `/transactions` - Transaction history (protected)
- `/contact` - Contact page
- `/terms` - Terms of service
- `/privacy` - Privacy policy

## API Integration

The frontend communicates with the backend API through the `api.ts` client, which handles:
- Authentication tokens (httpOnly cookies)
- Automatic token refresh
- Error handling
- Request/response formatting

See `/app/README.md` for complete API documentation.
