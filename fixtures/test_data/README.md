# Test Data

This directory contains test data for parity testing.

## Format

CSV files with columns: `open_time, open, high, low, close, volume`

## Files

- `BTCUSDT_1h_sample.csv` — 100 bars of BTCUSDT 1h data
- `ETHUSDT_1h_sample.csv` — 100 bars of ETHUSDT 1h data

## Usage

```python
from control_plane.backends.python_py2pine import PythonPy2PineBackend

backend = PythonPy2PineBackend(data_dir=Path("fixtures/test_data"))
df = backend.load_data("BTCUSDT", "1h")
```

## Note

For production use, data is loaded from `C:\Users\wigmore\trading_stack\data`.
This directory contains small samples for testing purposes.