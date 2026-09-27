# Virexo — Customer Intelligence & Action Recommendation System

This repository contains a notebook exploring the [credit card dataset](https://www.kaggle.com/datasets/arjunbhasin2013/ccdata) and an app that classifies a new customer into transactor or resolver.

The notebook performs exploratory data analysis, runs kmeans to identify clusters, implements a recommendation layer and suggest actions for new customers. The streamlit app provides interface to give recommendations for new customer.
## Notebook & App
The notebook is available at [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/huzaifamachinelearning/credit-card-action-recommender/blob/main/Virexo_task_5%2B6.ipynb)

The app is deployed at [app](https://credit-card-action-recommender-un9zfyx4fgurmmfaolxgm4.streamlit.app)
## Steps to reproduce
### notebook 
The notebook can be easily downloaded either separately or by cloning the repository. One can go to the link  [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/huzaifamachinelearning/credit-card-action-recommender/blob/main/Virexo_task_5%2B6.ipynb)
and play around with the notebook and save their  changes to thier own repository or google drive.
### running the app locally
clone the repository by running
   
   ``` git clone https://github.com/huzaifamachinelearning/credit-card-action-recommender.git```
   then run
   ```
   pip install -r requirements.txt
   streamlit run app.py
   ```
   to run the app locally.

### deploying the app   
1. Put this `virexo_app/` folder in a **public GitHub repository** (it can be its own repo, or a
   subfolder of your project repo).
2. Go to https://share.streamlit.io → **New app** → sign in with GitHub.
3. Select the repo/branch, set **Main file path** to `app.py` (or `virexo_app/app.py` if it is a
   subfolder), and click **Deploy**.
4. You get a permanent URL like `https://<name>.streamlit.app`.

 Streamlit Cloud installs from `requirements.txt` at the **repo root**. If you deploy the app as
 a subfolder, either move `requirements.txt` to the repo root or make `virexo_app/` its own repo.
   
   
## Files 

| File | Purpose |
|------|---------|
| `app.py` | Streamlit UI  |
| `recommender.py` | `SegmentRecommender` class contains the model mechanics and rule logic (duplicated from notebook) |
| `credit_card_data.csv` | Training data (8,950 customers); the model fits on startup taking less than 1 s |
| `requirements.txt` | Dependencies |
| `Virexo_task_5+6 | notebook that does EDA , runs the clustering algorithm,implements recommendation layer| 


## Workflow

```text
Credit Card Dataset
        ↓
Exploratory Data Analysis
        ↓
Preprocessing & Feature Engineering
        ↓
K-Means Clustering
        ↓
Customer Segmentation
        ↓
Recommendation Rules
        ↓
SegmentRecommender
        ↓
Streamlit Application
        ↓
Customer Segment + Confidence + Recommendation
```

## Usage
The content of this repository is suitable for educational purposes and it is not a system tested in the real world. One can gain a lot of knowledge from playing around with the notebook. This repository was created as the final capstone as an intern at Virexo Innovations

## Notes & limitations
- there is the duplication of logic of notebook in recommender.py. The alternative route(saving the logic from notebook and resuing it in the streammlit app) is not taken to avoid streamlit hosting issues.
- The model is **unsupervised** — segments are behavioural clusters, not a credit-risk model.
  Recommendations are **decision-support**, subject to human review, affordability checks and
  fair-lending rules.
- Fields left blank default to the population median.
  
