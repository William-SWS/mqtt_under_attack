import json

with open('/home/william/Projetos/mqtt_under_attack/notebooks_refactored/03_pipeline_05_05.ipynb', 'r') as f:
    nb = json.load(f)

for cell in nb['cells']:
    src = ''.join(cell.get('source', []))
    if 'ENSEMBLE - HARD VOTING' in src:
        new_source = []
        for line in cell.get('source', []):
            if 'y_pred_hard, _ = mode(preds_stack_opt, axis=0)' in line:
                new_source.append("    import pandas as pd\n")
                new_source.append("    # Substituindo scipy.stats.mode por pandas para suportar strings (classes)\n")
                new_source.append("    y_pred_hard = pd.DataFrame(preds_stack_opt).mode(axis=0).iloc[0].values\n")
            elif 'y_pred_hard = y_pred_hard.flatten()' in line:
                pass # removemos esta linha, já que values já é 1D
            else:
                new_source.append(line)
        cell['source'] = new_source
        break

with open('/home/william/Projetos/mqtt_under_attack/notebooks_refactored/03_pipeline_05_05.ipynb', 'w') as f:
    json.dump(nb, f, indent=1)

print("Correção do Hard Voting aplicada com sucesso.")
