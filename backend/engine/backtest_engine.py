# backend/engine/backtest_engine.py
import pandas as pd
import numpy as np
from typing import Dict, List, Any
import logging
from .portfolio import PortfolioManager
from .risk_manager import RiskManager
from .signal_generator import SignalGenerator, SignalType

logger = logging.getLogger(__name__)

class BacktestEngine:
    def __init__(self, initial_capital: float, sma_short: int, sma_long: int,
                 var_confidence: float, max_position_size: float, 
                 transaction_fee_rate: float, slippage_base_rate: float):
        
        self.portfolio = PortfolioManager(initial_capital)
        self.risk_manager = RiskManager(
            var_confidence=var_confidence,
            max_position_size=max_position_size,
            transaction_fee_rate=transaction_fee_rate,
            slippage_base_rate=slippage_base_rate
        )
        self.signal_generator = SignalGenerator(
            sma_short_window=sma_short,
            sma_long_window=sma_long
        )

    def run(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Runs the historical simulation row by row."""
        logger.info("Starting backtest loop...")
        
        # Ensure data is sorted by date
        data = data.sort_index()
        returns_history = []
        signals_log = []

        for date, row in data.iterrows():
            current_price = float(row['Close'])
            symbol = 'EQUITY'  # Assuming single asset for this test
            
            # 1. Update Portfolio Prices
            self.portfolio.update_prices(date, {symbol: current_price})
            
            # 2. Get Signal
            current_data = row.to_dict()
            historical_data = data.loc[:date].tail(20).to_dict('records')
            signal_info = self.signal_generator.generate_signal(current_data, historical_data)
            
            # 3. Track Returns for Risk Manager (VaR)
            if pd.notna(row.get('Returns')):
                returns_history.append(float(row['Returns']))
            
            # 4. Execute Logic if Signal is triggered
            if signal_info['signal'] != SignalType.HOLD:
                current_var = self.risk_manager.calculate_var(np.array(returns_history)) if returns_history else 0.02
                
                # Determine safe quantity
                quantity = self.risk_manager.calculate_position_size(
                    signal_info['signal'].value, 
                    self.portfolio.get_portfolio_value(),
                    current_price, 
                    current_var
                )

                if quantity > 0:
                    # Make quantity negative for SELL
                    trade_qty = quantity if signal_info['signal'] == SignalType.BUY else -quantity
                    
                    # Calculate friction
                    fee, slippage = self.risk_manager.calculate_transaction_costs(quantity, current_price, 0.01)
                    
                    # Ask Risk Manager for final approval
                    approved, reason = self.risk_manager.approve_trade(
                        signal_info['signal'].value, quantity, current_price,
                        self.portfolio.get_portfolio_value(), self.portfolio.cash,
                        sum(p.market_value for p in self.portfolio.positions.values())
                    )

                    if approved:
                        self.portfolio.execute_trade(
                            symbol, trade_qty, current_price, fee, slippage, signal_info['reason']
                        )
                        signals_log.append({
                            "date": date.isoformat(),
                            "action": signal_info['signal'].value,
                            "price": current_price,
                            "reason": signal_info['reason']
                        })

            # 5. Daily Snapshot
            # Calculate daily return (rough estimate for snapshot)
            daily_ret = returns_history[-1] if returns_history else 0.0
            self.portfolio.create_snapshot(date, daily_ret)

        # 6. Calculate Final Metrics
        final_value = self.portfolio.get_portfolio_value()
        total_return = (final_value - self.portfolio.initial_capital) / self.portfolio.initial_capital
        
        return {
            "summary": {
                "initial_capital": self.portfolio.initial_capital,
                "final_value": final_value,
                "total_return_pct": total_return * 100,
                "total_trades": len(self.portfolio.trade_history)
            },
            "daily_values": [{"date": s.date.isoformat(), "value": s.total_value} for s in self.portfolio.daily_snapshots],
            "trades": [{"date": t.date.isoformat(), "action": t.action, "qty": t.quantity, "price": t.price} for t in self.portfolio.trade_history],
            "risk_metrics": [{"var_history_length": len(self.risk_manager.var_history)}],
            "signals": signals_log
        }