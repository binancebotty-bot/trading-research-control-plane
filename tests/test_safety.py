"""
Test Safety
===========
Tests for research safety checks.
"""

import sys
import json
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from control_plane.safety import ResearchSafety, SafetyCheck, SafetyViolation, DatasetSplit, DatasetInfo


class TestSafetyViolations:
    """Test safety violation types."""
    
    def test_violations_exist(self):
        assert SafetyViolation.LOOK_AHEAD_BIAS
        assert SafetyViolation.OVERFITTING
        assert SafetyViolation.SURVIVORSHIP_BIAS
        assert SafetyViolation.PARAMETER_LEAKAGE
        assert SafetyViolation.DATA_LEAKAGE
        assert SafetyViolation.CHERRY_PICKING
        assert SafetyViolation.REPEATED_OPTIMISATION
        assert SafetyViolation.INCONSISTENT_DATASETS
        assert SafetyViolation.FALSE_PARITY
        assert SafetyViolation.DUPLICATE_EXPERIMENT
        assert SafetyViolation.UNRECORDED_FAILURE


class TestDatasetSplit:
    """Test dataset split types."""
    
    def test_splits_exist(self):
        assert DatasetSplit.TRAIN
        assert DatasetSplit.VALIDATION
        assert DatasetSplit.OUT_OF_SAMPLE
        assert DatasetSplit.FORWARD


class TestResearchSafety:
    """Test research safety."""
    
    def test_safety_creation(self):
        safety = ResearchSafety()
        assert safety is not None
    
    def test_check_look_ahead_bias_clean(self):
        safety = ResearchSafety()
        check = safety.check_look_ahead_bias("close > sma(close, 20)", ["sma"])
        assert check.passed is True
    
    def test_check_look_ahead_bias_violation(self):
        safety = ResearchSafety()
        check = safety.check_look_ahead_bias("close[1] > sma(close, 20)", ["sma"])
        # This should pass because close[1] is past data (positive offset = prior bar).
        assert check.passed is True

    def test_check_look_ahead_zero_and_literal_pass(self):
        safety = ResearchSafety()
        # Non-negative LITERAL indices are known-safe past-bar references.
        assert safety.check_look_ahead_bias("close[0] > sma(close, 20)", ["sma"]).passed is True
        assert safety.check_look_ahead_bias("high[2] < sma(close, 20)", ["sma"]).passed is True

    def test_check_look_ahead_dynamic_index_fails(self):
        safety = ResearchSafety()
        # Dynamic/unknown index -> conservatively flagged (not exempted).
        check = safety.check_look_ahead_bias("close[i] > sma(close, 20)", ["sma"])
        assert check.passed is False
        assert check.violation == SafetyViolation.LOOK_AHEAD_BIAS
        check2 = safety.check_look_ahead_bias("high[offset] < 1", ["sma"])
        assert check2.passed is False
        assert check2.violation == SafetyViolation.LOOK_AHEAD_BIAS

    def test_check_look_ahead_negative_offset_fails(self):
        safety = ResearchSafety()
        # close[-1] references a FUTURE bar -> genuine look-ahead, must still fail.
        check = safety.check_look_ahead_bias("close[-1] > sma(close, 20)", ["sma"])
        assert check.passed is False
        assert check.violation == SafetyViolation.LOOK_AHEAD_BIAS

    def test_check_look_ahead_realtime_repaint_fails(self):
        safety = ResearchSafety()
        # barstate.isrealtime is a repaint/realtime-only construct -> still flagged.
        check = safety.check_look_ahead_bias("if barstate.isrealtime\n    x = 1", ["sma"])
        assert check.passed is False
        assert check.violation == SafetyViolation.LOOK_AHEAD_BIAS
    
    def test_check_overfitting_no_degradation(self):
        safety = ResearchSafety()
        train = {"profit_factor": 1.5, "return_pct": 10.0}
        val = {"profit_factor": 1.4, "return_pct": 9.5}
        check = safety.check_overfitting(train, val)
        assert check.passed is True
    
    def test_check_overfitting_with_degradation(self):
        safety = ResearchSafety()
        train = {"profit_factor": 2.0, "return_pct": 20.0}
        val = {"profit_factor": 1.0, "return_pct": 5.0}
        check = safety.check_overfitting(train, val)
        assert check.passed is False
        assert check.violation == SafetyViolation.OVERFITTING
    
    def test_check_duplicate_experiment(self):
        safety = ResearchSafety()
        check1 = safety.check_duplicate_experiment("hash123")
        assert check1.passed is True
        check2 = safety.check_duplicate_experiment("hash123")
        assert check2.passed is False
        assert check2.violation == SafetyViolation.DUPLICATE_EXPERIMENT
    
    def test_check_false_parity_pass(self):
        safety = ResearchSafety()
        parity = {"passed": True, "discrepancies": [], "summary": "OK"}
        check = safety.check_false_parity(parity)
        assert check.passed is True
    
    def test_check_false_parity_fail(self):
        safety = ResearchSafety()
        parity = {"passed": False, "discrepancies": [{"difference": 5.0}], "summary": "FAIL"}
        check = safety.check_false_parity(parity)
        assert check.passed is False
        assert check.violation == SafetyViolation.FALSE_PARITY


class TestDatasetInfo:
    """Test dataset info."""
    
    def test_dataset_info_creation(self):
        info = DatasetInfo(
            split=DatasetSplit.TRAIN,
            symbol="BTCUSDT",
            timeframe="1h",
            start_date="2023-01-01",
            end_date="2023-06-30",
            bars=1000,
            hash="abc123",
        )
        assert info.split == DatasetSplit.TRAIN
        assert info.symbol == "BTCUSDT"
        assert info.bars == 1000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])