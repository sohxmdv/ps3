# backend/main.py
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

# Add parent directory to path so it can find the modules
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

# Import the new pipeline and metrics
from backend.data_pipeline import get_clean_data
from backend.engine.backtest_engine import BacktestEngine
from api.metrics import calculate_performance_metrics, build_equity_curve_payload

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    level=getattr(logging, log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Hedge Fund Risk Modeling System",
    description="API for running backtest simulations with risk management",
    version="1.0.0",
)

# Global variable to store the latest run for the React dashboard
latest_simulation_result = None

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SimulationParams(BaseModel):
    initial_capital: float = Field(float(os.getenv("DEFAULT_INITIAL_CAPITAL", 1000000)), ge=10000)
    sma_short_window: int = Field(int(os.getenv("DEFAULT_SMA_SHORT", 10)), ge=2, le=200)
    sma_long_window: int = Field(int(os.getenv("DEFAULT_SMA_LONG", 50)), ge=5, le=500)
    var_confidence: float = Field(float(os.getenv("DEFAULT_VAR_CONFIDENCE", 0.95)), ge=0.90, le=0.99)
    max_position_size: float = Field(float(os.getenv("DEFAULT_MAX_POSITION_SIZE", 0.25)), ge=0.05, le=0.50)
    transaction_fee_rate: float = Field(float(os.getenv("DEFAULT_TRANSACTION_FEE", 0.001)), ge=0.0, le=0.01)
    slippage_base_rate: float = Field(float(os.getenv("DEFAULT_SLIPPAGE_RATE", 0.0005)), ge=0.0, le=0.005)

# FIXED: Updated to match the React frontend's required format
class SimulationResponse(BaseModel):
    metrics: Dict[str, Any]
    chart: List[Dict[str, Any]]
    trades: List[Dict[str, Any]]

@app.get("/")
async def root():
    return {"message": "Hedge Fund Risk Modeling System API", "endpoints": {"simulate": "/api/simulate"}}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# NEW: The endpoint your React app is polling every 5 seconds
@app.get("/api/simulate/latest", response_model=SimulationResponse)
async def get_latest_simulation():
    global latest_simulation_result
    if latest_simulation_result is None:
        raise HTTPException(status_code=404, detail="No simulation run yet")
    return latest_simulation_result

@app.post("/api/simulate", response_model=SimulationResponse)
async def run_simulation(params: SimulationParams):
    try:
        data_dir_path = str(BASE_DIR / "data" / "raw")
        data = get_clean_data(data_dir_path=data_dir_path, save_processed=True)
        
        # Integration Fix
        data = data.rename(columns={'equity_Price': 'Close', 'equity_Returns': 'Returns', 'equity_SMA_10': 'SMA_10'})
        if 'SMA_50' not in data.columns:
            data['SMA_50'] = data['Close'].rolling(window=params.sma_long_window).mean().bfill()
        if 'RSI' not in data.columns:
            delta = data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            data['RSI'] = (100 - (100 / (1 + (gain / loss)))).bfill()

        engine = BacktestEngine(
            initial_capital=params.initial_capital,
            sma_short=params.sma_short_window,
            sma_long=params.sma_long_window,
            var_confidence=params.var_confidence,
            max_position_size=params.max_position_size,
            transaction_fee_rate=params.transaction_fee_rate,
            slippage_base_rate=params.slippage_base_rate
        )
        
        results = engine.run(data)
        
        benchmark_csv_path = str(BASE_DIR / "data" / "raw" / "equity_dataset.csv")
        
        frontend_metrics = calculate_performance_metrics(results['daily_values'], benchmark_path=benchmark_csv_path)
        frontend_chart = build_equity_curve_payload(results['daily_values'], benchmark_path=benchmark_csv_path)
        frontend_trades = [
            {
                "id": f"trade_{i}",
                "date": t["date"][:10],
                "action": t["action"],
                "asset": "EQUITY",
                "rationale": t.get("reason", "Strategy execution")
            } for i, t in enumerate(results['trades'])
        ]

        response = SimulationResponse(
            metrics=frontend_metrics,
            chart=frontend_chart,
            trades=frontend_trades
        )
        
        # Save to global cache so the /latest endpoint can serve it!
        global latest_simulation_result
        latest_simulation_result = response
        
        return response
    
    except Exception as e:
        logger.error(f"Simulation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Simulation error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "True").lower() == "true"
    logger.info(f"Starting server on {host}:{port}")
    uvicorn.run("main:app", host=host, port=port, reload=debug, log_level=log_level.lower())