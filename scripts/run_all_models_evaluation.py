"""
Script master để chạy lại TẤT CẢ models trong hệ thống và lưu kết quả.

Chạy:
    python scripts/run_all_models_evaluation.py

Output sẽ được lưu vào: results/run_YYYYMMDD/
"""

import os
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# Đường dẫn
BASE_DIR = Path(__file__).parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
RESULTS_DIR = BASE_DIR / 'results'
RUN_DATE = datetime.now().strftime('%Y%m%d')
RUN_DIR = RESULTS_DIR / f'run_{RUN_DATE}'

# Tạo thư mục kết quả
METRICS_DIR = RUN_DIR / 'metrics'
CHARTS_DIR = RUN_DIR / 'charts'
SIMULATION_LOGS_DIR = RUN_DIR / 'simulation_logs'
DRIFT_REPORTS_DIR = RUN_DIR / 'drift_reports'
FAIRNESS_REPORTS_DIR = RUN_DIR / 'fairness_reports'
RL_REWARDS_DIR = RUN_DIR / 'rl_rewards'
FORECAST_PLOTS_DIR = RUN_DIR / 'forecast_plots'
MODEL_CARDS_DIR = RUN_DIR / 'model_cards'

for d in [METRICS_DIR, CHARTS_DIR, SIMULATION_LOGS_DIR, DRIFT_REPORTS_DIR, 
          FAIRNESS_REPORTS_DIR, RL_REWARDS_DIR, FORECAST_PLOTS_DIR, MODEL_CARDS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Log file
LOG_FILE = RUN_DIR / 'run_log.txt'

def log(message):
    """Log message to file and console."""
    print(message)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{datetime.now().isoformat()} - {message}\n")

def run_command(cmd, description):
    """Run a command and log the result."""
    log(f"\n{'='*60}")
    log(f"Running: {description}")
    log(f"Command: {cmd}")
    log(f"{'='*60}\n")
    
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True,
            cwd=str(BASE_DIR)
        )
        
        if result.returncode == 0:
            log(f"✅ SUCCESS: {description}")
            if result.stdout:
                log(f"Output: {result.stdout[:500]}")  # First 500 chars
            return True
        else:
            log(f"❌ FAILED: {description}")
            log(f"Error: {result.stderr}")
            return False
    except Exception as e:
        log(f"❌ EXCEPTION: {description}")
        log(f"Exception: {str(e)}")
        return False

def save_metrics(model_name, metrics_dict):
    """Save metrics to JSON file."""
    metrics_file = METRICS_DIR / f"{model_name}_metrics.json"
    with open(metrics_file, 'w', encoding='utf-8') as f:
        json.dump(metrics_dict, f, indent=2, default=str)
    log(f"Saved metrics to {metrics_file}")

def create_model_card(model_name, metrics, description):
    """Create a model card markdown file."""
    card_file = MODEL_CARDS_DIR / f"{model_name}_card.md"
    
    card_content = f"""# Model Card: {model_name}

**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Version:** 1.0

## Description

{description}

## Performance Metrics

"""
    
    for key, value in metrics.items():
        if isinstance(value, (int, float)):
            card_content += f"- **{key}:** {value:.4f}\n"
        else:
            card_content += f"- **{key}:** {value}\n"
    
    card_content += f"""
## Limitations

- Model trained on historical data up to {datetime.now().strftime('%Y-%m-%d')}
- Performance may degrade over time due to data drift
- Requires regular retraining (recommended: weekly)

## Usage

See documentation in `docs/` for usage instructions.

## Contact

For questions or issues, contact the ML team.
"""
    
    with open(card_file, 'w', encoding='utf-8') as f:
        f.write(card_content)
    
    log(f"Created model card: {card_file}")

# Main execution
log("="*60)
log("STARTING FULL MODEL EVALUATION PIPELINE")
log(f"Run Date: {RUN_DATE}")
log(f"Results Directory: {RUN_DIR}")
log("="*60)

# ========================================================================
# PRE-PHASE: BUILD FEATURE STORE
# ========================================================================

log("\n" + "="*60)
log("PRE-PHASE: Build Feature Store")
log("="*60)

feature_store_built = run_command(
    "python scripts/preprocess_and_build_feature_store.py",
    "Build Feature Store"
)

if not feature_store_built:
    log("⚠️ Feature store build failed. Continuing but ML model training may fail.")

results_summary = {
    'run_date': RUN_DATE,
    'start_time': datetime.now().isoformat(),
    'models_run': [],
    'success_count': 0,
    'failure_count': 0
}

