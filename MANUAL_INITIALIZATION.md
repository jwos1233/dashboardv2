# Manual Initialization Guide

## 📋 **Complete Workflow for Manual Strategy Initialization**

This guide walks you through manually entering positions and syncing them with the automated system.

---

## 🎯 **When to Use This**

Use manual initialization when:
- ✅ Starting the strategy for the first time
- ✅ You want full control over entry execution
- ✅ You want to verify each position before entry
- ✅ Learning the system (recommended for first time)

---

## 📝 **Step-by-Step Process**

### **STEP 1: Analyze What to Enter**

Run the initialization analyzer:

```bash
python initialize_strategy.py
```

**What this does:**
- Runs backtest to today
- Shows current theoretical positions
- Filters out positions that would have been stopped
- Displays entry orders with historical stops

**Example output:**
```
ENTRY ORDERS (Matching Backtest State)
================================================================================
Ticker   Weight   Entry$       Current$     Stop$        Risk$        Risk%     
--------------------------------------------------------------------------------
ARKK       58.4%  $     57.56  $     88.98  $     54.75  $     34.23      38.5%
QQQ        23.6%  $    520.03  $    629.07  $    511.25  $    117.82      18.7%
IWM        27.0%  $    219.94  $    246.23  $    215.67  $     30.56      12.4%
REMX       22.4%  $     49.24  $     70.50  $     47.02  $     23.48      33.3%
URA        17.3%  $     40.45  $     55.12  $     38.93  $     16.19      29.4%
TLT        12.0%  $     88.25  $     90.29  $     87.33  $      2.96       3.3%
GLD        10.3%  $    364.38  $    368.12  $    350.12  $     18.00       4.9%
CPER        9.8%  $     30.85  $     31.53  $     29.75  $      1.78       5.7%
```

**Save this output** - you'll need the stop prices when entering positions.

---

### **STEP 2: Manually Enter Positions in IB**

For each position shown in Step 1:

#### **A. Calculate Position Size**

**Formula:**
```
Position Value = Account Value × Weight
Quantity = Position Value / Current Price
```

**Example for ARKK (58.4% weight, $50k account):**
```
Position Value = $50,000 × 0.584 = $29,200
Quantity = $29,200 / $88.98 = 328.2 contracts
```

#### **B. Enter the Position**

**In IB TWS or Gateway:**

1. **Create Order:**
   - Symbol: `ARKK` (CFD)
   - Action: `BUY`
   - Quantity: `328.2`
   - Order Type: `MARKET`
   - Time in Force: `DAY`

2. **Submit Order**

3. **Wait for Fill** - note the actual fill price

4. **Repeat for all 8 positions**

---

#### **C. Place Stop Orders**

**CRITICAL:** For each position, place a stop order immediately after entry.

**In IB TWS or Gateway:**

1. **Create Stop Order:**
   - Symbol: `ARKK` (CFD)
   - Action: `SELL`
   - Quantity: `328.2` (same as position)
   - Order Type: `STOP`
   - Stop Price: `$54.75` (from initialization script)
   - Time in Force: `GTC` (Good Till Cancelled)

2. **Submit Order**

3. **Verify** stop order is active

4. **Repeat for all 8 positions**

---

### **Position Entry Checklist**

Use this checklist as you enter each position:

```
[ ] ARKK
    [ ] Market order executed: _____ @ $______
    [ ] Stop order placed: _____ @ $54.75
    
[ ] QQQ
    [ ] Market order executed: _____ @ $______
    [ ] Stop order placed: _____ @ $511.25
    
[ ] IWM
    [ ] Market order executed: _____ @ $______
    [ ] Stop order placed: _____ @ $215.67
    
[ ] REMX
    [ ] Market order executed: _____ @ $______
    [ ] Stop order placed: _____ @ $47.02
    
[ ] URA
    [ ] Market order executed: _____ @ $______
    [ ] Stop order placed: _____ @ $38.93
    
[ ] TLT
    [ ] Market order executed: _____ @ $______
    [ ] Stop order placed: _____ @ $87.33
    
[ ] GLD
    [ ] Market order executed: _____ @ $______
    [ ] Stop order placed: _____ @ $350.12
    
[ ] CPER
    [ ] Market order executed: _____ @ $______
    [ ] Stop order placed: _____ @ $29.75
```

---

### **STEP 3: Sync with Automated System**

After entering all positions, sync them with the position tracking system:

```bash
python sync_manual_positions.py --port 4002
```

**What this does:**
1. Connects to IB
2. Reads your positions from IB account
3. Reads your stop orders from IB
4. Matches with expected backtest state
5. Creates `position_state.json`
6. Enables daily system to manage positions

**Example output:**
```
================================================================================
STEP 1: READING POSITIONS FROM IB
================================================================================

Found 8 positions:
  ARKK:
    Quantity: 328.20
    Avg Cost: $88.98
    Market Value: $29,198.00
    Unrealized P&L: $0.00
  ...

================================================================================
STEP 2: READING STOP ORDERS FROM IB
================================================================================

Found 8 open orders
  ARKK: Stop @ $54.75 (Order ID: 12345)
  QQQ: Stop @ $511.25 (Order ID: 12346)
  ...

================================================================================
STEP 3: GETTING EXPECTED POSITIONS FROM BACKTEST
================================================================================

Expected positions from backtest: 8
  ARKK:
    Expected stop: $54.75
    Entry date: 2025-05-14
    Entry price: $57.56
  ...

================================================================================
STEP 4: MATCHING & CREATING POSITION STATE
================================================================================

Processing ARKK...
  + Found stop order: $54.75
  + Matched with backtest
    Expected stop: $54.75
    Entry date: 2025-05-14
  
...

================================================================================
SYNC COMPLETE
================================================================================

+ Synced 8 positions
+ State saved to: position_state.json
```

