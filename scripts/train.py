import os
import joblib
import optuna
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis, QuadraticDiscriminantAnalysis
from sklearn.naive_bayes import GaussianNB
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import cross_val_score

MODELS_REQUIRING_SCALING = ['LDA', 'QDA', 'GaussianNB']
RANDOM_STATE = 42

def build_model_from_trial(model_name, trial):
    if model_name == 'LDA':
        solver = trial.suggest_categorical('solver', ['svd', 'lsqr'])
        if solver == 'lsqr':
            shrinkage = trial.suggest_categorical('shrinkage', ['auto', None])
            return LinearDiscriminantAnalysis(solver=solver, shrinkage=shrinkage)
        return LinearDiscriminantAnalysis(solver=solver)
    
    if model_name == 'QDA':
        reg_param = trial.suggest_float('reg_param', 0.01, 0.95)
        return QuadraticDiscriminantAnalysis(reg_param=reg_param)
        
    if model_name == 'GaussianNB':
        var_smoothing = trial.suggest_float('var_smoothing', 1e-12, 1e-7, log=True)
        return GaussianNB(var_smoothing=var_smoothing)
        
    if model_name == 'DecisionTree':
        return DecisionTreeClassifier(
            max_depth=trial.suggest_int('max_depth', 2, 20),
            min_samples_split=trial.suggest_int('min_samples_split', 2, 15),
            min_samples_leaf=trial.suggest_int('min_samples_leaf', 1, 8),
            random_state=RANDOM_STATE,
        )
        
    if model_name == 'RandomForest':
        return RandomForestClassifier(
            n_estimators=trial.suggest_int('n_estimators', 30, 120),
            max_depth=trial.suggest_int('max_depth', 3, 20),
            min_samples_split=trial.suggest_int('min_samples_split', 2, 15),
            min_samples_leaf=trial.suggest_int('min_samples_leaf', 1, 8),
            random_state=RANDOM_STATE,
            n_jobs=1,
        )
        
    if model_name == 'GradientBoosting':
        return GradientBoostingClassifier(
            n_estimators=trial.suggest_int('n_estimators', 30, 120),
            max_depth=trial.suggest_int('max_depth', 2, 8),
            learning_rate=trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
            min_samples_split=trial.suggest_int('min_samples_split', 2, 15),
            random_state=RANDOM_STATE,
        )
    raise ValueError(f'Unsupported model: {model_name}')

def objective_factory(model_name, X_train, y_train):
    def objective(trial):
        model = build_model_from_trial(model_name, trial)
        
        if model_name in MODELS_REQUIRING_SCALING:
            estimator = Pipeline([('scaler', StandardScaler()), ('model', model)])
        else:
            estimator = model
            
        try:
            scores = cross_val_score(
                estimator,
                X_train,
                y_train,
                cv=2, # Reduced for faster execution
                scoring='f1_weighted',
                error_score=np.nan,
            )
            if np.isnan(scores).all():
                raise optuna.exceptions.TrialPruned()
            return float(np.nanmean(scores))
        except Exception:
            raise optuna.exceptions.TrialPruned()
    return objective

def train_and_optimize(model_name, X_train, y_train, n_trials=10, models_dir='models_optimized'):
    """
    Optimizes hyperparameters and saves the best model.
    """
    # Force single thread for Optuna to prevent freezing with some joblib setups, use TPESampler
    study = optuna.create_study(direction='maximize', sampler=optuna.samplers.TPESampler(seed=RANDOM_STATE))
    
    print(f"Running Optuna for {model_name}...")
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    study.optimize(objective_factory(model_name, X_train, y_train), n_trials=n_trials, show_progress_bar=False)
    
    print(f"Best params for {model_name}: {study.best_params}")
    
    # Train best model
    best_model = build_model_from_trial(model_name, study.best_trial)
    
    if model_name in MODELS_REQUIRING_SCALING:
        final_model = Pipeline([('scaler', StandardScaler()), ('model', best_model)])
    else:
        final_model = best_model
        
    final_model.fit(X_train, y_train)
    
    # Save the model
    os.makedirs(models_dir, exist_ok=True)
    model_path = os.path.join(models_dir, f"{model_name}_optimized.joblib")
    joblib.dump(final_model, model_path)
    print(f"Saved optimized model to {model_path}")
    
    return final_model, study.best_params
