# Bug Fix: Top 10 Position Limit Not Enforced

## Problem

The strategy generates **top 10 positions**, but after execution, the portfolio held **12 positions** instead of 10. Positions that dropped out of the top 10 (DBC, MUB, XLE) were not being closed.

## Root Cause

The issue was in `ib_executor.py` lines 334-348. The code had this logic:

```python
if contract and position_manager:
    success = position_manager.exit_position(contract, reason='QUAD_CHANGE')
    if success:
        executed_trades.append(ticker)
elif contract:
    # Fallback: direct order without position manager
    ...
```

**The Problem:**
1. `position_manager.exit_position()` only closes positions that are in its internal state file (`position_state.json`)
2. Positions added manually or before position manager was implemented are NOT in this state
3. When `exit_position()` returns `False`, the code did NOT fall back to closing directly
4. The fallback only ran if `position_manager` was `None`

**Result:** Unmanaged positions (DBC, MUB, XLE) were never closed, violating the top 10 rule.

## The Fix

Changed the logic in `ib_executor.py` to:

1. **Try position manager first** - If position is managed, close it properly (cancels stops, logs trade)
2. **Fallback to direct close** - If position_manager doesn't handle it, close it directly via IB API
3. **Ensures all non-target positions are closed** - Regardless of whether they're in position_manager state

## Code Changes

**File:** `ib_executor.py` (lines 328-364)

**Before:**
- Only closed positions via position_manager
- No fallback if position wasn't in position_manager state

**After:**
- Tries position_manager first
- Falls back to direct close if needed
- Prints warning when falling back: "Position not managed by position_manager, closing directly..."

## Impact

✅ **Top 10 limit will now be strictly enforced**
✅ **All positions not in target will be closed**
✅ **Works for both managed and unmanaged positions**
✅ **Backward compatible** - existing managed positions still handled properly

## Testing Recommendations

1. **Verify current positions:**
   ```powershell
   python -c "from ib_insync import *; ib = IB(); ib.connect('127.0.0.1', 4002, clientId=999); print([p.contract.symbol for p in ib.positions()])"
   ```

2. **Check position_state.json:**
   - See which positions are in the position manager state
   - Positions NOT in state will now be closed via fallback

3. **Next rebalance:**
   - Watch for "Closing..." messages for positions not in top 10
   - Watch for "Position not managed by position_manager, closing directly..." warnings

## Manual Cleanup (Optional)

If you want to manually close DBC, MUB, XLE before the next scheduled run:

```python
from ib_executor import IBExecutor

with IBExecutor(port=4002) as ib_exec:
    for ticker in ['DBC', 'MUB', 'XLE']:
        contract = ib_exec.create_cfd_contract(ticker)
        positions = ib_exec.get_current_positions()
        if ticker in positions:
            quantity = int(abs(positions[ticker]))
            action = 'SELL' if positions[ticker] > 0 else 'BUY'
            trade = ib_exec.place_order(contract, quantity, action)
            print(f"Closed {ticker}: {trade}")
```

Or wait for the next scheduled rebalance - the fixed code will close them automatically.

## Date Fixed

November 10, 2025

## Status

✅ **FIXED** - Bug identified and patched in `ib_executor.py`

