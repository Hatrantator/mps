from fastapi import FastAPI

app = FastAPI(title="Mydroponic")

@app.get("/")
def read_root():
    return {"message": "Hello from Mydroponic!"}
