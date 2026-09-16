import json

import firebase_admin
from firebase_admin import credentials, firestore

import config

_app = None


def _init_app():
    global _app
    if _app is not None:
        return _app

    raw = config.FIREBASE_SERVICE_ACCOUNT_JSON
    if not raw:
        raise RuntimeError(
            "FIREBASE_SERVICE_ACCOUNT_JSON 환경 변수가 설정되지 않았습니다. "
            ".env 파일 또는 배포 환경 변수를 확인하세요."
        )

    if raw.strip().startswith("{"):
        cred = credentials.Certificate(json.loads(raw))
    else:
        cred = credentials.Certificate(raw)

    _app = firebase_admin.initialize_app(cred)
    return _app


def get_db():
    _init_app()
    return firestore.client()
