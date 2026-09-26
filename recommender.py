"""
Virexo — Customer Segment Assignment & Recommendation Engine (reusable module).

This packages the Week-5/6 notebook logic into a single class so both the notebook
and the Streamlit app share one implementation:

    model = SegmentRecommender.from_training("credit_card_data.csv")
    result = model.predict({"BALANCE": 200, "PURCHASES": 4000, ...})

The model is unsupervised (KMeans, k=2) fit on log1p + standardized features.
Fitting on 8,950 rows takes well under a second, so the app fits on startup.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from sklearn.preprocessing import FunctionTransformer, StandardScaler
from sklearn.pipeline import make_pipeline, Pipeline
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

# Raw schema (after dropping CUST_ID) the model is trained on, in order.
BASE_COLUMNS = [
    'BALANCE', 'BALANCE_FREQUENCY', 'PURCHASES', 'ONEOFF_PURCHASES',
    'INSTALLMENTS_PURCHASES', 'CASH_ADVANCE', 'PURCHASES_FREQUENCY',
    'ONEOFF_PURCHASES_FREQUENCY', 'PURCHASES_INSTALLMENTS_FREQUENCY',
    'CASH_ADVANCE_FREQUENCY', 'CASH_ADVANCE_TRX', 'PURCHASES_TRX',
    'CREDIT_LIMIT', 'PAYMENTS', 'MINIMUM_PAYMENTS', 'PRC_FULL_PAYMENT', 'TENURE',
]

# Rule registry: priority 1 = act first. `is_credit` flags actions that change a
# credit line / lending product, which are gated on low-confidence assignments.
RULES = [
    # rule, segment,        priority, action, rationale, target_kpi, is_credit
    ('R1', 'Transactors', 1, 'Pre-approve a credit-limit increase',
     'Unused capacity plus servicing above the minimum means headroom converts to spend at limited incremental risk.',
     'Interchange/spend uplift; PD flat', True),
    ('R2', 'Transactors', 2, 'Offer rewards / premium-card upgrade',
     'Frequent, high-volume merchant spend monetises via interchange; rewards deepen wallet share.',
     'Interchange revenue; retention', False),
    ('R3', 'Transactors', 2, 'Send targeted activation nudges',
     'A reliable but under-engaged user is low-cost to reactivate.',
     'Active-rate; monthly spend', False),
    ('R4', 'Transactors', 3, 'Offer one-off to installment conversion',
     'One-off-heavy segment; optional installment plans add interest income from a low-risk payer.',
     'Interest income', False),
    ('R5', 'Cash-Advance Revolvers', 1, 'Offer a lower-APR installment / consolidation loan for cash advances',
     'Cash advances charge interest from day one; a cheaper structured product lowers customer cost and improves '
     'repayment odds while retaining the balance.',
     'Roll-to-delinquency down; balances retained', True),
    ('R6', 'Cash-Advance Revolvers', 1, 'Enable near-limit / high-utilization alerts',
     'Utilization above the 90th percentile is a leading stress signal.',
     'Over-limit incidents; delinquency', False),
    ('R7', 'Cash-Advance Revolvers', 2, 'Hold (do not cut) credit-limit increases pending 2-3 cycles',
     'Elevated utilization with slower repayment is associated with higher risk; holding is the proportionate step.',
     'Expected loss; fair-treatment', True),
    ('R8', 'Cash-Advance Revolvers', 1, 'Enroll in autopay + reminders; surface hardship / wellness tools',
     'Paying at or below the minimum with a near-zero full-payment rate raises delinquency odds; support is the '
     'responsible first action.',
     'Delinquency rate; customer welfare', False),
    ('R9', 'Any', 1, 'Route to manual review - borderline assignment',
     'The customer sits near the segment boundary; apply conservative defaults and make no automated credit change.',
     'Decision quality', False),
]


def _safe(n, d):
    return (n / d).replace([np.inf, -np.inf], np.nan).fillna(0)


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Deterministic feature builder: reindex to the training schema, then derive
    the five engineered features (division-by-zero guarded to 0)."""
    out = df.reindex(columns=BASE_COLUMNS).copy()
    out['credit_util']        = _safe(out['BALANCE'], out['CREDIT_LIMIT'])
    out['cash_reliance']      = _safe(out['CASH_ADVANCE'], out['PURCHASES'] + out['CASH_ADVANCE'])
    out['payment_to_min']     = _safe(out['PAYMENTS'], out['MINIMUM_PAYMENTS'])
    out['avg_purchase_value'] = _safe(out['PURCHASES'], out['PURCHASES_TRX'])
    out['total_trx']          = out['PURCHASES_TRX'] + out['CASH_ADVANCE_TRX']
    return out


