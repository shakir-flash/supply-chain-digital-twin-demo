# Supply Chain Digital Twin — Interview Demo (Home Depot)

A streamlined **supply chain digital twin** built for scenario planning, cost tradeoffs, and service risk insights.  
This demo integrates **data pipeline, optimization, SQL-backed insights, and an interactive Streamlit dashboard** with a clean, branded header tailored for The Home Depot interview presentation.

---

## Features at a Glance

- 📊 Executive dashboard with lean KPIs (Total cost, Transport cost, Unmet units)
- 🌐 Interactive transport network map with service-time coloring
- ⚙️ Scenario planning levers (regional demand multipliers, DC capacity adjustments)
- 🧮 Data pipeline for cleaning, optimization, and KPI computation
- 📦 SQLite warehouse + CSV/PNG outputs for reproducibility
- 🔎 SQL-backed analytics and natural language query router
- 🤖 Optional LLM integration via Ollama for contextual Q&A
- 🖼️ Custom Home Depot–themed header for presentation polish

---

## Tech Stack

- **Language**: Python 3.10+
- **Frontend**: [Streamlit](https://streamlit.io/), Plotly, AgGrid
- **Backend**: [FastAPI](https://fastapi.tiangolo.com/), Uvicorn
- **Data**: Pandas, NumPy, SciPy, SQLAlchemy, SQLite
- **Visualization**: Plotly, Matplotlib, Seaborn
- **LLM (Optional)**: Ollama, custom agent (Llama 2:7b LLM model running)
- **Infra**: Works locally on Windows, macOS, Linux

---

## Installation & Dependencies

### 1. Clone the repo
```bash
git clone https://github.com/your-username/supply-chain-digital-twin-demo.git
cd supply-chain-digital-twin-demo
```

### 2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate   # macOS/Linux
venv\Scripts\activate    # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

**Key dependencies:**

- streamlit
- fastapi
- uvicorn
- pandas
- numpy
- scipy
- sqlalchemy
- plotly
- matplotlib
- seaborn
- python-multipart
- ollama (optional, for LLM)

---

## How to Run

### Option A: Full pipeline + Streamlit dashboard (recommended)

Run the data pipeline:
```bash
python model/run_pipeline.py
```
This will generate cleaned datasets, run optimization, compute KPIs, and save outputs into `data/results/` and charts into `data/charts/`.

Launch the Streamlit dashboard:
```bash
streamlit run app/frontend/app.py
```
Then open the provided local URL in your browser.

---

### Option B: Backend API (FastAPI only)

Start the backend service:
```bash
uvicorn app.backend.main:app --reload
```
Endpoints will be available at `http://127.0.0.1:8000`.

---

## Components

- **Pipeline** (`model/run_pipeline.py`)  
  Orchestrates cleaning, optimization, KPI calculation, and output generation.

- **Backend API** (`app/backend/main.py`)  
  Provides REST endpoints for KPIs, costs, utilization, scenarios, and NLQ.

- **Frontend Dashboard** (`app/frontend/app.py`)  
  Streamlit app with tabs for dashboard, costs, utilization, transport map, SQL explorer.

- **Custom Header** (`app/frontend/components/hd_header.py`)  
  Branded Home Depot header with gradient orange styling, meta info, and KPI badges.

- **Analytics Router** (`analytics/answer_engine_sql.py`)  
  Maps intent queries (e.g., “total transport cost”) to SQL statements.

- **LLM Agent (Optional)** (`llm/agent.py`)  
  Connects to Ollama for natural language Q&A.

---

## Data Flow

1. **Raw data** → `data/raw/`
2. **Cleaning** → `data/clean/`
3. **Optimization + KPIs** → `data/results/`
4. **Visualization** → `data/charts/`
5. **Warehouse** → `data/warehouse.db`

---

## Home Depot Interview Customization

- Custom header component (`hd_header.py`) with Home Depot logo and orange gradient
- Focus on three lean KPIs: Total cost, Transport cost, Unmet units
- Executive-ready visuals: cleaner fonts, badges, gradient header
- Configurable scenario levers via sidebar in the dashboard

---

## Example Workflow

Launch the app:
```bash
streamlit run app/frontend/app.py
```

Click **Run Full Pipeline**  
View KPIs and charts  
Explore transport map with service-time highlighting  
Use scenario controls to adjust demand/capacity  
Query the system using the NLQ tab

---

## License

This repository is intended for demonstration and interview purposes only.  
No commercial use without permission.

---

## Project Structure

```text
supply-chain-digital-twin-demo/
│
├── app/
│   ├── backend/                # FastAPI backend
│   │   └── main.py
│   ├── frontend/               # Streamlit frontend
│   │   ├── app.py
│   │   └── components/
│   │       └── hd_header.py    # Home Depot header component
│
├── analytics/                  # SQL intent router
├── llm/                        # Ollama + agent integration
├── model/                      # Data pipeline & optimization
│   └── run_pipeline.py
│
├── data/
│   ├── raw/                    # Raw inputs
│   ├── clean/                  # Cleaned datasets
│   └── results/                # Optimized outputs + KPIs
│
├── visualization.py            # Charting utilities
├── config.py                   # Config & levers
├── requirements.txt            # Dependencies
└── README.md
```
