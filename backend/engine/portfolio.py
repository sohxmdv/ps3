# backend/engine/portfolio.py
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@dataclass
class Position:
    """Represents a single position in the portfolio"""
    symbol: str
    quantity: int
    avg_price: float
    current_price: float
    entry_date: datetime
    
    @property
    def market_value(self) -> float:
        return self.quantity * self.current_price
    
    @property
    def unrealized_pnl(self) -> float:
        return self.quantity * (self.current_price - self.avg_price)

@dataclass
class Trade:
    """Records a completed trade"""
    date: datetime
    symbol: str
    action: str  # 'BUY' or 'SELL'
    quantity: int
    price: float
    transaction_cost: float
    slippage_cost: float
    reason: str
    
    @property
    def total_cost(self) -> float:
        return (self.quantity * self.price) + self.transaction_cost + self.slippage_cost

@dataclass
class PortfolioSnapshot:
    """Daily snapshot of portfolio state"""
    date: datetime
    cash: float
    positions_value: float
    total_value: float
    daily_return: float
    num_positions: int
    
    @property
    def portfolio_value(self) -> float:
        return self.cash + self.positions_value

class PortfolioManager:
    """
    Manages portfolio state including cash, positions, and trade history.
    """
    
    def __init__(self, initial_capital: float = 1_000_000.0):
        """
        Initialize portfolio with starting capital.
        
        Args:
            initial_capital: Starting cash amount
        """
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions: Dict[str, Position] = {}
        self.trade_history: List[Trade] = []
        self.daily_snapshots: List[PortfolioSnapshot] = []
        self.current_date: Optional[datetime] = None
        
        logger.info(f"Portfolio initialized with ${initial_capital:,.2f}")
    
    def update_prices(self, date: datetime, price_data: Dict[str, float]):
        """
        Update current prices for all positions.
        
        Args:
            date: Current trading date
            price_data: Dict mapping symbol to current price
        """
        self.current_date = date
        
        for symbol, position in self.positions.items():
            if symbol in price_data:
                position.current_price = price_data[symbol]
    
    def can_execute_trade(self, symbol: str, quantity: int, price: float, 
                         transaction_cost: float, slippage_cost: float) -> bool:
        """
        Check if portfolio has sufficient cash to execute a trade.
        
        Args:
            symbol: Trading symbol
            quantity: Number of shares (positive for buy, negative for sell)
            price: Current price per share
            transaction_cost: Transaction fee
            slippage_cost: Slippage cost
            
        Returns:
            bool: True if trade can be executed
        """
        if quantity > 0:  # Buy order
            total_cost = (quantity * price) + transaction_cost + slippage_cost
            return self.cash >= total_cost
        elif quantity < 0:  # Sell order
            abs_quantity = abs(quantity)
            if symbol not in self.positions:
                return False
            return self.positions[symbol].quantity >= abs_quantity
        return False
    
    def execute_trade(self, symbol: str, quantity: int, price: float,
                     transaction_cost: float, slippage_cost: float,
                     reason: str) -> Optional[Trade]:
        """
        Execute a trade and update portfolio state.
        
        Args:
            symbol: Trading symbol
            quantity: Number of shares (positive for buy, negative for sell)
            price: Execution price
            transaction_cost: Transaction fee
            slippage_cost: Slippage cost
            reason: Signal/reason for the trade
            
        Returns:
            Trade object if successful, None otherwise
        """
        if not self.can_execute_trade(symbol, quantity, price, transaction_cost, slippage_cost):
            logger.warning(f"Cannot execute trade: {symbol} qty={quantity}")
            return None
        
        trade = Trade(
            date=self.current_date,
            symbol=symbol,
            action='BUY' if quantity > 0 else 'SELL',
            quantity=abs(quantity),
            price=price,
            transaction_cost=transaction_cost,
            slippage_cost=slippage_cost,
            reason=reason
        )
        
        if quantity > 0:  # Buy
            total_cost = (quantity * price) + transaction_cost + slippage_cost
            self.cash -= total_cost
            
            if symbol in self.positions:
                # Average up/down
                pos = self.positions[symbol]
                total_quantity = pos.quantity + quantity
                total_cost_basis = (pos.quantity * pos.avg_price) + (quantity * price)
                pos.quantity = total_quantity
                pos.avg_price = total_cost_basis / total_quantity
            else:
                # New position
                self.positions[symbol] = Position(
                    symbol=symbol,
                    quantity=quantity,
                    avg_price=price,
                    current_price=price,
                    entry_date=self.current_date
                )
        else:  # Sell
            abs_quantity = abs(quantity)
            total_proceeds = (abs_quantity * price) - transaction_cost - slippage_cost
            self.cash += total_proceeds
            
            pos = self.positions[symbol]
            pos.quantity -= abs_quantity
            if pos.quantity == 0:
                del self.positions[symbol]
        
        self.trade_history.append(trade)
        logger.info(f"Executed {trade.action} {abs(quantity)} {symbol} @ ${price:.2f}")
        return trade
    
    def create_snapshot(self, date: datetime, daily_return: float = 0.0) -> PortfolioSnapshot:
        """
        Create a snapshot of current portfolio state.
        
        Args:
            date: Snapshot date
            daily_return: Daily portfolio return
            
        Returns:
            PortfolioSnapshot object
        """
        positions_value = sum(pos.market_value for pos in self.positions.values())
        
        snapshot = PortfolioSnapshot(
            date=date,
            cash=self.cash,
            positions_value=positions_value,
            total_value=self.cash + positions_value,
            daily_return=daily_return,
            num_positions=len(self.positions)
        )
        
        self.daily_snapshots.append(snapshot)
        return snapshot
    
    def get_portfolio_value(self) -> float:
        """Get current total portfolio value."""
        positions_value = sum(pos.market_value for pos in self.positions.values())
        return self.cash + positions_value
    
    def reset(self):
        """Reset portfolio to initial state."""
        self.cash = self.initial_capital
        self.positions = {}
        self.trade_history = []
        self.daily_snapshots = []
        self.current_date = None
        
        logger.info("Portfolio reset to initial state")