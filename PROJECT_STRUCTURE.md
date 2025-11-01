# Project Structure

## 📁 **File Organization**

---

## 🎯 **START HERE (First Time Users)**

| File | Purpose |
|------|---------|
| **READY_FOR_LIVE.md** | ⭐ **Start here!** Complete overview, checklist, commands |
| **README.md** | Strategy overview, performance metrics |
| **MANUAL_INITIALIZATION.md** | Step-by-step setup for first-time entry |

---

## 📚 **Documentation**

### **Strategy Understanding:**
| File | What It Covers |
|------|---------------|
| **STRATEGY_EXPLAINED.md** | How the strategy works, entry/exit rules |
| **PRODUCTION_SUMMARY.md** | Evolution from v1.0 to v3.0, metrics |
| **TWO_STEP_ENTRY.md** | Why 1-day confirmation matters (28% rejection) |

### **Setup & Operations:**
| File | What It Covers |
|------|---------------|
| **IB_SETUP_GUIDE.md** | Complete Interactive Brokers setup |
| **GETTING_STARTED_IB.md** | Quick IB connection guide |
| **QUICKSTART.md** | Quick reference commands |
| **README_LIVE_TRADING.md** | Live trading workflow |

### **Technical Details:**
| File | What It Covers |
|------|---------------|
| **POSITION_MANAGER_INTEGRATION.md** | How stop losses are managed |
| **IMPLEMENTATION_SUMMARY.md** | Two-step entry implementation |

---

## 🐍 **Python Scripts**

### **Core Strategy Modules:**
| File | Purpose |
|------|---------|
| **quad_portfolio_backtest.py** | Full backtest engine (420% strategy) |
| **signal_generator.py** | Daily signal generation |
| **config.py** | Asset allocations & quadrant definitions |

### **Execution & Trading:**
| File | Purpose |
|------|---------|
| **live_trader.py** | ⭐ Main orchestrator (night & morning runs) |
| **ib_executor.py** | Interactive Brokers API integration |
| **position_manager.py** | Position state & stop order management |
| **pending_orders.py** | 1-day entry confirmation system |
| **telegram_notifier.py** | Alert notifications |

### **Initialization:**
| File | Purpose |
|------|---------|
| **initialize_strategy.py** | Analyze mid-stream entry positions |
| **sync_manual_positions.py** | Sync manually entered positions |
| **test_ib_connection.py** | Verify IB connection |

### **Analysis & Testing:**
| File | Purpose |
|------|---------|
| **run_production_backtest.py** | Quick performance check |
| **monte_carlo_backtest.py** | Risk validation (500 simulations) |
| **analyze_backtest.py** | Position history & return attribution |

---

## 📊 **Data Files (Generated at Runtime)**

### **Daily Operations:**
- `night_plan_YYYYMMDD.txt` - Tonight's execution plan
- `morning_report_YYYYMMDD.txt` - Execution results
- `signals_YYYYMMDD.json` - Signal archive

### **State Tracking:**
- `position_state.json` - Current positions & stops
- `trade_history.csv` - All trades log
- `entry_rejections.csv` - Rejected entries
- `pending_entries.json` - Overnight pending orders

### **Analysis Outputs:**
- `monte_carlo_bootstrap_500.csv` - Simulation data
- `monte_carlo_bootstrap_500.png` - Risk charts
- `allocation_history.png` - Position timeline
- `return_attribution.png` - Return breakdown
- `backtest_analysis_report.txt` - Detailed analysis

*Note: Runtime files are in .gitignore*

---

## 📦 **Configuration Files**

| File | Purpose |
|------|---------|
| **requirements.txt** | Python dependencies |
| **.gitignore** | Files to exclude from Git |

---

## 🎮 **Usage by Task**

### **"I want to understand the strategy"**
1. Read: `STRATEGY_EXPLAINED.md`
2. Run: `python run_production_backtest.py`
3. Run: `python analyze_backtest.py`

### **"I want to set up IB"**
1. Read: `IB_SETUP_GUIDE.md`
2. Run: `python test_ib_connection.py --port 4002`

### **"I want to initialize and go live"**
1. Read: `MANUAL_INITIALIZATION.md`
2. Run: `python initialize_strategy.py`
3. Manual entry in IB
4. Run: `python sync_manual_positions.py --port 4001`

### **"I want to run daily operations"**
1. Read: `QUICKSTART.md`
2. Night: `python live_trader.py --step night --live --port 4001`
3. Morning: `python live_trader.py --step morning --live --port 4001`

### **"I want to validate the strategy"**
1. Run: `python monte_carlo_backtest.py --type bootstrap --n 500`
2. Run: `python analyze_backtest.py`
3. Review results

---

## 📊 **File Count Summary**

- **Documentation:** 12 .md files
- **Core Modules:** 9 .py files
- **Analysis Tools:** 4 .py files
- **Config/Utils:** 2 files
- **Total:** 27 production files

**Clean, organized, production-ready!** ✅

---

## 🚀 **Quick Navigation**

**New User?** → `READY_FOR_LIVE.md`  
**Ready to Trade?** → `MANUAL_INITIALIZATION.md`  
**Daily Trading?** → `QUICKSTART.md`  
**Need Help?** → `IB_SETUP_GUIDE.md`  
**Want Details?** → `STRATEGY_EXPLAINED.md`  

---

**Everything you need, nothing you don't.** 🎯

