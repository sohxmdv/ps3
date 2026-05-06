# Hedge Fund Risk Modeling & Semi-Automated Trading System

## Team Information
- **Team Name**: Kabhi Code Kabhi Bug
- **Year**: 3rd Year
- **All-Female Team**: No

## Architecture Overview
Our system is a quantitative finance platform designed to combine algorithmic trading with institutional-style risk management through a modular three-layer architecture.

Architecture Deep-Dive
1. Data Pipeline Layer (Python & Pandas)
The ingestion engine handles heterogeneous datasets including equity OHLC, macroeconomic indicators, and sentiment data. The Imputation Engine utilizes Last Observation Carried Forward (LOCF) to resolve asynchronous time-series gaps, ensuring a standardized "Clean Aligned Timeline" for the backtester, eliminating look-ahead bias.

2. Quant Engine & API (FastAPI)
Acting as the system's brain, the Signal Generator produces trade triggers which are immediately intercepted by the Risk Manager Gatekeeper. This layer calculates Value at Risk (VaR) and enforces strict position limits. Before final execution, the Portfolio State Manager adjusts for slippage and transaction costs to maintain a realistic equity curve.

3. Insights Dashboard (Next.js & Recharts)
The frontend provides an interactive cockpit for fund managers. It features Explainable Audit Logs that detail why specific signals were blocked by risk protocols, alongside real-time KPI cards (Sharpe Ratio, Max Drawdown) to visualize the strategy's risk-adjusted performance.

Technical Stack
Backend: Python, FastAPI, Pandas, NumPy

Frontend: Next.js, TypeScript, Recharts, Tailwind CSS

Risk Logic: VaR Modeling, Volatility Filtering, Slippage Simulation

### System Architecture Diagram
```mermaid
graph TD
    classDef frontend fill:#3178c6,stroke:#fff,stroke-width:2px,color:#fff;
    classDef backend fill:#009688,stroke:#fff,stroke-width:2px,color:#fff;
    classDef data fill:#f39c12,stroke:#fff,stroke-width:2px,color:#fff;
    classDef risk fill:#e74c3c,stroke:#fff,stroke-width:2px,color:#fff;

    subgraph Layer1 [1. Data Pipeline Layer Python / Pandas]
        A1[Raw Datasets: Equity, Macro, Assets]:::data
        A2[Data Loader & CSV Merger]:::data
        A3[Imputation Engine]:::data
        A4[(Clean Aligned Timeline)]:::data
        A1 --> A2
        A2 -->|Handle missing values & LOCF| A3
        A3 -->|Standardized Datetime| A4
    end

    subgraph Layer2 [2. Quant Engine & API FastAPI]
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

    subgraph Layer3 [3. Insights Dashboard Next.js]
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