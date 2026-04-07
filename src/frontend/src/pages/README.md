# Pages — Route-Level Page Components

Each file in this directory corresponds to a top-level route defined in `App.tsx`. Pages compose smaller components from `components/` and call the API layer from `api/`.

## Files

| File | Route | Description |
|------|-------|-------------|
| `LandingPage.tsx` | `/` | Public zone map showing sensor health; visible without login |
| `LoginPage.tsx` | `/login` | Username/password login form; stores JWT in `AuthContext` |
| `RegisterRequestPage.tsx` | `/register` | New-user registration request form (requires admin approval) |
| `AccountPage.tsx` | `/account` | View and edit the logged-in user's profile; admins can manage all accounts |
| `ThresholdsPage.tsx` | `/thresholds` | Threshold CRUD dashboard with live alert panel and severity charts |
