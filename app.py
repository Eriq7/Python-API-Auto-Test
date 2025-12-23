from fastapi import FastAPI, Query, Form
from fastapi.responses import JSONResponse
from datetime import datetime
import copy  # ✅ NEW

app = FastAPI()

def resp(status: int, message: str, data=None):
    """
    测试在读: status + message
    额外返回 status_code + msg 只是兼容，不影响测试
    """
    payload = {
        "status": status,
        "message": message,
        "status_code": status,
        "msg": message,
    }
    if data is not None:
        payload["data"] = data
    return JSONResponse(status_code=200, content=payload)

# ====== 内存数据（为触发用例 07/08 设计）======
EVENTS = [
    # 用例 01/02 必须能查到
    {"eid": 1, "name": "红米", "limit": 100, "address": "北京", "start_time": "2024-01-01 10:00:00"},
    # 用例 07：eid=3 已存在 -> 10022 + "event id already exists"
    {"eid": 3, "name": "华为荣耀8发布会", "limit": 2000, "address": "深圳福田会展中心", "start_time": "2018-12-10 12:00:00"},
    # 用例 08：name 已存在（但 eid=10 不能存在，否则会先触发 10022）
    {"eid": 11, "name": "红米Pro发布会", "limit": 2000, "address": "北京会展中心", "start_time": "2018-12-10 12:00:00"},
]

GUESTS = [
    # 用例 11/12：eid=1 必须能查到（phone 为空字符串也应 success）
    {"eid": 1, "realname": "张三", "phone": "13355557777", "email": "a@b.com"},
]

# ✅ NEW: 固定初始快照（用于 reset）
EVENTS_INIT = copy.deepcopy(EVENTS)
GUESTS_INIT = copy.deepcopy(GUESTS)

# ✅ NEW: reset endpoint（CI/重复运行稳定）
@app.post("/api/test/reset")
def test_reset():
    global EVENTS, GUESTS
    EVENTS = copy.deepcopy(EVENTS_INIT)
    GUESTS = copy.deepcopy(GUESTS_INIT)
    return resp(200, "reset success")

# ====== 1) get_event_list ======
@app.get("/api/get_event_list/")
def get_event_list(
    eid: str = Query(default=None),
    name: str = Query(default=None),
):
    # 用例 03：eid 和 name 都空
    if (eid is None or eid == "") and (name is None or name == ""):
        return resp(10021, "parameter error")

    # 按 eid 查
    if eid not in (None, ""):
        result = [e for e in EVENTS if str(e["eid"]) == str(eid)]
    # 按 name 查
    elif name not in (None, ""):
        result = [e for e in EVENTS if e["name"] == name]
    else:
        result = []

    # 用例 04/05：查不到
    if not result:
        return resp(10022, "query result is empty")

    # 用例 01/02：success
    return resp(200, "success", result)

# ====== 2) add_event ======
@app.post("/api/add_event/")
def add_event(
    eid: str = Form(...),
    name: str = Form(...),
    limit: str = Form(...),
    address: str = Form(...),
    start_time: str = Form(...),
):
    # 用例 06：空参数
    if not all([eid, name, limit, address, start_time]):
        return resp(10021, "parameter error")

    # 用例 07：eid 已存在 -> 10022
    if any(str(e["eid"]) == str(eid) for e in EVENTS):
        return resp(10022, "event id already exists")

    # 用例 08：name 已存在 -> 10023
    if any(e["name"] == name for e in EVENTS):
        return resp(10023, "event name already exists")

    # 用例 09：时间格式错误 -> 10024 + 固定文案
    try:
        datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
    except Exception:
        return resp(10024, "start_time format error. It must be in YYYY-MM-DD HH:MM:SS format.")

    # 用例 10：成功 -> 200 + add event success
    EVENTS.append({
        "eid": int(eid),
        "name": name,
        "limit": limit,
        "address": address,
        "start_time": start_time,
    })
    return resp(200, "add event success")

# ====== 3) get_guest_list ======
@app.get("/api/get_guest_list/")
def get_guest_list(
    eid: str = Query(default=None),
    phone: str = Query(default=None),
):
    # 用例 13：eid 为空（不管 phone） -> 10021 + "eid cannot be empty"
    if eid is None or eid == "":
        return resp(10021, "eid cannot be empty")

    # 用例 12：phone="" 当作没传
    phone_eff = None if phone in (None, "") else str(phone)

    result = [g for g in GUESTS if str(g["eid"]) == str(eid)]
    if phone_eff is not None:
        result = [g for g in result if str(g["phone"]) == phone_eff]

    # 用例 14/15：查不到
    if not result:
        return resp(10022, "query result is empty")

    # 用例 11/12：success
    return resp(200, "success", result)
