# backend/engine/signal_generator.py
from typing import Dict, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class SignalType(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

class SignalGenerator:
    """
    Generates trading signals based on technical indicators.
    Primary strategy: SMA Crossover with configurable parameters.
    """
    
    def __init__(self, sma_short_window: int = 10, sma_long_window: int = 50,
                 rsi_period: int = 14, rsi_overbought: float = 70.0,
                 rsi_oversold: float = 30.0, volatility_lookback: int = 20):
        """
        Initialize signal generator with strategy parameters.
        
        Args:
            sma_short_window: Short-term SMA window
            sma_long_window: Long-term SMA window
            rsi_period: RSI calculation period
            rsi_overbought: RSI overbought threshold
            rsi_oversold: RSI oversold threshold
            volatility_lookback: Lookback period for volatility calculation
        """
        self.sma_short_window = sma_short_window
        self.sma_long_window = sma_long_window
        self.rsi_period = rsi_period
        self.rsi_overbought = rsi_overbought
        self.rsi_oversold = rsi_oversold
        self.volatility_lookback = volatility_lookback
        
        # State tracking
        self.previous_signal: Optional[SignalType] = None
        self.position_held: bool = False
        
        logger.info(f"SignalGenerator initialized: SMA({sma_short_window}/{sma_long_window})")
    
    def generate_signal(self, current_data: Dict, historical_data: list = None) -> Dict:
        """
        Generate trading signal based on current market data.
        
        Args:
            current_data: Dict with keys 'SMA_10', 'SMA_50', 'Close', 'Returns', etc.
            historical_data: Optional list of recent data points for additional analysis
            
        Returns:
            Dict containing signal info:
                - signal: SignalType enum value
                - confidence: float 0-1
                - reason: str explanation
                - indicators: dict of calculated indicators
        """
        signal = self._primary_strategy(current_data)
        
        # Add secondary confirmation if historical data available
        if historical_data and len(historical_data) >= self.volatility_lookback:
            confidence = self._calculate_confidence(current_data, historical_data)
            signal['confidence'] = confidence
            
            # Override signal if confidence too low
            if confidence < 0.3:
                signal['signal'] = SignalType.HOLD
                signal['reason'] += " (Low confidence - holding)"
        else:
            signal['confidence'] = 0.7  # Default confidence
        
        # Track signal changes
        if signal['signal'] != SignalType.HOLD:
            self.previous_signal = signal['signal']
        
        return signal
    
    def _primary_strategy(self, data: Dict) -> Dict:
        """
        Primary SMA crossover strategy with RSI filter.
        
        Args:
            data: Current market data point
            
        Returns:
            Signal dict
        """
        sma_10 = data.get('SMA_10')
        sma_50 = data.get('SMA_50')
        close_price = data.get('Close')
        rsi = data.get('RSI', 50)
        
        indicators = {
            'sma_10': sma_10,
            'sma_50': sma_50,
            'close': close_price,
            'rsi': rsi
        }
        
        # Default to HOLD if required data missing
        if sma_10 is None or sma_50 is None or close_price is None:
            return {
                'signal': SignalType.HOLD,
                'confidence': 0.0,
                'reason': f"Insufficient data: SMA_10={sma_10}, SMA_50={sma_50}",
                'indicators': indicators
            }
        
        reason_parts = []
        
        # SMA Crossover logic
        if sma_10 > sma_50 and close_price > sma_10:
            signal = SignalType.BUY
            reason_parts.append(f"Bullish SMA crossover (SMA10=${sma_10:.2f} > SMA50=${sma_50:.2f})")
        elif sma_10 < sma_50 and close_price < sma_10:
            signal = SignalType.SELL
            reason_parts.append(f"Bearish SMA crossover (SMA10=${sma_10:.2f} < SMA50=${sma_50:.2f})")
        else:
            signal = SignalType.HOLD
            reason_parts.append(f"No clear signal (SMA10=${sma_10:.2f}, SMA50=${sma_50:.2f})")
        
        # RSI filter
        if rsi is not None:
            if signal == SignalType.BUY and rsi > self.rsi_overbought:
                signal = SignalType.HOLD
                reason_parts.append(f"RSI overbought ({rsi:.1f} > {self.rsi_overbought}) - holding")
            elif signal == SignalType.SELL and rsi < self.rsi_oversold:
                signal = SignalType.HOLD
                reason_parts.append(f"RSI oversold ({rsi:.1f} < {self.rsi_oversold}) - holding")
        
        return {
            'signal': signal,
            'confidence': 0.6,  # Will be refined by confidence method
            'reason': " | ".join(reason_parts),
            'indicators': indicators
        }
    
    def _calculate_confidence(self, current_data: Dict, historical_data: list) -> float:
        """
        Calculate signal confidence based on multiple factors.
        
        Args:
            current_data: Current market data
            historical_data: Recent historical data points
            
        Returns:
            Confidence score 0-1
        """
        confidence = 0.5  # Base confidence
        
        # Factor 1: Trend strength (using recent returns)
        if len(historical_data) >= 5:
            recent_returns = [d.get('Returns', 0) for d in historical_data[-5:] if d.get('Returns') is not None]
            if recent_returns:
                positive_returns = sum(1 for r in recent_returns if r > 0)
                trend_strength = abs(positive_returns / len(recent_returns) - 0.5) * 2
                confidence += trend_strength * 0.2
        
        # Factor 2: Volatility (lower vol = higher confidence)
        if len(historical_data) >= self.volatility_lookback:
            returns = [d.get('Returns', 0) for d in historical_data[-self.volatility_lookback:] 
                      if d.get('Returns') is not None]
            if returns:
                import numpy as np
                volatility = np.std(returns)
                if volatility > 0:
                    vol_score = max(0, 1 - (volatility * 10))
                    confidence += vol_score * 0.2
        
        # Factor 3: SMA divergence strength
        sma_10 = current_data.get('SMA_10')
        sma_50 = current_data.get('SMA_50')
        if sma_10 and sma_50 and sma_50 > 0:
            divergence = abs(sma_10 - sma_50) / sma_50
            divergence_score = min(1.0, divergence * 20)
            confidence += divergence_score * 0.1
        
        return min(1.0, confidence)
    
    def should_exit_position(self, current_data: Dict, entry_price: float) -> Dict:
        """
        Determine if current position should be exited.
        
        Args:
            current_data: Current market data
            entry_price: Price at which position was entered
            
        Returns:
            Exit signal dict
        """
        current_price = current_data.get('Close', 0)
        if current_price == 0:
            return {'signal': SignalType.HOLD, 'reason': 'No price data'}
        
        # Stop loss: 5% below entry
        stop_loss = entry_price * 0.95
        if current_price <= stop_loss:
            return {
                'signal': SignalType.SELL,
                'confidence': 0.9,
                'reason': f"Stop loss triggered: Current=${current_price:.2f} <= Stop=${stop_loss:.2f}",
                'indicators': {'entry_price': entry_price, 'stop_loss': stop_loss}
            }
        
        # Take profit: 10% above entry
        take_profit = entry_price * 1.10
        if current_price >= take_profit:
            return {
                'signal': SignalType.SELL,
                'confidence': 0.8,
                'reason': f"Take profit triggered: Current=${current_price:.2f} >= Target=${take_profit:.2f}",
                'indicators': {'entry_price': entry_price, 'take_profit': take_profit}
            }
        
        # SMA exit signal
        sma_10 = current_data.get('SMA_10')
        sma_50 = current_data.get('SMA_50')
        if sma_10 and sma_50 and sma_10 < sma_50 and current_price < sma_10:
            return {
                'signal': SignalType.SELL,
                'confidence': 0.6,
                'reason': f"Bearish SMA crossover: SMA10=${sma_10:.2f} < SMA50=${sma_50:.2f}",
                'indicators': {'sma_10': sma_10, 'sma_50': sma_50}
            }
        
        return {
            'signal': SignalType.HOLD,
            'confidence': 0.5,
            'reason': "No exit signal triggered",
            'indicators': {'current_price': current_price}
        }
    
    def reset(self):
        """Reset signal generator state."""
        self.previous_signal = None
        self.position_held = False
        logger.info("SignalGenerator reset")