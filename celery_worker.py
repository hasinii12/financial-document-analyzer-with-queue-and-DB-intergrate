## Celery worker for handling concurrent analysis requests
from celery import Celery
from datetime import datetime
from database import SessionLocal, AnalysisResult
from crewai import Crew, Process
from agents import financial_analyst
from task import analyze_financial_document as analyze_financial_document_task3


# Initialize Celery with Redis as broker and backend
celery_app = Celery(
    "financial_analyzer",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    worker_concurrency=4,           # Handle 4 concurrent requests
    task_acks_late=True,            # Acknowledge task after completion
    worker_prefetch_multiplier=1,   # One task per worker at a time
)


def run_crew(query: str, file_path: str = "data/sample.pdf"):
    """Run the CrewAI crew for financial analysis"""
    financial_crew = Crew(
        agents=[financial_analyst],
        tasks=[analyze_financial_document_task],
        process=Process.sequential,
    )
    result = financial_crew.kickoff({"query": query})
    return str(result)


@celery_app.task(bind=True, max_retries=3)
def analyze_document_task(self, job_id: str, query: str, file_path: str):
    """
    Celery task to analyze a financial document asynchronously.
    Retries up to 3 times on failure.
    """
    db = SessionLocal()
    try:
        # Update status to processing
        job = db.query(AnalysisResult).filter(AnalysisResult.id == job_id).first()
        if job:
            job.status = "processing"
            db.commit()

        # Run the CrewAI analysis
        result = run_crew(query=query, file_path=file_path)

        # Update status to completed
        job = db.query(AnalysisResult).filter(AnalysisResult.id == job_id).first()
        if job:
            job.status = "completed"
            job.result = result
            job.completed_at = datetime.utcnow()
            db.commit()

        return {"status": "completed", "result": result}

    except Exception as exc:
        # Update status to failed
        job = db.query(AnalysisResult).filter(AnalysisResult.id == job_id).first()
        if job:
            job.status = "failed"
            job.error = str(exc)
            job.completed_at = datetime.utcnow()
            db.commit()

        # Retry on failure with exponential backoff
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)

    finally:
        # Clean up uploaded file
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass
        db.close()
