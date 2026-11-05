#!/usr/bin/env python3
"""IAM302t Group 3: reviewer-requested S08 sensitivity and shortcut audit.

Read-only inputs under data/.  All preprocessing fits S07 training groups only.
S08 is used for *diagnostic sensitivity*, not independent model selection.
"""
from __future__ import annotations
import csv
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix,accuracy_score,precision_score,recall_score,f1_score

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT/'data'; RESULTS=ROOT/'results'; FIGURES=ROOT/'figures'
RESULTS.mkdir(exist_ok=True); FIGURES.mkdir(exist_ok=True)
TRAIN_ALL=pd.read_csv(DATA/'ml_features_neutral_67.csv')
TEST=pd.read_csv(DATA/'s08_ml_features_88.csv')
ENRICHED=pd.read_csv(DATA/'s08_enriched_88.csv')
ORIG=pd.read_csv(DATA/'s08_model_metrics_89.csv')
FP_ORIG=pd.read_csv(DATA/'s08_false_positives_90.csv')
TRAIN=TRAIN_ALL[TRAIN_ALL.session_id!='S03'].copy()
assert (len(TRAIN_ALL),len(TRAIN),len(TEST),len(ENRICHED))==(20,15,90,3542)
assert TRAIN.pilot_label.value_counts().to_dict()=={0:8,1:7}
assert TEST.pilot_label.value_counts().to_dict()=={0:77,1:13}
assert set(TRAIN.session_id).isdisjoint(set(TEST.session_id))

POINT=['point_mean_qname_length','point_mean_qname_entropy','point_mean_subdomain_entropy',
       'point_mean_interarrival_s','point_cv_interarrival','point_servfail_ratio']
GRAPH=['graph_unique_qnames','graph_unique_subdomains','graph_singleton_ratio',
       'graph_qname_frequency_entropy','graph_client_domain_degree',
       'graph_domain_client_degree','graph_domain_answer_ip_degree',
       'graph_client_domain_query_share']
MODELS={'CTRL_NULL':['point_null_ratio'],'POINT_NO_TYPE':POINT,
        'GRAPH_NO_TYPE':GRAPH,'HYBRID_NO_TYPE':POINT+GRAPH}
PROXIES=['graph_client_domain_degree','graph_client_domain_query_share','graph_domain_answer_ip_degree']

# Baseline and median imputation operate with the same train/test split.
# New imputation strategies and feature subsets are predeclared reviewer diagnostics.
STRATEGIES=[('ORIGINAL_ZERO','constant',False,False),
            ('ZERO_MISSING_FLAG','constant',True,False),
            ('TRAIN_MEDIAN','median',False,False),
            ('TRAIN_MEDIAN_FLAG','median',True,False),
            ('ORIGINAL_ZERO_N_GE_2','constant',False,True),
            ('TRAIN_MEDIAN_FLAG_N_GE_2','median',True,True)]

def fit_predict(train:pd.DataFrame,test:pd.DataFrame,features:list[str],
                impute:str='constant',indicator:bool=False):
    # Fit imputer on S07 only, and add *all-column* missing flags if requested.
    # SimpleImputer(add_indicator=True) alone would NOT flag new missingness
    # appearing only in S08, because S07 training columns have zero NaNs.
    if impute=='constant':
        imp=SimpleImputer(strategy='constant',fill_value=0,keep_empty_features=True)
    else:
        imp=SimpleImputer(strategy='median',keep_empty_features=True)
    X_train=train[features].astype(float).to_numpy()
    X_test=test[features].astype(float).to_numpy()
    Xtr=imp.fit_transform(X_train)  # S07 only
    Xte=imp.transform(X_test)
    if indicator:
        Xtr=np.column_stack([Xtr,np.isnan(X_train).astype(float)])
        Xte=np.column_stack([Xte,np.isnan(X_test).astype(float)])
        assert Xtr.shape[1]==2*len(features)
    pipe=Pipeline([('scaler',StandardScaler()),
                   ('classifier',LogisticRegression(C=.5,class_weight='balanced',
                                                 max_iter=2000,random_state=42))])
    pipe.fit(Xtr,train.pilot_label.to_numpy(int))
    return pipe.predict(Xte), pipe.predict_proba(Xte)[:,1]

def assess(kind,name,features,train,test,impute,indicator,filtered=False):
    y=test.pilot_label.to_numpy(int)
    pred,p=fit_predict(train,test,features,impute,indicator)
    tn,fp,fn,tp=map(int,confusion_matrix(y,pred,labels=[0,1]).ravel())
    out={'analysis':kind,'variant':name,'n_train':len(train),'n_test':len(test),
         'n_features':len(features),'imputation':impute,'missing_indicator':bool(indicator),
         'drop_n_lt_2':bool(filtered),'TN':tn,'FP':fp,'FN':fn,'TP':tp,
         'accuracy':float(accuracy_score(y,pred)),
         'precision':float(precision_score(y,pred,zero_division=0)),
         'recall':float(recall_score(y,pred,zero_division=0)),
         'f1':float(f1_score(y,pred,zero_division=0)),
         'fpr':float(fp/(fp+tn)) if fp+tn>0 else float('nan')}
    errors=test.loc[y!=pred,['session_id','window_index','client_ip','analysis_domain','query_count','pilot_label']].copy()
    errors['predicted']=pred[y!=pred]
    errors['score']=p[y!=pred]
    errors['variant']=name
    return out,errors