class SegmentRecommender:
    """Assigns a customer to a segment and returns prioritised, confidence-scaled actions."""

    def __init__(self, pipeline, medians, thresholds, intensity_cuts,
                 transactor_label, revolver_label, segments, rules_df,
                 pca, pca_population):
        self.pipeline = pipeline
        self.medians = medians
        self.thresholds = thresholds
        self.intensity_cuts = intensity_cuts
        self.TRANSACTOR = transactor_label
        self.REVOLVER = revolver_label
        self.segments = segments
        self.rules_df = rules_df
        self.pca = pca
        self.pca_population = pca_population   # DataFrame: PC1, PC2, segment

    # ---- training -------------------------------------------------------
    @classmethod
    def from_training(cls, source="credit_card_data.csv"):
        raw = pd.read_csv(source)
        if 'CUST_ID' in raw.columns:
            raw = raw.drop('CUST_ID', axis=1)
        # impute each column with ITS OWN median (Week-4 review fix)
        raw['CREDIT_LIMIT'] = raw['CREDIT_LIMIT'].fillna(raw['CREDIT_LIMIT'].median())
        raw['MINIMUM_PAYMENTS'] = raw['MINIMUM_PAYMENTS'].fillna(raw['MINIMUM_PAYMENTS'].median())
        medians = raw.median(numeric_only=True).to_dict()

        feats = build_features(raw)
        pipeline = Pipeline([
            ('preprocessing', make_pipeline(
                FunctionTransformer(func=np.log1p, inverse_func=np.expm1),
                StandardScaler())),
            ('kmean', KMeans(n_clusters=2, n_init=10, random_state=42)),
        ]).fit(feats)
        labels = pipeline['kmean'].labels_

        # identify segments from centroids (higher cash_reliance -> revolvers)
        by_cash = feats.assign(cluster=labels).groupby('cluster')['cash_reliance'].mean()
        revolver = int(by_cash.idxmax())
        transactor = int(by_cash.idxmin())
        segments = {
            transactor: {'name': 'Transactors',
                         'profile': 'Merchant-payment oriented; lower utilization and revolving balances. '
                                    'Majority segment (~65%); lower-risk core of the book.'},
            revolver: {'name': 'Cash-Advance Revolvers',
                       'profile': 'Higher reliance on cash advances, higher balances and utilization, slower repayment. '
                                  'Smaller segment (~35%); higher-margin but statistically higher-risk.'},
        }

        thresholds = {
            'util_low':    float(feats['credit_util'].quantile(0.33)),
            'util_high':   float(feats['credit_util'].quantile(0.66)),
            'util_vhigh':  float(feats['credit_util'].quantile(0.90)),
            'pay_strong':  float(feats['payment_to_min'].quantile(0.60)),
            'purch_high':  float(feats['PURCHASES'].quantile(0.66)),
            'cash_heavy':  0.50,
            'freq_active': 0.50,
        }

        # confidence distribution -> data-driven borderline + intensity tiers
        Xn = pipeline['preprocessing'].transform(feats)
        conf = cls._confidence(pipeline['kmean'].transform(Xn))
        thresholds['conf_border'] = float(np.percentile(conf, 10))
        intensity_cuts = (float(np.percentile(conf, 33)), float(np.percentile(conf, 66)))

        rules_df = pd.DataFrame(
            RULES, columns=['rule', 'segment', 'priority', 'action', 'rationale',
                            'target_kpi', 'is_credit']).set_index('rule')

        pca = PCA(n_components=2, random_state=42).fit(Xn)
        p2 = pca.transform(Xn)
        pca_population = pd.DataFrame({
            'PC1': p2[:, 0], 'PC2': p2[:, 1],
            'segment': [segments[l]['name'] for l in labels]})

        return cls(pipeline, medians, thresholds, intensity_cuts, transactor,
                   revolver, segments, rules_df, pca, pca_population)

    # ---- inference helpers ---------------------------------------------
    @staticmethod
    def _confidence(dist):
        """Margin confidence in [0,1]: 0 = on the boundary, ->1 = firmly inside a segment."""
        nt = np.sort(dist, axis=1)[:, :2]
        d_near, d_far = nt[:, 0], nt[:, 1]
        return (d_far - d_near) / (d_far + d_near)

    def _intensity(self, confidence):
        lo, hi = self.intensity_cuts
        return 'Strong' if confidence >= hi else ('Moderate' if confidence >= lo else 'Soft')

    def _complete(self, customer: dict) -> pd.DataFrame:
        """Fill any missing fields with population medians -> one-row raw frame."""
        row = dict(self.medians)
        row.update({k: v for k, v in customer.items() if v is not None})
        return pd.DataFrame([row])[BASE_COLUMNS]

    def _fired_rules(self, k, label, borderline):
        T = self.thresholds
        fired = []
        if label == self.TRANSACTOR:
            if k['credit_util'] < T['util_low'] and k['payment_to_min'] >= T['pay_strong'] and not borderline:
                fired.append('R1')
            if k['purch_freq'] >= T['freq_active'] and k['purchases'] >= T['purch_high']:
                fired.append('R2')
            if k['purch_freq'] < T['freq_active']:
                fired.append('R3')
            fired.append('R4')
        else:
            if k['cash_reliance'] > T['cash_heavy'] or k['credit_util'] > T['util_high']:
                fired.append('R5')
            if k['credit_util'] > T['util_vhigh']:
                fired.append('R6')
            fired.append('R7')
            if k['payment_to_min'] < 1.0 or k['full_pay_rate'] < 0.05:
                fired.append('R8')
        if borderline:
            fired.append('R9')
        return fired

    # ---- public API -----------------------------------------------------
    def predict(self, customer: dict) -> dict:
        raw = self._complete(customer)
        feats = build_features(raw)
        Xn = self.pipeline['preprocessing'].transform(feats)
        dist = self.pipeline['kmean'].transform(Xn)
        label = int(dist.argmin(axis=1)[0])
        confidence = float(self._confidence(dist)[0])
        borderline = confidence < self.thresholds['conf_border']
        tier = self._intensity(confidence)

        frow = feats.iloc[0]
        kpis = {
            'credit_util':    float(frow['credit_util']),
            'cash_reliance':  float(frow['cash_reliance']),
            'payment_to_min': float(frow['payment_to_min']),
            'purch_freq':     float(frow['PURCHASES_FREQUENCY']),
            'purchases':      float(frow['PURCHASES']),
            'full_pay_rate':  float(frow['PRC_FULL_PAYMENT']),
        }

        recs = []
        for rule in self._fired_rules(kpis, label, borderline):
            meta = self.rules_df.loc[rule]
            if bool(meta['is_credit']) and borderline and rule != 'R9':
                continue  # never auto-execute a credit action on a low-confidence assignment
            recs.append({
                'rule': rule,
                'priority': int(meta['priority']),
                'intensity': 'Manual review' if rule == 'R9' else tier,
                'action': str(meta['action']),
                'rationale': str(meta['rationale']),
                'target_kpi': str(meta['target_kpi']),
            })
        recs.sort(key=lambda r: r['priority'])

        pc = self.pca.transform(Xn)[0]
        return {
            'segment': self.segments[label]['name'],
            'segment_profile': self.segments[label]['profile'],
            'label': label,
            'confidence': confidence,
            'intensity': tier,
            'borderline': borderline,
            'kpis': kpis,
            'recommendations': recs,
            'pca_point': (float(pc[0]), float(pc[1])),
        }
