from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pathlib import Path
from backend.database import get_db, TaskRecord
from backend.tools.calculator_tool import safe_calculate, compute_tco, compare_numeric_values
from backend.tools.report_exporter import export_pdf, export_excel
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional

router = APIRouter(prefix="/analysis", tags=["Analysis"])


@router.get("/task/{task_id}/result")
async def get_task_result(task_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TaskRecord).where(TaskRecord.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status != "completed":
        return {"status": task.status, "message": "Task not yet completed"}
    return {
        "task_id": task_id,
        "task_type": task.task_type,
        "status": task.status,
        "result": task.result,
        "workflow_steps": task.workflow_steps,
    }


class ReportUpdateRequest(BaseModel):
    summary: str
    key_insights: List[str] = Field(default_factory=list)
    risks: str = ""
    pros_cons: str = ""
    numerical_data: str = ""
    recommendation: str = ""
    comparison_strengths_weaknesses: str = ""
    comparison_risk_assessment: str = ""
    comparison_table: List[Dict[str, Any]] = Field(default_factory=list)


@router.put("/task/{task_id}/report")
async def update_task_report(
    task_id: str,
    req: ReportUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(TaskRecord).where(TaskRecord.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status != "completed":
        raise HTTPException(status_code=409, detail="Only completed reports can be edited")

    task_result = dict(task.result or {})
    report_data = {**(task_result.get("report") or {}), **req.model_dump()}
    report_name = f"report_{task_id}"
    pdf_path = export_pdf(report_data, report_name)
    excel_path = export_excel(report_data, report_name)

    task_result.update(
        {
            "report": report_data,
            "pdf_path": pdf_path,
            "excel_path": excel_path,
            "human_approved": True,
        }
    )
    task.result = task_result
    task.workflow_steps = list(task.workflow_steps or []) + [
        "human_review: report reviewed and approved"
    ]
    await db.commit()
    return {
        "task_id": task_id,
        "report": report_data,
        "pdf_path": pdf_path,
        "excel_path": excel_path,
    }


@router.get("/task/{task_id}/download/pdf")
async def download_pdf(task_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TaskRecord).where(TaskRecord.id == task_id))
    task = result.scalar_one_or_none()
    if not task or task.status != "completed":
        raise HTTPException(status_code=404, detail="Task not completed or not found")
    if not task.result or not task.result.get("human_approved"):
        raise HTTPException(status_code=409, detail="Report requires human review and approval")
    pdf_path = task.result.get("pdf_path", "") if task.result else ""
    if not pdf_path or not Path(pdf_path).exists():
        raise HTTPException(status_code=404, detail="PDF not found")
    return FileResponse(pdf_path, media_type="application/pdf", filename=Path(pdf_path).name)


@router.get("/task/{task_id}/download/excel")
async def download_excel(task_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TaskRecord).where(TaskRecord.id == task_id))
    task = result.scalar_one_or_none()
    if not task or task.status != "completed":
        raise HTTPException(status_code=404, detail="Task not completed or not found")
    if not task.result or not task.result.get("human_approved"):
        raise HTTPException(status_code=409, detail="Report requires human review and approval")
    excel_path = task.result.get("excel_path", "") if task.result else ""
    if not excel_path or not Path(excel_path).exists():
        raise HTTPException(status_code=404, detail="Excel file not found")
    return FileResponse(
        excel_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=Path(excel_path).name,
    )


class CalcRequest(BaseModel):
    expression: str


class TCORequest(BaseModel):
    initial: float
    annual_maintenance: float
    years: int
    other_costs: Optional[float] = 0.0


class CompareNumericRequest(BaseModel):
    values: Dict[str, float]


@router.post("/calculate")
def calculate(req: CalcRequest):
    result = safe_calculate(req.expression)
    return {"expression": req.expression, "result": result}


@router.post("/tco")
def tco(req: TCORequest):
    return compute_tco({
        "initial": req.initial,
        "annual_maintenance": req.annual_maintenance,
        "years": req.years,
        "other_costs": req.other_costs,
    })


@router.post("/compare-numeric")
def compare_numeric(req: CompareNumericRequest):
    return compare_numeric_values(req.values)
