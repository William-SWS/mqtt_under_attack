import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import accuracy_score, precision_score, f1_score, log_loss, confusion_matrix

def evaluate_model(model_name, model, X_test, y_test):
    """
    Evaluates a trained model.
    """
    classes = sorted(y_test.unique())
    
    # Check if model supports predict_proba
    if hasattr(model, "predict_proba"):
        probabilities = model.predict_proba(X_test)
        l_loss = log_loss(y_test, probabilities, labels=classes)
    else:
        probabilities = None
        l_loss = np.nan
        
    y_pred = model.predict(X_test)
    
    metrics = {
        'accuracy': accuracy_score(y_test, y_pred),
        'precision': precision_score(y_test, y_pred, average='weighted', zero_division=0),
        'f1': f1_score(y_test, y_pred, average='weighted', zero_division=0),
        'log_loss': l_loss
    }
    
    cm = confusion_matrix(y_test, y_pred, labels=classes)
    
    fp_per_class = (cm.sum(axis=0) - np.diag(cm)).tolist()
    fn_per_class = (cm.sum(axis=1) - np.diag(cm)).tolist()
    
    return {
        'metrics': metrics,
        'confusion_matrix': cm,
        'fp_per_class': fp_per_class,
        'fn_per_class': fn_per_class,
        'y_pred': y_pred,
        'probabilities': probabilities
    }

def generate_report(results_list, reports_dir='reports_optimized'):
    """
    Generates the CSV and PNG reports from the evaluation results.
    """
    os.makedirs(reports_dir, exist_ok=True)
    
    # Generate CSV
    df_results = pd.DataFrame([
        {
            'Model': r['model_name'],
            'Accuracy': r['metrics']['accuracy'],
            'Precision': r['metrics']['precision'],
            'F1 Score': r['metrics']['f1'],
            'Log Loss': r['metrics']['log_loss'],
        } for r in results_list
    ])
    
    csv_path = os.path.join(reports_dir, 'final_results.csv')
    df_results.sort_values(by='F1 Score', ascending=False).to_csv(csv_path, index=False)
    print(f"Saved evaluation metrics to {csv_path}")
    
    # Generate Plot (F1 Score comparison)
    plt.figure(figsize=(10, 6))
    sns.barplot(x='Model', y='F1 Score', data=df_results.sort_values(by='F1 Score', ascending=False))
    plt.title('F1 Score per Model (Optimized)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plot_path = os.path.join(reports_dir, 'f1_scores.png')
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved F1 comparison plot to {plot_path}")
    
    # Optional: We could also save confusion matrices here
    for r in results_list:
        model_name = r['model_name']
        cm = r['confusion_matrix']
        plt.figure(figsize=(6, 4))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', cbar=False)
        plt.title(f'Confusion Matrix - {model_name}')
        plt.xlabel('Predicted')
        plt.ylabel('Real')
        plt.tight_layout()
        cm_path = os.path.join(reports_dir, f'cm_{model_name}.png')
        plt.savefig(cm_path, dpi=150, bbox_inches='tight')
        plt.close()
        
    print(f"Saved all confusion matrices to {reports_dir}")
