#!/usr/bin/env python3
"""
Pipeline Completo: Detecção de Ataques DoS em MQTT
Executa todo o fluxo de análise e gera relatórios
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Para rodar sem display
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')
import json
import joblib

# Machine Learning
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis, QuadraticDiscriminantAnalysis
from sklearn.naive_bayes import GaussianNB, BernoulliNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.feature_selection import SelectKBest, mutual_info_classif, f_classif, VarianceThreshold
from sklearn.linear_model import LassoCV
from sklearn.svm import LinearSVC

# Métricas
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score,
                             log_loss, classification_report, confusion_matrix)

# Otimização
import optuna
from optuna.samplers import TPESampler

# Configuração
RANDOM_STATE = 42
np.random.seed(RANDOM_STATE)

# Diretórios
BASE_DIR = Path('/home/william/Projetos/mqtt_under_attack')
DATA_DIR = BASE_DIR / 'data' / 'raw' / 'MQTT Under Attack Dataset'
REFACTORED_DIR = BASE_DIR / 'data_refactored' / 'processed'
REPORTS_DIR = BASE_DIR / 'reports_refactored'
MODELS_DIR = BASE_DIR / 'models_refactored'

# Criar diretórios
REFACTORED_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)

print("="*80)
print("PIPELINE: DETECÇÃO DE ATAQUES DoS EM MQTT")
print("="*80)

# ============================================================================
# 1. CARREGAMENTO DOS DADOS
# ============================================================================
print("\n[1/10] Carregando dados DoS...")
dos_path = DATA_DIR / 'DoS.csv'
df = pd.read_csv(dos_path)
print(f"  ✓ Dataset carregado: {df.shape[0]} amostras, {df.shape[1]} colunas")
print(f"  ✓ Classes: {df['type'].unique().tolist()}")

# ============================================================================
# 2. LIMPEZA DE DADOS
# ============================================================================
print("\n[2/10] Limpando dados...")

columns_to_remove = [
    # Metadados do frame
    'frame.time_delta_displayed', 'frame.time_epoch', 'frame.time_invalid',
    'frame.time_relative', 'frame.coloring_rule.name', 'frame.coloring_rule.string',
    'frame.comment', 'frame.comment.expert', 'frame.encap_type', 'frame.file_off',
    'frame.ignored', 'frame.incomplete', 'frame.interface_id', 'frame.interface_name',
    'frame.link_nr', 'frame.marked', 'frame.md5_hash', 'frame.number', 'frame.offset_shift',
    # Identificadores
    'ip.src', 'ip.dst', 'eth.src', 'eth.dst', 'tcp.srcport', 'tcp.dstport',
    # Campos vazios
    'mqtt.clientid', 'mqtt.conack.flags', 'mqtt.conflags', 'mqtt.dupflag',
    'mqtt.hdrflags', 'mqtt.msg', 'mqtt.msgid', 'mqtt.passwd', 'mqtt.passwd_len',
    'mqtt.proto_len', 'mqtt.protoname', 'mqtt.sub.qos', 'mqtt.suback.qos',
    'mqtt.topic', 'mqtt.username', 'mqtt.username_len', 'mqtt.ver',
    'mqtt.willmsg', 'mqtt.willmsg_len', 'mqtt.willtopic', 'mqtt.willtopic_len'
]

existing_cols_to_remove = [col for col in columns_to_remove if col in df.columns]
df_clean = df.drop(columns=existing_cols_to_remove)

print(f"  ✓ {len(existing_cols_to_remove)} colunas removidas")
print(f"  ✓ {len(df_clean.columns)} colunas restantes")

# Salvar dataset limpo
df_clean.to_csv(REFACTORED_DIR / 'DoS_clean.csv', index=False)

# ============================================================================
# 3. ENGENHARIA DE FEATURES
# ============================================================================
print("\n[3/10] Criando features de intervalo...")

# Recarregar para obter timestamp
df_full = pd.read_csv(dos_path)

if 'frame.time_epoch' in df_full.columns and 'mqtt.msgtype' in df_full.columns:
    df_full = df_full.sort_values('frame.time_epoch').reset_index(drop=True)
    df_full['publish_gap'] = 0.0
    df_full['connect_gap'] = 0.0

    for traffic_type in df_full['type'].unique():
        mask = df_full['type'] == traffic_type
        subset = df_full[mask].copy()

        if len(subset) > 1:
            timestamps = subset['frame.time_epoch'].values
            msgtypes = subset['mqtt.msgtype'].fillna(0).values

            # Publish gaps (msgtype == 3)
            publish_indices = np.where(msgtypes == 3)[0]
            if len(publish_indices) > 1:
                publish_times = timestamps[publish_indices]
                publish_gaps = np.diff(publish_times)
                for i, idx in enumerate(publish_indices[1:], 1):
                    actual_idx = subset.index[idx]
                    df_full.loc[actual_idx, 'publish_gap'] = publish_gaps[i-1]

            # Connect gaps (msgtype == 1)
            connect_indices = np.where(msgtypes == 1)[0]
            if len(connect_indices) > 1:
                connect_times = timestamps[connect_indices]
                connect_gaps = np.diff(connect_times)
                for i, idx in enumerate(connect_indices[1:], 1):
                    actual_idx = subset.index[idx]
                    df_full.loc[actual_idx, 'connect_gap'] = connect_gaps[i-1]

    # Adicionar ao dataset limpo
    df_clean['publish_gap'] = df_full['publish_gap'].values
    df_clean['connect_gap'] = df_full['connect_gap'].values

    print(f"  ✓ publish_gap: {(df_clean['publish_gap'] != 0).sum()} registros não-zero")
    print(f"  ✓ connect_gap: {(df_clean['connect_gap'] != 0).sum()} registros não-zero")
else:
    print("  ✗ Timestamp não encontrado, criando gaps zerados")
    df_clean['publish_gap'] = 0.0
    df_clean['connect_gap'] = 0.0

# Salvar com gaps
df_clean.to_csv(REFACTORED_DIR / 'DoS_with_gaps.csv', index=False)

# ============================================================================
# 4. PREPARAÇÃO DOS DADOS
# ============================================================================
print("\n[4/10] Preparando dados para ML...")

X = df_clean.drop('type', axis=1)
y = df_clean['type']

# Preencher nulos
X = X.fillna(0)

# Dividir dados
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
)

# Normalizar
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Converter para DataFrame
X_train_scaled = pd.DataFrame(X_train_scaled, columns=X.columns, index=X_train.index)
X_test_scaled = pd.DataFrame(X_test_scaled, columns=X.columns, index=X_test.index)

print(f"  ✓ Treino: {len(X_train)} amostras")
print(f"  ✓ Teste: {len(X_test)} amostras")
print(f"  ✓ Features: {X.shape[1]}")

# ============================================================================
# 5. BASELINE - MODELOS DE BAIXO CUSTO
# ============================================================================
print("\n[5/10] Executando baseline...")

def evaluate_model(model, X_train, X_test, y_train, y_test):
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test) if hasattr(model, 'predict_proba') else None

    metrics = {
        'accuracy': accuracy_score(y_test, y_pred),
        'precision': precision_score(y_test, y_pred, average='weighted', zero_division=0),
        'recall': recall_score(y_test, y_pred, average='weighted', zero_division=0),
        'f1': f1_score(y_test, y_pred, average='weighted', zero_division=0),
    }

    if y_prob is not None:
        try:
            metrics['log_loss'] = log_loss(y_test, y_prob)
        except:
            metrics['log_loss'] = np.nan
    else:
        metrics['log_loss'] = np.nan

    return metrics

baseline_models = {
    'LDA': LinearDiscriminantAnalysis(),
    'QDA': QuadraticDiscriminantAnalysis(),
    'GaussianNB': GaussianNB(),
    'BernoulliNB': BernoulliNB(),
    'KNN': KNeighborsClassifier(n_neighbors=5),
    'DecisionTree': DecisionTreeClassifier(random_state=RANDOM_STATE, max_depth=10),
    'RandomForest': RandomForestClassifier(n_estimators=50, random_state=RANDOM_STATE, max_depth=10),
    'GradientBoosting': GradientBoostingClassifier(n_estimators=50, random_state=RANDOM_STATE, max_depth=5)
}

baseline_results = []
for name, model in baseline_models.items():
    if name in ['LDA', 'QDA', 'KNN']:
        metrics = evaluate_model(model, X_train_scaled, X_test_scaled, y_train, y_test)
    else:
        metrics = evaluate_model(model, X_train, X_test, y_train, y_test)

    baseline_results.append({'modelo': name, **metrics})
    print(f"  ✓ {name}: F1={metrics['f1']:.4f}")

baseline_df = pd.DataFrame(baseline_results)
baseline_df = baseline_df.sort_values('f1', ascending=False)
baseline_df.to_csv(REPORTS_DIR / 'baseline_results.csv', index=False)

print(f"\n  Melhor baseline: {baseline_df.iloc[0]['modelo']} (F1={baseline_df.iloc[0]['f1']:.4f})")

# ============================================================================
# 6. SELEÇÃO DE FEATURES
# ============================================================================
print("\n[6/10] Executando seleção de features...")

def get_selected_features(X, y, selector_name, n_features=15):
    feature_names = X.columns.tolist()

    if selector_name == 'LowVariance':
        selector = VarianceThreshold(threshold=0.01)
        X_selected = selector.fit_transform(X)
        selected_mask = selector.get_support()
        selected = [feature_names[i] for i in range(len(feature_names)) if selected_mask[i]]
        return selected[:n_features] if len(selected) > n_features else selected

    elif selector_name == 'Pearson':
        selector = SelectKBest(score_func=f_classif, k=n_features)
        selector.fit(X, y)
        scores = selector.scores_
        top_indices = np.argsort(scores)[-n_features:][::-1]
        return [feature_names[i] for i in top_indices]

    elif selector_name == 'Fisher':
        selector = SelectKBest(score_func=f_classif, k=n_features)
        selector.fit(X, y)
        scores = selector.scores_
        top_indices = np.argsort(scores)[-n_features:][::-1]
        return [feature_names[i] for i in top_indices]

    elif selector_name == 'mRMR':
        selector = SelectKBest(score_func=mutual_info_classif, k=n_features)
        selector.fit(X, y)
        scores = selector.scores_
        top_indices = np.argsort(scores)[-n_features:][::-1]
        return [feature_names[i] for i in top_indices]

    elif selector_name == 'LassoCV':
        lasso = LassoCV(cv=5, random_state=RANDOM_STATE, max_iter=2000)
        le = LabelEncoder()
        y_encoded = le.fit_transform(y)
        lasso.fit(X, y_encoded)
        coef_importance = np.abs(lasso.coef_)
        top_indices = np.argsort(coef_importance)[-n_features:][::-1]
        return [feature_names[i] for i in top_indices]

    elif selector_name == 'LinearSVC_L1':
        le = LabelEncoder()
        y_encoded = le.fit_transform(y)
        lsvc = LinearSVC(C=0.1, penalty='l1', dual=False, max_iter=5000, random_state=RANDOM_STATE)
        lsvc.fit(X, y_encoded)
        coef_importance = np.abs(lsvc.coef_).flatten() if len(lsvc.coef_.shape) > 1 else np.abs(lsvc.coef_)
        top_indices = np.argsort(coef_importance)[-n_features:][::-1]
        return [feature_names[i] for i in top_indices]

    elif selector_name == 'ExtraTrees':
        et = RandomForestClassifier(n_estimators=50, random_state=RANDOM_STATE, max_depth=10)
        et.fit(X, y)
        importances = et.feature_importances_
        top_indices = np.argsort(importances)[-n_features:][::-1]
        return [feature_names[i] for i in top_indices]

    return feature_names[:n_features]

selectors = ['LowVariance', 'Pearson', 'Fisher', 'mRMR', 'LassoCV', 'LinearSVC_L1', 'ExtraTrees']
N_FEATURES = 15

selected_features_dict = {}
for selector in selectors:
    try:
        features = get_selected_features(X_train, y_train, selector, N_FEATURES)
        selected_features_dict[selector] = features
        print(f"  ✓ {selector}: {len(features)} features")
    except Exception as e:
        print(f"  ✗ {selector}: {e}")
        selected_features_dict[selector] = X.columns.tolist()[:N_FEATURES]

# Salvar features selecionadas
with open(REPORTS_DIR / 'selected_features.json', 'w') as f:
    json.dump(selected_features_dict, f, indent=2)

# Features de consenso
all_features = set()
for features in selected_features_dict.values():
    all_features.update(features)

consensus_df = pd.DataFrame(index=sorted(all_features), columns=selectors)
for selector, features in selected_features_dict.items():
    consensus_df[selector] = [feat in features for feat in consensus_df.index]

consensus_df['count'] = consensus_df.sum(axis=1)
consensus_df = consensus_df.sort_values('count', ascending=False)

consensus_threshold = len(selectors) // 2 + 1
consensus_features = consensus_df[consensus_df['count'] >= consensus_threshold].index.tolist()

print(f"\n  Features de consenso (≥{consensus_threshold} seletores): {len(consensus_features)}")

# ============================================================================
# 7. TREINAMENTO COM SELEÇÃO DE FEATURES
# ============================================================================
print("\n[7/10] Treinando com features selecionadas...")

top_models = baseline_df.head(3)['modelo'].tolist()
selection_results = []

for selector_name, features in selected_features_dict.items():
    X_train_sel = X_train[features]
    X_test_sel = X_test[features]
    X_train_sel_scaled = X_train_scaled[features]
    X_test_sel_scaled = X_test_scaled[features]

    for model_name in top_models:
        model = baseline_models[model_name]

        if model_name in ['LDA', 'QDA', 'KNN']:
            metrics = evaluate_model(
                model.__class__(**model.get_params()),
                X_train_sel_scaled, X_test_sel_scaled, y_train, y_test
            )
        else:
            metrics = evaluate_model(
                model.__class__(**model.get_params()),
                X_train_sel, X_test_sel, y_train, y_test
            )

        selection_results.append({
            'seletor': selector_name,
            'modelo': model_name,
            'n_features': len(features),
            **metrics
        })

selection_df = pd.DataFrame(selection_results)
selection_df.to_csv(REPORTS_DIR / 'selection_results.csv', index=False)

best_by_selector = selection_df.loc[selection_df.groupby('seletor')['f1'].idxmax()]
print(f"  Melhor seleção: {best_by_selector.iloc[0]['seletor']} + {best_by_selector.iloc[0]['modelo']} (F1={best_by_selector.iloc[0]['f1']:.4f})")

# ============================================================================
# 8. ENSEMBLE
# ============================================================================
print("\n[8/10] Executando ensemble...")

if len(consensus_features) == 0:
    consensus_features = selected_features_dict['Pearson']

X_train_cons = X_train[consensus_features]
X_test_cons = X_test[consensus_features]
X_train_cons_scaled = X_train_scaled[consensus_features]
X_test_cons_scaled = X_test_scaled[consensus_features]

# Soft Voting
voting_clf = VotingClassifier(
    estimators=[
        ('rf', RandomForestClassifier(n_estimators=50, random_state=RANDOM_STATE, max_depth=10)),
        ('gb', GradientBoostingClassifier(n_estimators=50, random_state=RANDOM_STATE, max_depth=5)),
        ('dt', DecisionTreeClassifier(random_state=RANDOM_STATE, max_depth=10)),
    ],
    voting='soft'
)

voting_clf.fit(X_train_cons, y_train)
y_pred_voting = voting_clf.predict(X_test_cons)
y_prob_voting = voting_clf.predict_proba(X_test_cons)

soft_voting_metrics = {
    'accuracy': accuracy_score(y_test, y_pred_voting),
    'f1': f1_score(y_test, y_pred_voting, average='weighted'),
    'precision': precision_score(y_test, y_pred_voting, average='weighted', zero_division=0),
    'recall': recall_score(y_test, y_pred_voting, average='weighted', zero_division=0),
    'log_loss': log_loss(y_test, y_prob_voting)
}

# Averaging
ensemble_models = {
    'rf': RandomForestClassifier(n_estimators=50, random_state=RANDOM_STATE, max_depth=10),
    'gb': GradientBoostingClassifier(n_estimators=50, random_state=RANDOM_STATE, max_depth=5),
    'dt': DecisionTreeClassifier(random_state=RANDOM_STATE, max_depth=10)
}

probs_list = []
for name, model in ensemble_models.items():
    model.fit(X_train_cons, y_train)
    probs_list.append(model.predict_proba(X_test_cons))

avg_probs = np.mean(probs_list, axis=0)
y_pred_averaging = voting_clf.classes_[np.argmax(avg_probs, axis=1)]

averaging_metrics = {
    'accuracy': accuracy_score(y_test, y_pred_averaging),
    'f1': f1_score(y_test, y_pred_averaging, average='weighted'),
    'precision': precision_score(y_test, y_pred_averaging, average='weighted', zero_division=0),
    'recall': recall_score(y_test, y_pred_averaging, average='weighted', zero_division=0),
    'log_loss': log_loss(y_test, avg_probs)
}

ensemble_comparison = pd.DataFrame([
    {'Método': 'Soft Voting', **soft_voting_metrics},
    {'Método': 'Averaging', **averaging_metrics}
])
ensemble_comparison.to_csv(REPORTS_DIR / 'ensemble_results.csv', index=False)

print(f"  Soft Voting: F1={soft_voting_metrics['f1']:.4f}")
print(f"  Averaging: F1={averaging_metrics['f1']:.4f}")

# ============================================================================
# 9. OTIMIZAÇÃO COM OPTUNA
# ============================================================================
print("\n[9/10] Otimizando hiperparâmetros com Optuna...")

optuna.logging.set_verbosity(optuna.logging.WARNING)
N_TRIALS = 30

def objective_rf(trial):
    n_estimators = trial.suggest_int('n_estimators', 10, 200)
    max_depth = trial.suggest_int('max_depth', 3, 30)
    min_samples_split = trial.suggest_int('min_samples_split', 2, 20)
    min_samples_leaf = trial.suggest_int('min_samples_leaf', 1, 10)

    model = RandomForestClassifier(
        n_estimators=n_estimators, max_depth=max_depth,
        min_samples_split=min_samples_split, min_samples_leaf=min_samples_leaf,
        random_state=RANDOM_STATE, n_jobs=-1
    )
    scores = cross_val_score(model, X_train_cons, y_train, cv=3, scoring='f1_weighted')
    return scores.mean()

def objective_gb(trial):
    n_estimators = trial.suggest_int('n_estimators', 10, 200)
    max_depth = trial.suggest_int('max_depth', 2, 10)
    learning_rate = trial.suggest_float('learning_rate', 0.01, 0.5, log=True)

    model = GradientBoostingClassifier(
        n_estimators=n_estimators, max_depth=max_depth,
        learning_rate=learning_rate, random_state=RANDOM_STATE
    )
    scores = cross_val_score(model, X_train_cons, y_train, cv=3, scoring='f1_weighted')
    return scores.mean()

def objective_knn(trial):
    n_neighbors = trial.suggest_int('n_neighbors', 3, 30)
    weights = trial.suggest_categorical('weights', ['uniform', 'distance'])
    metric = trial.suggest_categorical('metric', ['euclidean', 'manhattan'])

    model = KNeighborsClassifier(n_neighbors=n_neighbors, weights=weights, metric=metric)
    scores = cross_val_score(model, X_train_cons_scaled, y_train, cv=3, scoring='f1_weighted')
    return scores.mean()

# Otimizar
study_rf = optuna.create_study(direction='maximize', sampler=TPESampler(seed=RANDOM_STATE))
study_rf.optimize(objective_rf, n_trials=N_TRIALS, show_progress_bar=False)
print(f"  RF otimizado: F1(CV)={study_rf.best_value:.4f}")

study_gb = optuna.create_study(direction='maximize', sampler=TPESampler(seed=RANDOM_STATE))
study_gb.optimize(objective_gb, n_trials=N_TRIALS, show_progress_bar=False)
print(f"  GB otimizado: F1(CV)={study_gb.best_value:.4f}")

study_knn = optuna.create_study(direction='maximize', sampler=TPESampler(seed=RANDOM_STATE))
study_knn.optimize(objective_knn, n_trials=N_TRIALS, show_progress_bar=False)
print(f"  KNN otimizado: F1(CV)={study_knn.best_value:.4f}")

# Avaliar modelos otimizados
optuna_results = []

rf_opt = RandomForestClassifier(**study_rf.best_params, random_state=RANDOM_STATE)
rf_opt.fit(X_train_cons, y_train)
y_pred_rf = rf_opt.predict(X_test_cons)
y_prob_rf = rf_opt.predict_proba(X_test_cons)

optuna_results.append({
    'modelo': 'Random Forest (Optuna)',
    'accuracy': accuracy_score(y_test, y_pred_rf),
    'f1': f1_score(y_test, y_pred_rf, average='weighted'),
    'precision': precision_score(y_test, y_pred_rf, average='weighted', zero_division=0),
    'recall': recall_score(y_test, y_pred_rf, average='weighted', zero_division=0),
    'log_loss': log_loss(y_test, y_prob_rf)
})

gb_opt = GradientBoostingClassifier(**study_gb.best_params, random_state=RANDOM_STATE)
gb_opt.fit(X_train_cons, y_train)
y_pred_gb = gb_opt.predict(X_test_cons)
y_prob_gb = gb_opt.predict_proba(X_test_cons)

optuna_results.append({
    'modelo': 'Gradient Boosting (Optuna)',
    'accuracy': accuracy_score(y_test, y_pred_gb),
    'f1': f1_score(y_test, y_pred_gb, average='weighted'),
    'precision': precision_score(y_test, y_pred_gb, average='weighted', zero_division=0),
    'recall': recall_score(y_test, y_pred_gb, average='weighted', zero_division=0),
    'log_loss': log_loss(y_test, y_prob_gb)
})

knn_opt = KNeighborsClassifier(**study_knn.best_params)
knn_opt.fit(X_train_cons_scaled, y_train)
y_pred_knn = knn_opt.predict(X_test_cons_scaled)
y_prob_knn = knn_opt.predict_proba(X_test_cons_scaled)

optuna_results.append({
    'modelo': 'KNN (Optuna)',
    'accuracy': accuracy_score(y_test, y_pred_knn),
    'f1': f1_score(y_test, y_pred_knn, average='weighted'),
    'precision': precision_score(y_test, y_pred_knn, average='weighted', zero_division=0),
    'recall': recall_score(y_test, y_pred_knn, average='weighted', zero_division=0),
    'log_loss': log_loss(y_test, y_prob_knn)
})

optuna_df = pd.DataFrame(optuna_results)
optuna_df.to_csv(REPORTS_DIR / 'optuna_results.csv', index=False)

print(f"\n  Melhor modelo otimizado: {optuna_df.loc[optuna_df['f1'].idxmax(), 'modelo']} (F1={optuna_df['f1'].max():.4f})")

# ============================================================================
# 10. RESULTADOS FINAIS E RELATÓRIO
# ============================================================================
print("\n[10/10] Gerando relatório final...")

# Consolidar resultados
all_results = []

# Baseline
for _, row in baseline_df.iterrows():
    all_results.append({'categoria': 'Baseline', 'modelo': row['modelo'], **row.drop('modelo')})

# Seleção
for selector in best_by_selector['seletor'].unique():
    row = best_by_selector[best_by_selector['seletor'] == selector].iloc[0]
    all_results.append({
        'categoria': f"Seleção ({row['seletor']})",
        'modelo': row['modelo'],
        'accuracy': row['accuracy'],
        'f1': row['f1'],
        'precision': row['precision'],
        'recall': row['recall'],
        'log_loss': row.get('log_loss', np.nan)
    })

# Ensemble
all_results.append({'categoria': 'Ensemble', 'modelo': 'Soft Voting', **soft_voting_metrics})
all_results.append({'categoria': 'Ensemble', 'modelo': 'Averaging', **averaging_metrics})

# Otimizados
for row in optuna_results:
    all_results.append({'categoria': 'Otimizado (Optuna)', **row})

final_results = pd.DataFrame(all_results)
final_results = final_results.sort_values('f1', ascending=False)
final_results.to_csv(REPORTS_DIR / 'final_results_all_models.csv', index=False)

# Identificar melhor modelo
best_model = final_results.iloc[0]

print("\n" + "="*80)
print("RESULTADO FINAL")
print("="*80)
print(f"Categoria: {best_model['categoria']}")
print(f"Modelo: {best_model['modelo']}")
print(f"F1 Score: {best_model['f1']:.4f}")
print(f"Acurácia: {best_model['accuracy']:.4f}")
print("="*80)

# Salvar modelos
joblib.dump(rf_opt, MODELS_DIR / 'best_rf_model.pkl')
joblib.dump(gb_opt, MODELS_DIR / 'best_gb_model.pkl')
joblib.dump(knn_opt, MODELS_DIR / 'best_knn_model.pkl')
joblib.dump(scaler, MODELS_DIR / 'scaler.pkl')

# Salvar info
model_info = {
    'consensus_features': consensus_features,
    'selected_features_by_method': selected_features_dict,
    'best_params': {
        'rf': study_rf.best_params,
        'gb': study_gb.best_params,
        'knn': study_knn.best_params
    }
}

with open(MODELS_DIR / 'model_info.json', 'w') as f:
    json.dump(model_info, f, indent=2)

print(f"\n✓ Modelos salvos em {MODELS_DIR}")
print(f"✓ Relatórios salvos em {REPORTS_DIR}")
print(f"✓ Dados processados salvos em {REFACTORED_DIR}")

# Gerar relatório Markdown
report = f"""# Relatório de Análise: Detecção de Ataques DoS em MQTT

