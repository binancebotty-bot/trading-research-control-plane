# Security

## Overview

This repository is a **RESEARCH** system only. It does not execute live trades, handle real capital, or store credentials in Git.

## Safety Boundaries

```
┌─────────────────────────────────────────────────────────────────┐
│                        RESEARCH (THIS REPO)                     │
│  - No live orders                                               │
│  - No credentials in Git                                        │
│  - .gitignore, .env.example enforced                            │
│  - Paper/simulation only                                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      PAPER / SIMULATION                         │
│  - Simulated execution with realistic costs                     │
│  - No real capital at risk                                      │
│  - Separate environment                                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    TRADING EXECUTION (SEPARATE)                 │
│  - Live order execution                                         │
│  - Real capital                                                 │
│  - Requires explicit approval                                   │
│  - NOT in this repository                                       │
└─────────────────────────────────────────────────────────────────┘
```

## Secret Management

### .gitignore

The following are NEVER committed to Git:

```
# Secrets
.env
.env.local
.env.production
*.pem
*.key
credentials.json

# Python
__pycache__/
*.pyc
*.pyo
*.egg-info/
dist/
build/

# Node
node_modules/

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db

# Logs
logs/
*.log

# Experiments (may contain sensitive data)
experiments/
```

### .env.example

Template for environment variables (no real values):

```bash
# TradingView Official API (when available)
TRADINGVIEW_API_KEY=your_api_key_here
TRADINGVIEW_USERNAME=your_username
TRADINGVIEW_PASSWORD=your_password
TRADINGVIEW_TRANSPORT=mcp

# Custom TV MCP
TV_MCP_DIR=C:\Users\wigmore\trading_stack\tradingview-mcp-jackson
TV_MCP_TRANSPORT=stdio
TV_MCP_HTTP_PORT=9223
TV_CDP_PORT=9222

# Python Backtester
TRADING_STACK_DIR=C:\Users\wigmore\trading_stack
DATA_DIR=C:\Users\wigmore\trading_stack\data
CAPITAL=10000
FEE_PCT=0.0008

# Research Pipeline
MAX_WORKERS=4
MIN_TRADES=10
MIN_PROFIT_FACTOR=1.0
MAX_DRAWDOWN_PCT=20.0
```

## Secret Detection

### Pre-Commit Hook

```python
# scripts/check_secrets.py
import re
import sys
from pathlib import Path

SECRET_PATTERNS = [
    (r'api[_-]?key\s*[=:]\s*["\'][a-zA-Z0-9]{32,}["\']', 'API key'),
    (r'password\s*[=:]\s*["\'][^"\']{8,}["\']', 'Password'),
    (r'token\s*[=:]\s*["\'][a-zA-Z0-9]{32,}["\']', 'Token'),
    (r'secret\s*[=:]\s*["\'][a-zA-Z0-9]{32,}["\']', 'Secret'),
    (r'-----BEGIN (RSA |EC |DSA )?PRIVATE KEY-----', 'Private key'),
]

def check_file(path: Path) -> list:
    findings = []
    content = path.read_text(errors='ignore')
    for pattern, name in SECRET_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            findings.append(f"Potential {name} found in {path}")
    return findings

def main():
    findings = []
    for path in Path('.').rglob('*'):
        if path.is_file() and path.suffix in ['.py', '.js', '.json', '.md', '.txt', '.yaml', '.yml']:
            findings.extend(check_file(path))
    
    if findings:
        print("SECRET DETECTION FAILED:")
        for f in findings:
            print(f"  - {f}")
        sys.exit(1)
    print("No secrets detected.")

if __name__ == '__main__':
    main()
```

## API Key Security

- API keys stored in `.env` (never in Git)
- `.env` loaded via `python-dotenv`
- Keys never logged or persisted in experiment records
- Keys never included in error messages
- Keys never sent to external services (except intended API)

## Network Security

- All API calls use HTTPS
- CDP connection to localhost only (port 9222)
- MCP HTTP server binds to localhost only (port 9223)
- No external network connections except intended APIs

## Data Security

- Experiment records stored locally
- No sensitive data in logs
- No credentials in provenance records
- Data files (CSV) contain only OHLCV data

## Access Control

- Repository access controlled by GitHub permissions
- No public write access
- Branch protection rules recommended
- Required reviews for main branch

## Audit Trail

- All experiments logged with unique IDs
- All pipeline executions logged
- All safety checks logged
- All parity comparisons logged
- Immutable experiment records (lock mechanism)

## Incident Response

If a secret is accidentally committed:
1. Immediately revoke the exposed credential
2. Remove from Git history (BFG Repo-Cleaner or git filter-branch)
3. Force push to remote
4. Notify all contributors
5. Review access logs for misuse

## Compliance

- No personal data collected
- No financial data stored
- No trading credentials in code
- Research results are synthetic/simulated
- No regulatory concerns (research only)