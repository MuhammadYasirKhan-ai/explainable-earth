# DEPLOY.md: step by step (Roman Urdu + English commands)

Sab commands project folder `explainable-earth` ke andar chalane hain.

## Step 1: Local par chalao (5 min)
```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
streamlit run streamlit_app.py     # browser mein http://localhost:8501
```
Agar app khul jaye aur 3 tabs nazar aayein to theek hai.

## Step 2: NASA ka taza data lao (2 min)
Bundled data 2022 tak hai. Taza data (2025 tak) laane ke liye:
```bash
python -m explainable_earth.data --refresh
python -c "import shutil; from explainable_earth.data import CACHE_PATH, BUNDLED_PATH; shutil.copy(CACHE_PATH, BUNDLED_PATH)"
python -m explainable_earth.data        # last year check karo
```
Is se GitHub/cloud wali app mein bhi taza data hoga. Agar refresh fail ho (internet/NASA site), bundled data hi rehne do, app phir bhi chalegi.

## Step 3: Tests chalao (2 min)
```bash
ruff check . && mypy && pytest --cov=explainable_earth
```
Sab pass hone chahiye. Agar koi test fail ho (taza data se numbers badal sakte hain), error mujhe bhej do.

## Step 4: GitHub par daalo (5 min)
1. github.com par jao, **New repository** banao: naam `explainable-earth`, **Public**, README/.gitignore add NA karo.
2. Phir:
```bash
git init
git add .
git commit -m "Explainable Earth: NASA Space Apps 2026"
git branch -M main
git remote add origin https://github.com/<YOUR_USERNAME>/explainable-earth.git
git push -u origin main
```
`<YOUR_USERNAME>` apne GitHub username se badlo. Password ki jagah GitHub Personal Access Token ya GitHub Desktop use karo.

## Step 5: Online deploy karo, free (5 min)
Streamlit Community Cloud:
1. share.streamlit.io par GitHub se login karo.
2. **Create app** -> **Deploy a public app from GitHub**.
3. Repository: `<YOUR_USERNAME>/explainable-earth`, Branch: `main`, Main file path: `streamlit_app.py`.
4. **Deploy** dabao. 2-5 minute mein link milega: `https://<name>.streamlit.app`.
5. Link kholo aur check karo ke teeno tabs chal rahe hain. Link README mein "Live demo" ke saath paste karo, commit + push karo.

Alternative (agar Streamlit Cloud na chale): Docker se deploy, `Dockerfile` already maujood hai:
```bash
docker build -t explainable-earth .
docker run -p 8501:8501 explainable-earth
```
Ye Render, Railway ya Fly.io par bhi chalta hai.

## Step 6: Demo banao (10 min)
Screen recording, 30 second ya kam: trend chart -> "Who drives the trend?" tab -> Arctic bar chart. Ya 7 slides (outline `SUBMISSION.md` mein). Google Drive/YouTube par daalo, sharing "Anyone with the link", aur poora `https://...` link copy karo.

## Step 7: NASA Space Apps form (10 min)
- **Project Demonstration:** demo ka public link
- **Project:** GitHub repo link (ya live app link)
- **Summary / Project Details / NASA Data:** `SUBMISSION.md` se copy karo. Numbers apni app ke numbers se match karo (Step 2 ke baad badal sakte hain).
- **Use of SI:** code aur text/documentation wale options tick karo (Claude by Anthropic). Agar AI se bana logo/image use kiya to uspar visible "SI-generated" watermark lagao.
- Dono verification boxes tick karo, **Save Progress**, phir **Submit for Judging**.

Deadline: **Sunday 15 November, 11:59 PM** (local time). Is ke baad edit nahi hota.

## Common masle
| Masla | Hal |
|---|---|
| `ModuleNotFoundError: explainable_earth` | `streamlit run streamlit_app.py` use karo (root se) ya `pip install -e .` |
| Refresh button error | NASA site se connection nahi; bundled data use karo |
| Streamlit Cloud build fail | `requirements.txt` repo root mein hai? Python 3.12 select karo |
| `git push` rejected | Repo naya aur khali hona chahiye; `git pull --rebase origin main` phir push |
