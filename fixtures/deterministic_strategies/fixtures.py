"""
Deterministic Strategy Fixtures
===============================
These strategies are specifically designed for parity testing.
They use controlled inputs and no randomness.
"""

# Fixture 1: SMA Crossover
SMA_CROSSOVER_PINE = """
//@version=5
strategy("SMA Crossover Parity Test", overlay=true)
fast = input.int(10, "Fast SMA")
slow = input.int(30, "Slow SMA")
if ta.crossover(ta.sma(close, fast), ta.sma(close, slow))
    strategy.entry("Long", strategy.long)
if ta.crossunder(ta.sma(close, fast), ta.sma(close, slow))
    strategy.close("Long")
"""

# Fixture 2: RSI Mean Reversion
RSI_MEAN_REVERSION_PINE = """
//@version=5
strategy("RSI Mean Reversion Parity Test", overlay=true)
rsiLength = input.int(14, "RSI Length")
overbought = input.int(70, "Overbought")
oversold = input.int(30, "Oversold")
rsi = ta.rsi(close, rsiLength)
if rsi < oversold
    strategy.entry("Long", strategy.long)
if rsi > overbought
    strategy.close("Long")
"""

# Fixture 3: ATR Breakout
ATR_BREAKOUT_PINE = """
//@version=5
strategy("ATR Breakout Parity Test", overlay=true)
atrLength = input.int(14, "ATR Length")
atrMult = input.float(2.0, "ATR Multiplier")
atr = ta.atr(atrLength)
if close > close[1] + atr * atrMult
    strategy.entry("Long", strategy.long)
if close < close[1] - atr * atrMult
    strategy.close("Long")
"""

# Fixture 4: Bollinger Band Mean Reversion
BOLLINGER_MEAN_REVERSION_PINE = """
//@version=5
strategy("Bollinger Mean Reversion Parity Test", overlay=true)
length = input.int(20, "Length")
mult = input.float(2.0, "Multiplier")
basis = ta.sma(close, length)
dev = mult * ta.stdev(close, length)
upper = basis + dev
lower = basis - dev
if close < lower
    strategy.entry("Long", strategy.long)
if close > basis
    strategy.close("Long")
"""

# Fixture 5: MACD Crossover
MACD_CROSSOVER_PINE = """
//@version=5
strategy("MACD Crossover Parity Test", overlay=true)
fast = input.int(12, "Fast")
slow = input.int(26, "Slow")
signal = input.int(9, "Signal")
[macdLine, signalLine, _] = ta.macd(close, fast, slow, signal)
if ta.crossover(macdLine, signalLine)
    strategy.entry("Long", strategy.long)
if ta.crossunder(macdLine, signalLine)
    strategy.close("Long")
"""

# Python equivalents for parity testing
SMA_CROSSOVER_PYTHON = """
import pandas as pd
import numpy as np

def sma_crossover(df, fast=10, slow=30):
    '''SMA Crossover strategy for parity testing.'''
    df = df.copy()
    df['sma_fast'] = df['close'].rolling(fast).mean()
    df['sma_slow'] = df['close'].rolling(slow).mean()
    df['signal'] = 0
    df.loc[df['sma_fast'] > df['sma_slow'], 'signal'] = 1
    df.loc[df['sma_fast'] <= df['sma_slow'], 'signal'] = 0
    df['position'] = df['signal'].diff()
    return df
"""

RSI_MEAN_REVERSION_PYTHON = """
import pandas as pd
import numpy as np

def rsi_mean_reversion(df, rsi_length=14, overbought=70, oversold=30):
    '''RSI Mean Reversion strategy for parity testing.'''
    df = df.copy()
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(rsi_length).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(rsi_length).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    df['signal'] = 0
    df.loc[df['rsi'] < oversold, 'signal'] = 1
    df.loc[df['rsi'] > overbought, 'signal'] = 0
    df['position'] = df['signal'].diff()
    return df
"""

ATR_BREAKOUT_PYTHON = """
import pandas as pd
import numpy as np

def atr_breakout(df, atr_length=14, atr_mult=2.0):
    '''ATR Breakout strategy for parity testing.'''
    df = df.copy()
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df['atr'] = tr.rolling(atr_length).mean()
    df['signal'] = 0
    df.loc[df['close'] > df['close'].shift() + df['atr'] * atr_mult, 'signal'] = 1
    df.loc[df['close'] < df['close'].shift() - df['atr'] * atr_mult, 'signal'] = 0
    df['position'] = df['signal'].diff()
    return df
"""

BOLLINGER_MEAN_REVERSION_PYTHON = """
import pandas as pd
import numpy as np

def bollinger_mean_reversion(df, length=20, mult=2.0):
    '''Bollinger Band Mean Reversion strategy for parity testing.'''
    df = df.copy()
    df['basis'] = df['close'].rolling(length).mean()
    df['dev'] = df['close'].rolling(length).std() * mult
    df['upper'] = df['basis'] + df['dev']
    df['lower'] = df['basis'] - df['dev']
    df['signal'] = 0
    df.loc[df['close'] < df['lower'], 'signal'] = 1
    df.loc[df['close'] > df['basis'], 'signal'] = 0
    df['position'] = df['signal'].diff()
    return df
"""

MACD_CROSSOVER_PYTHON = """
import pandas as pd
import numpy as np

def macd_crossover(df, fast=12, slow=26, signal=9):
    '''MACD Crossover strategy for parity testing.'''
    df = df.copy()
    exp1 = df['close'].ewm(span=fast, adjust=False).mean()
    exp2 = df['close'].ewm(span=slow, adjust=False).mean()
    df['macd'] = exp1 - exp2
    df['signal_line'] = df['macd'].ewm(span=signal, adjust=False).mean()
    df['signal'] = 0
    df.loc[df['macd'] > df['signal_line'], 'signal'] = 1
    df.loc[df['macd'] <= df['signal_line'], 'signal'] = 0
    df['position'] = df['signal'].diff()
    return df
"""

# Export all fixtures
FIXTURES = {
    'sma_crossover': {
        'pine': SMA_CROSSOVER_PINE,
        'python': SMA_CROSSOVER_PYTHON,
        'parameters': {'fast': 10, 'slow': 30},
    },
    'rsi_mean_reversion': {
        'pine': RSI_MEAN_REVERSION_PINE,
        'python': RSI_MEAN_REVERSION_PYTHON,
        'parameters': {'rsi_length': 14, 'overbought': 70, 'oversold': 30},
    },
    'atr_breakout': {
        'pine': ATR_BREAKOUT_PINE,
        'python': ATR_BREAKOUT_PYTHON,
        'parameters': {'atr_length': 14, 'atr_mult': 2.0},
    },
    'bollinger_mean_reversion': {
        'pine': BOLLINGER_MEAN_REVERSION_PINE,
        'python': BOLLINGER_MEAN_REVERSION_PYTHON,
        'parameters': {'length': 20, 'mult': 2.0},
    },
    'macd_crossover': {
        'pine': MACD_CROSSOVER_PINE,
        'python': MACD_CROSSOVER_PYTHON,
        'parameters': {'fast': 12, 'slow': 26, 'signal': 9},
    },
}