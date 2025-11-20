import os
from typing import List, Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="RARE API", description="Automation solutions and recommendations")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Solution(BaseModel):
    id: str
    title: str
    category: str
    description: str
    impact: str = Field(description="What improves: time saved, errors reduced, etc.")
    tools: List[str]
    complexity: str  # Low | Medium | High


class RecommendRequest(BaseModel):
    industry: Optional[str] = None
    team_size: Optional[str] = None  # solo, small, medium, enterprise
    goals: List[str]  # ["save_time", "reduce_errors", "increase_sales", "better_visibility"]
    processes: List[str]  # ["lead_intake", "invoicing", "marketing", "support", "hr", "inventory", "reporting"]


# Curated catalog (static for MVP)
CATALOG: List[Solution] = [
    Solution(
        id="lead-capture-crm",
        title="Acquisizione lead → CRM",
        category="Vendite",
        description="Raccogli i lead da form e landing e inseriscili automaticamente nel CRM con deduplicazione e arricchimento dati.",
        impact="Riduce tempi manuali e migliora la qualità dei dati",
        tools=["Webhooks", "Zapier/Make", "HubSpot/Pipedrive"],
        complexity="Low",
    ),
    Solution(
        id="invoice-automation",
        title="Fatturazione automatica",
        category="Finance",
        description="Genera fatture dai contratti/ordini, inviale e registra i pagamenti con riconciliazione.",
        impact="Riduce errori e velocizza il cash-flow",
        tools=["ERP/Conta", "Stripe", "Zapier"],
        complexity="Medium",
    ),
    Solution(
        id="marketing-drip",
        title="Email drip marketing",
        category="Marketing",
        description="Sequenze email automatiche basate su comportamento utente e segmenti.",
        impact="Aumenta conversioni e LTV",
        tools=["Mailchimp/Customer.io", "Segment", "Webhook"],
        complexity="Low",
    ),
    Solution(
        id="support-triage",
        title="Smistamento ticket con AI",
        category="Supporto",
        description="Classifica automaticamente i ticket per priorità, lingua e argomento, assegnandoli al team giusto.",
        impact="Riduce i tempi di risposta",
        tools=["Helpdesk", "AI classifier", "Webhook"],
        complexity="Medium",
    ),
    Solution(
        id="ops-dashboard",
        title="Dashboard operativa live",
        category="Operazioni",
        description="Unifica dati da CRM, supporto e fatturazione in un'unica dashboard con KPI aggiornati.",
        impact="Migliora visibilità e decisioni",
        tools=["BigQuery", "Metabase/Looker", "ETL"],
        complexity="High",
    ),
]


@app.get("/")
def read_root():
    return {"message": "RARE backend attivo"}


@app.get("/api/solutions", response_model=List[Solution])
def list_solutions():
    return CATALOG


@app.post("/api/recommend", response_model=List[Solution])
def recommend(req: RecommendRequest):
    # Simple scoring: match goals and processes to catalog keywords
    keywords = set((req.industry or "").lower().split())
    keywords.update(req.goals)
    keywords.update(req.processes)

    def score(sol: Solution) -> int:
        s = sol.title.lower() + " " + sol.category.lower() + " " + sol.description.lower()
        base = 0
        for kw in keywords:
            if kw and kw in s:
                base += 2
        # small bonus by goal heuristics
        if "reduce_errors" in req.goals and "error" in s:
            base += 2
        if "save_time" in req.goals and "tempo" in s:
            base += 2
        if sol.complexity == "Low" and (req.team_size in {"solo", "small", None}):
            base += 1
        return base

    ranked = sorted(CATALOG, key=score, reverse=True)
    return ranked[:3]


@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}


@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    
    try:
        # Try to import database module
        from database import db
        
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            
            # Try to list collections to verify connectivity
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]  # Show first 10 collections
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
            
    except ImportError:
        response["database"] = "❌ Database module not found (run enable-database first)"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    
    # Check environment variables
    import os
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    
    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
