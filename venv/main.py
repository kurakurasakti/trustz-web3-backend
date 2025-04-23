from fastapi import FastAPI, UploadFile, Form
from analyzers.github import analyze_github
from analyzers.resume import analyze_resume
import uvicorn

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "TrustScore AI backend is running."}

@app.post("/analyze/github")
async def analyze_github_endpoint(username: str = Form(...)):
    result = analyze_github(username)
    return result

@app.post("/analyze/resume")
async def analyze_resume_endpoint(file: UploadFile):
    content = await file.read()
    result = analyze_resume(content.decode("utf-8"))
    return result

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)