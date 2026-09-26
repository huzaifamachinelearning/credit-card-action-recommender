"""
Virexo — Customer Intelligence & Action Recommendation System (Streamlit app).

Run locally:   streamlit run app.py
The whole script re-runs top-to-bottom on every interaction; the trained model is
cached with @st.cache_resource so it is fit only once.
"""
import os
import altair as alt
import pandas as pd
import streamlit as st

from recommender import SegmentRecommender, BASE_COLUMNS

DATA_PATH = os.path.join(os.path.dirname(__file__), "credit_card_data.csv")

st.set_page_config(page_title="Virexo Customer Intelligence", page_icon="💳", layout="wide")


@st.cache_resource(show_spinner="Fitting the segmentation model...")
def load_model():
    return SegmentRecommender.from_training(DATA_PATH)


model = load_model()

# ---- preset example customers -------------------------------------------------
PRESETS = {
    "— custom —": {},
    "Low-risk frequent transactor": dict(
        BALANCE=200, CASH_ADVANCE=0, PURCHASES=4000, ONEOFF_PURCHASES=3000,
        INSTALLMENTS_PURCHASES=1000, PURCHASES_FREQUENCY=0.9, PURCHASES_TRX=40,
        CASH_ADVANCE_TRX=0, CREDIT_LIMIT=8000, PAYMENTS=4200, MINIMUM_PAYMENTS=300,
        PRC_FULL_PAYMENT=0.9),
    "Heavy cash-advance revolver": dict(
        BALANCE=7000, CASH_ADVANCE=6000, PURCHASES=100, ONEOFF_PURCHASES=100,
        INSTALLMENTS_PURCHASES=0, PURCHASES_FREQUENCY=0.1, CASH_ADVANCE_FREQUENCY=0.8,
        PURCHASES_TRX=2, CASH_ADVANCE_TRX=15, CREDIT_LIMIT=8000, PAYMENTS=800,
        MINIMUM_PAYMENTS=900, PRC_FULL_PAYMENT=0.0),
    "Dormant low-utilization transactor": dict(
        BALANCE=50, CASH_ADVANCE=0, PURCHASES=150, ONEOFF_PURCHASES=150,
        INSTALLMENTS_PURCHASES=0, PURCHASES_FREQUENCY=0.1, PURCHASES_TRX=3,
        CASH_ADVANCE_TRX=0, CREDIT_LIMIT=6000, PAYMENTS=200, MINIMUM_PAYMENTS=60,
        PRC_FULL_PAYMENT=0.5),
}

st.title(" Customer Intelligence & Action Recommendation System")
st.caption("Assign a new credit-card customer to a behavioural segment and generate "
           "prioritised, confidence-scaled actions. Built on the Week-4 KMeans segmentation.")

# ---- sidebar: inputs ----------------------------------------------------------
with st.sidebar:
    st.header("New customer")
    preset_name = st.selectbox("Start from a preset", list(PRESETS.keys()))
    preset = PRESETS[preset_name]

    def dflt(field, fallback):
        return float(preset.get(field, model.medians.get(field, fallback)))

    st.subheader("Key fields")
    vals = {}
    vals['BALANCE']            = st.number_input("Balance", min_value=0.0, value=dflt('BALANCE', 0.0), step=100.0)
    vals['CREDIT_LIMIT']       = st.number_input("Credit limit", min_value=1.0, value=dflt('CREDIT_LIMIT', 3000.0), step=500.0)
    vals['PURCHASES']          = st.number_input("Purchases (total)", min_value=0.0, value=dflt('PURCHASES', 0.0), step=100.0)
    vals['CASH_ADVANCE']       = st.number_input("Cash advance (total)", min_value=0.0, value=dflt('CASH_ADVANCE', 0.0), step=100.0)
    vals['PAYMENTS']           = st.number_input("Payments (total)", min_value=0.0, value=dflt('PAYMENTS', 0.0), step=100.0)
    vals['MINIMUM_PAYMENTS']   = st.number_input("Minimum payments", min_value=0.0, value=dflt('MINIMUM_PAYMENTS', 0.0), step=50.0)
    vals['PURCHASES_FREQUENCY']= st.slider("Purchases frequency", 0.0, 1.0, value=dflt('PURCHASES_FREQUENCY', 0.5))
    vals['PRC_FULL_PAYMENT']   = st.slider("Full-payment rate", 0.0, 1.0, value=dflt('PRC_FULL_PAYMENT', 0.0))

    with st.expander("Advanced fields (optional)"):
        for f in ['ONEOFF_PURCHASES', 'INSTALLMENTS_PURCHASES', 'PURCHASES_TRX',
                  'CASH_ADVANCE_TRX', 'CASH_ADVANCE_FREQUENCY', 'BALANCE_FREQUENCY',
                  'ONEOFF_PURCHASES_FREQUENCY', 'PURCHASES_INSTALLMENTS_FREQUENCY', 'TENURE']:
            vals[f] = st.number_input(f.replace('_', ' ').title(),
                                      min_value=0.0, value=dflt(f, 0.0),
                                      help="Defaults to the population median if left unset.")
    go = st.button("Get recommendations", type="primary", width="stretch")

