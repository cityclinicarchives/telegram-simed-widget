import os
import re
from typing import Any, Dict, List

import requests
import urllib3
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Убираем возможные битые настройки SSL/прокси из окружения Windows
os.environ.pop("SSL_CERT_FILE", None)
os.environ.pop("REQUESTS_CA_BUNDLE", None)
os.environ.pop("CURL_CA_BUNDLE", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ.pop("HTTP_PROXY", None)

load_dotenv()

SIMED_MEDORG_ID = int(os.getenv("SIMED_MEDORG_ID", "20"))
SIMED_BRANCH_ID = int(os.getenv("SIMED_BRANCH_ID", "1"))
SIMED_BASE_URL = "https://inetreception.simplex48.ru/api/Web"
SIMED_SITE_URL = "https://inetreception.simplex48.ru/"
RECAPTCHA_SITE_KEY = os.getenv("RECAPTCHA_SITE_KEY", "")

app = FastAPI(title="Telegram Simed Booking Backend")

app.mount("/webapp", StaticFiles(directory="webapp", html=True), name="webapp")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def simed_headers() -> Dict[str, str]:
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": SIMED_SITE_URL,
    }


def simed_session() -> requests.Session:
    session = requests.Session()
    session.trust_env = False
    return session


def simed_get(url: str):
    session = simed_session()
    return session.get(
        url,
        headers=simed_headers(),
        timeout=30,
        verify=False,
    )


def simed_post_json(url: str, payload: dict):
    session = simed_session()
    return session.post(
        url,
        json=payload,
        headers=simed_headers(),
        timeout=30,
        verify=False,
    )


def simed_post_form(url: str, payload: dict):
    session = simed_session()

    # прогрев сессии
    session.get(
        SIMED_SITE_URL,
        headers=simed_headers(),
        timeout=30,
        verify=False,
    )

    headers = simed_headers()
    headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"

    return session.post(
        url,
        data=payload,
        headers=headers,
        timeout=30,
        verify=False,
    )


def normalize_phone(phone: str) -> str:
    digits = re.sub(r"\D", "", phone or "")

    if len(digits) == 11 and digits.startswith("7"):
        return digits[1:]

    if len(digits) == 11 and digits.startswith("8"):
        return digits[1:]

    return digits


class WorkerCellsRequest(BaseModel):
    worker_id: int
    doctor_id: int
    date_start: str
    date_end: str


class RecordDirectRequest(BaseModel):
    doctor_id: int
    worker_id: int
    date: str
    time_interval: str
    name: str
    phone: str
    recaptcha: str
    seoCode: str = ""


class ConfirmRequest(BaseModel):
    request_key: str
    code: str


@app.get("/config")
def config():
    return {
        "recaptcha_site_key": RECAPTCHA_SITE_KEY,
        "medorg_id": SIMED_MEDORG_ID,
        "branch_id": SIMED_BRANCH_ID,
    }


@app.get("/specializations")
def specializations():
    url = f"{SIMED_BASE_URL}/allspec/{SIMED_MEDORG_ID}"

    try:
        r = simed_get(url)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "stage": "specializations",
                "url": url,
                "error": repr(e),
            },
        )


@app.get("/doctors")
def doctors(spec_id: int):
    url = f"{SIMED_BASE_URL}/allmedicdesc/{SIMED_MEDORG_ID}/{SIMED_BRANCH_ID}/{spec_id}"

    try:
        r = simed_get(url)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "stage": "doctors",
                "url": url,
                "error": repr(e),
            },
        )


@app.post("/worker-cells")
def worker_cells(req: WorkerCellsRequest):
    url = f"{SIMED_BASE_URL}/WorkerCells"

    payload = {
        "medorg_id": SIMED_MEDORG_ID,
        "branch_id": SIMED_BRANCH_ID,
        "worker_id": req.worker_id,
        "doctor_id": req.doctor_id,
        "date_start": req.date_start,
        "date_end": req.date_end,
    }

    try:
        r = simed_post_json(url, payload)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "stage": "worker-cells",
                "url": url,
                "error": repr(e),
            },
        )

    slots: List[Dict[str, Any]] = []

    for worker in data.get("workers", []):
        for sched in worker.get("schedule", []):
            for cell in sched.get("cells", []):
                if cell.get("free") is True:
                    slots.append({
                        "date": cell.get("date"),
                        "time_start": cell.get("time_start"),
                        "time_end": cell.get("time_end"),
                        "time_interval": f"{cell.get('time_start')}-{cell.get('time_end')}",
                        "worker_id": req.worker_id,
                        "doctor_id": req.doctor_id,
                    })

    return {
        "success": data.get("success"),
        "message": data.get("message", ""),
        "slots": slots,
        "raw": data,
    }


@app.post("/record-direct")
def record_direct(req: RecordDirectRequest):
    phone = normalize_phone(req.phone)

    if len(phone) != 10:
        raise HTTPException(
            status_code=400,
            detail="Телефон должен содержать 10 цифр после +7/8"
        )

    url = f"{SIMED_BASE_URL}/recordDirect"

    payload = {
        "MEDORG_ID": str(SIMED_MEDORG_ID),
        "DOCT_ID": str(req.doctor_id),
        "BRA_ID": str(SIMED_BRANCH_ID),
        "WORK_ID": str(req.worker_id),
        "Date": req.date,
        "timeInterval": req.time_interval,
        "Name": req.name,
        "ReCaptcha": req.recaptcha,
        "Phone": phone,
        "seoCode": req.seoCode or "",
    }

    try:
        r = simed_post_form(url, payload)
        r.raise_for_status()
        text = r.text.strip().strip('"')
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "stage": "record-direct",
                "url": url,
                "error": repr(e),
            },
        )

    if text == "-1":
        return {
            "success": False,
            "request_key": None,
            "message": "СиМед отклонил заявку: -1. Чаще всего причина — reCAPTCHA site key, слот, телефон или связка doctor_id/worker_id.",
        }

    return {
        "success": True,
        "request_key": text,
    }


@app.get("/send-medorg-sms/{medorg_id}")
def send_medorg_sms(medorg_id: int):
    url = f"{SIMED_BASE_URL}/SendMedOrgSMS/{medorg_id}"

    try:
        r = simed_get(url)
        r.raise_for_status()
        return {"value": r.text.strip().strip('"')}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "stage": "send-medorg-sms",
                "url": url,
                "error": repr(e),
            },
        )


@app.get("/send-rand/{request_key}")
def send_rand(request_key: str):
    url = f"{SIMED_BASE_URL}/SendRand/{request_key}"

    try:
        r = simed_get(url)
        r.raise_for_status()
        return {"code": r.text.strip().strip('"')}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "stage": "send-rand",
                "url": url,
                "error": repr(e),
            },
        )


@app.post("/confirm")
def confirm(req: ConfirmRequest):
    url = f"{SIMED_BASE_URL}/confirmation/{req.request_key}/{req.code}"

    try:
        r = simed_get(url)
        r.raise_for_status()
        text = r.text.strip().strip('"')
        return {
            "success": text == "1",
            "raw": text,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "stage": "confirm",
                "url": url,
                "error": repr(e),
            },
        )
