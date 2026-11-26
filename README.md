# Order Service

간단한 주문 관리 API 입니다.

## 실행

```bash
pip install -r requirements.txt
python scripts/seed.py
uvicorn app.main:app --reload
```

http://localhost:8000/docs 에서 API를 확인할 수 있습니다.

## 테스트

```bash
pytest
```

## DB 초기화

```bash
python scripts/reset_db.py
```
