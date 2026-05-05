import json

with open('/home/william/Projetos/mqtt_under_attack/notebooks_refactored/03_pipeline_05_05.ipynb', 'r') as f:
    nb = json.load(f)

insert_idx = -1
for i, cell in enumerate(nb['cells']):
    src = ''.join(cell.get('source', []))
    if '# Definir espacos de busca e funcao objetivo do Optuna' in src:
        insert_idx = i
        break

if insert_idx != -1:
    setup_cell = {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Preparar datasets com as features de consenso (Usado pelo Optuna Global e Ensemble)\n",
            "print(f\"Usando features de consenso: {consensus_features}\")\n",
            "X_train_cons = X_train[consensus_features]\n",
            "X_test_cons = X_test[consensus_features]\n",
            "X_train_cons_scaled = X_train_scaled[consensus_features]\n",
            "X_test_cons_scaled = X_test_scaled[consensus_features]\n"
        ]
    }
    nb['cells'].insert(insert_idx, setup_cell)
    
    with open('/home/william/Projetos/mqtt_under_attack/notebooks_refactored/03_pipeline_05_05.ipynb', 'w') as f:
        json.dump(nb, f, indent=1)
    print("Notebook corrigido com sucesso!")
else:
    print("Não encontrei o local de inserção.")
