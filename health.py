from fastapi import FastAPI
app = FastAPI()

@app.get("/healthz")
def healthz(): return {"ok": True}

@app.get("/readyz")
def readyz(): return {"ready": True}
