"""Журнал заказов «Образы» через Google Apps Script (тестовый режим)."""
import hashlib
import re
import uuid
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import requests

CODE = re.compile(r"^[A-Za-z0-9_.:-]{1,100}$")


class JournalError(RuntimeError):
    pass


def now():
    return datetime.now(ZoneInfo("Europe/Moscow")).strftime("%d.%m.%Y %H:%M:%S")


def sha256(data):
    return hashlib.sha256(data.encode("utf-8") if isinstance(data, str) else data).hexdigest()


class OrderManager:
    def __init__(self, script_url, token, *, test_failure=None):
        if not script_url.startswith("https://script.google.com/macros/s/") or not script_url.endswith("/exec"):
            raise ValueError("Неверный адрес опубликованного Apps Script")
        if not token:
            raise ValueError("Не задан секрет журнала")
        self.url = script_url
        self.token = token
        self.test_failure = test_failure

    @classmethod
    def from_streamlit_secrets(cls):
        import streamlit as st
        cfg = st.secrets["order_journal"]
        failure = None
        if st.secrets.get("TEST_FAILURE_MODE", False):
            failure = st.session_state.get("journal_test_failure", "none")
        return cls(str(cfg["script_url"]), str(cfg["token"]), test_failure=failure)

    def _call(self, action, **fields):
        if self.test_failure == "all" or self.test_failure == action:
            raise JournalError("Тестовый сбой журнала: " + action)
        payload_request = {"token": self.token, "action": action, **fields}
        for attempt in range(3):
            try:
                response = requests.post(self.url, json=payload_request, timeout=25)
                response.raise_for_status()
                payload = response.json()
                if not isinstance(payload, dict) or not payload.get("ok"):
                    raise JournalError("Apps Script отклонил операцию: " + str(
                        payload.get("error", "unknown") if isinstance(payload, dict) else "invalid_response"))
                return payload
            except (requests.RequestException, ValueError) as exc:
                if attempt == 2:
                    raise JournalError("Нет подтверждения записи в журнал") from exc
                time.sleep(attempt + 1)

    def create_order(self, tariff, amount_rub, *, order_id=None):
        if not isinstance(tariff, str) or not CODE.fullmatch(tariff):
            raise ValueError("Неверный тариф")
        if type(amount_rub) is not int or amount_rub < 0:
            raise ValueError("Неверная сумма")
        order_id = order_id or ("OBR-" + uuid.uuid4().hex[:20].upper())
        if not CODE.fullmatch(order_id):
            raise ValueError("Неверный номер заказа")
        self._call("create_order", order_id=order_id, tariff=tariff, amount_rub=amount_rub)
        return order_id

    def log_event(self, order_id, event_type, *, operation="", status="ok",
                  result=None, details_code="", event_id=None):
        event_id = event_id or str(uuid.uuid4())
        for value in (order_id, event_type, operation or "x", status, details_code or "x", event_id):
            if not isinstance(value, str) or not CODE.fullmatch(value):
                raise ValueError("В журнале допустимы только технические коды")
        self._call("log_event", event_id=event_id, order_id=order_id,
                   event_type=event_type, operation=operation, status=status,
                   result_sha256=sha256(result) if result is not None else "",
                   details_code=details_code)
        return event_id

    def get_order(self, order_id):
        return self._call("get_order", order_id=order_id).get("order")

    def get_events(self, order_id):
        return self._call("get_events", order_id=order_id).get("events", [])

    def update_order(self, order_id, *, payment_id=None, payment_status=None,
                     service_status=None, result=None, result_displayed=False):
        fields = {"order_id": order_id, "result_displayed": bool(result_displayed)}
        if payment_id is not None:
            fields["payment_id"] = payment_id
        if payment_status is not None:
            fields["payment_status"] = payment_status
        if service_status is not None:
            fields["service_status"] = service_status
        if result is not None:
            fields["result_sha256"] = sha256(result)
        self._call("update_order", **fields)
