# MTS Risk Management Module - MVP Build Plan

## Phase 1: Core Foundation (Tasks 1-8)

### Task 1: Create Basic Project Structure
**Goal**: Set up the minimal folder structure and empty files
**Files**: Create all directories and `__init__.py` files from the architecture
**Test**: `python -c "import src.risk_management; print('Structure created')"` succeeds
**End State**: Importable package structure exists

### Task 2: Define Core Data Models
**Goal**: Create the basic data models for risk assessment
**Files**: `src/risk_management/models/risk_models.py`
**Code**: Define `RiskAssessment`, `TradingSignal`, `PortfolioState` dataclasses
**Test**: Can instantiate all models with sample data
**End State**: Core data structures exist and are importable

### Task 3: Create Risk Configuration Schema
**Goal**: Define the JSON configuration structure
**Files**: `src/risk_management/config/risk_config.json`
**Code**: JSON with all risk limits (max_drawdown: 0.20, daily_loss: 0.05, etc.)
**Test**: JSON loads without errors and contains required keys
**End State**: Configuration file exists and is valid JSON

### Task 4: Implement Configuration Loader
**Goal**: Load and validate risk configuration
**Files**: `src/risk_management/core/risk_orchestrator.py` (partial)
**Code**: `_load_config()` method that reads and validates JSON
**Test**: Can load config and access `max_drawdown_limit` value
**End State**: Configuration can be loaded and accessed

### Task 5: Create Basic Position Size Calculator
**Goal**: Implement simple fixed-percentage position sizing
**Files**: `src/risk_management/calculators/position_calculator.py`
**Code**: Single method that calculates 2% of account equity
**Test**: Given $10,000 equity, returns $200 position size
**End State**: Basic position sizing works

### Task 6: Implement Stop Loss Calculator
**Goal**: Calculate stop loss price based on 2% position risk
**Files**: Add method to `risk_orchestrator.py`
**Code**: `_calculate_stop_loss_price()` method
**Test**: Given LONG signal at $100 with $200 position, returns $96 stop loss
**End State**: Stop loss calculation works for LONG/SHORT

### Task 7: Create Risk/Reward Calculator
**Goal**: Calculate basic risk/reward ratio
**Files**: Add method to `risk_orchestrator.py`
**Code**: `_calculate_risk_reward_ratio()` method using stop loss distance
**Test**: Given entry $100, stop $95, target $110, returns 2.0 ratio
**End State**: Risk/reward calculation works

### Task 8: Build Minimal Risk Assessment
**Goal**: Create basic risk assessment that combines all calculations
**Files**: Complete basic `assess_trade_risk()` method
**Code**: Method that uses position calc, stop loss, R/R ratio
**Test**: Given a trading signal, returns populated RiskAssessment object
**End State**: Basic risk assessment pipeline works

## Phase 2: Risk Rules & Validation (Tasks 9-12)

### Task 9: Implement Drawdown Rule Validation
**Goal**: Check if trade would exceed 20% max drawdown
**Files**: `src/risk_management/validators/trade_validator.py`
**Code**: `validate_drawdown_limit()` method
**Test**: Rejects trade that would cause >20% drawdown, approves safe trades
**End State**: Drawdown limit enforcement works

### Task 10: Implement Daily Loss Limit Validation
**Goal**: Check if trade would exceed 5% daily loss limit
**Files**: Add method to `trade_validator.py`
**Code**: `validate_daily_loss_limit()` method
**Test**: Rejects trade exceeding daily limit, approves within limit
**End State**: Daily loss limit enforcement works

### Task 11: Create Portfolio State Tracker
**Goal**: Track current portfolio state for risk calculations
**Files**: `src/risk_management/state/portfolio_state.py`
**Code**: Class to track equity, positions, current drawdown, daily P&L
**Test**: Can update state and retrieve current values
**End State**: Portfolio state tracking works

### Task 12: Integrate Validation into Assessment
**Goal**: Add validation checks to main risk assessment
**Files**: Update `risk_orchestrator.py` to use validators
**Code**: Call validation methods before approving trades
**Test**: Assessment rejects trades violating risk limits
**End State**: Risk limits are enforced in assessments

## Phase 3: JSON Output & Integration (Tasks 13-16)

### Task 13: Create JSON Formatter
**Goal**: Convert risk assessment to structured JSON
**Files**: `src/risk_management/utils/json_formatter.py`
**Code**: `format_risk_assessment()` method producing structured JSON
**Test**: Produces valid JSON with all required fields
**End State**: Risk assessments can be output as JSON

### Task 14: Add JSON Output to Orchestrator
**Goal**: Add `to_json()` method to risk orchestrator
**Files**: Update `risk_orchestrator.py`
**Code**: `to_json()` method using the formatter
**Test**: `orchestrator.to_json(assessment)` returns valid JSON string
**End State**: Main orchestrator can output JSON

### Task 15: Create Paper Trading Integration Interface
**Goal**: Define interface for paper trading integration
**Files**: `src/risk_management/integrations/paper_trading_integration.py`
**Code**: `PaperTradingRiskManager` class with `assess_signal()` method
**Test**: Can call integration and get risk assessment
**End State**: Paper trading can request risk assessments

### Task 16: Create State Persistence
**Goal**: Save and load risk state to/from files
**Files**: `src/risk_management/state/risk_state_manager.py`
**Code**: `save_state()` and `load_state()` methods for JSON files
**Test**: Can save portfolio state and reload it correctly
**End State**: Risk state persists between runs

## Phase 4: Testing & Validation (Tasks 17-20)

### Task 17: Create Sample Test Data
**Goal**: Generate realistic test signals and portfolio states
**Files**: `src/risk_management/tests/test_data.py`
**Code**: Functions to create sample TradingSignal and PortfolioState objects
**Test**: Can generate various test scenarios
**End State**: Test data generation works

### Task 18: Write Integration Test
**Goal**: Test complete risk assessment flow
**Files**: `src/risk_management/tests/test_integration.py`
**Code**: Test that processes signal through full assessment pipeline
**Test**: End-to-end test passes with expected JSON output
**End State**: Full integration works

### Task 19: Add Error Handling
**Goal**: Handle errors gracefully in risk assessment
**Files**: Update `risk_orchestrator.py` with try/catch blocks
**Code**: Wrap main methods in error handling, return error assessments
**Test**: Invalid inputs return error assessments instead of crashing
**End State**: Error handling works

### Task 20: Create CLI Interface for Testing
**Goal**: Command-line tool to test risk assessments
**Files**: `src/risk_management/cli.py`
**Code**: Simple CLI that takes signal parameters and outputs JSON assessment
**Test**: `python cli.py --asset BTC --signal LONG --price 50000` works
**End State**: Manual testing interface exists

## Success Criteria for MVP

**Input**: Trading signal with asset, signal type, price, confidence
**Output**: JSON risk assessment with:
- Recommended position size (based on account equity)
- Stop loss price (2% position risk)
- Risk/reward ratio
- Approval/rejection decision
- Risk limit compliance

**Key Validations**:
- ✅ Max drawdown limit (20%)
- ✅ Daily loss limit (5%)
- ✅ Per-trade stop loss (2%)
- ✅ Position sizing based on account equity

**Integration Points**:
- ✅ Paper trading engine can request assessments
- ✅ State persists between runs
- ✅ JSON output format ready for consumption

**Total Tasks**: 20
**Estimated Completion**: Each task should take 15-30 minutes
**MVP Delivery**: Fully functional risk management module with JSON API