# UDO AI Microservice (Google Cloud Run + Vertex AI)

บริการ Microservice สำหรับประมวลผลคำตอบ AI Overview สไตล์ Google เชื่อมโยงกับ Google Vertex AI (Gemini 1.5 Flash) และคลังสินค้าของ UDO Trading

---

## 1. วิธี Deploy ขึ้น Google Cloud Run (คำสั่งเดียว)

เปิด Terminal ในโฟลเดอร์นี้ แล้วรันคำสั่ง:

```bash
gcloud run deploy udo-ai-service \
  --source . \
  --region asia-southeast1 \
  --allow-unauthenticated
```

หรือรันสคริปต์อัตโนมัติ:
```bash
./deploy.sh
```

เมื่อสั่ง Deploy เสร็จสิ้น คุณจะได้รับ **Service URL** เช่น:
`https://udo-ai-service-xxxxxxxx-as.a.run.app`

---

## 2. วิธีเชื่อมต่อกับเว็บไซต์ UDO (PHP Gateway)

นำ URL ที่ได้จาก Cloud Run ไปใส่ในไฟล์ `frontend/public/api/config.php`:

```php
define('CLOUD_RUN_URL', 'https://udo-ai-service-xxxxxxxx-as.a.run.app');
```

เมื่อใส่แล้ว หน้าเว็บจะยิงผ่าน PHP ไปดึงคำตอบสดๆ จาก Cloud Run ทันที!

---

## 3. การทดสอบในเครื่อง Local (หากต้องการ)

```bash
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8080
```

ทดสอบยิงค้นหา:
`http://localhost:8080/api/ai-search?q=ลวดเชื่อมสแตนเลส`

---

## 4. โครงสร้างไฟล์ในโฟลเดอร์นี้

* `main.py`: ระบบ FastAPI รับคำขอ คุยกับ Vertex AI และส่งออก JSON
* `knowledge.py`: ระบบค้นหาและสกัดสินค้า UDO จากแคตตาล็อก 1,356 ชิ้น
* `data/udo_catalog_index.json`: ฐานข้อมูลสินค้า UDO ที่คลีนแล้ว
* `Dockerfile`: คอนฟิกคอนเทนเนอร์สำหรับ Cloud Run
* `requirements.txt`: รายการแพ็กเกจ Python
* `deploy.sh`: สคริปต์คำสั่ง Deploy
