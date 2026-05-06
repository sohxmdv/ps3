# Hedge Fund Risk Modeling & Semi-Automated Trading System

## Team Information
- **Team Name**: Kabhi Code Kabhi Bug
- **Year**: 3rd Year
- **All-Female Team**: No

## Architecture Overview
Our system utilizes a modular, microservices-inspired architecture designed to seamlessly ingest asynchronous financial data, execute risk-aware trading strategies, and deliver explainable metrics. The system is decoupled into three primary layers: The Data Pipeline, The Quant Engine (Backend), and The Insights Dashboard (Frontend).

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

#### Describe your approach here. Keep it short and clear.

    - How does your system ingest and preprocess the varying data sources (market, macro, sentiment)?
    - What risk modeling techniques were selected, and how are they integrated into the trading decision pipeline?
    - How does your semi-automated strategy generate signals while respecting portfolio constraints and handling realistic conditions like slippage?
    - How is the dashboard designed to provide explainable insights and key metrics (Sharpe, drawdown) to stakeholders?

**Note:** Please do not change the format or spelling of anything in this README. The fields are extracted using a script, so any changes to the structure or formatting may break the extraction process.
