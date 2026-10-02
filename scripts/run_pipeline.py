"""
Run Research Pipeline
=====================
Execute the complete fast-search → TV-validation pipeline.
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from control_plane.pipeline import ResearchPipeline


def main():
    parser = argparse.ArgumentParser(description="Run research pipeline")
    parser.add_argument("--strategy", default="jackson_scalper_baseline_v1",
                       help="Strategy name")
    parser.add_argument("--symbol", default="BTCUSDT", help="Trading symbol")
    parser.add_argument("--timeframe", default="1h", help="Timeframe")
    parser.add_argument("--hypothesis", default="Test strategy performance",
                       help="Research hypothesis")
    parser.add_argument("--max-workers", type=int, default=4,
                       help="Max parallel workers")
    args = parser.parse_args()
    
    print("=" * 70)
    print("RESEARCH PIPELINE EXECUTION")
    print("=" * 70)
    print(f"Started: {datetime.now().isoformat()}")
    print(f"Strategy: {args.strategy}")
    print(f"Symbol: {args.symbol}")
    print(f"Timeframe: {args.timeframe}")
    print(f"Hypothesis: {args.hypothesis}")
    print()
    
    pipeline = ResearchPipeline(max_workers=args.max_workers)
    
    result = pipeline.run_pipeline(
        hypothesis=args.hypothesis,
        strategy_name=args.strategy,
        symbol=args.symbol,
        timeframe=args.timeframe,
        parameters={},
        param_grid=None,
        filter_top_n=5,
        min_trades=10,
        min_profit_factor=1.0,
        max_drawdown_pct=20.0,
    )
    
    print()
    print("=" * 70)
    print("PIPELINE RESULTS")
    print("=" * 70)
    print(f"Experiment ID: {result.experiment_id}")
    print(f"Decision: {result.decision}")
    print(f"Rejection Reason: {result.rejection_reason or 'N/A'}")
    print(f"Stages Completed: {len(result.stages_completed)}")
    print(f"Total Time: {result.total_time_ms:.0f}ms")
    print()
    
    if result.best_python_result:
        print("Python Results:")
        print(f"  Return: {result.best_python_result.metrics.get('return_pct', 'N/A')}%")
        print(f"  Trades: {result.best_python_result.metrics.get('n_trades', 'N/A')}")
        print(f"  Profit Factor: {result.best_python_result.metrics.get('profit_factor', 'N/A')}")
        print(f"  Max Drawdown: {result.best_python_result.metrics.get('max_dd_pct', 'N/A')}%")
        print()
    
    if result.parity_result:
        print("Parity Results:")
        print(f"  Passed: {result.parity_result.passed}")
        print(f"  Discrepancies: {len(result.parity_result.discrepancies)}")
        print(f"  Summary: {result.parity_result.summary}")
        print()
    
    if result.evidence_paths:
        print("Evidence:")
        for path in result.evidence_paths:
            print(f"  - {path}")
        print()
    
    # Save result
    output_path = Path(f"experiments/{result.experiment_id}/pipeline_result.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump({
            'experiment_id': result.experiment_id,
            'hypothesis': result.hypothesis,
            'strategy_name': result.strategy_name,
            'symbol': result.symbol,
            'timeframe': result.timeframe,
            'decision': result.decision,
            'rejection_reason': result.rejection_reason,
            'stages_completed': [s.value for s in result.stages_completed],
            'total_time_ms': result.total_time_ms,
            'timestamp': result.timestamp,
        }, f, indent=2, default=str)
    
    print(f"Result saved to: {output_path}")
    print("=" * 70)
    
    return result


if __name__ == "__main__":
    main()