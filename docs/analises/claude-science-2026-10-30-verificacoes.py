"""Verificações só de leitura sobre data/raw/MQTT Under Attack Dataset/DoS.csv.

Reproduz a limpeza da aula 02 (46 colunas) e os gaps da aula 03 (sem rótulo), e mede:
  A. estrutura de grupos (fluxo bidirecional) e pureza de rótulo;
  B. duplicatas exatas de vetor de features entre treino e teste no split aleatório;
  C. DecisionTree default sob split aleatório, por fluxo (StratifiedGroupKFold) e temporal por classe;
  D. avaliação restrita a pacotes MQTT e a regra "é MQTT => DoS";
  E. seletor ANOVA dentro x fora da CV (viés da seleção fora da validação);
  F. largura do IC bootstrap do F1 macro no teste.
Uso: python verificacoes_split.py <raiz_do_repo>   (não escreve nada no repositório)
"""

import re
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.impute import SimpleImputer
from sklearn.metrics import confusion_matrix, f1_score, matthews_corrcoef
from sklearn.model_selection import StratifiedGroupKFold, StratifiedKFold, train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.tree import DecisionTreeClassifier

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
SEED = 42


def drop_columns_from_lesson() -> list[str]:
    text = (ROOT / "docs/02-carga-e-limpeza.md").read_text()
    blocks = re.findall(r"DROP_COLUMNS = \(\n(.*?)\n\s*\)\n", text, re.S)
    cands = [re.findall(r'^\s*"([^"]+)",', b, re.M) for b in blocks]
    cols = max(cands, key=len)
    assert len(cols) == 46 == len(set(cols))
    return cols


def message_gap(df, msgtype):
    is_type = df["mqtt.msgtype"] == msgtype
    times = df.loc[is_type, "frame.time_epoch"].sort_values(kind="stable")
    return times.diff().fillna(0.0).reindex(df.index, fill_value=0.0)


def metrics(y, p):
    tn, fp, fn, tp = confusion_matrix(y, p, labels=[0, 1]).ravel()
    return {
        "f1_macro": round(f1_score(y, p, average="macro"), 4),
        "mcc": round(matthews_corrcoef(y, p), 4),
        "recall_dos": round(tp / (tp + fn), 4) if tp + fn else np.nan,
        "fpr": round(fp / (fp + tn), 4) if fp + tn else np.nan,
        "n": len(y),
        "n_dos": int(tp + fn),
        "n_normal": int(tn + fp),
    }


def dt():
    return make_pipeline(
        SimpleImputer(strategy="constant", fill_value=0), DecisionTreeClassifier(random_state=SEED)
    )


raw = pd.read_csv(ROOT / "data/raw/MQTT Under Attack Dataset/DoS.csv", low_memory=False)
g = raw.copy()
g["publish_gap"] = message_gap(raw, 3)
g["connect_gap"] = message_gap(raw, 1)
clean = g.drop(columns=drop_columns_from_lesson())
FEATS = [c for c in clean.columns if c != "type"]
assert len(FEATS) == 22
X = clean[FEATS]
y = (clean["type"] == "DoS").astype(int).to_numpy()
t = raw["frame.time_epoch"] - raw["frame.time_epoch"].min()
is_mqtt = raw["mqtt.msgtype"].notna().to_numpy()

# chave de fluxo bidirecional; pacotes sem IP ficam agrupados pelo par de MAC
a = raw["ip.src"].astype(str) + ":" + raw["tcp.srcport"].astype(str)
b = raw["ip.dst"].astype(str) + ":" + raw["tcp.dstport"].astype(str)
flow = pd.Series(np.where(a < b, a + ">" + b, b + ">" + a), index=raw.index)
noip = raw["ip.src"].isna()
mac = raw["eth.src"].astype(str) + ">" + raw["eth.dst"].astype(str)
flow[noip] = "noip|" + mac[noip]
groups = flow.astype("category").cat.codes.to_numpy()

out = {}
gs = pd.DataFrame({"g": groups, "y": y}).groupby("g")["y"].agg(["size", "nunique"])
out["A_n_flows"] = len(gs)
out["A_mixed_label_flows_rows"] = (int((gs["nunique"] > 1).sum()), int(gs.loc[gs["nunique"] > 1, "size"].sum()))
out["A_largest_flow_share"] = round(gs["size"].max() / len(y), 4)

# ---- B/C: split aleatório (o do paper)
idx = np.arange(len(y))
tr, te = train_test_split(idx, test_size=0.2, stratify=y, random_state=SEED)
out["random_sizes"] = (len(tr), len(te))
key = X.fillna(-999).round(9).astype(str).agg("|".join, axis=1)
train_keys = set(key.iloc[tr])
dup = key.iloc[te].isin(train_keys).to_numpy()
lab_by_key = pd.Series(y[tr]).groupby(key.iloc[tr].to_numpy()).agg(lambda s: set(s))
conflict = np.array(
    [len(lab_by_key.get(k, set()) | {yy}) > 1 for k, yy in zip(key.iloc[te], y[te])]
)
out["B_test_rows_with_exact_dup_in_train(all,DoS,normal)"] = tuple(
    round(v, 4) for v in (dup.mean(), dup[y[te] == 1].mean(), dup[y[te] == 0].mean())
)
out["B_test_rows_dup_with_conflicting_label"] = round(conflict.mean(), 4)
out["B_test_rows_whose_flow_is_in_train"] = round(np.isin(groups[te], np.unique(groups[tr])).mean(), 4)
out["B_n_unique_feature_vectors"] = key.nunique()

