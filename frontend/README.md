# KrishiAdvisor React frontend

This is a separate React + Vite frontend. The existing Flask/Jinja frontend in
`../templates` is preserved and continues to work.

## Development

1. Start the existing Flask backend from the project root:

   ```powershell
   python app.py
   ```

2. Install frontend dependencies:

   ```powershell
   cd frontend
   npm install
   ```

3. Start Vite:

   ```powershell
   npm run dev
   ```

Open `http://localhost:5173`. Vite proxies `/api/*` requests to the Flask
server at `http://127.0.0.1:5000`.

The React dashboard uses the Flask session cookie. Log in through the existing
Flask login page before opening the React dashboard:

`http://127.0.0.1:5000/login`

## Current React routes

- `/` - React home page
- `/advisor` - React AI advisor connected to `/api/crops` and `/api/predict`
- `/dashboard` - React dashboard connected to `/api/dashboard`
- `/planner` - React crop planning page connected to `/api/planner`
- `/stock` - React inventory view connected to `/api/stock`
- `/sales` - React sales history connected to `/api/sales`
- `/profile` - React farmer profile connected to `/api/profile`

The React advisor also has an **AI farmer guidance** button. It sends the
numerical prediction and farmer inputs to a protected Flask endpoint. The AI
provider key stays on the Flask server and is never placed in React or exposed
to the browser.

The remaining Flask pages are intentionally unchanged and can be migrated to
React incrementally.