# 1) Faithful replay of the four original models. Abort on any numerical mismatch.
base_rows=[];base_errors=[]
for name,fs in MODELS.items():
    row,err=assess('baseline',name,fs,TRAIN,TEST,'constant',False)
    base_rows.append(row)
    base_errors.append(err)
    original=ORIG.loc[ORIG.model==name].iloc[0]
    for key in ['TN','FP','FN','TP']:
        assert row[key]==int(original[key]), (name,key,row[key],original[key])
    assert abs(row['f1']-float(original['f1']))<1e-6
pd.DataFrame(base_rows).to_csv(RESULTS/'01_baseline_verified.csv',index=False)

# 2) Missing-value sensitivity: 4 configurations x 6 strategies.
sens_rows=[]; sens_errors=[]
for strat,impute,flag,filtered in STRATEGIES:
    tr=TRAIN.loc[TRAIN.query_count>=2].copy() if filtered else TRAIN
    te=TEST.loc[TEST.query_count>=2].copy() if filtered else TEST
    for model,fs in MODELS.items():
        row,err=assess('missing_value',model+'__'+strat,fs,tr,te,impute,flag,filtered)
        row['model']=model; row['strategy']=strat
        sens_rows.append(row)
        sens_errors.append(err)
pd.DataFrame(sens_rows).to_csv(RESULTS/'02_missing_value_sensitivity.csv',index=False)
pd.concat(sens_errors,ignore_index=True).to_csv(RESULTS/'02_errors_by_strategy.csv',index=False)

# 3) Ablation of graph proxies and trivial count signals; same model family/preprocessing.
ABLS={
 'GRAPH_FULL':GRAPH,
 'GRAPH_MINUS_CLIENT_DOMAIN_DEGREE':[f for f in GRAPH if f!='graph_client_domain_degree'],
 'GRAPH_MINUS_CLIENT_DOMAIN_QUERY_SHARE':[f for f in GRAPH if f!='graph_client_domain_query_share'],
 'GRAPH_MINUS_DOMAIN_ANSWER_IP_DEGREE':[f for f in GRAPH if f!='graph_domain_answer_ip_degree'],
 'GRAPH_MINUS_3_PROXIES':[f for f in GRAPH if f not in PROXIES],
 'GRAPH_MINUS_QNAME_COUNT':[f for f in GRAPH if f!='graph_unique_qnames'],
 'GRAPH_MINUS_3_PROXIES_AND_QNAME_COUNT':[f for f in GRAPH if f not in PROXIES+['graph_unique_qnames']],
 'GRAPH_MINIMAL_DIVERSITY':['graph_singleton_ratio','graph_qname_frequency_entropy','graph_domain_client_degree'],
 'POINT_FULL':POINT,
 'POINT_MINUS_SERVFAIL':[f for f in POINT if f!='point_servfail_ratio'],
 'HYBRID_FULL':POINT+GRAPH,
 'HYBRID_MINUS_3_PROXIES':POINT+[f for f in GRAPH if f not in PROXIES],
 'HYBRID_MINUS_3_PROXIES_AND_QNAME_COUNT':POINT+[f for f in GRAPH if f not in PROXIES+['graph_unique_qnames']]
}
ablation=[]; abl_errors=[]
for name,fs in ABLS.items():
    row,err=assess('ablation',name,fs,TRAIN,TEST,'constant',False)
    ablation.append(row); abl_errors.append(err)
pd.DataFrame(ablation).to_csv(RESULTS/'03_feature_ablation.csv',index=False)
pd.concat(abl_errors,ignore_index=True).to_csv(RESULTS/'03_ablation_errors.csv',index=False)

# 4) Six original FPs, missing fields, duplicate point vectors.
point_errors=pd.concat(base_errors,ignore_index=True)
point_errors=point_errors[(point_errors.variant=='POINT_NO_TYPE') & (point_errors.pilot_label==0)].copy()
point_errors=point_errors.merge(TEST[['session_id','window_index','client_ip','analysis_domain']+POINT+['graph_unique_qnames']],
                                on=['session_id','window_index','client_ip','analysis_domain'],how='left')
point_errors['point_missing_count']=point_errors[POINT].isna().sum(axis=1)
point_errors.to_csv(RESULTS/'04_six_false_positives_diagnostic.csv',index=False)

