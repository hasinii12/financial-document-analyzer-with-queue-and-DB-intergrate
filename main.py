from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends
from sqlalchemy.orm import Session
import os
import uuid
from datetime import datetime

from crewai import Crew, Process
from task import analyze_financial_document as analyze_financial_document_task
from task import analyze_financial_document as analyze_financial_document_task
from database import init_db, get_db, AnalysisResult, User
from celery_worker import analyze_document_task

app = FastAPI(title="Financial Document Analyzer")

# Initialize database on startup
@app.on_event("startup")
def startup_event():
    init_db()


def run_crew(query: str, file_path: str = "data/sample.pdf"):
    """To run the whole crew"""
    financial_crew = Crew(
        agents=[financial_analyst],
        tasks=[analyze_financial_document_task],
        process=Process.sequential,
    )
    result = financial_crew.kickoff({"query": query})
    return result


# ─────────────────────────────────────────────
# Health Check
# ─────────────────────────────────────────────
@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Financial Document Analyzer API is running"}


# ─────────────────────────────────────────────
# Async Analysis with Queue (Bonus Feature)
# ─────────────────────────────────────────────
@app.post("/analyze/async")
async def analyze_async(
    file: UploadFile = File(...),
    query: str = Form(default="Analyze this financial document for investment insights"),
    db: Session = Depends(get_db)
):
    """
    Submit a financial document for async analysis via Celery queue.
    Returns a job_id to check status later.
    Handles concurrent requests without blocking.
    """
    job_id = str(uuid.uuid4())
    file_path = f"data/financial_document_{job_id}.pdf"

    try:
        os.makedirs("data", exist_ok=True)

        # Save uploaded file
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        if not query or query.strip() == "":
            query = "Analyze this financial document for investment insights"

        # Save job to database with pending status
        job = AnalysisResult(
            id=job_id,
            filename=file.filename,
            query=query.strip(),
            status="pending"
        )
        db.add(job)
        db.commit()

        # Submit to Celery queue
        analyze_document_task.apply_async(
            args=[job_id, query.strip(), file_path],
            task_id=job_id
        )

        return {
            "status": "queued",
            "job_id": job_id,
            "message": "Document submitted for analysis. Use /analyze/status/{job_id} to check progress."
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error queuing document: {str(e)}")


# ─────────────────────────────────────────────
# Check Job Status
# ─────────────────────────────────────────────
@app.get("/analyze/status/{job_id}")
async def get_job_status(job_id: str, db: Session = Depends(get_db)):
    """Check the status of an async analysis job"""
    job = db.query(AnalysisResult).filter(AnalysisResult.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "job_id": job.id,
        "status": job.status,
        "filename": job.filename,
        "query": job.query,
        "result": job.result if job.status == "completed" else None,
        "error": job.error if job.status == "failed" else None,
        "created_at": job.created_at,
        "completed_at": job.completed_at
    }


# ─────────────────────────────────────────────
# Sync Analysis (Original Feature)
# ─────────────────────────────────────────────
@app.post("/analyze")
async def analyze_document(
    file: UploadFile = File(...),
    query: str = Form(default="Analyze this financial document for investment insights"),
    db: Session = Depends(get_db)
):
    """Analyze financial document synchronously and store result in database"""

    file_id = str(uuid.uuid4())
    file_path = f"data/financial_document_{file_id}.pdf"

    try:
        os.makedirs("data", exist_ok=True)

        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        if not query or query.strip() == "":
            query = "Analyze this financial document for investment insights"

        # Save to database with processing status
        job = AnalysisResult(
            id=file_id,
            filename=file.filename,
            query=query.strip(),
            status="processing"
        )
        db.add(job)
        db.commit()

        # Run analysis
        response = run_crew(query=query.strip(), file_path=file_path)

        # Update database with result
        job.status = "completed"
        job.result = str(response)
        job.completed_at = datetime.utcnow()
        db.commit()

        return {
            "status": "success",
            "job_id": file_id,
            "query": query,
            "analysis": str(response),
            "file_processed": file.filename
        }

    except Exception as e:
        # Update database with error
        job = db.query(AnalysisResult).filter(AnalysisResult.id == file_id).first()
        if job:
            job.status = "failed"
            job.error = str(e)
            job.completed_at = datetime.utcnow()
            db.commit()
        raise HTTPException(status_code=500, detail=f"Error processing financial document: {str(e)}")

    finally:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass


# ─────────────────────────────────────────────
# Database Endpoints (Bonus Feature)
# ─────────────────────────────────────────────
@app.get("/analyses")
async def get_all_analyses(db: Session = Depends(get_db)):
    """Retrieve all past analysis results from database"""
    analyses = db.query(AnalysisResult).order_by(AnalysisResult.created_at.desc()).all()
    return {
        "total": len(analyses),
        "analyses": [
            {
                "job_id": a.id,
                "filename": a.filename,
                "query": a.query,
                "status": a.status,
                "created_at": a.created_at,
                "completed_at": a.completed_at
            }
            for a in analyses
        ]
    }


@app.get("/analyses/{job_id}")
async def get_analysis(job_id: str, db: Session = Depends(get_db)):
    """Retrieve a specific analysis result by job ID"""
    analysis = db.query(AnalysisResult).filter(AnalysisResult.id == job_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return {
        "job_id": analysis.id,
        "filename": analysis.filename,
        "query": analysis.query,
        "status": analysis.status,
        "result": analysis.result,
        "error": analysis.error,
        "created_at": analysis.created_at,
        "completed_at": analysis.completed_at
    }


@app.delete("/analyses/{job_id}")
async def delete_analysis(job_id: str, db: Session = Depends(get_db)):
    """Delete a specific analysis result"""
    analysis = db.query(AnalysisResult).filter(AnalysisResult.id == job_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    db.delete(analysis)
    db.commit()
    return {"message": f"Analysis {job_id} deleted successfully"}


# ─────────────────────────────────────────────
# User Endpoints (Bonus Feature)
# ─────────────────────────────────────────────
@app.post("/users")
async def create_user(name: str, email: str, db: Session = Depends(get_db)):
    """Create a new user"""
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(name=name, email=email)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"user_id": user.id, "name": user.name, "email": user.email, "created_at": user.created_at}


@app.get("/users")
async def get_all_users(db: Session = Depends(get_db)):
    """Retrieve all users"""
    users = db.query(User).all()
    return {
        "total": len(users),
        "users": [{"user_id": u.id, "name": u.name, "email": u.email, "created_at": u.created_at} for u in users]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000, reload=False)
