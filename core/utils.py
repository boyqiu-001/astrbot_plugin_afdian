from __future__ import annotations

from datetime import datetime
from typing import Any


def format_time(timestamp: Any) -> str | None:
    """格式化时间戳为日期时间字符串。"""
    if timestamp in (None, "", 0, "0"):
        return None

    try:
        return datetime.fromtimestamp(int(timestamp)).strftime("%Y-%m-%d %H:%M:%S")
    except (TypeError, ValueError, OSError):
        return str(timestamp)


def has_custom_order_id(value: Any) -> bool:
    """递归判断 payload 中是否存在 custom_order_id 字段。"""
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key).lower() == "custom_order_id":
                return True
            if has_custom_order_id(child):
                return True
        return False

    if isinstance(value, list):
        return any(has_custom_order_id(item) for item in value)

    return False


def parse_order(order: dict[str, Any], payload: dict[str, Any] | None = None) -> str:
    """解析订单数据，生成摘要图片文本。"""
    custom_exists = has_custom_order_id(payload if payload is not None else order)

    fields = {
        "交易号": order.get("out_trade_no"),
        "计划标题": order.get("plan_title"),
        "用户名": order.get("user_name"),
        "用户ID": order.get("user_id"),
        "计划ID": order.get("plan_id"),
        "时长": f"{order['month']}个月" if order.get("month") else None,
        "总金额": order.get("total_amount"),
        "展示金额": order.get("show_amount"),
        "订单状态": order.get("status"),
        "产品类型": order.get("product_type"),
        "折扣": order.get("discount"),
        "备注": order.get("remark"),
        "兑换码ID": order.get("redeem_id"),
        "是否存在custom_order_id": "是" if custom_exists else "否",
        "创建时间": format_time(order.get("create_time")),
    }

    lines = ["📦 订单信息："]
    lines.extend(
        f"- {key}: {value}"
        for key, value in fields.items()
        if value not in (None, "", "N/A")
    )

    sku_detail = order.get("sku_detail", [])
    sku_lines = [
        (
            f"  - {sku.get('name', '未知')} × {sku.get('count', 'N/A')} "
            f"(SKU ID: {sku.get('sku_id', 'N/A')})"
        )
        for sku in sku_detail
        if isinstance(sku, dict) and any(sku.get(key) for key in ("name", "count", "sku_id"))
    ]
    if sku_lines:
        lines.append("- SKU 列表：")
        lines.extend(sku_lines)

    return "\n".join(lines)


def parse_sponsors(data: dict[str, Any]) -> list[str]:
    """解析赞助者数据，生成摘要图片文本。"""
    formatted_list: list[str] = []

    for item in data.get("list", []):
        user = item.get("user", {})
        current = item.get("current_plan", {})

        sponsor_info = {
            "name": user.get("name", ""),
            "user_id": user.get("user_id", ""),
            "total_amount": float(item.get("all_sum_amount", 0) or 0),
            "current_plan": {
                "name": current.get("name", ""),
                "price": float(current.get("price", 0) or 0),
            },
            "first_pay": format_time(item.get("first_pay_time")),
            "last_pay": format_time(item.get("last_pay_time")),
        }

        lines = [
            f"🎉 赞助主体： {sponsor_info['name']}（ID: {sponsor_info['user_id']}）\n",
            f"📦 赞助方案：{sponsor_info['current_plan']['name']}（{sponsor_info['current_plan']['price']:.2f}）元\n",
            f"📆 首次赞助：{sponsor_info['first_pay'] or 'N/A'}\n",
            f"📆 最近赞助：{sponsor_info['last_pay'] or 'N/A'}\n",
            f"💰 总计赞助：{sponsor_info['total_amount']:.2f}元",
        ]

        formatted_list.append("\n".join(lines))

    return formatted_list
