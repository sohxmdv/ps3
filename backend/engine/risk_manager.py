# backend/engine/risk_manager.py
from typing import Dict, Optional, Tuple
import numpy as np
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class RiskLevel(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class RiskManager:
    """
    Manages risk controls including VaR, position sizing, and slippage.
    Prevents catastrophic losses through multiple risk constraints.
    """
    
    def __init__(self, 
                 var_confidence: float = 0.95,
                 var_horizon: int = 20,
                 max_position_size: float = 0.25,  # 25% of portfolio
                 max_leverage: float = 1.5,
                 transaction_fee_rate: float = 0.001,  # 0.1%
                 slippage_base_rate: float = 0.0005,  # 0.05%
                 slippage_vol_scaling: float = 0.1):
        """
        Initialize risk manager with configurable parameters.
        
        Args:
            var_confidence: Confidence level for VaR calculation
            var_horizon: Historical window for VaR
            max_position_size: Maximum position as fraction of portfolio
            max_leverage: Maximum allowed leverage
            transaction_fee_rate: Transaction fee as percentage
            slippage_base_rate: Base slippage rate
            slippage_vol_scaling: Volatility scaling factor for slippage
        """
        self.var_confidence = var_confidence
        self.var_horizon = var_horizon
        self.max_position_size = max_position_size
        self.max_leverage = max_leverage
        self.transaction_fee_rate = transaction_fee_rate
        self.slippage_base_rate = slippage_base_rate
        self.slippage_vol_scaling = slippage_vol_scaling
        
        # Risk tracking
        self.var_history: list = []
        self.risk_events: list = []
        
        logger.info(f"RiskManager initialized: VaR={var_confidence*100}%, MaxPos={max_position_size*100}%")
    
    def calculate_var(self, returns: np.ndarray) -> float:
        """
        Calculate Value at Risk (VaR) using historical method.
        
        Args:
            returns: Array of historical returns
            
        Returns:
            VaR value (as positive number representing potential loss)
        """
        if len(returns) < self.var_horizon:
            logger.warning(f"Insufficient data for VaR: {len(returns)} < {self.var_horizon}")
            return 0.02  # Default 2% VaR
        
        # Use recent window
        recent_returns = returns[-self.var_horizon:]
        
        # Historical VaR at specified confidence level
        var_percentile = 100 * (1 - self.var_confidence)
        var = np.percentile(recent_returns, var_percentile)
        
        # Store for tracking
        self.var_history.append(abs(var))
        
        return abs(var)  # Return as positive number
    
    def calculate_expected_shortfall(self, returns: np.ndarray) -> float:
        """
        Calculate Expected Shortfall (CVaR) for tail risk.
        
        Args:
            returns: Array of historical returns
            
        Returns:
            Expected shortfall value
        """
        if len(returns) < self.var_horizon:
            return 0.03  # Default 3%
        
        recent_returns = returns[-self.var_horizon:]
        var = np.percentile(recent_returns, 100 * (1 - self.var_confidence))
        
        # Average of returns worse than VaR
        tail_returns = recent_returns[recent_returns <= var]
        if len(tail_returns) > 0:
            return abs(np.mean(tail_returns))
        return abs(var)
    
    def calculate_position_size(self, signal: str, portfolio_value: float,
                               current_price: float, var: float) -> int:
        """
        Calculate safe position size based on risk constraints.
        
        Args:
            signal: 'BUY' or 'SELL'
            portfolio_value: Current portfolio value
            current_price: Current asset price
            var: Current VaR estimate
            
        Returns:
            Recommended position size in shares
        """
        if current_price <= 0:
            return 0
        
        # Maximum position based on portfolio percentage
        max_position_value = portfolio_value * self.max_position_size
        max_shares = int(max_position_value / current_price)
        
        # Risk-adjusted position sizing (Kelly-inspired)
        if var > 0:
            risk_adjusted_value = (portfolio_value * 0.1) / var  # Risk 10% of portfolio / VaR
            risk_shares = int(risk_adjusted_value / current_price)
            max_shares = min(max_shares, risk_shares)
        
        # Ensure at least 1 share if we want to trade
        if signal == 'BUY':
            return max(1, max_shares)
        else:
            return max_shares
    
    def calculate_transaction_costs(self, quantity: int, price: float, 
                                   volatility: float = 0.01) -> Tuple[float, float]:
        """
        Calculate transaction fees and slippage.
        
        Args:
            quantity: Number of shares
            price: Current price per share
            volatility: Current market volatility estimate
            
        Returns:
            Tuple of (transaction_fee, slippage_cost)
        """
        trade_value = quantity * price
        
        # Transaction fee
        transaction_fee = trade_value * self.transaction_fee_rate
        
        # Slippage: increases with trade size and volatility
        slippage_rate = self.slippage_base_rate + (volatility * self.slippage_vol_scaling)
        slippage_cost = trade_value * slippage_rate
        
        logger.debug(f"Costs: Fee=${transaction_fee:.2f}, Slippage=${slippage_cost:.2f} " 
                    f"(rate={slippage_rate*100:.3f}%)")
        
        return transaction_fee, slippage_cost
    
    def approve_trade(self, signal: str, quantity: int, price: float,
                     portfolio_value: float, cash: float, 
                     current_positions_value: float) -> Tuple[bool, str]:
        """
        Final risk approval for a trade.
        
        Args:
            signal: 'BUY' or 'SELL'
            quantity: Requested quantity
            price: Current price
            portfolio_value: Total portfolio value
            cash: Available cash
            current_positions_value: Value of existing positions
            
        Returns:
            Tuple of (approved: bool, reason: str)
        """
        trade_value = quantity * price
        
        if quantity <= 0:
            return False, "Invalid quantity"
        
        # Check for extreme market conditions
        if len(self.var_history) > 0:
            recent_var = np.mean(self.var_history[-5:])
            if recent_var > 0.05:  # 5% daily VaR is extreme
                self.risk_events.append({
                    'type': 'HIGH_VAR',
                    'var': recent_var,
                    'message': f"VaR too high: {recent_var*100:.2f}%"
                })
                return False, f"Extreme risk conditions: VaR={recent_var*100:.2f}%"
        
        # Check position size limits
        if signal == 'BUY':
            # Can we afford it?
            if trade_value > cash:
                return False, f"Insufficient cash: Need ${trade_value:,.2f}, Have ${cash:,.2f}"
            
            # Will position be too large?
            new_position_value = current_positions_value + trade_value
            if new_position_value > portfolio_value * self.max_position_size:
                return False, f"Position size limit exceeded: {new_position_value/portfolio_value*100:.1f}%"
            
            # Leverage check
            leverage = (current_positions_value + trade_value) / portfolio_value
            if leverage > self.max_leverage:
                return False, f"Leverage limit exceeded: {leverage:.2f}x"
        
        # All checks passed
        return True, "Trade approved"
    
    def get_risk_level(self, var: float, positions_value: float, 
                       portfolio_value: float) -> RiskLevel:
        """
        Determine current risk level.
        
        Args:
            var: Current VaR estimate
            positions_value: Value of positions
            portfolio_value: Total portfolio value
            
        Returns:
            RiskLevel enum
        """
        if portfolio_value == 0:
            return RiskLevel.LOW
        
        exposure_ratio = positions_value / portfolio_value
        
        # Risk scoring
        risk_score = 0
        
        # VaR contribution
        if var > 0.05:
            risk_score += 3
        elif var > 0.03:
            risk_score += 2
        elif var > 0.01:
            risk_score += 1
        
        # Exposure contribution
        if exposure_ratio > 0.8:
            risk_score += 3
        elif exposure_ratio > 0.5:
            risk_score += 2
        elif exposure_ratio > 0.2:
            risk_score += 1
        
        # Determine level
        if risk_score >= 5:
            return RiskLevel.CRITICAL
        elif risk_score >= 3:
            return RiskLevel.HIGH
        elif risk_score >= 1:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def get_slippage_adjusted_price(self, price: float, signal: str, 
                                   volatility: float = 0.01) -> float:
        """
        Adjust price for slippage.
        
        Args:
            price: Current market price
            signal: 'BUY' or 'SELL'
            volatility: Market volatility
            
        Returns:
            Slippage-adjusted execution price
        """
        slippage_rate = self.slippage_base_rate + (volatility * self.slippage_vol_scaling)
        
        if signal == 'BUY':
            # Buying at slightly higher price
            return price * (1 + slippage_rate)
        else:
            # Selling at slightly lower price
            return price * (1 - slippage_rate)
    
    def reset(self):
        """Reset risk manager state."""
        self.var_history = []
        self.risk_events = []
        logger.info("RiskManager reset")