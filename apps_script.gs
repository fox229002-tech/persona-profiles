/**
 * «Образы» — защищённый тестовый журнал заказов.
 * Откройте Google Sheets -> Расширения -> Apps Script.
 * Свойства проекта -> Свойства скрипта:
 * JOURNAL_TOKEN = длинная случайная строка (та же, что в Streamlit Secrets).
 * Развернуть -> Новое развертывание -> Веб-приложение:
 * Выполнять от моего имени; доступ: Все (Anyone).
 * Токен не добавлять в URL и не публиковать в GitHub.
 */
const SHEET_ID = '1Efm4TXFbsv9T6dVjHYmGDRDcYzKCcJIZbiGqFhVfXYA';
const ORDER_HEADERS = ['order_id','created_at_msk','tariff','amount_rub','currency','payment_id','payment_status','paid_at_msk','service_status','result_sha256','result_displayed_at_msk','updated_at_msk'];
const EVENT_HEADERS = ['event_id','order_id','event_at_msk','event_type','operation','status','result_sha256','details_code'];
const CODE = /^[A-Za-z0-9_.:-]{1,100}$/;
const RECOVERY_HASH_COLUMN = 13;
function recoveryHash_(value) {
  if (typeof value !== 'string' || !/^[a-f0-9]{64}$/.test(value)) throw Error('invalid_recovery_hash');
  return value;
}
function recoveryColumn_(s) {
  if (s.getMaxColumns() < RECOVERY_HASH_COLUMN) s.insertColumnsAfter(s.getMaxColumns(), RECOVERY_HASH_COLUMN - s.getMaxColumns());
  const header = String(s.getRange(1, RECOVERY_HASH_COLUMN).getValue());
  if (header && header !== 'recovery_hash') throw Error('recovery_column_conflict');
  if (!header) s.getRange(1, RECOVERY_HASH_COLUMN).setValue('recovery_hash');
}

