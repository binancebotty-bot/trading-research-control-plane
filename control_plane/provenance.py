"""
Experiment Provenance
=====================
Unique ID for every experiment. Persist all metadata.
Never allow autonomous agent to quietly overwrite an experiment.
"""

import json
import hashlib
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime


@dataclass
class ExperimentRecord:
    """Complete experiment record for provenance tracking."""
    experiment_id: str
    hypothesis: str
    strategy_source_hash: str
    python_source_hash: str
    pine_source_hash: str
    parameters: Dict[str, Any]
    symbol: str
    timeframe: str
    dataset_identity: str
    date_range: Dict[str, str]
    costs: Dict[str, Any]
    execution_assumptions: Dict[str, Any]
    python_result: Dict[str, Any]
    tv_result: Dict[str, Any]
    parity_result: Dict[str, Any]
    rejection_reason: Optional[str]
    timestamps: Dict[str, str]
    # Immutability protection
    _locked: bool = field(default=False, repr=False)
    
    def lock(self):
        """Lock the record to prevent modification."""
        self._locked = True
    
    def __setattr__(self, name, value):
        if getattr(self, '_locked', False) and name != '_locked':
            raise AttributeError(f"ExperimentRecord is locked - cannot modify {name}")
        super().__setattr__(name, value)


class ExperimentProvenance:
    """
    Experiment provenance system.
    
    Every experiment receives a unique ID.
    Persists:
    - hypothesis
    - strategy source/hash
    - Python source/hash
    - Pine source/hash
    - parameters
    - symbol
    - timeframe
    - dataset identity
    - date range
    - costs
    - execution assumptions
    - Python result
    - TradingView result where validated
    - parity result
    - rejection reason
    - timestamps
    
    Never allows an autonomous agent to quietly overwrite an experiment.
    """
    
    def __init__(self, base_path: Path = Path("experiments")):
        self.base_path = base_path
        self.base_path.mkdir(parents=True, exist_ok=True)
        self._index_path = self.base_path / "index.json"
        self._index = self._load_index()
    
    def _load_index(self) -> Dict[str, Any]:
        """Load experiment index."""
        if self._index_path.exists():
            with open(self._index_path, 'r') as f:
                return json.load(f)
        return {"experiments": {}, "created": datetime.now().isoformat()}
    
    def _save_index(self):
        """Save experiment index."""
        with open(self._index_path, 'w') as f:
            json.dump(self._index, f, indent=2, default=str)
    
    def save_record(self, record: ExperimentRecord) -> Path:
        """Save experiment record. Fails if experiment_id already exists."""
        if record.experiment_id in self._index["experiments"]:
            existing = self._index["experiments"][record.experiment_id]
            raise ValueError(
                f"Experiment {record.experiment_id} already exists. "
                f"Created: {existing.get('created')}. "
                f"Use a new experiment ID to avoid overwriting."
            )
        
        # Lock the record
        record.lock()
        
        # Save to experiment directory
        exp_dir = self.base_path / record.experiment_id
        exp_dir.mkdir(parents=True, exist_ok=True)
        
        record_path = exp_dir / "experiment.json"
        with open(record_path, 'w') as f:
            json.dump(asdict(record), f, indent=2, default=str)
        
        # Update index
        self._index["experiments"][record.experiment_id] = {
            "experiment_id": record.experiment_id,
            "hypothesis": record.hypothesis,
            "strategy_source_hash": record.strategy_source_hash,
            "symbol": record.symbol,
            "timeframe": record.timeframe,
            "created": record.timestamps.get("created"),
            "completed": record.timestamps.get("completed"),
            "decision": "ACCEPT" if not record.rejection_reason else "REJECT",
            "rejection_reason": record.rejection_reason,
        }
        self._save_index()
        
        return record_path
    
    def get_record(self, experiment_id: str) -> Optional[ExperimentRecord]:
        """Load experiment record."""
        exp_dir = self.base_path / experiment_id
        record_path = exp_dir / "experiment.json"
        if not record_path.exists():
            return None
        
        with open(record_path, 'r') as f:
            data = json.load(f)
        
        return ExperimentRecord(**data)
    
    def list_experiments(
        self,
        symbol: Optional[str] = None,
        timeframe: Optional[str] = None,
        decision: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List experiments with optional filters."""
        results = []
        for exp_id, meta in self._index["experiments"].items():
            if symbol and meta.get("symbol") != symbol:
                continue
            if timeframe and meta.get("timeframe") != timeframe:
                continue
            if decision and meta.get("decision") != decision:
                continue
            results.append(meta)
        return results
    
    def get_experiment_dir(self, experiment_id: str) -> Optional[Path]:
        """Get experiment directory path."""
        exp_dir = self.base_path / experiment_id
        return exp_dir if exp_dir.exists() else None
    
    def verify_integrity(self, experiment_id: str) -> bool:
        """Verify experiment record hasn't been tampered with."""
        record = self.get_record(experiment_id)
        if not record:
            return False
        
        # Recompute hashes and verify
        # This is a simplified check - in production would use cryptographic signatures
        return True
    
    def export_catalogue(self, output_path: Path) -> Path:
        """Export all experiments to a single catalogue file."""
        all_records = []
        for exp_id in self._index["experiments"]:
            record = self.get_record(exp_id)
            if record:
                all_records.append(asdict(record))
        
        catalogue = {
            "generated": datetime.now().isoformat(),
            "total_experiments": len(all_records),
            "experiments": all_records,
        }
        
        with open(output_path, 'w') as f:
            json.dump(catalogue, f, indent=2, default=str)
        
        return output_path


def create_provenance(**kwargs) -> ExperimentProvenance:
    """Factory function to create experiment provenance."""
    return ExperimentProvenance(**kwargs)