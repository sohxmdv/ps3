# Hedge Fund Risk Modeling & Semi-Automated Trading System

## Team Information
- **Team Name**: Kabhi Code Kabhi Bug
- **Year**: 3rd Year
- **All-Female Team**: No

## Architecture Overview
Our system is designed with a decoupled, microservices-style architecture to separate heavy financial computation from the user interface. The flow is divided into three distinct layers: The Data Pipeline, The Quant Engine (Backend), and The Insights Dashboard (Frontend).

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

Architectural Flow & Explanation
1. Data Ingestion & Preprocessing (The Foundation)
To prevent forward-looking bias, our system ingests multiple asynchronous datasets (equity, macro, multi-asset) using Pandas. Missing values (such as initial SMA_10 rows) are handled via backward filling, and monthly macroeconomic data is aligned to daily stock prices using Last Observation Carried Forward (LOCF). This results in a single, pristine timeline.

2. The Quant Engine & Risk Gatekeeper (Backend)
Built on FastAPI, this is the mathematical brain of the system. It operates in a strict loop:

Signal Generation: Analyzes moving average crossovers and sentiment scores to suggest trades.

Risk Management: Before any trade is executed, the Risk Manager calculates the Parametric Value at Risk (VaR). If a trade exposes the portfolio beyond our predefined risk limits (e.g., >5% capital allocation), the trade is blocked or resized.

Realistic Execution: Approved trades are passed to the Portfolio Manager, which strictly deducts transaction fees and simulated market slippage from the cash balance to ensure realistic backtesting.

3. Insights Dashboard & Metrics (Frontend)
The backend calculates final financial performance metrics (Sharpe Ratio, Alpha, Beta, and Maximum Drawdown) and serves them to a Next.js frontend. The dashboard utilizes Recharts to visualize the portfolio's equity curve against market benchmarks and provides a scrolling "Explainability Log." This log proves our system is not a black box by detailing exactly why every trade was made and what friction costs were applied.


### File Structure
```text
hedge-fund-system/
├── data/                           # (Data Engineer's Domain)
│   ├── equity_dataset.csv
│   ├── macro-dataet.csv
│   ├── multi_assetdataset.csv
│   └── oil_dataset.csv
│
├── backend/                        # (Quant Developer's Domain)
│   ├── main.py                     # FastAPI application entry point
│   ├── requirements.txt            # Python dependencies (pandas, fastapi, uvicorn, scipy)
│   ├── data_pipeline/              # Scripts to ingest/clean data
│   │   ├── __init__.py
│   │   ├── loader.py               # Merges the CSV files into one DataFrame
│   │   └── preprocessor.py         # Imputes missing values and aligns dates
│   ├── engine/                     # Core trading & risk logic
│   │   ├── __init__.py
│   │   ├── portfolio.py            # Tracks cash, deducts slippage & fees
│   │   ├── risk_manager.py         # Calculates VaR, enforces position limits
│   │   └── signal_generator.py     # Generates Buy/Sell signals (Moving Averages)
│   └── api/                        # REST API layer
│       ├── __init__.py
│       ├── routes.py               # Houses the POST /api/simulate endpoint
│       └── metrics.py              # Calculates Sharpe, Alpha, Beta, Drawdown
│
├── frontend/                       # (Analytics Engineer's Domain)
│   ├── package.json
│   ├── tailwind.config.js
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx            # Main dashboard view
│   │   │   ├── layout.tsx
│   │   │   └── globals.css
│   │   ├── components/             # Reusable UI parts
│   │   │   ├── KPICards.tsx        # Displays Sharpe, Drawdown, etc.
│   │   │   ├── PerformanceChart.tsx# The main Recharts line graph
│   │   │   ├── TradeLogTable.tsx   # The explainable audit trail
│   │   │   └── SimulationControls.tsx # Sliders for risk inputs
│   │   └── lib/
│   │       └── api.ts              # Fetch logic to connect to localhost:8000
```
#### Describe your approach here. Keep it short and clear.

    - How does your system ingest and preprocess the varying data sources (market, macro, sentiment)?
    - What risk modeling techniques were selected, and how are they integrated into the trading decision pipeline?
    - How does your semi-automated strategy generate signals while respecting portfolio constraints and handling realistic conditions like slippage?
    - How is the dashboard designed to provide explainable insights and key metrics (Sharpe, drawdown) to stakeholders?

**Note:** Please do not change the format or spelling of anything in this README. The fields are extracted using a script, so any changes to the structure or formatting may break the extraction process.
