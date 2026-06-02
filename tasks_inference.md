# Tasks: Export Datasets for Inference (Jupyter Notebook `03_pipeline_05_05.ipynb`)

Este plano de tarefas descreve as modificações necessárias no notebook para exportar os datasets de treino e teste utilizados por cada par de seletor/modelo e atualizar a documentação do projeto.

---

## 1. Modificações no Jupyter Notebook `notebooks_refactored/03_pipeline_05_05.ipynb`

### [x] Inserir Lógica de Salvamento no Loop do Optuna por Seletor
No loop principal de otimização dos modelos por seletor (onde os modelos são treinados e avaliados), insira a lógica para extrair e exportar os conjuntos de dados em formato CSV.

**Código a ser injetado:**
```python
# Salvar datasets de treino e teste para inferência
if model_name in MODELS_REQUIRING_SCALING:
    # Se o modelo necessitar de scaling, exporta os dados já normalizados
    train_df = pd.DataFrame(X_train_sel_scaled, columns=features, index=X_train_sel.index).copy()
    test_df = pd.DataFrame(X_test_sel_scaled, columns=features, index=X_test_sel.index).copy()
else:
    # Caso contrário, exporta as features brutas selecionadas
    train_df = X_train_sel.copy()
    test_df = X_test_sel.copy()

# Adiciona a coluna target
train_df['type'] = y_train
test_df['type'] = y_test

# Gera tags de arquivo padronizadas
train_file_tag = f"train_optuna_by_selector_{sanitize_name(selector_name)}_{sanitize_name(model_name)}.csv"
test_file_tag = f"test_optuna_by_selector_{sanitize_name(selector_name)}_{sanitize_name(model_name)}.csv"

# Resolve os caminhos relativos ao diretório da pasta notebooks_refactored/
train_path_inference = Path('../data/inference/train') / train_file_tag
test_path_inference = Path('../data/inference/test') / test_file_tag

# Cria os diretórios se não existirem
train_path_inference.parent.mkdir(parents=True, exist_ok=True)
test_path_inference.parent.mkdir(parents=True, exist_ok=True)

# Salva em arquivos CSV
train_df.to_csv(train_path_inference, index=False)
test_df.to_csv(test_path_inference, index=False)
```

**Local exato de inserção:**
Injetar a lógica logo após a linha onde os modelos são serializados em disco:
```python
joblib.dump(tuned_model, model_path_optuna)
joblib.dump(tuned_model, model_path_refactored)
```

---

## 2. Execução e Geração dos Arquivos

### [ ] Executar o Notebook `notebooks_refactored/03_pipeline_05_05.ipynb`
- Abra o notebook no ambiente Jupyter.
- Execute a opção **"Restart Kernel and Run All Cells"** para executar todo o pipeline de ML e processar as 42 combinações.
- Confirme que os arquivos CSV foram criados e salvos corretamente nas pastas:
  - `data/inference/train/`
  - `data/inference/test/`

---

## 3. Validação dos Artefatos de Inferência

### [ ] Verificar a Integridade dos Datasets
- [ ] Validar se a quantidade de linhas em cada dataset de teste exportado é exatamente 18.925.
- [ ] Validar se as colunas correspondem às features selecionadas pelo respectivo seletor mais a coluna de label `type`.
- [ ] Validar se os valores das features para o modelo `LDA` estão devidamente escalados (StandardScaler aplicado).
