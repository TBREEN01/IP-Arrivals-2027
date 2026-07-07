# PVD/BOS Arrivals Board — Setup

One-time setup, about 10 minutes. After this, it runs itself.

## 1. Create a GitHub account (if you don't have one)
Free, at github.com/join.

## 2. Create a new repository
- Click "+" (top right) → "New repository"
- Name it something like `pvd-arrivals` (doesn't matter, becomes part of your URL)
- Set to **Public** (simplest — free Actions minutes are unlimited for public repos)
- Skip adding a README/gitignore — leave it empty
- Click "Create repository"

## 3. Upload these files
On the new repo's page, click "Add file" → "Upload files", then drag in:
- `fetch_flights.py`
- `flights_source.json`
- `index.html`
- `README.md` (optional, just for your reference)

Then separately create the workflow file (GitHub requires it in a specific folder):
- Click "Add file" → "Create new file"
- Name it exactly: `.github/workflows/update.yml` (the slashes create the folders automatically)
- Paste in the workflow content
- Commit directly to `main`

## 4. Add your API key as a secret
- Go to the repo's **Settings** tab → **Secrets and variables** → **Actions**
- Click **New repository secret**
- Name: `AERODATABOX_KEY`
- Value: paste your AeroDataBox/RapidAPI key
- Save

This keeps your key private — it's never visible in the code or to anyone viewing the dashboard.

## 5. Give the workflow permission to save data
- Settings → **Actions** → **General** → scroll to "Workflow permissions"
- Select **Read and write permissions**
- Save

## 6. Turn on GitHub Pages
- Settings → **Pages**
- Under "Build and deployment" → Source: **Deploy from a branch**
- Branch: `main`, folder: `/ (root)`
- Save

GitHub will give you a URL like:
`https://YOUR-USERNAME.github.io/pvd-arrivals/`

**That's the link you share with your team.** Anyone who opens it sees the same live board — no login, no key, works on phone/tablet/laptop.

## 7. Run it once manually to kick things off
- Go to the **Actions** tab → click "Update Flight Data" (left sidebar) → **Run workflow** → Run workflow
- Wait ~30 seconds, refresh the Actions page — it should show a green checkmark
- Then open your Pages URL — you should see today's flights start populating

After that, it runs automatically every 10 minutes on its own. No further action needed from you.

## Notes
- GitHub's free scheduled runs aren't always exactly on the minute — expect ±5 min of drift sometimes, still well within "close to real-time."
- The polling is adaptive: flights far from their arrival time are checked hourly; flights within 30 minutes of landing are checked every ~8 minutes, so the board updates fastest exactly when it matters.
- If you need to add/change flights for a different day, just edit `flights_source.json` in the repo (click the file → pencil icon → edit → commit) and update the date in `.github/workflows/update.yml` (the `python3 fetch_flights.py 2026-07-08` line).
