# Formal report

# **Summary of Findings**
## General Insights
1. 51 percent of people only make purchases and take no cash in advance
2. 22% of people only take cash in advance and not make purchases.
3. 69% of the people use their creditcard to the highest degree of frequency
remaining 31% are thinly spread among lower frequencies and bank can introduce perks to intice the remaining inactive customers

4.  more than 65% of people do not pay full payment ever
5. Portion for One-off purchases is fixed in the purchases of customers(70%)
6. It also looks like that some frequencies  balnce_frequencie are unnaturally cut off at 1.(what is the reason? how was data collected?)

## The most dominant pattern CASH_ADVANCE
cluster 0 consumers use credit card for purchases transfering money directly to merchants(as the credit card is meant to be used ).Cluster 1 is smaller than Cluster 0. They take cash in advance a lot and spend it outside of the credit card system . There are stricter interest conditions for this kind of cash withdrawl which may suggest that they need money urgently



## Debt
cluster 0 customers have lower debt and have consumed lower proprtion of their credit limit. Cluster 1 customers are closer to their credit limit and have more debt to the bank


## PAYMENT TO BALANCE Ratio
cluster 0 have done more payment for one unit of debt they have. If we combine that with the fact that they generally have lower balance(ie debt) this means they payback quickly and dont let balance pile up

On the other hand cluster 1 have smaller ratio, consistent with carrying revolving balances for longer

## BALANCE_FREQUENCY show no difference
both groups inherit the pattern of the overall data set where a significant portion of the clientle are active to the highest degree and customers are thinly spread among the remining degrees

## cluster 1 takes cash out in larger amounts and and pays it back incrementally
both clusters have the same balance_frequency but cluster 1 has less total_trx. on the other hand avg_transact_value is greater for cluster1. That is cluster1 customers  borrow money in larger amounts and in fewer number of transactions.Given that both clusters exhibit similar balance frequency, Cluster 1 customers would likely repay their larger cash advances over a greater number of installments, with each installment representing a smaller amount on average.

## installments vs one-off:
 There seem to be quite a few hardliners in cluster 0 with installments hardliners being more common.

## Borrowing Frequency
36% of cluster 0 is actively doing purchases to the highest frequency.
while a large bulk of cluster 1 are not drawing cash in advance much frequently.
In other words cluster 1 leads cluster 0 in borrwoing frequency.



## Characteristics,differences and Interpretation of Clusters
### Cluster 0
1. Cluster 0 consists of people who use the credit card  to pay the merchant directly.
2. These people usually have lower debts
3. They have consumed less proportion of their credit card limit.
4.  They are in the majority
5.  A significant portion of the clientle in this cluster are active to the highest degree and  ohters are thinly spread among the remaining degrees
6. They do more no of borrowing transactions (as compared to cluster 1) and on average take out  a lower debt(relative to cluster 1) per transaction
7. They have the same balance_frequency(degree of interaction) as cluster 1.
8. There are significant hardliners of installments and oneofff purchases(54%)   present in this group.
9.  cluster 0 is behind cluster 1 in borrowing frequency.
10. They are the healthy core customer base
11. the linear correlation between purchases and oneoff_purchases in cluster 0 is strong with oneoff_purchases making 72% of each person's purchases on average


### Cluster 1
1. As a contrast to this there is cluster 1 which consist of people who use the credit card to get cash.
2. They take cash in advance a lot and spend it outside of the credit card system . There are stricter interest conditions for this kind of cash withdrawl which may suggest that they need money urgently.

3. They ususally have higher debts.
4. They have consumed more proportion of their credit card limit.
5. They are less in numbers than cluster 0.
6. They do less no of borrowing transactions (as compared to cluster 0) and on average take out  a higher  debt(relative to cluster 0) per transaction
7. They have the same balance_frequency(degree of interaction) as cluster 0.
8. cluster 1 is ahead of cluster 0 in borrowing frequency.
9. They are the higher-margin but higher-risk part of the customer base.

