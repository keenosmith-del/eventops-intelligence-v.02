# Frontend

React 19, Vite, strict TypeScript, React Router, custom CSS and Fetch API. Views: Sign-in, Overview, Knowledge Assistant, Agent Workspace, Verification Results and Execution History.

```sh
cd frontend
cp .env.example .env  # only when no configured file exists
npm ci
npm run dev
npm test
npm run build
```

Set `VITE_API_URL=http://localhost:5050` for local development. Production must set the actual HTTPS API URL at build time. It contains no credentials. API calls include cookies; backend origin policy must match the browser origin exactly. Run the backend separately.

Saved conversations are loaded from PostgreSQL on navigation and refresh. Agent status and results poll the real API; no execution history is manufactured. Loading, service errors, empty views and unsupported responses are rendered distinctly. Original source records are collapsible; verified CSV downloads use authenticated fetch. The layout adapts to mobile with horizontal navigation and scrollable results.

The font stylesheet requests Google Fonts and falls back to system sans-serif when unavailable. Static fictional directory data is published at `/reference/directory.json`; this endpoint remains accessible without signing in, while operational histories stay backend protected. `vercel.json` retains SPA routing without rewriting reference resources.

Tests use jsdom and mocked fetch. They verify session restoration/logout, navigation, saved messages/evidence, loading/errors, result rendering and credentialed requests. They do not establish live Google or Gemini behavior; use the live checklist separately.
