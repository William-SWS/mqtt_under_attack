import json
import re

with open('notebooks_refactored/01_dos_complete_pipeline.ipynb', 'r') as f:
    nb = json.load(f)

for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = "".join(cell['source'])
        
        # 1. Replace X.fillna(0) with train_test_split and SimpleImputer
        if 'X = X.fillna(0)' in source:
            new_source = """from sklearn.impute import SimpleImputer

# MANTENDO NULOS PARA IMPUTACAO APOS O SPLIT
# X = X.fillna(0) # REMOVIDO PARA EVITAR LEAKAGE

# Dividir em treino e teste (com nulos)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
)

print(f"Treino antes da imputacao nulos: {X_train.isnull().sum().sum()}")
print(f"Teste antes da imputacao nulos: {X_test.isnull().sum().sum()}")

# Imputar valores ausentes APOS o split (Cenario 1 - Constant = 0)
imputer = SimpleImputer(strategy='constant', fill_value=0)

X_train_imputed = imputer.fit_transform(X_train)
X_test_imputed = imputer.transform(X_test)

X_train = pd.DataFrame(X_train_imputed, columns=X_train.columns, index=X_train.index)
X_test = pd.DataFrame(X_test_imputed, columns=X_test.columns, index=X_test.index)

print(f"Treino apos imputacao nulos: {X_train.isnull().sum().sum()}")
print(f"Teste apos imputacao nulos: {X_test.isnull().sum().sum()}")

print(f"\\nTreino: {X_train.shape[0]} amostras")
print(f"Teste: {X_test.shape[0]} amostras")
print(f"\\nDistribuição no treino:\\n{y_train.value_counts()}")
print(f"\\nDistribuição no teste:\\n{y_test.value_counts()}")
"""
            cell['source'] = [line + '\n' for line in new_source.split('\n')[:-1]]
            continue
            
        # 2. Modify output paths
        source = source.replace('../reports_refactored/', '../reports/reports_refactored_constant/')
        source = source.replace("Path('../models/models_optuna')", "Path('../models/models_refactored_strategy_constant/optuna')")
        source = source.replace("Path('../models/models_refactored')", "Path('../models/models_refactored_strategy_constant/base')")
        
        # 3. Rename final reports if they exist
        source = source.replace('optuna_by_selector_comparison.csv', 'optuna_by_selector_comparison_cenario1_constant.csv')
        
        cell['source'] = [line + ('\n' if not line.endswith('\n') else '') for line in source.split('\n') if line]

with open('notebooks_refactored/02_dos_complete_pipeline.ipynb', 'w') as f:
    json.dump(nb, f, indent=2)