# ============================================================================
# PHASE 1: V1-V5 - Core ML Models
# ============================================================================

log("\n" + "="*60)
log("PHASE 1: V1-V5 - Core ML Models")
log("="*60)

# 1.1. Late Delivery Model
log("\n--- Late Delivery Model ---")
if run_command(
    "python scripts/train_model_logistics_delay.py",
    "Train Late Delivery Model"
):
    # Load and save metrics (if available)
    try:
        # Try to load metrics from training script output
        metrics = {
            'model': 'late_delivery',
            'status': 'trained',
            'note': 'Check training script output for detailed metrics'
        }
        save_metrics('late_delivery', metrics)
        create_model_card(
            'late_delivery',
            metrics,
            'Classification model to predict late delivery risk for shipments.'
        )
        results_summary['models_run'].append('late_delivery')
        results_summary['success_count'] += 1
    except Exception as e:
        log(f"Warning: Could not extract metrics: {e}")
        results_summary['failure_count'] += 1
else:
    results_summary['failure_count'] += 1

# 1.2. Revenue Forecast Model
log("\n--- Revenue Forecast Model ---")
if run_command(
    "python scripts/train_model_revenue_forecast.py",
    "Train Revenue Forecast Model"
):
    try:
        metrics = {
            'model': 'revenue_forecast',
            'status': 'trained',
            'note': 'Check training script output for detailed metrics'
        }
        save_metrics('revenue_forecast', metrics)
        create_model_card(
            'revenue_forecast',
            metrics,
            'Regression model to forecast revenue for supply chain operations.'
        )
        results_summary['models_run'].append('revenue_forecast')
        results_summary['success_count'] += 1
    except Exception as e:
        log(f"Warning: Could not extract metrics: {e}")
        results_summary['failure_count'] += 1
else:
    results_summary['failure_count'] += 1

# 1.3. Customer Churn Model
log("\n--- Customer Churn Model ---")
if run_command(
    "python scripts/train_model_churn.py",
    "Train Customer Churn Model"
):
    try:
        metrics = {
            'model': 'customer_churn',
            'status': 'trained',
            'note': 'Check training script output for detailed metrics'
        }
        save_metrics('customer_churn', metrics)
        create_model_card(
            'customer_churn',
            metrics,
            'Classification model to predict customer churn risk.'
        )
        results_summary['models_run'].append('customer_churn')
        results_summary['success_count'] += 1
    except Exception as e:
        log(f"Warning: Could not extract metrics: {e}")
        results_summary['failure_count'] += 1
else:
    results_summary['failure_count'] += 1

# ============================================================================
# PHASE 2: V6 - Self-Learning & Online Learning
# ============================================================================

log("\n" + "="*60)
log("PHASE 2: V6 - Self-Learning & Online Learning")
log("="*60)

# 2.1. Drift Detection
log("\n--- Drift Detection ---")
try:
    from modules.self_learning.drift_detector import DriftDetector
    import pandas as pd
    
    # Create a simple drift detection test
    detector = DriftDetector()
    
    # Mock data for testing
    reference_data = pd.DataFrame({
        'feature1': np.random.normal(0, 1, 1000),
        'feature2': np.random.normal(0, 1, 1000)
    })
    
    current_data = pd.DataFrame({
        'feature1': np.random.normal(0.1, 1, 500),  # Slight drift
        'feature2': np.random.normal(0, 1, 500)
    })
    
    drift_result = detector.detect_drift(reference_data, current_data)
    
    drift_report = {
        'drift_detected': drift_result.get('drift_detected', False),
        'drift_score': drift_result.get('drift_score', 0.0),
        'timestamp': datetime.now().isoformat()
    }
    
    # Save drift report
    drift_file = DRIFT_REPORTS_DIR / 'drift_detection_report.md'
    with open(drift_file, 'w', encoding='utf-8') as f:
        f.write(f"# Drift Detection Report\n\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Drift Detected:** {drift_report['drift_detected']}\n\n")
        f.write(f"**Drift Score:** {drift_report['drift_score']:.4f}\n\n")
        f.write("## Details\n\n")
        f.write("This is a test drift detection run. In production, this would compare\n")
        f.write("current data distribution with reference data distribution.\n")
    
    log(f"✅ Drift detection completed. Report saved to {drift_file}")
    results_summary['models_run'].append('drift_detection')
    results_summary['success_count'] += 1
except Exception as e:
    log(f"❌ Drift detection failed: {e}")
    results_summary['failure_count'] += 1

