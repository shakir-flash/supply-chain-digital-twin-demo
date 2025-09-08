# Supply Chain Digital Twin — Network Refresh Demo

End-to-end pipeline that mirrors a Network Strategy annual refresh:
**Data → Clean → Optimize → KPIs → Scenarios → Visuals → Conversational NLQ.**

## Run

```bash
pip install -r requirements.txt
python main.py
# backend
uvicorn app.backend.main:app --reload --port 8000
# frontend
streamlit run app/frontend/app.py
