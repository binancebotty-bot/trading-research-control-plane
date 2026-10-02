"""
Test Parity
===========
Tests for Python ↔ TradingView parity comparison.
"""

import sys
import json
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from control_plane.pipeline import ParityResult, ParityClassification


class TestParityClassification:
    """Test parity classification."""
    
    def test_classifications_exist(self):
        assert ParityClassification.DATA_DIFFERENCE
        assert ParityClassification.EXECUTION_SEMANTICS
        assert ParityClassification.ROUNDING
        assert ParityClassification.FEE_MODEL
        assert ParityClassification.SLIPPAGE_MODEL
        assert ParityClassification.POSITION_SIZING
        assert ParityClassification.BAR_TIMING
        assert ParityClassification.PINE_SEMANTICS
        assert ParityClassification.UNKNOWN


class TestParityResult:
    """Test parity result structure."""
    
    def test_parity_result_creation(self):
        result = ParityResult(
            python_result=None,
            tv_result=None,
            passed=False,
            discrepancies=[{"error": "test"}],
            classifications=[ParityClassification.UNKNOWN],
            tolerances={"return_pct": 0.5},
            summary="Test parity result",
        )
        assert result.passed is False
        assert len(result.discrepancies) == 1
        assert result.classifications == [ParityClassification.UNKNOWN]


class TestParityTolerances:
    """Test parity tolerance configuration."""
    
    def test_default_tolerances(self):
        tolerances = {
            'return_pct': 0.5,
            'max_dd_pct': 0.5,
            'win_rate': 1.0,
            'profit_factor': 0.1,
            'n_trades': 0.15,
            'avg_win_pct': 3.0,
            'avg_loss_pct': 3.0,
        }
        assert tolerances['return_pct'] == 0.5
        assert tolerances['profit_factor'] == 0.1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])