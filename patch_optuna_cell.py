import json

with open('/home/william/Projetos/mqtt_under_attack/notebooks_refactored/03_pipeline_05_05.ipynb', 'r') as f:
    nb = json.load(f)

for cell in nb['cells']:
    src = ''.join(cell.get('source', []))
    if 'def objective_factory(model_name):' in src:
        new_source = []
        # Check if already patched
        if 'X_train_cons = X_train[consensus_features]' not in src:
            new_source.extend([
                "# [CORREÇÃO APLICADA AQUI] Preparar os dados de consenso antes de iniciar o Optuna\n",
                "print(f\"Preparando X_train_cons com {len(consensus_features)} features de consenso...\")\n",
                "X_train_cons = X_train[consensus_features]\n",
                "X_test_cons = X_test[consensus_features]\n",
                "X_train_cons_scaled = X_train_scaled[consensus_features]\n",
                "X_test_cons_scaled = X_test_scaled[consensus_features]\n\n"
            ])
        new_source.extend(cell['source'])
        cell['source'] = new_source
        break

with open('/home/william/Projetos/mqtt_under_attack/notebooks_refactored/03_pipeline_05_05.ipynb', 'w') as f:
    json.dump(nb, f, indent=1)

print("Patch aplicado.")
