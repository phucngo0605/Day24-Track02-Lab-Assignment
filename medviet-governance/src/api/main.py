# src/api/main.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import JSONResponse
import pandas as pd
from src.access.rbac import get_current_user, require_permission
from src.pii.anonymizer import MedVietAnonymizer

app = FastAPI(title="MedViet Data API", version="1.0.0")
anonymizer = MedVietAnonymizer()

# --- ENDPOINT 1 ---
@app.get("/api/patients/raw")
@require_permission(resource="patient_data", action="read")
async def get_raw_patients(
    current_user: dict = Depends(get_current_user)
):
    """
    Trả về raw patient data (chỉ admin được phép).
    Load từ data/raw/patients_raw.csv
    Trả về 10 records đầu tiên dưới dạng JSON.
    """
    try:
        df = pd.read_csv("data/raw/patients_raw.csv")
        return JSONResponse(content=df.head(10).to_dict(orient="records"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- ENDPOINT 2 ---
@app.get("/api/patients/anonymized")
@require_permission(resource="training_data", action="read")
async def get_anonymized_patients(
    current_user: dict = Depends(get_current_user)
):
    """
    Trả về anonymized data (ml_engineer và admin được phép).
    Load raw data → anonymize → trả về JSON.
    """
    try:
        df = pd.read_csv("data/raw/patients_raw.csv")
        df_anon = anonymizer.anonymize_dataframe(df)
        return JSONResponse(content=df_anon.head(10).to_dict(orient="records"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- ENDPOINT 3 ---
@app.get("/api/metrics/aggregated")
@require_permission(resource="aggregated_metrics", action="read")
async def get_aggregated_metrics(
    current_user: dict = Depends(get_current_user)
):
    """
    Trả về aggregated metrics (data_analyst, ml_engineer, admin).
    Ví dụ: số bệnh nhân theo từng loại bệnh (không có PII).
    """
    try:
        df = pd.read_csv("data/raw/patients_raw.csv")
        metrics = {
            "total_patients": len(df),
            "disease_distribution": df["benh"].value_counts().to_dict(),
            "avg_test_result": float(df["ket_qua_xet_nghiem"].mean()),
            "age_groups": {
                "18-30": len(df[df["ngay_sinh"].str.contains("199[4-9]|200[0-8]", na=False)]),
                "31-50": len(df[df["ngay_sinh"].str.contains("197[4-9]|198[0-9]|199[0-3]", na=False)]),
                "51+": len(df[df["ngay_sinh"].str.contains("19[0-6][0-9]|197[0-3]", na=False)])
            }
        }
        return JSONResponse(content=metrics)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- ENDPOINT 4 ---
@app.delete("/api/patients/{patient_id}")
@require_permission(resource="patient_data", action="delete")
async def delete_patient(
    patient_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Chỉ admin được xóa. Các role khác nhận 403.
    """
    try:
        df = pd.read_csv("data/raw/patients_raw.csv")
        if patient_id not in df["patient_id"].values:
            raise HTTPException(status_code=404, detail="Patient not found")

        df = df[df["patient_id"] != patient_id]
        df.to_csv("data/raw/patients_raw.csv", index=False)

        return JSONResponse(content={
            "message": f"Patient {patient_id} deleted successfully",
            "deleted_by": current_user["username"]
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "ok", "service": "MedViet Data API"}