# ---- main panel: results ------------------------------------------------------
if not go:
    st.info(" Fill in the customer's fields (or pick a preset) and click **Get recommendations**.")
    st.stop()

result = model.predict(vals)

seg_is_revolver = result['label'] == model.REVOLVER
# Shrink metric values so long segment names (e.g. "Cash-Advance Revolvers")
# fit instead of being truncated with an ellipsis.
st.markdown(
    "<style>[data-testid='stMetricValue']{font-size:1.4rem;white-space:normal;}</style>",
    unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)
c1.metric("Assigned segment", result['segment'])
c2.metric("Assignment confidence", f"{result['confidence']:.2f}",
          help="0 = on the boundary between segments, 1 = firmly inside one segment.")
c3.metric("Delivery intensity", "Manual review" if result['borderline'] else result['intensity'],
          help="How proactively actions are delivered — scales with confidence.")

st.write(f"**Segment profile:** {result['segment_profile']}")
if result['borderline']:
    st.warning("⚠️ Borderline assignment — automated credit actions are suppressed; "
               "the case is routed to manual review.")

st.subheader("Recommended actions (prioritised)")
rec_df = pd.DataFrame(result['recommendations'])
if len(rec_df):
    rec_df = rec_df.rename(columns={'priority': 'P', 'rule': 'Rule', 'intensity': 'Intensity',
                                    'action': 'Action', 'rationale': 'Why it fits',
                                    'target_kpi': 'Target KPI'})
    st.dataframe(rec_df[['P', 'Rule', 'Intensity', 'Action', 'Why it fits', 'Target KPI']],
                 hide_index=True, width="stretch")
else:
    st.write("No actions triggered.")

# ---- KPI + PCA views ----------------------------------------------------------
left, right = st.columns([1, 1.4])
with left:
    st.subheader("Customer KPIs")
    k = result['kpis']
    st.dataframe(pd.DataFrame({
        'KPI': ['Credit utilization', 'Cash reliance', 'Payment-to-minimum',
                'Purchase frequency', 'Purchases', 'Full-payment rate'],
        'Value': [f"{k['credit_util']:.2f}", f"{k['cash_reliance']:.2f}",
                  f"{k['payment_to_min']:.2f}", f"{k['purch_freq']:.2f}",
                  f"{k['purchases']:.0f}", f"{k['full_pay_rate']:.2f}"],
    }), hide_index=True, width="stretch")

with right:
    st.subheader("Where this customer sits (PCA map)")
    pop = model.pca_population.sample(min(2500, len(model.pca_population)), random_state=0)
    seg_scale = alt.Scale(domain=['Transactors', 'Cash-Advance Revolvers'],
                          range=['#0072B2', '#E69F00'])  # contrasting blue / orange
    base = alt.Chart(pop).mark_circle(size=18, opacity=0.35).encode(
        x='PC1:Q', y='PC2:Q',
        color=alt.Color('segment:N', scale=seg_scale, legend=alt.Legend(title="Segment")))
    pt = pd.DataFrame([{'PC1': result['pca_point'][0], 'PC2': result['pca_point'][1],
                        'segment': 'This customer'}])
    star = alt.Chart(pt).mark_point(size=400, shape='diamond', color='red',
                                    filled=True, stroke='black').encode(x='PC1:Q', y='PC2:Q')
    st.altair_chart(base + star, width="stretch")

st.caption("Decision-support only — subject to human review, affordability checks and fair-lending rules. "
           "Segments are behavioural clusters, not a credit-risk model.")
