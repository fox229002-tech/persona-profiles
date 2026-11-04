"""Тестовый журнал заказов «Образы» в Google Sheets.

Требует google-auth и requests. Не хранит тексты профилей или данные плательщиков.
Google Sheets не обеспечивает транзакционность: модуль предназначен для тестирования.
"""
import hashlib
import json
import re
import uuid
from datetime import datetime, timezone

from google.auth.transport.requests import AuthorizedSession
from google.oauth2 import service_account

HEADERS = {
    'Заказы': ['order_id','created_at_utc','tariff','amount_rub','currency','payment_id','payment_status','paid_at_utc','service_status','result_sha256','result_displayed_at_utc','updated_at_utc'],
    'События': ['event_id','order_id','event_at_utc','event_type','operation','status','result_sha256','details_code'],
}
CODE = re.compile(r'^[a-zA-Z0-9_.:-]{1,100}$')


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def sha256(data):
    return hashlib.sha256(data.encode('utf-8') if isinstance(data, str) else data).hexdigest()


class JournalError(RuntimeError):
    pass


class OrderManager:
    def __init__(self, spreadsheet_id, service_account_info):
        credentials = service_account.Credentials.from_service_account_info(
            service_account_info, scopes=['https://www.googleapis.com/auth/spreadsheets'])
        self.http = AuthorizedSession(credentials)
        self.base = f'https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/'

    @classmethod
    def from_streamlit_secrets(cls):
        import streamlit as st
        cfg = st.secrets['google_sheets']
        key = cfg['service_account_json']
        return cls(cfg['spreadsheet_id'], json.loads(key) if isinstance(key, str) else dict(key))

    def _api(self, method, path, *, params=None, body=None):
        try:
            r = self.http.request(method, self.base + path, params=params, json=body, timeout=15)
            r.raise_for_status()
            return r.json()
        except Exception as exc:
            raise JournalError('Google Sheets недоступен или отклонил запрос') from exc

    def _rows(self, tab):
        return self._api('GET', f'{tab}!A2:Z').get('values', [])

    def _append(self, tab, row):
        self._api('POST', f'{tab}!A1:append', params={
            'valueInputOption':'RAW', 'insertDataOption':'INSERT_ROWS'}, body={'values':[row]})

    def create_order(self, tariff, amount_rub):
        """Записать заказ перед оплатой; при ошибке не переходить к оплате."""
        if not CODE.fullmatch(tariff) or type(amount_rub) is not int or amount_rub < 0:
            raise ValueError('Неверный тариф или сумма')
        order_id = 'OBR-' + uuid.uuid4().hex[:20].upper()
        t = now()
        self._append('Заказы', [order_id,t,tariff,str(amount_rub),'RUB','','created','','pending','','',t])
        return order_id

    def log_event(self, order_id, event_type, *, operation='', status='ok',
                  result=None, details_code='', event_id=None):
        """Повтор с тем же event_id подавляет последовательные дубли, но не гонки."""
        event_id = event_id or str(uuid.uuid4())
        if any(not CODE.fullmatch(v) for v in
               (event_id,order_id,event_type,operation or 'x',status,details_code or 'x')):
            raise ValueError('В журнал разрешены только короткие технические коды')
        if any(row and row[0] == event_id for row in self._rows('События')):
            return event_id
        self._append('События', [event_id,order_id,now(),event_type,operation,status,
                                sha256(result) if result is not None else '',details_code])
        return event_id

    def get_order(self, order_id):
        for row in self._rows('Заказы'):
            if row and row[0] == order_id:
                return dict(zip(HEADERS['Заказы'], (row + ['']*12)[:12]))
        return None

    def get_events(self, order_id):
        return [dict(zip(HEADERS['События'],(r+['']*8)[:8]))
                for r in self._rows('События') if len(r)>1 and r[1]==order_id]

    def update_order(self, order_id, *, payment_id=None, payment_status=None,
                     service_status=None, result=None, result_displayed=False):
        """Статус paid задавать только после серверного подтверждения провайдера."""
        for index, row in enumerate(self._rows('Заказы'), start=2):
            if row and row[0] == order_id:
                v = (row + ['']*12)[:12]
                if payment_id is not None:
                    if not CODE.fullmatch(payment_id): raise ValueError('Неверный payment_id')
                    v[5] = payment_id
                if payment_status is not None:
                    if payment_status not in ('created','pending','paid','failed','refunded'):
                        raise ValueError('Неверный payment_status')
                    v[6] = payment_status
                    if payment_status == 'paid' and not v[7]: v[7] = now()
                if service_status is not None:
                    if service_status not in ('pending','processing','completed','failed'):
                        raise ValueError('Неверный service_status')
                    v[8] = service_status
                if result is not None: v[9] = sha256(result)
                if result_displayed: v[10] = now()
                v[11] = now()
                self._api('PUT', f'Заказы!A{index}:L{index}',
                          params={'valueInputOption':'RAW'},body={'values':[v]})
                return
        raise JournalError('Заказ не найден')