function output(data) {
  return ContentService.createTextOutput(JSON.stringify(data)).setMimeType(ContentService.MimeType.JSON);
}
function checkCode(v, optional) {
  if (optional && (v === '' || v === undefined || v === null)) return '';
  if (typeof v !== 'string' || !CODE.test(v)) throw Error('invalid_code');
  return v;
}
function msk() { return Utilities.formatDate(new Date(), 'Europe/Moscow', 'dd.MM.yyyy HH:mm:ss'); }
function sheet(name) {
  const s = SpreadsheetApp.openById(SHEET_ID).getSheetByName(name);
  if (!s) throw Error('sheet_missing');
  return s;
}
function findRow(s, id) {
  const last = s.getLastRow();
  if (last < 2) return 0;
  const ids = s.getRange(2,1,last-1,1).getValues();
  for (let i=0;i<ids.length;i++) if (String(ids[i][0])===id) return i+2;
  return 0;
}
function rowObject(headers, row) {
  const o={}; headers.forEach((h,i)=>o[h]=String(row[i]??'')); return o;
}
function run(p) {
  const action = checkCode(p.action);
  if (action === 'temp_save' || action === 'temp_get') {
    return temporaryResult_(p);
  }
  if (action === 'generation_claim' || action === 'generation_finish') {
    const order = checkCode(p.order_id), op = checkCode(p.operation);
    if (!['descriptions','profile','compatibility'].includes(op)) throw Error('invalid_operation');
    const credential = recoveryHash_(p.recovery_hash);
    const orders = sheet('Заказы'), row = findRow(orders, order);
    if (!row) throw Error('order_not_found');
    recoveryColumn_(orders);
    if (String(orders.getRange(row,RECOVERY_HASH_COLUMN).getValue()) !== credential)
      throw Error('access_denied');
    const events = sheet('События'), last = events.getLastRow();
    const records = last < 2 ? [] : events.getRange(2,1,last-1,8).getValues();
    const relevant = records.filter(r => String(r[1]) === order &&
      String(r[4]) === op && ['generation_claim','generation_finish'].includes(String(r[3])));
    const latest = relevant.length ? relevant[relevant.length-1] : null;
    const claimId = checkCode(p.claim_id);
    if (action === 'generation_claim') {
      if (latest && String(latest[3]) === 'generation_finish' && String(latest[5]) === 'completed')
        return {ok:true,status:'completed'};
      if (latest && String(latest[3]) === 'generation_claim') {
        // A lease prevents parallel AI requests even across Streamlit sessions.
        const age = Date.now() - Number(latest[7]);
        if (age >= 0 && age < 10 * 60 * 1000) return {ok:true,status:'processing'};
        // After an abandoned lease, a new claim is allowed.
      }
      events.appendRow([claimId,order,msk(),'generation_claim',op,'processing','',String(Date.now())]);
      return {ok:true,status:'claimed'};
    }
    if (!latest || String(latest[3]) !== 'generation_claim' ||
        String(latest[0]) !== claimId) throw Error('claim_not_active');
    const status = checkCode(p.status);
    if (!['completed','failed','released'].includes(status)) throw Error('invalid_generation_status');
    events.appendRow([Utilities.getUuid(),order,msk(),'generation_finish',op,status,'',claimId]);
    return {ok:true,status};
  }
  if (action === 'create_order') {
    const id=checkCode(p.order_id), tariff=checkCode(p.tariff);
    if (!Number.isInteger(p.amount_rub) || p.amount_rub<0) throw Error('invalid_amount');
    const s=sheet('Заказы');
    const recoveryHash = p.recovery_hash === undefined ? '' : recoveryHash_(p.recovery_hash);
    if (recoveryHash) recoveryColumn_(s);
    const existing = findRow(s,id);
    if (existing) {
      if (recoveryHash) {
        const current = String(s.getRange(existing, RECOVERY_HASH_COLUMN).getValue());
        if (current && current !== recoveryHash) throw Error('recovery_hash_conflict');
        if (!current) s.getRange(existing, RECOVERY_HASH_COLUMN).setValue(recoveryHash);
      }
      return {ok:true,order_id:id};
    }
    const t=msk();
    s.appendRow([id,t,tariff,p.amount_rub,'RUB','','created','','pending','','',t,recoveryHash]);
    return {ok:true,order_id:id};
  }
  if (action === 'log_event') {
    const id=checkCode(p.event_id), order=checkCode(p.order_id);
    const type=checkCode(p.event_type), op=checkCode(p.operation,true);
    const status=checkCode(p.status), hash=checkCode(p.result_sha256,true);
    const details=checkCode(p.details_code,true);
    const s=sheet('События');
    if (findRow(s,id)) return {ok:true,event_id:id};
    s.appendRow([id,order,msk(),type,op,status,hash,details]);
    return {ok:true,event_id:id};
  }
  if (action === 'get_order' || action === 'get_events') {
    const id=checkCode(p.order_id);
    if (action==='get_order') {
      const s=sheet('Заказы'), r=findRow(s,id);
      return {ok:true,order:r?rowObject(ORDER_HEADERS,s.getRange(r,1,1,12).getValues()[0]):null};
    }
    const s=sheet('События'), last=s.getLastRow();
    const rows=last<2?[]:s.getRange(2,1,last-1,8).getValues();
    return {ok:true,events:rows.filter(r=>String(r[1])===id).map(r=>rowObject(EVENT_HEADERS,r))};
  }
  if (action === 'update_order') {
    const id=checkCode(p.order_id), s=sheet('Заказы'), r=findRow(s,id);
    if (!r) throw Error('order_not_found');
    const v=s.getRange(r,1,1,12).getValues()[0];
    if (p.payment_id !== undefined) v[5]=checkCode(p.payment_id);
    if (p.payment_status !== undefined) {
      if (!['created','pending','paid','failed','refunded'].includes(p.payment_status)) throw Error('invalid_payment_status');
      v[6]=p.payment_status;
      if (p.payment_status==='paid' && !v[7]) v[7]=msk();
    }
    if (p.service_status !== undefined) {
      if (!['pending','processing','completed','failed'].includes(p.service_status)) throw Error('invalid_service_status');
      v[8]=p.service_status;
    }
    if (p.result_sha256 !== undefined) v[9]=checkCode(p.result_sha256);
    if (p.result_displayed && !v[10]) v[10]=msk();
    v[11]=msk();
    s.getRange(r,1,1,12).setValues([v]);
    return {ok:true};
  }
  throw Error('unknown_action');
}
function doPost(e) {
  try {
    const p=JSON.parse(e.postData.contents);
    const token=PropertiesService.getScriptProperties().getProperty('JOURNAL_TOKEN');
    if (!token || typeof p.token!=='string' || p.token!==token) throw Error('unauthorized');
    const lock=LockService.getScriptLock();
    lock.waitLock(20000);
    try { return output(run(p)); }
    finally { lock.releaseLock(); }
  } catch (err) { return output({ok:false,error:String(err.message||err)}); }
}