**Data:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}
**Dataset:** DoS.csv
**Amostras:** {len(df)}
**Features Iniciais:** {len(df.columns) - 1}

---

## 1. Resumo Executivo

Este relatório apresenta uma análise completa de modelos de machine learning para detecção de ataques DoS em tráfego MQTT.

### Resultado Principal
- **Melhor Modelo:** {best_model['modelo']} ({best_model['categoria']})
- **F1 Score:** {best_model['f1']:.4f}
- **Acurácia:** {best_model['accuracy']:.4f}

---

## 2. Limpeza de Dados

**Features removidas:** {len(existing_cols_to_remove)}
**Features restantes:** {len(df_clean.columns) - 1}

---

## 3. Engenharia de Features

**Novas features criadas:**
- **publish_gap:** Intervalo entre mensagens PUBLISH
- **connect_gap:** Intervalo entre mensagens CONNECT

---

## 4. Baseline - Modelos de Baixo Custo

| Modelo | Acurácia | F1 Score | Precisão | Recall |
|--------|----------|----------|----------|--------|
"""

for _, row in baseline_df.iterrows():
    report += f"| {row['modelo']} | {row['accuracy']:.4f} | {row['f1']:.4f} | {row['precision']:.4f} | {row['recall']:.4f} |\n"

report += f"""

