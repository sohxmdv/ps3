# Hedge Fund Risk Modeling & Semi-Automated Trading System

## Team Information
- **Team Name**: Kabhi Code Kabhi Bug
- **Year**: 3rd Year
- **All-Female Team**: No

## Overview
This project separates heavy financial computation from the user interface to create a modular trading system.
The architecture is divided into three layers:
- **Data Pipeline** for ingesting and aligning raw time series data
- **Quant Engine (Backend)** for signal generation, risk management, and trade simulation
- **Insights Dashboard (Frontend)** for visualization and explainability

## Architecture Overview
Our system follows a decoupled design that keeps data processing, quant logic, and the dashboard separate.
This improves maintainability and makes it easier to extend each layer independently.

### System Architecture Diagram
```mermaid
graph TD
    %% Define Styles
    classDef frontend fill:#3178c6,stroke:#fff,stroke-width:2px,color:#fff;
    classDef backend fill:#009688,stroke:#fff,stroke-width:2px,color:#fff;
    classDef data fill:#f39c12,stroke:#fff,stroke-width:2px,color:#fff;
    classDef risk fill:#e74c3c,stroke:#fff,stroke-width:2px,color:#fff;

    %% Data Ingestion Layer
    subgraph 1. Data Pipeline Layer (Python / Pandas)
        A1[Raw Datasets: Equity, Macro, Assets]:::data
        A2[Data Loader & CSV Merger]:::data
        A3[Imputation Engine]:::data
        A4[(Clean Aligned Timeline)]:::data
        A1 --> A2
        A2 -->|Handle missing values & LOCF| A3
        A3 -->|Standardized Datetime| A4
    end

    %% Backend API & Quant Engine
    subgraph 2. Quant Engine & API (FastAPI)
        B1(Signal Generator):::backend
        B2(Risk Manager Gatekeeper):::risk
        B3(Portfolio State Manager):::backend
        B4(Financial Metrics Engine):::backend

        A4 -->|Market & Sentiment Data| B1
        B1 -->|Buy/Sell Signals| B2
        A4 -->|Volatility Data| B2
        B2 -->|VaR Check & Position Limits| B3
        B3 -->|Apply Slippage & Fees| B3
        B3 -->|Execution Logs| B4
    end

    %% Frontend Dashboard
    subgraph 3. Insights Dashboard (Next.js)
        C1[Client Dashboard UI]:::frontend
        C2[Recharts Performance Graph]:::frontend
        C3[Risk KPI Cards]:::frontend
        C4[Explainable Audit Log]:::frontend

        C1 -->|POST /api/simulate| B3
        B4 -.->|JSON Response: Timeline & Metrics| C1
        C1 --> C2
        C1 --> C3
        C1 --> C4
    end
```

## Architectural Flow & Explanation

1. **Data Ingestion & Preprocessing**
   - Ingests asynchronous datasets (equity, macro, multi-asset) using Pandas.
   - Missing values are handled through backward filling.
   - Monthly macro data is aligned to daily prices using Last Observation Carried Forward (LOCF).
   - The result is a clean, aligned single timeline for analysis.

2. **The Quant Engine & Risk Gatekeeper (Backend)**
   - Built on FastAPI, this backend performs signal generation, risk checks, and portfolio simulation.
   - **Signal Generation** analyzes moving average crossovers and sentiment indicators to propose trades.
   - **Risk Management** computes Parametric Value at Risk (VaR) and enforces allocation limits.
   - **Execution Simulation** applies transaction fees and slippage to make backtests more realistic.

3. **Insights Dashboard & Metrics (Frontend)**
   - The backend computes performance metrics such as Sharpe Ratio, Alpha, Beta, and Maximum Drawdown.
   - A Next.js dashboard visualizes the equity curve, risk KPIs, and explainable trade logs.
   - The explainability log details the reason for each trade and the cost assumptions used.

## File Structure
```text
ps3/
├── data/
│   └── raw/
│       ├── equity_dataset.csv
│       ├── macro_dataset.csv
│       ├── multi_asset_dataset.csv
│       └── oil_dataset.csv
├── backend/
│   ├── __init__.py
│   ├── requirements.txt
│   └── data_pipeline/
│       └── engine/
│           ├── __init__.py
│           ├── backtest_engine.py
│           ├── main.py
│           ├── portfolio.py
│           ├── risk_manager.py
│           └── signal_generator.py
└── frontend/
```

## Setup
For backend setup instructions, see `setup.md`.

#### Describe your approach here. Keep it short and clear.

    - How does your system ingest and preprocess the varying data sources (market, macro, sentiment)?
    - What risk modeling techniques were selected, and how are they integrated into the trading decision pipeline?
    - How does your semi-automated strategy generate signals while respecting portfolio constraints and handling realistic conditions like slippage?
    - How is the dashboard designed to provide explainable insights and key metrics (Sharpe, drawdown) to stakeholders?

**Note:** Please do not change the format or spelling of anything in this README. The fields are extracted using a script, so any changes to the structure or formatting may break the extraction process.