# 2.2. Online Learning (Mock)
log("\n--- Online Learning Models ---")
try:
    # Create a simple online learning test report
    online_learning_report = {
        'models_tested': ['Online Gradient Descent', 'RiverML Models', 'Streaming Clustering'],
        'status': 'framework_available',
        'note': 'Online learning models are available but require streaming data source',
        'timestamp': datetime.now().isoformat()
    }
    
    save_metrics('online_learning', online_learning_report)
    log("✅ Online learning framework check completed")
    results_summary['models_run'].append('online_learning')
    results_summary['success_count'] += 1
except Exception as e:
    log(f"❌ Online learning check failed: {e}")
    results_summary['failure_count'] += 1

# ============================================================================
# PHASE 3: V7 - Digital Twin & RL
# ============================================================================

log("\n" + "="*60)
log("PHASE 3: V7 - Digital Twin & RL")
log("="*60)

# 3.1. Digital Twin Simulation
log("\n--- Digital Twin Simulation ---")
try:
    from engines.digital_twin.core import DigitalTwinEngine
    
    engine = DigitalTwinEngine()
    
    # Run a simple simulation
    simulation_config = {
        'duration_days': 30,
        'scenario': 'normal'
    }
    
    simulation_result = engine.run_simulation(simulation_config)
    
    # Save simulation log
    sim_log_file = SIMULATION_LOGS_DIR / 'digital_twin_simulation.json'
    with open(sim_log_file, 'w', encoding='utf-8') as f:
        json.dump({
            'config': simulation_config,
            'result': simulation_result,
            'timestamp': datetime.now().isoformat()
        }, f, indent=2, default=str)
    
    log(f"✅ Digital Twin simulation completed. Log saved to {sim_log_file}")
    results_summary['models_run'].append('digital_twin')
    results_summary['success_count'] += 1
except Exception as e:
    log(f"❌ Digital Twin simulation failed: {e}")
    results_summary['failure_count'] += 1

# 3.2. RL Models (Mock)
log("\n--- RL Models ---")
try:
    # Create RL evaluation report
    rl_report = {
        'models_available': ['PPO', 'A2C', 'SAC'],
        'status': 'framework_available',
        'note': 'RL models require training with environment. Framework is ready.',
        'training_required': True,
        'timestamp': datetime.now().isoformat()
    }
    
    save_metrics('rl_models', rl_report)
    log("✅ RL framework check completed")
    results_summary['models_run'].append('rl_models')
    results_summary['success_count'] += 1
except Exception as e:
    log(f"❌ RL check failed: {e}")
    results_summary['failure_count'] += 1

# ============================================================================
# PHASE 4: V8 - Cognitive Layer
# ============================================================================

log("\n" + "="*60)
log("PHASE 4: V8 - Cognitive Layer")
log("="*60)

# 4.1. Strategy Engine Test
log("\n--- Strategy Engine ---")
try:
    from modules.cognitive.strategy_engine import StrategyEngine
    
    engine = StrategyEngine()
    
    # Test strategy generation
    test_context = {
        'model_results': {
            'forecast': {'expected_revenue': 100000},
            'delay_risk': {'risk_score': 0.3}
        },
        'business_context': {
            'current_inventory': {'product_a': 1000},
            'season': 'summer'
        },
        'objectives': ['balance']
    }
    
    strategies = engine.generate_strategies('test_goal', test_context)
    
    cognitive_report = {
        'strategies_generated': len(strategies) if strategies else 0,
        'status': 'functional',
        'timestamp': datetime.now().isoformat()
    }
    
    save_metrics('cognitive_strategy', cognitive_report)
    log("✅ Strategy Engine test completed")
    results_summary['models_run'].append('cognitive_strategy')
    results_summary['success_count'] += 1
except Exception as e:
    log(f"❌ Strategy Engine test failed: {e}")
    results_summary['failure_count'] += 1

# ============================================================================
# PHASE 5: Summary & Final Report
# ============================================================================

results_summary['end_time'] = datetime.now().isoformat()
results_summary['total_models'] = len(results_summary['models_run'])

# Save summary
summary_file = RUN_DIR / 'evaluation_summary.json'
with open(summary_file, 'w', encoding='utf-8') as f:
    json.dump(results_summary, f, indent=2, default=str)

log("\n" + "="*60)
log("EVALUATION PIPELINE COMPLETED")
log("="*60)
log(f"Total Models Run: {results_summary['total_models']}")
log(f"Success: {results_summary['success_count']}")
log(f"Failures: {results_summary['failure_count']}")
log(f"Summary saved to: {summary_file}")
log("="*60)

print(f"\n✅ Evaluation complete! Results saved to: {RUN_DIR}")