# 5) Missingness of features split by label.
features=POINT+GRAPH+['point_null_ratio']
missing=[]
for typ,rows in [('TRAIN_S07',TRAIN),('TEST_S08',TEST)]:
 for label,g in rows.groupby('pilot_label'):
    for f in features:
        missing.append({'split':typ,'label':int(label),'n_groups':len(g),'feature':f,
                        'missing_count':int(g[f].isna().sum()),
                        'missing_rate':float(g[f].isna().mean())})
pd.DataFrame(missing).to_csv(RESULTS/'05_missingness_by_class.csv',index=False)

# 6) Question raised by teacher: SERVFAIL and long latency by class.
response=[]
for label,g in ENRICHED.groupby('ground_truth_label'):
    lat=pd.to_numeric(g.response_latency_ms,errors='coerce')
    rcode=pd.to_numeric(g.rcode,errors='coerce')
    response.append({'label':int(label),'queries':len(g),
                     'matched':int((g.response_matched==1).sum()),
                     'NOERROR':int((rcode==0).sum()),
                     'SERVFAIL':int((rcode==2).sum()),
                     'latency_gt_10000ms':int((lat>10000).sum()),
                     'unmatched_queries':int((g.response_matched==0).sum())})
pd.DataFrame(response).to_csv(RESULTS/'06_dns_response_by_class.csv',index=False)

# 7) Query-name count distribution; direct S08 diagnostic, not model evidence.
uniq=[]
for label,g in TEST.groupby('pilot_label'):
    uniq.append({'label':int(label),'n_groups':len(g),'min_unique_qnames':int(g.graph_unique_qnames.min()),
                 'median_unique_qnames':float(g.graph_unique_qnames.median()),
                 'max_unique_qnames':int(g.graph_unique_qnames.max())})
pd.DataFrame(uniq).to_csv(RESULTS/'07_qname_count_by_class.csv',index=False)

# 8) Post-hoc simple rules from the observed S08 value ranges.
# IMPORTANT: thresholds selected after examining S08; diagnostic only.
rule_rows=[]
for name, pred in [
 ('UNIQUE_QNAMES_GT_10', (TEST.graph_unique_qnames > 10).astype(int)),
 ('QNAME_ENTROPY_GT_3', (TEST.graph_qname_frequency_entropy > 3).astype(int)),
]:
 y=TEST.pilot_label.to_numpy(int)
 tn,fp,fn,tp=map(int,confusion_matrix(y,np.asarray(pred),labels=[0,1]).ravel())
 rule_rows.append({'rule':name,'threshold_chosen_on':'S08_POST_HOC',
                   'TN':tn,'FP':fp,'FN':fn,'TP':tp,
                   'accuracy':float(accuracy_score(y,pred))})
pd.DataFrame(rule_rows).to_csv(RESULTS/'08_posthoc_simple_rules.csv',index=False)

# Figures, no retouching of original values.
sens=pd.DataFrame(sens_rows)
fig,ax=plt.subplots(figsize=(10,4.8))
order=[x[0] for x in STRATEGIES]
models=['CTRL_NULL','POINT_NO_TYPE','GRAPH_NO_TYPE','HYBRID_NO_TYPE']
w=.19; x=np.arange(len(order))
for j,m in enumerate(models):
 vals=[sens[(sens.strategy==s)&(sens.model==m)].f1.iloc[0] for s in order]
 ax.bar(x+(j-1.5)*w,vals,width=w,label=m)
ax.set_xticks(x,order,rotation=18,ha='right');ax.set_ylabel('F1 (S08 diagnostic)');ax.set_ylim(0,1.08)
ax.set_title('Missing-data sensitivity (read denominators in CSV)')
ax.legend(fontsize=8,loc='lower right');fig.tight_layout();fig.savefig(FIGURES/'missing_value_f1.png',dpi=160);plt.close(fig)
abl=pd.DataFrame(ablation)
fig,ax=plt.subplots(figsize=(10,5.6));ax.barh(abl.variant[::-1],abl.f1[::-1]);ax.set_xlim(0,1.08)
ax.set_xlabel('F1 on S08 (diagnostic)');ax.set_title('Feature ablation: same 15 S07 training groups')
fig.tight_layout();fig.savefig(FIGURES/'feature_ablation_f1.png',dpi=160);plt.close(fig)

print('PASS: 4 original model confusion matrices / F1 reproduced')
print('Missing-value sensitivity:')
print(sens[['model','strategy','n_test','FP','FN','f1','fpr']].to_string(index=False))
print('Ablation:')
print(abl[['variant','FP','FN','f1','fpr']].to_string(index=False))
print('DNS response by class:')
print(pd.DataFrame(response).to_string(index=False))
print('Six FP diagnostics:')
print(point_errors[['window_index','analysis_domain','query_count','point_missing_count','point_mean_interarrival_s','point_cv_interarrival']].to_string(index=False))
print('All outputs:',RESULTS)
