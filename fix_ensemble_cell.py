import json

with open('/home/william/Projetos/mqtt_under_attack/notebooks_refactored/03_pipeline_05_05.ipynb', 'r') as f:
    nb = json.load(f)

for i, cell in enumerate(nb['cells']):
    src = ''.join(cell.get('source', []))
    if 'Gerando predições dos modelos otimizados' in src:
        new_source = [
            "import time\n",
            "import numpy as np\n",
            "from scipy.stats import mode\n",
            "from sklearn.metrics import confusion_matrix, accuracy_score, precision_score, f1_score, log_loss\n",
            "\n",
            "# 0. Setup: Gerar predições dos modelos otimizados\n",
            "print(\"Gerando predições dos modelos otimizados...\")\n",
            "if not optuna_trained_models:\n",
            "    print(\"AVISO: Nenhum modelo otimizado foi encontrado (optuna_trained_models está vazio).\")\n",
            "    print(\"As etapas de Ensemble serão ignoradas.\")\n",
            "    ensemble_model_names_opt = []\n",
            "    probs_stack_opt = np.array([])\n",
            "    preds_stack_opt = np.array([])\n",
            "    classes = sorted(y_test.unique()) if 'y_test' in globals() else []\n",
            "else:\n",
            "    ensemble_model_names_opt = list(optuna_trained_models.keys())\n",
            "    classes = sorted(y_test.unique())\n",
            "\n",
            "    optuna_predictions = {}\n",
            "    for name, model in optuna_trained_models.items():\n",
            "        if name in MODELS_REQUIRING_SCALING:\n",
            "            Xte = X_test_cons_scaled\n",
            "        else:\n",
            "            Xte = X_test_cons\n",
            "        \n",
            "        probs = model.predict_proba(Xte)\n",
            "        preds = model.predict(Xte)\n",
            "        optuna_predictions[name] = {'probabilities': probs, 'predictions': preds}\n",
            "\n",
            "    probs_stack_opt = np.stack([optuna_predictions[m]['probabilities'] for m in ensemble_model_names_opt], axis=0)\n",
            "    preds_stack_opt = np.stack([optuna_predictions[m]['predictions'] for m in ensemble_model_names_opt], axis=0)\n",
            "    print(f\"Predições geradas para {len(ensemble_model_names_opt)} modelos.\")\n"
        ]
        cell['source'] = new_source
        
    elif 'ENSEMBLE - AVERAGING' in src:
        new_source = [
            "# 1. Averaging (Média simples das probabilidades)\n",
            "print(\"=\" * 70)\n",
            "print(\"ENSEMBLE - AVERAGING (MODELOS OTIMIZADOS)\")\n",
            "print(\"=\" * 70)\n",
            "if len(ensemble_model_names_opt) == 0:\n",
            "    print(\"Ignorado por falta de modelos base.\")\n",
            "    averaging_metrics = {'accuracy': np.nan, 'precision': np.nan, 'f1': np.nan, 'log_loss': np.nan}\n",
            "else:\n",
            "    averaging_start = time.perf_counter()\n",
            "    avg_probs = probs_stack_opt.mean(axis=0)\n",
            "    y_pred_averaging = np.array(classes)[np.argmax(avg_probs, axis=1)]\n",
            "    cm_averaging = confusion_matrix(y_test, y_pred_averaging, labels=classes)\n",
            "\n",
            "    averaging_metrics = {\n",
            "        'accuracy': accuracy_score(y_test, y_pred_averaging),\n",
            "        'precision': precision_score(y_test, y_pred_averaging, average='weighted', zero_division=0),\n",
            "        'f1': f1_score(y_test, y_pred_averaging, average='weighted', zero_division=0),\n",
            "        'log_loss': log_loss(y_test, avg_probs, labels=classes),\n",
            "    }\n",
            "\n",
            "    averaging_fp = (cm_averaging.sum(axis=0) - np.diag(cm_averaging)).tolist()\n",
            "    averaging_fn = (cm_averaging.sum(axis=1) - np.diag(cm_averaging)).tolist()\n",
            "    averaging_total_sec = time.perf_counter() - averaging_start\n",
            "\n",
            "    append_timing_record(\n",
            "        'ensemble_averaging',\n",
            "        tempo_total_sec=averaging_total_sec,\n",
            "        status='success',\n",
            "    )\n",
            "\n",
            "    print(\"Métricas Averaging:\")\n",
            "    for metric, value in averaging_metrics.items():\n",
            "        print(f\"  {metric}: {value:.4f}\")\n"
        ]
        cell['source'] = new_source

    elif 'ENSEMBLE - HARD VOTING' in src:
        new_source = [
            "# 2. Hard Voting (Voto Majoritário)\n",
            "print(\"=\" * 70)\n",
            "print(\"ENSEMBLE - HARD VOTING (MODELOS OTIMIZADOS)\")\n",
            "print(\"=\" * 70)\n",
            "if len(ensemble_model_names_opt) == 0:\n",
            "    print(\"Ignorado por falta de modelos base.\")\n",
            "    hard_voting_metrics = {'accuracy': np.nan, 'precision': np.nan, 'f1': np.nan, 'log_loss': np.nan}\n",
            "else:\n",
            "    hard_voting_start = time.perf_counter()\n",
            "    y_pred_hard, _ = mode(preds_stack_opt, axis=0)\n",
            "    y_pred_hard = y_pred_hard.flatten()\n",
            "    cm_hard = confusion_matrix(y_test, y_pred_hard, labels=classes)\n",
            "\n",
            "    hard_voting_metrics = {\n",
            "        'accuracy': accuracy_score(y_test, y_pred_hard),\n",
            "        'precision': precision_score(y_test, y_pred_hard, average='weighted', zero_division=0),\n",
            "        'f1': f1_score(y_test, y_pred_hard, average='weighted', zero_division=0),\n",
            "        'log_loss': np.nan, # Hard voting não produz probabilidades válidas para log loss nativo\n",
            "    }\n",
            "\n",
            "    hard_voting_fp = (cm_hard.sum(axis=0) - np.diag(cm_hard)).tolist()\n",
            "    hard_voting_fn = (cm_hard.sum(axis=1) - np.diag(cm_hard)).tolist()\n",
            "    hard_voting_total_sec = time.perf_counter() - hard_voting_start\n",
            "\n",
            "    append_timing_record(\n",
            "        'ensemble_hard_voting',\n",
            "        tempo_total_sec=hard_voting_total_sec,\n",
            "        status='success',\n",
            "    )\n",
            "\n",
            "    print(\"Métricas Hard Voting:\")\n",
            "    for metric, value in hard_voting_metrics.items():\n",
            "        print(f\"  {metric}: {value:.4f}\")\n"
        ]
        cell['source'] = new_source

    elif 'ENSEMBLE - SMART SOFT VOTING' in src:
        new_source = [
            "# 3. Smart Soft Voting (Pesos Otimizados via Optuna)\n",
            "print(\"=\" * 70)\n",
            "print(\"ENSEMBLE - SMART SOFT VOTING (PESOS OTIMIZADOS)\")\n",
            "print(\"=\" * 70)\n",
            "if len(ensemble_model_names_opt) == 0:\n",
            "    print(\"Ignorado por falta de modelos base.\")\n",
            "    smart_voting_metrics = {'accuracy': np.nan, 'precision': np.nan, 'f1': np.nan, 'log_loss': np.nan}\n",
            "else:\n",
            "    smart_voting_start = time.perf_counter()\n",
            "    def ensemble_objective(trial):\n",
            "        weights = [trial.suggest_float(f'w_{m}', 0.0, 1.0) for m in ensemble_model_names_opt]\n",
            "        w_array = np.array(weights)\n",
            "        if w_array.sum() == 0:\n",
            "            return 0.0\n",
            "        w_array = w_array / w_array.sum()\n",
            "        \n",
            "        weighted_probs = np.tensordot(w_array, probs_stack_opt, axes=(0, 0))\n",
            "        y_pred = np.array(classes)[np.argmax(weighted_probs, axis=1)]\n",
            "        return f1_score(y_test, y_pred, average='weighted', zero_division=0)\n",
            "\n",
            "    study_ensemble = optuna.create_study(direction='maximize', sampler=TPESampler(seed=RANDOM_STATE))\n",
            "    study_ensemble.optimize(ensemble_objective, n_trials=100, show_progress_bar=False)\n",
            "\n",
            "    best_weights = np.array([study_ensemble.best_params[f'w_{m}'] for m in ensemble_model_names_opt])\n",
            "    if best_weights.sum() > 0:\n",
            "        best_weights = best_weights / best_weights.sum()\n",
            "    else:\n",
            "        best_weights = np.ones(len(best_weights)) / len(best_weights)\n",
            "\n",
            "    print(\"Pesos otimizados pelo Optuna:\")\n",
            "    for m, w in zip(ensemble_model_names_opt, best_weights):\n",
            "        print(f\"  {m}: {w:.4f}\")\n",
            "\n",
            "    weighted_probs_opt = np.tensordot(best_weights, probs_stack_opt, axes=(0, 0))\n",
            "    y_pred_smart = np.array(classes)[np.argmax(weighted_probs_opt, axis=1)]\n",
            "    cm_smart = confusion_matrix(y_test, y_pred_smart, labels=classes)\n",
            "\n",
            "    smart_voting_metrics = {\n",
            "        'accuracy': accuracy_score(y_test, y_pred_smart),\n",
            "        'precision': precision_score(y_test, y_pred_smart, average='weighted', zero_division=0),\n",
            "        'f1': f1_score(y_test, y_pred_smart, average='weighted', zero_division=0),\n",
            "        'log_loss': log_loss(y_test, weighted_probs_opt, labels=classes),\n",
            "    }\n",
            "\n",
            "    smart_voting_fp = (cm_smart.sum(axis=0) - np.diag(cm_smart)).tolist()\n",
            "    smart_voting_fn = (cm_smart.sum(axis=1) - np.diag(cm_smart)).tolist()\n",
            "    smart_voting_total_sec = time.perf_counter() - smart_voting_start\n",
            "\n",
            "    append_timing_record(\n",
            "        'ensemble_smart_voting',\n",
            "        tempo_total_sec=smart_voting_total_sec,\n",
            "        status='success',\n",
            "    )\n",
            "\n",
            "    print(\"\\nMétricas Smart Soft Voting:\")\n",
            "    for metric, value in smart_voting_metrics.items():\n",
            "        print(f\"  {metric}: {value:.4f}\")\n"
        ]
        cell['source'] = new_source

    elif 'Comparar metodos de ensemble atualizados' in src:
        new_source = [
            "# Comparar metodos de ensemble atualizados\n",
            "if len(ensemble_model_names_opt) > 0:\n",
            "    ensemble_comparison = pd.DataFrame([\n",
            "        {'Metodo': 'Averaging', **averaging_metrics},\n",
            "        {'Metodo': 'Hard Voting', **hard_voting_metrics},\n",
            "        {'Metodo': 'Smart Soft Voting', **smart_voting_metrics},\n",
            "    ])\n",
            "    print(\"\\nComparacao dos Metodos de Ensemble (Otimizados):\")\n",
            "    print(ensemble_comparison.to_string(index=False))\n",
            "    ensemble_comparison.to_csv('../reports/reports_ensemble_v2/ensemble_results.csv', index=False)\n",
            "    np.save('../reports/reports_ensemble_v2/cm_averaging.npy', cm_averaging)\n",
            "    np.save('../reports/reports_ensemble_v2/cm_hard_voting.npy', cm_hard)\n",
            "    np.save('../reports/reports_ensemble_v2/cm_smart_voting.npy', cm_smart)\n",
            "    print('OK: resultados e matrizes de ensemble salvos')\n",
            "else:\n",
            "    print(\"Sem modelos base para comparar métodos de ensemble.\")\n"
        ]
        cell['source'] = new_source

with open('/home/william/Projetos/mqtt_under_attack/notebooks_refactored/03_pipeline_05_05.ipynb', 'w') as f:
    json.dump(nb, f, indent=1)

print("Notebook ensemble cells guarded successfully!")
