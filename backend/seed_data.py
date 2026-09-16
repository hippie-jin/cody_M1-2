"""
data/btc_usd_365d.csv 를 읽어 Firestore 'data' 컬렉션에 초기 데이터를 넣는 스크립트.

실행 방법:
    cd backend
    source venv/bin/activate
    python seed_data.py
"""

import csv
from pathlib import Path

from firebase_client import get_db

CSV_PATH = Path(__file__).resolve().parent.parent / "data" / "btc_usd_365d.csv"


def main():
    db = get_db()
    collection = db.collection("data")

    if list(collection.limit(1).stream()):
        answer = input("이미 데이터가 존재합니다. 계속 추가하시겠습니까? (y/N): ")
        if answer.lower() != "y":
            print("중단합니다.")
            return

    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    print(f"{len(rows)}개 데이터를 업로드합니다...")
    batch = db.batch()
    for i, row in enumerate(rows, start=1):
        doc_ref = collection.document()
        batch.set(
            doc_ref,
            {"date": row["date"], "value": float(row["price_usd"]), "memo": None},
        )
        if i % 400 == 0:
            batch.commit()
            batch = db.batch()
    batch.commit()
    print("완료되었습니다.")


if __name__ == "__main__":
    main()