**Top 3:**
1. {baseline_df.iloc[0]['modelo']}: F1={baseline_df.iloc[0]['f1']:.4f}
2. {baseline_df.iloc[1]['modelo']}: F1={baseline_df.iloc[1]['f1']:.4f}
3. {baseline_df.iloc[2]['modelo']}: F1={baseline_df.iloc[2]['f1']:.4f}

---

## 5. Seleção de Features

**Métodos utilizados:** {', '.join(selectors)}

**Features de consenso ({len(consensus_features)}):**
{chr(10).join([f'- {feat}' for feat in consensus_features])}

---

## 6. Ensemble

| Método | Acurácia | F1 Score |
|--------|----------|----------|
| Soft Voting | {soft_voting_metrics['accuracy']:.4f} | {soft_voting_metrics['f1']:.4f} |
| Averaging | {averaging_metrics['accuracy']:.4f} | {averaging_metrics['f1']:.4f} |

---

## 7. Otimização com Optuna

**Número de trials:** {N_TRIALS}

### Random Forest
- Melhor F1 (CV): {study_rf.best_value:.4f}
- Parâmetros: {study_rf.best_params}

### Gradient Boosting
- Melhor F1 (CV): {study_gb.best_value:.4f}
- Parâmetros: {study_gb.best_params}

### KNN
- Melhor F1 (CV): {study_knn.best_value:.4f}
- Parâmetros: {study_knn.best_params}

---

## 8. Ranking Final (Top 10)

| Posição | Categoria | Modelo | F1 Score | Acurácia |
|---------|-----------|--------|----------|----------|
"""

for i, (_, row) in enumerate(final_results.head(10).iterrows(), 1):
    report += f"| {i} | {row['categoria']} | {row['modelo']} | {row['f1']:.4f} | {row['accuracy']:.4f} |\n"

report += f"""

---

## 9. Conclusões

1. **Melhor abordagem:** {best_model['categoria']} com o modelo {best_model['modelo']}
2. **Features importantes:** {', '.join(consensus_features[:5])}
3. **Otimização:** Ganho de {optuna_df['f1'].max() - baseline_df['f1'].max():.4f} em F1 com Optuna

---

*Relatório gerado automaticamente*
"""

with open(REPORTS_DIR / 'RELATORIO_FINAL.md', 'w') as f:
    f.write(report)

print(f"\n✓ Relatório salvo: {REPORTS_DIR / 'RELATORIO_FINAL.md'}")
print("\n" + "="*80)
print("PIPELINE CONCLUÍDO COM SUCESSO!")
print("="*80)