---

### **STEP 4: Verify Sync**

Check that `position_state.json` was created correctly:

```bash
cat position_state.json
```

**Should look like:**
```json
{
  "positions": {
    "ARKK": {
      "quantity": 328.2,
      "entry_price": 88.98,
      "stop_price": 54.75,
      "stop_order_id": 12345,
      "manually_entered": true,
      "entry_date": "2025-05-14",
      "atr": 2.81
    },
    ...
  },
  "metadata": {
    "last_updated": "2025-11-01T14:30:00",
    "initialized_manually": true,
    "sync_date": "2025-11-01T14:30:00"
  }
}
```

**Verify:**
- ✅ All 8 positions are listed
- ✅ Quantities match your IB positions
- ✅ Stop prices match what you entered
- ✅ Stop order IDs are present

---

### **STEP 5: Begin Daily Operations**

You're now ready to run the daily system!

**Every evening after market close (4:00 PM EST):**
```bash
python live_trader.py --step night
```
- Generates new signals
- Saves pending entries

**Every morning before market open (9:29 AM EST):**
```bash
python live_trader.py --step morning --live --port 4002
```
- Confirms entries (1-day EMA check)
- Adjusts positions (delta-only trading)
- Manages stops
- Updates `position_state.json`

---

## 🔧 **Troubleshooting**

### **Problem: No positions found in IB**

**Solution:**
- Make sure you've entered positions first
- Check you're connected to correct account (paper vs live)
- Verify IB Gateway/TWS is running

---

### **Problem: No stop orders found**

**Solution:**
- Place stop orders for all positions
- Make sure stop order type is `STOP` (not `STOP LIMIT`)
- Verify stop orders are `GTC` (Good Till Cancelled)
- Re-run sync script

---

### **Problem: Stop price mismatch**

**Warning:**
```
ARKK: Stop mismatch (IB: $55.00, Expected: $54.75)
```

**This is OK if:**
- You intentionally adjusted the stop
- Difference is small (<1%)

**This is NOT OK if:**
- You entered wrong stop price
- Fix in IB and re-run sync

---

### **Problem: Position not in expected backtest**

**Warning:**
```
XYZ: Not in expected positions from backtest
```

**Causes:**
- Position is stopped out in backtest (shouldn't enter)
- You entered wrong ticker
- You added extra position not in strategy

**Solution:**
- Check initialization script output
- Verify ticker is in the list
- Consider exiting position if not in strategy

---

## 📊 **After Sync - What Happens**

### **Daily Workflow**

Once synced, the system automatically:

1. **Tracks your positions** using `position_state.json`

2. **Monitors stops daily**
   - Checks if price hit stop
   - Exits position if stopped
   - Cancels stop order in IB
   - Updates state file

3. **Adjusts positions** based on new signals
   - Only trades the delta (5% threshold)
   - Rebalances existing positions
   - Adds new positions with fresh stops
   - Removes positions that exit strategy

4. **Manages stops automatically**
   - Places new stops for new positions
   - Keeps existing stops (static ATR)
   - Cancels stops when exiting positions

---

## ⚠️ **Important Notes**

### **Stops Are Static**

Stops **do NOT trail** - they stay at entry level:
- Entry: $88.98
- Stop: $54.75
- Price moves to $120: Stop STAYS at $54.75

**This is correct** - matches backtest behavior.

---

### **Risk Grows as Winners Run**

As positions win, risk from current price grows:
- ARKK entered at $57.56, stop at $54.75 = 4.9% risk
- ARKK now at $88.98, stop still $54.75 = 38.5% risk

**This is correct** - matches backtest state.

---

### **Delta-Only Trading**

System only trades when position needs >5% adjustment:
- Target: 58%, Current: 60% → No trade (within 5%)
- Target: 58%, Current: 70% → Trade (sell down)
- Target: 58%, Current: 45% → Trade (buy up)

Reduces unnecessary trading and costs.

---

## 📋 **Complete Checklist**

Before considering initialization complete:

- [ ] Ran `initialize_strategy.py` - got list of 8 positions
- [ ] Entered all 8 positions in IB (market orders)
- [ ] Placed all 8 stop orders in IB (stop orders at historical levels)
- [ ] Ran `sync_manual_positions.py` - synced successfully
- [ ] Verified `position_state.json` created correctly
- [ ] Verified stop order IDs are in state file
- [ ] Tested night run: `python live_trader.py --step night`
- [ ] Tested morning run: `python live_trader.py --step morning` (dry run)
- [ ] Ready for live: `python live_trader.py --step morning --live --port 4002`

---

## 🎓 **Next Steps**

1. **Monitor for 1 week** in paper trading
   - Watch how system adjusts positions
   - Verify stops work correctly
   - Check daily reports

2. **Review performance weekly**
   - Check `trade_history.csv`
   - Review `entry_rejections.csv`
   - Verify ~28% rejection rate

3. **Scale to live when confident**
   - Start with 25-50% capital
   - Monitor closely first month
   - Scale up gradually

---

## 🆘 **Need Help?**

If sync fails or something doesn't match:

1. **Check IB connection**
   ```bash
   python test_ib_connection.py --port 4002
   ```

2. **Verify positions manually in IB**
   - Go to Portfolio → Positions
   - Count positions
   - Check stop orders

3. **Re-run initialization analyzer**
   ```bash
   python initialize_strategy.py
   ```
   - Compare with what you entered

4. **Delete position_state.json and re-sync**
   ```bash
   rm position_state.json
   python sync_manual_positions.py --port 4002
   ```

---

**The manual initialization process is complete once `position_state.json` is created and verified!**

After that, the system runs fully automatically with the two-step daily process.

