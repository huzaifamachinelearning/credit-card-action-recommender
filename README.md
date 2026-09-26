# Virexo — Customer Intelligence & Action Recommendation System

A Streamlit web app that assigns a new credit-card customer to a behavioural **segment**
and generates **prioritised, confidence-scaled actions**. It operationalises the Week-4
KMeans segmentation and the Week-5/6 recommendation engine.

## What it does

1. **Segment assignment** — reproduces the trained feature pipeline (`log1p` → `StandardScaler`
   → `KMeans`, k=2) and assigns the customer to **Transactors** or **Cash-Advance Revolvers**,
   with a **confidence** score (distance-to-centroid margin, 0 = boundary, 1 = firmly inside).
2. **Recommendation layer** — a documented, rule-based engine. Segment sets the archetype;
   the customer's own KPIs decide which actions fire and their priority. Action **intensity
   scales with confidence**, and **credit actions are suppressed on borderline assignments**
   (routed to manual review instead).
3. **Visuals** — customer KPI table and a 2-D PCA map showing where the customer sits relative
   to the whole customer base.

## Files

| File | Purpose |
|------|---------|
| `app.py` | Streamlit UI (form → results) |
| `recommender.py` | `SegmentRecommender` class — all model + rule logic (shared with the notebook) |
| `credit_card_data.csv` | Training data (8,950 customers); the model fits on startup (<1s) |
| `requirements.txt` | Dependencies |

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open http://localhost:8501.

## Deploy a public link (Streamlit Community Cloud — free)

1. Put this `virexo_app/` folder in a **public GitHub repository** (it can be its own repo, or a
   subfolder of your project repo).
2. Go to https://share.streamlit.io → **New app** → sign in with GitHub.
3. Select the repo/branch, set **Main file path** to `app.py` (or `virexo_app/app.py` if it is a
   subfolder), and click **Deploy**.
4. You get a permanent URL like `https://<name>.streamlit.app` — that is the link to submit.

> Streamlit Cloud installs from `requirements.txt` at the **repo root**. If you deploy the app as
> a subfolder, either move `requirements.txt` to the repo root or make `virexo_app/` its own repo.

## Quick temporary link (optional, for testing)

```bash
streamlit run app.py           # terminal 1
npx localtunnel --port 8501    # terminal 2  (or: ngrok http 8501)
```

## Notes & limitations

- The model is **unsupervised** — segments are behavioural clusters, not a credit-risk model.
  Recommendations are **decision-support**, subject to human review, affordability checks and
  fair-lending rules.
- Fields left blank default to the population median.
- Reproducible: fixed `random_state=42`; thresholds are percentile-based on the training data.
