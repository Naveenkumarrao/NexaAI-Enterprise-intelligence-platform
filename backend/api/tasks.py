import uuid
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Optional
from backend.database import get_db, TaskRecord, DocumentRecord
from backend.graph.workflow import run_workflow
from backend.agents.state import AgentState

router = APIRouter(prefix="/tasks", tags=["Tasks"])


class TaskCreateRequest(BaseModel):
    user_instruction: str
    task_type: Optional[str] = ""
    document_ids: List[str]


async def execute_workflow_task(task_id: str, state: AgentState):
    from backend.database import AsyncSessionLocal
    from sqlalchemy import update as sql_update
    from datetime import datetime

    async with AsyncSessionLocal() as db:
        try:
            await db.execute(
                sql_update(TaskRecord)
                .where(TaskRecord.id == task_id)
                .values(status="running", updated_at=datetime.utcnow())
            )
            await db.commit()

            final_state = await run_workflow(state)

            result = {
                "analysis": final_state.get("analysis_result", {}),
                "comparison": final_state.get("comparison_result", {}),
                "report": final_state.get("report_data", {}),
                "pdf_path": final_state.get("pdf_path", ""),
                "excel_path": final_state.get("excel_path", ""),
            }

            await db.execute(
                sql_update(TaskRecord)
                .where(TaskRecord.id == task_id)
                .values(
                    status="completed",
                    workflow_steps=final_state.get("workflow_steps", []),
                    result=result,
                    updated_at=datetime.utcnow(),
                )
            )
            await db.commit()

        except Exception as e:
            await db.execute(
                sql_update(TaskRecord)
                .where(TaskRecord.id == task_id)
                .values(status="failed", error=str(e), updated_at=datetime.utcnow())
            )
            await db.commit()


@router.post("/")
async def create_task(
    req: TaskCreateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    # Validate documents exist
    doc_paths = []
    for doc_id in req.document_ids:
        result = await db.execute(select(DocumentRecord).where(DocumentRecord.id == doc_id))
        doc = result.scalar_one_or_none()
        if not doc:
            raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")
        doc_paths.append(doc.file_path)

    task_id = str(uuid.uuid4())
    record = TaskRecord(
        id=task_id,
        task_type=req.task_type or "analysis",
        user_instruction=req.user_instruction,
        status="pending",
        workflow_steps=[],
    )
    db.add(record)
    await db.commit()

    initial_state: AgentState = {
        "task_id": task_id,
        "task_type": req.task_type or "",
        "user_instruction": req.user_instruction,
        "document_ids": req.document_ids,
        "document_paths": doc_paths,
        "extracted_texts": {},
        "chunks": {},
        "embeddings_ready": False,
        "combined_index_id": "",
        "retrieved_context": "",
        "analysis_result": {},
        "comparison_result": {},
        "report_data": {},
        "pdf_path": "",
        "excel_path": "",
        "workflow_steps": [],
        "next": "",
        "error": None,
    }

    background_tasks.add_task(execute_workflow_task, task_id, initial_state)

    return {"task_id": task_id, "status": "pending", "message": "Workflow started"}


@router.get("/")
async def list_tasks(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TaskRecord).order_by(TaskRecord.created_at.desc()))
    tasks = result.scalars().all()
    return [
        {
            "task_id": t.id,
            "task_type": t.task_type,
            "user_instruction": t.user_instruction,
            "status": t.status,
            "created_at": str(t.created_at),
            "updated_at": str(t.updated_at),
        }
        for t in tasks
    ]


@router.get("/{task_id}")
async def get_task(task_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TaskRecord).where(TaskRecord.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {
        "task_id": task.id,
        "task_type": task.task_type,
        "user_instruction": task.user_instruction,
        "status": task.status,
        "workflow_steps": task.workflow_steps,
        "result": task.result,
        "error": task.error,
        "created_at": str(task.created_at),
        "updated_at": str(task.updated_at),
    }
