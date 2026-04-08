import os
import sys

# Append scripts to path so we can import from them
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))

from data_loader import load_and_preprocess
from train import train_and_optimize
from evaluate import evaluate_model, generate_report

def main():
    print("="*60)
    print("Starting MQTT DoS Classification Pipeline")
    print("="*60)
    
    # 1. Load Data
    data_path = 'data/raw/MQTT Under Attack Dataset/DoS.csv'
    if not os.path.exists(data_path):
        print(f"Error: Dataset not found at {data_path}")
        return
        
    X_train, X_test, X_train_scaled, X_test_scaled, y_train, y_test = load_and_preprocess(data_path)
    print("Data processed successfully.")
    
    # 2. Train, Optimize and Evaluate
    model_names = ['LDA', 'QDA', 'GaussianNB', 'DecisionTree', 'RandomForest', 'GradientBoosting']
    results = []
    
    models_dir = 'models_optimized'
    reports_dir = 'reports_optimized'
    
    for model_name in model_names:
        print(f"\n--- Processing {model_name} ---")
        
        # We use raw X_train because train_and_optimize adds a scaler pipeline if needed.
        # Reduced budgets for RandomForest/GB to execute faster overall
        n_trials = 2 if model_name in ['RandomForest', 'GradientBoosting'] else 5 
        
        final_model, best_params = train_and_optimize(
            model_name, X_train, y_train, n_trials=n_trials, models_dir=models_dir
        )
        
        eval_dict = evaluate_model(model_name, final_model, X_test, y_test)
        eval_dict['model_name'] = model_name
        results.append(eval_dict)
        
        metrics = eval_dict['metrics']
        print(f"Result for {model_name}: F1 Score: {metrics['f1']:.4f} | Accuracy: {metrics['accuracy']:.4f}")
        
    # 3. Generate Reports (CSV and PNG)
    print("\n" + "="*60)
    print("Generating Reports...")
    generate_report(results, reports_dir=reports_dir)
    print("="*60)
    print("Pipeline execution completed successfully.")

if __name__ == '__main__':
    main()
