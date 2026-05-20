import json
import re
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


DATA_DIR = Path(__file__).resolve().parent / "data"
ORDERS_PATH = DATA_DIR / "orders.json"


@dataclass(frozen=True)
class Order:
    order_id: str
    phone: str
    customer_name: str
    origin: str
    destination: str
    carrier: str
    status: str
    last_update: str  # ISO8601
    eta: str  # ISO8601 date or datetime
    tracking_events: List[Dict[str, Any]]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def seed_orders_if_missing() -> None:
    """Create a small mock 'real order' DB on disk if absent."""
    _ensure_data_dir()
    if ORDERS_PATH.exists():
        return

    now = _now_iso()
    sample_orders: List[Order] = [
        Order(
            order_id="ORD202604130001",
            phone="13800138000",
            customer_name="张三",
            origin="上海-浦东",
            destination="北京-朝阳",
            carrier="顺丰",
            status="运输中",
            last_update=now,
            eta="2026-04-14",
            tracking_events=[
                {"time": "2026-04-13T02:10:00+00:00", "location": "上海-浦东", "event": "已揽收"},
                {"time": "2026-04-13T06:30:00+00:00", "location": "上海转运中心", "event": "已发出"},
            ],
        ),
        Order(
            order_id="ORD202604130002",
            phone="13900139000",
            customer_name="李四",
            origin="广州-天河",
            destination="深圳-南山",
            carrier="中通",
            status="派送中",
            last_update=now,
            eta="2026-04-13",
            tracking_events=[
                {"time": "2026-04-12T23:05:00+00:00", "location": "广州-天河", "event": "已揽收"},
                {"time": "2026-04-13T03:20:00+00:00", "location": "深圳分拨中心", "event": "到达"},
                {"time": "2026-04-13T07:40:00+00:00", "location": "深圳-南山", "event": "派送中"},
            ],
        ),
        Order(
            order_id="ORD202604130003",
            phone="13700137000",
            customer_name="王五",
            origin="成都-武侯",
            destination="重庆-渝中",
            carrier="圆通",
            status="已签收",
            last_update=now,
            eta="2026-04-12",
            tracking_events=[
                {"time": "2026-04-11T12:00:00+00:00", "location": "成都-武侯", "event": "已揽收"},
                {"time": "2026-04-12T05:10:00+00:00", "location": "重庆转运中心", "event": "到达"},
                {"time": "2026-04-12T09:30:00+00:00", "location": "重庆-渝中", "event": "已签收"},
            ],
        ),
    ]

    payload = {"version": 1, "generated_at": now, "orders": [asdict(o) for o in sample_orders]}
    ORDERS_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_orders() -> List[Dict[str, Any]]:
    seed_orders_if_missing()
    data = json.loads(ORDERS_PATH.read_text(encoding="utf-8"))
    orders = data.get("orders", [])
    if not isinstance(orders, list):
        return []
    return orders


def query_orders(
    *,
    order_id: Optional[str] = None,
    phone: Optional[str] = None,
    customer_name: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Query mock orders by one or more fields."""
    orders = load_orders()

    def norm(s: Optional[str]) -> str:
        return (s or "").strip().lower()

    oid = norm(order_id)
    ph = re.sub(r"\D", "", phone or "")
    nm = norm(customer_name)

    results: List[Dict[str, Any]] = []
    for o in orders:
        if oid and norm(str(o.get("order_id"))) != oid:
            continue
        if ph and re.sub(r"\D", "", str(o.get("phone", ""))) != ph:
            continue
        if nm and nm not in norm(str(o.get("customer_name", ""))):
            continue
        results.append(o)
    return results


def extract_order_query(user_text: str) -> Dict[str, Optional[str]]:
    """
    Best-effort extraction from Chinese logistics query:
    - order_id: like ORD202604130001 / SF123...
    - phone: 11-digit mainland number
    - customer_name: "张三/李四" following "姓名/收件人/客户"
    """
    text = (user_text or "").strip()

    phone_match = re.search(r"(?<!\d)(1\d{10})(?!\d)", text)
    phone = phone_match.group(1) if phone_match else None

    order_id_match = re.search(r"\b([A-Za-z]{2,6}\d{6,}|ORD\d{12,})\b", text)
    order_id = order_id_match.group(1) if order_id_match else None

    name_match = re.search(r"(?:姓名|收件人|客户)\s*[:：]?\s*([\u4e00-\u9fff]{2,4})", text)
    customer_name = name_match.group(1) if name_match else None

    return {"order_id": order_id, "phone": phone, "customer_name": customer_name}


def format_order_result(order: Dict[str, Any]) -> str:
    events = order.get("tracking_events") or []
    events_sorted = sorted(
        [e for e in events if isinstance(e, dict)],
        key=lambda e: str(e.get("time", "")),
        reverse=True,
    )
    latest = events_sorted[0] if events_sorted else {}

    lines = [
        "【真实订单查询结果（模拟库）】",
        f"- 订单号：{order.get('order_id')}",
        f"- 收件人：{order.get('customer_name')}（手机尾号{str(order.get('phone',''))[-4:]}）",
        f"- 承运商：{order.get('carrier')}",
        f"- 路线：{order.get('origin')} → {order.get('destination')}",
        f"- 当前状态：{order.get('status')}（更新时间：{order.get('last_update')}）",
        f"- 预计到达：{order.get('eta')}",
    ]

    if latest:
        lines.append(f"- 最新轨迹：{latest.get('time')}｜{latest.get('location')}｜{latest.get('event')}")
    return "\n".join(lines)