## **Recommendation Rules**
| Rule | Segment | Priority | Condition | Action | Rationale | Target KPI | Is Credit Action |
|---|---|---:|---|---|---|---|---|
| R1 | Transactors | 1 | `util < util_low AND pay_to_min >= pay_strong AND not borderline` | Pre-approve a credit-limit increase | Unused capacity + servicing above minimum → headroom converts to spend at limited incremental risk | Interchange/spend uplift; PD flat | True |
| R2 | Transactors | 2 | `purch_freq >= freq_active AND PURCHASES >= purch_high` | Offer rewards / premium-card upgrade | Frequent high-volume merchant spend monetises via interchange; rewards deepen wallet share | Interchange revenue; retention | False |
| R3 | Transactors | 2 | `purch_freq < freq_active` | Send targeted activation nudges | Reliable but under-engaged users are low-cost to reactivate | Active-rate; monthly spend | False |
| R4 | Transactors | 3 | `always (low priority)` | Offer one-off → installment conversion | One-off-heavy segment; optional plans add interest income from low-risk payers | Interest income | False |
| R5 | Cash-Advance Revolvers | 1 | `cash_reliance > cash_heavy OR util > util_high` | Offer lower-APR installment / consolidation loan for cash advances | Cash advances charge interest from day one; a cheaper product lowers cost and improves repayment odds while retaining the balance | Roll-to-delinquency down; balances retained | True |
| R6 | Cash-Advance Revolvers | 1 | `util > util_vhigh` | Enable near-limit / high-utilization alerts | Utilization above the 90th percentile is a leading stress signal | Over-limit incidents; delinquency | False |
| R7 | Cash-Advance Revolvers | 2 | `always (medium)` | Hold (do not cut) credit-limit increases pending 2–3 cycles | Elevated utilization + slower repayment are associated with higher risk; holding is proportionate | Expected loss; fair-treatment | True |
| R8 | Cash-Advance Revolvers | 1 | `pay_to_min < 1 OR full_pay_rate < 0.05` | Enroll in autopay + reminders; surface hardship / wellness tools | Paying at/below minimum with ~0 full payment raises delinquency odds; support is the responsible first action | Delinquency rate; customer welfare | False |
| R9 | Any | 1 | `confidence < conf_border` | Route to manual review — borderline assignment | Near the segment boundary; apply conservative defaults, no automated credit change | Decision quality | False |

## **Why the recommendations fit each segment**

**Transactors** are the lower-risk, merchant-payment core. The evidence (earlier sections) shows lower balances, lower
utilization, and repayment consistently above the minimum. The rational business move is to grow revenue on proven-safe
customers: extend headroom where utilization is low and servicing is strong (R1), monetise heavy spenders through
rewards/interchange (R2), reactivate those which are under-engaged (R3), and convert one-off spend into interest-bearing
installments (R4). Each rule targets *revenue* because the *risk* is already demonstrated to be low.

**Cash-Advance Revolvers** rely on cash advances, carry higher balances/utilization, and repay a smaller share per cycle.
Cash advances are the most expensive way for them to borrow (interest from day one). So the leading action is to
replace that expensive borrowing with a cheaper structured product (R5) — this lowers *their* cost and improves the
bank's repayment odds simultaneously. Genuine stress signals (very high utilization, sub-minimum payment, ~0 full payment)
trigger alerts and support (R6, R8) rather than punishment, and credit is held, not cut (R7).

**Across both**, uncertain (borderline) assignments never trigger automated credit changes (R9).

##**Justifying the modeling approach**
1. The first motivator for the modeling approach were the visualizations suggesting two clusters
2. This was further confirmed by silhouette scores
3. But the same score was too low signaling significant cluster overlap
4. Thus recommendations were heavily based on the kpis rather than the assigned clusters. The assigned cluster only acted as an indicator.



##**Evaluation, limitations & responsible use**

**How we evaluate the approach**
1. The approach uses kmeans clustering to identify potential clusters. This is only valid if the supposed clusters are circular and not any other shape(like elliptical)

2. The two cluster argument is also supported by visuals.

3. Much of the recommendation is driven by kpis and decision thresholds because clusters are not clear cut (silhouette_score ~0.2).



**Improvements**
1. recalibrated,calculated assignment confidence(instead of guesswork).
2. Rules moved into a dataframe.
3. assign intensity to actions and actions are tied to confidence scores.
4.  Re-run examples and population view with the improved engine.
5.  segment-profile table, segment fingerprint and a 2-D PCA map with a new customer placed on it
6.  Persist the whole system to a single deployable artifact.

**Limitations**

- **Unsupervised foundation**  segments are behavioural clusters identified throug an algorithm. We dont know for certain whether they map onto real world.
- **Snapshot data** features are a single window; a customer's behaviour (and therefore segment) can drift over time,
   so assignment should be re-run periodically.
- **Modest separation** silhouette ~0.27 means segments overlap
- **need for more information**:more information fields about the customers can help the model adapt better


**Responsible use**
- Recommendations are **decision-support**, subject to human review and should be considered as consulting material rather than absolute authority.
- While incorporating the model's suggestions into decisions, it would be helpful to first determine why the model predicted what it did and are there any aspects that it has overlooked.