m = dt().fit(X.iloc[tr], y[tr])
p = m.predict(X.iloc[te])
out["C_random_holdout"] = metrics(y[te], p)
out["D_random_only_mqtt_packets"] = metrics(y[te][is_mqtt[te]], p[is_mqtt[te]])
out["D_random_only_non_mqtt"] = metrics(y[te][~is_mqtt[te]], p[~is_mqtt[te]])
out["D_rule_is_mqtt_on_test"] = metrics(y[te], is_mqtt[te].astype(int))
nomqtt = [c for c in FEATS if not c.startswith("mqtt.")]
m2 = dt().fit(X.iloc[tr][nomqtt], y[tr])
out["D_random_without_mqtt_features"] = metrics(y[te], m2.predict(X.iloc[te][nomqtt]))
out["D_without_mqtt_feature_list"] = nomqtt

# F: IC bootstrap do F1 macro
rng = np.random.default_rng(SEED)
yt = y[te]
bs = [
    f1_score(yt[s], p[s], average="macro")
    for s in (rng.integers(0, len(te), len(te)) for _ in range(1000))
]
out["F_bootstrap_f1_macro_ci95"] = (round(np.percentile(bs, 2.5), 4), round(np.percentile(bs, 97.5), 4))

# ---- C: StratifiedGroupKFold por fluxo x StratifiedKFold
sgk = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=SEED)
rows = []
for a_, b_ in sgk.split(X, y, groups):
    mm = dt().fit(X.iloc[a_], y[a_])
    r = metrics(y[b_], mm.predict(X.iloc[b_]))
    r["test_frac"] = round(len(b_) / len(y), 3)
    r["dos_frac_test"] = round(y[b_].mean(), 3)
    rows.append(r)
out["C_group_flow_5fold"] = pd.DataFrame(rows)
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
rows = []
for a_, b_ in skf.split(X, y):
    mm = dt().fit(X.iloc[a_], y[a_])
    rows.append(metrics(y[b_], mm.predict(X.iloc[b_])))
out["C_random_5fold"] = pd.DataFrame(rows)

# ---- C: temporal
cut = t.quantile(0.8)
trT, teT = idx[t <= cut], idx[t > cut]
out["C_temporal_global_cut(s,train_dos,train_normal,test_dos,test_normal)"] = (
    round(cut, 1), int(y[trT].sum()), int((1 - y[trT]).sum()), int(y[teT].sum()), int((1 - y[teT]).sum())
)
trC, teC = [], []
for cls in (0, 1):
    ii = idx[y == cls]
    ii = ii[np.argsort(t.to_numpy()[ii], kind="stable")]
    n = int(round(0.8 * len(ii)))
    trC += list(ii[:n])
    teC += list(ii[n:])
trC, teC = np.array(trC), np.array(teC)
mt = dt().fit(X.iloc[trC], y[trC])
out["C_temporal_per_class"] = metrics(y[teC], mt.predict(X.iloc[teC]))
out["C_temporal_per_class_test_rows_whose_flow_is_in_train"] = round(
    np.isin(groups[teC], np.unique(groups[trC])).mean(), 4
)

# ---- E: seletor ANOVA top-15 fora x dentro da CV (DecisionTree default)
Xtr, ytr = X.iloc[tr], y[tr]
imp = SimpleImputer(strategy="constant", fill_value=0).fit(Xtr)
sel = SelectKBest(f_classif, k=15).fit(imp.transform(Xtr), ytr)
cols_out = list(np.array(FEATS)[sel.get_support()])
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
s_out, s_in, same = [], [], []
for a_, b_ in cv.split(Xtr, ytr):
    mo = dt().fit(Xtr.iloc[a_][cols_out], ytr[a_])
    s_out.append(f1_score(ytr[b_], mo.predict(Xtr.iloc[b_][cols_out]), average="macro"))
    mi = make_pipeline(
        SimpleImputer(strategy="constant", fill_value=0),
        SelectKBest(f_classif, k=15),
        DecisionTreeClassifier(random_state=SEED),
    ).fit(Xtr.iloc[a_], ytr[a_])
    s_in.append(f1_score(ytr[b_], mi.predict(Xtr.iloc[b_]), average="macro"))
    same.append(set(np.array(FEATS)[mi[1].get_support()]) == set(cols_out))
out["E_selector_outside_cv_f1(mean,std)"] = (round(np.mean(s_out), 5), round(np.std(s_out), 5))
out["E_selector_inside_cv_f1(mean,std)"] = (round(np.mean(s_in), 5), round(np.std(s_in), 5))
out["E_folds_where_inside_selection_equals_outside"] = f"{sum(same)}/5"

t0 = time.perf_counter()
dt().fit(X.iloc[tr], y[tr])
out["dt_fit_s"] = round(time.perf_counter() - t0, 2)

for k_, v in out.items():
    print(f"== {k_}")
    print(v.to_string() if isinstance(v, pd.DataFrame) else v)
