# Seattle Tennis Court Reservations Dashboard

Checks which public Seattle Parks tennis courts have reservations today (8am–4pm window).

## How it works

The Active.com booking system only shows *tomorrow's* availability, not today's. This scraper runs every night at **11:55 PM Pacific**, captures tomorrow's data, and stores it so you can check it any time on the day-of.

## Setup (one time)

### 1. Create a GitHub repo

```bash
cd tennis-courts
git init
git add .
git commit -m "Initial commit"
gh repo create seattle-tennis-courts --public --source=. --push
```

### 2. Enable GitHub Pages

- Go to your repo on GitHub → **Settings** → **Pages**
- Source: **Deploy from a branch**, branch: `main`, folder: `/ (root)`
- Save. Your dashboard will be live at `https://YOUR-USERNAME.github.io/seattle-tennis-courts/`

### 3. Enable GitHub Actions write permission

- Go to **Settings** → **Actions** → **General** → scroll to **Workflow permissions**
- Select **Read and write permissions** → Save

That's it. The scraper runs automatically every night. You can also trigger it manually from the **Actions** tab → **Scrape Tennis Court Reservations** → **Run workflow**.

## Running locally

```bash
pip install -r requirements.txt
python scrape.py          # fetches tomorrow's data
python -m http.server     # serves the dashboard at http://localhost:8000
```

## Courts tracked

- Amy Yee Tennis Center (AYTC) — 6 courts
- Bryant Playground — 2 courts
- Froula Playground — 2 courts
- Laurelhurst Playfield — 4 courts
- Lower Woodland Playfield — 10 courts + 3 upper courts
- Meadowbrook Playfield — 6 courts
- Montlake Playfield — 2 courts
- Volunteer Park — 4 courts (upper + lower)
- Wallingford Playfield — 2 courts
