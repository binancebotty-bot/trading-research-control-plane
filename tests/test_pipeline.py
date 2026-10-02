"""
Test Pipeline
=============
Tests for the research pipeline.
"""

import sys
import json
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from control_plane.pipeline import ResearchPipeline, PipelineStage, PipelineResult


class TestPipelineStages:
    """Test pipeline stages."""
    
    def test_stages_exist(self):
        assert PipelineStage.HYPOTHESIS
        assert PipelineStage.PYTHON_IMPL
        assert PipelineStage.FAST_BACKTEST
        assert PipelineStage.PARALLEL_EXPLORATION
        assert PipelineStage.CANDIDATE_FILTERING
        assert PipelineStage.PINE_GENERATION
        assert PipelineStage.TV_COMPILE
        assert PipelineStage.TV_STRATEGY_TESTER
        assert PipelineStage.TV_EXTRACTION
        assert PipelineStage.PARITY_COMPARISON
        assert PipelineStage.DECISION
        assert PipelineStage.PERSIST


class TestResearchPipeline:
    """Test research pipeline."""
    
    def test_pipeline_creation(self):
        pipeline = ResearchPipeline()
        assert pipeline is not None
    
    def test_pipeline_has_backends(self):
        pipeline = ResearchPipeline()
        assert pipeline.python_backend is not None
        assert pipeline.tv_mcp_backend is not None
        assert pipeline.official_tv_backend is not None
    
    def test_pipeline_has_provenance(self):
        pipeline = ResearchPipeline()
        assert pipeline.provenance is not None
    
    def test_pipeline_has_safety(self):
        pipeline = ResearchPipeline()
        assert pipeline.safety is not None
    
    def test_pipeline_has_observability(self):
        pipeline = ResearchPipeline()
        assert pipeline.observability is not None


class TestPipelineResult:
    """Test pipeline result structure."""
    
    def test_result_creation(self):
        result = PipelineResult(
            experiment_id="test123",
            hypothesis="Test hypothesis",
            strategy_name="test_strategy",
            symbol="BTCUSDT",
            timeframe="1h",
            parameters={},
            stages_completed=[PipelineStage.HYPOTHESIS],
            python_results=[],
            best_python_result=None,
            tv_result=None,
            parity_result=None,
            decision="REJECT",
            rejection_reason="Test rejection",
            evidence_paths=[],
            total_time_ms=1000,
            timestamp="2026-01-01T00:00:00",
        )
        assert result.experiment_id == "test123"
        assert result.decision == "REJECT"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])