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

# Import the new pipeline from the __init__.py file
from backend.data_pipeline import get_clean_data
from backend.engine.backtest_engine import BacktestEngine

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

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SimulationParams(BaseModel):
    """Parameters for backtest simulation"""

    initial_capital: float = Field(
        float(os.getenv("DEFAULT_INITIAL_CAPITAL", 1000000)),
        ge=10000,
        description="Starting capital",
    )
    sma_short_window: int = Field(
        int(os.getenv("DEFAULT_SMA_SHORT", 10)),
        ge=2,
        le=200,
        description="Short SMA window",
    )
    sma_long_window: int = Field(
        int(os.getenv("DEFAULT_SMA_LONG", 50)),
        ge=5,
        le=500,
        description="Long SMA window",
    )
    var_confidence: float = Field(
        float(os.getenv("DEFAULT_VAR_CONFIDENCE", 0.95)),
        ge=0.90,
        le=0.99,
        description="VaR confidence level",
    )
    max_position_size: float = Field(
        float(os.getenv("DEFAULT_MAX_POSITION_SIZE", 0.25)),
        ge=0.05,
        le=0.50,
        description="Max position size as fraction",
    )
    transaction_fee_rate: float = Field(
        float(os.getenv("DEFAULT_TRANSACTION_FEE", 0.001)),
        ge=0.0,
        le=0.01,
        description="Transaction fee rate",
    )
    slippage_base_rate: float = Field(
        float(os.getenv("DEFAULT_SLIPPAGE_RATE", 0.0005)),
        ge=0.0,
        le=0.005,
        description="Base slippage rate",
    )


class SimulationResponse(BaseModel):
    """Response from simulation endpoint"""

    status: str
    summary: Dict[str, Any]
    daily_values: List[Dict[str, Any]]
    trades: List[Dict[str, Any]]
    risk_metrics: List[Dict[str, Any]]
    signals: List[Dict[str, Any]]


@app.get("/")
async def root():
    """Root endpoint with API documentation"""
    return {
        "message": "Hedge Fund Risk Modeling System API",
        "version": "1.0.0",
        "docs_url": "/docs",
        "endpoints": {"simulate": "/api/simulate", "health": "/health"},
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Dynamically find the data/raw folder
        data_dir_path = str(BASE_DIR / "data" / "raw")
        data = get_clean_data(data_dir_path=data_dir_path, save_processed=False)
        return {
            "status": "healthy",
            "service": "backtest-engine",
            "data_available": len(data) > 0,
            "data_points": len(data),
        }
    except Exception as e:
        return {"status": "degraded", "service": "backtest-engine", "error": str(e)}


@app.post("/api/simulate", response_model=SimulationResponse)
async def run_simulation(params: SimulationParams):
    """
    Run backtest simulation with given parameters.
    """
    try:
        logger.info(f"Starting simulation with params: {params}")

        # Get clean data from Data Engineer's pipeline
        try:
            data_dir_path = str(BASE_DIR / "data" / "raw")
            data = get_clean_data(data_dir_path=data_dir_path, save_processed=True)

            # --- THE INTEGRATION FIX ---
            # 1. Rename columns to match what the Backtest Engine expects
            data = data.rename(
                columns={
                    "equity_Price": "Close",
                    "equity_Returns": "Returns",
                    "equity_SMA_10": "SMA_10",
                }
            )

            # 2. Calculate the missing indicators required by the Signal Generator
            if "SMA_50" not in data.columns:
                data["SMA_50"] = (
                    data["Close"].rolling(window=params.sma_long_window).mean().bfill()
                )

            if "RSI" not in data.columns:
                delta = data["Close"].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                data["RSI"] = 100 - (100 / (1 + rs))
                data["RSI"] = data["RSI"].bfill()
            # ---------------------------

            logger.info(f"Loaded data: {len(data)} rows, columns: {list(data.columns)}")
        except Exception as e:
            logger.error(f"Failed to load data: {e}")
            raise HTTPException(
                status_code=500, detail=f"Data pipeline error: {str(e)}"
            )

        # Initialize and run backtest engine
        engine = BacktestEngine(
            initial_capital=params.initial_capital,
            sma_short=params.sma_short_window,
            sma_long=params.sma_long_window,
            var_confidence=params.var_confidence,
            max_position_size=params.max_position_size,
            transaction_fee_rate=params.transaction_fee_rate,
            slippage_base_rate=params.slippage_base_rate,
        )

        results = engine.run(data)

        logger.info(
            f"Simulation complete. Final value: ${results['summary']['final_value']:,.2f}"
        )

        return SimulationResponse(
            status="success",
            summary=results["summary"],
            daily_values=results["daily_values"],
            trades=results["trades"],
            risk_metrics=results["risk_metrics"],
            signals=results["signals"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Simulation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Simulation error: {str(e)}")


@app.get("/api/simulate")
async def run_simulation_get(
    initial_capital: float = Query(
        float(os.getenv("DEFAULT_INITIAL_CAPITAL", 1000000)),
        ge=10000,
        description="Starting capital",
    ),
    sma_short_window: int = Query(
        int(os.getenv("DEFAULT_SMA_SHORT", 10)),
        ge=2,
        le=200,
        description="Short SMA window",
    ),
    sma_long_window: int = Query(
        int(os.getenv("DEFAULT_SMA_LONG", 50)),
        ge=5,
        le=500,
        description="Long SMA window",
    ),
    var_confidence: float = Query(
        float(os.getenv("DEFAULT_VAR_CONFIDENCE", 0.95)),
        ge=0.90,
        le=0.99,
        description="VaR confidence",
    ),
    max_position_size: float = Query(
        float(os.getenv("DEFAULT_MAX_POSITION_SIZE", 0.25)),
        ge=0.05,
        le=0.50,
        description="Max position size",
    ),
    transaction_fee_rate: float = Query(
        float(os.getenv("DEFAULT_TRANSACTION_FEE", 0.001)),
        ge=0.0,
        le=0.01,
        description="Fee rate",
    ),
    slippage_base_rate: float = Query(
        float(os.getenv("DEFAULT_SLIPPAGE_RATE", 0.0005)),
        ge=0.0,
        le=0.005,
        description="Slippage rate",
    ),
):
    """
    Run simulation with GET parameters (useful for testing).
    """
    params = SimulationParams(
        initial_capital=initial_capital,
        sma_short_window=sma_short_window,
        sma_long_window=sma_long_window,
        var_confidence=var_confidence,
        max_position_size=max_position_size,
        transaction_fee_rate=transaction_fee_rate,
        slippage_base_rate=slippage_base_rate,
    )
    return await run_simulation(params)


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "True").lower() == "true"

    logger.info(f"Starting server on {host}:{port}")
    uvicorn.run(
        "main:app", host=host, port=port, reload=debug, log_level=log_level.lower()
    )
