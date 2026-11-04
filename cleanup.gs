/**
 * Образы — ИЗОЛИРОВАННЫЙ тест очистки временных файлов.
 * Не подключён к app.py и не изменяет журнал заказов.
 *
 * Установка: вставить этот файл в ТОТ ЖЕ проект Apps Script,
 * включить Сервисы -> Drive API (расширенный сервис),
 * затем выполнить cleanupSetup() и подтвердить разрешения.
 *
 * ВАЖНО: удаляет НАВСЕГДА только файлы с префиксом OBR_TMP_
 * внутри специально созданной папки, ID которой хранится
 * в свойствах скрипта. Не использовать папку с другими файлами.
 */
const CLEANUP_TEST_TTL_MS = 2 * 60 * 1000;
const CLEANUP_PREFIX = 'OBR_TMP_';
const CLEANUP_FOLDER_PROP = 'OBR_CLEANUP_TEST_FOLDER_ID';
const CLEANUP_DELETED_PROP = 'OBR_CLEANUP_TEST_DELETED_TOTAL';
const CLEANUP_LAST_PROP = 'OBR_CLEANUP_TEST_LAST_RUN';

function cleanupFolder_() {
  const props = PropertiesService.getScriptProperties();
  const id = props.getProperty(CLEANUP_FOLDER_PROP);
  if (!id) throw Error('Run cleanupSetup() first');
  return DriveApp.getFolderById(id);
}

function cleanupSetup() {
  const props = PropertiesService.getScriptProperties();
  let id = props.getProperty(CLEANUP_FOLDER_PROP);
  let folder;
  if (id) {
    folder = DriveApp.getFolderById(id);
  } else {
    folder = DriveApp.createFolder('Образы — ТЕСТ временного хранения');
    props.setProperty(CLEANUP_FOLDER_PROP, folder.getId());
    props.setProperty(CLEANUP_DELETED_PROP, '0');
  }
  const exists = ScriptApp.getProjectTriggers()
    .some(t => t.getHandlerFunction() === 'cleanupExpiredFiles');
  if (!exists) {
    ScriptApp.newTrigger('cleanupExpiredFiles').timeBased().everyMinutes(1).create();
  }
  Logger.log('Test folder: ' + folder.getUrl() + '; trigger installed: true');
  return folder.getUrl();
}

/** Создаёт тестовый файл с фиктивными данными (НЕ результат исследования). */
function cleanupCreateTestFile() {
  const folder = cleanupFolder_();
  const expiry = Date.now() + CLEANUP_TEST_TTL_MS;
  const name = CLEANUP_PREFIX + expiry + '_' + Utilities.getUuid() + '.txt';
  const file = folder.createFile(name, 'TEST ONLY: fake ciphertext, no user data', MimeType.PLAIN_TEXT);
  Logger.log('Created: ' + file.getId() + '; expires: ' + new Date(expiry).toISOString());
  return file.getId();
}

/** Проверяет истечение срока и удаляет навсегда, НЕ перемещая в корзину. */
function cleanupExpiredFiles() {
  const folder = cleanupFolder_();
  const files = folder.getFiles();
  const now = Date.now();
  let removed = 0, active = 0, expired = 0, errors = 0;
  while (files.hasNext()) {
    const file = files.next();
    const match = /^OBR_TMP_(\d{13})_(?:[0-9a-f-]+|[A-Za-z0-9-]+_(?:profile|compatibility)_[0-9a-f-]+)\.txt$/i.exec(file.getName());
    if (!match) continue; // чужие файлы не трогаем
    if (Number(match[1]) > now) { active++; continue; }
    expired++;
    try {
      // Требуется включить расширенный сервис Google Drive API.
      Drive.Files.remove(file.getId());
      removed++;
    } catch (err) {
      errors++;
      Logger.log('Delete failed for ' + file.getId() + ': ' + err);
    }
  }
  const props = PropertiesService.getScriptProperties();
  props.setProperty(CLEANUP_DELETED_PROP,
    String(Number(props.getProperty(CLEANUP_DELETED_PROP) || '0') + removed));
  props.setProperty(CLEANUP_LAST_PROP, new Date().toISOString());
  const result = {active, expired, removed, errors,
    deletedTotal: Number(props.getProperty(CLEANUP_DELETED_PROP))};
  Logger.log(JSON.stringify(result));
  return result;
}

/** Счётчик: запустить вручную в редакторе Apps Script. */
function cleanupStatus() {
  const files = cleanupFolder_().getFiles();
  const now = Date.now();
  let active = 0, expired = 0;
  while (files.hasNext()) {
    const name = files.next().getName();
    const m = /^OBR_TMP_(\d{13})_(?:[0-9a-f-]+|[A-Za-z0-9-]+_(?:profile|compatibility)_[0-9a-f-]+)\.txt$/i.exec(name);
    if (!m) continue;
    if (Number(m[1]) <= now) expired++; else active++;
  }
  const props = PropertiesService.getScriptProperties();
  const result = {active, expired,
    deletedTotal: Number(props.getProperty(CLEANUP_DELETED_PROP) || '0'),
    lastRun: props.getProperty(CLEANUP_LAST_PROP) || 'never',
    ttlMinutes: CLEANUP_TEST_TTL_MS / 60000};
  Logger.log(JSON.stringify(result));
  return result;
}

/**
 * Временное хранилище: только зашифрованные данные.
 * Вызов ТОЛЬКО из авторизованного run(p) в Код.gs; не публиковать
 * отдельный незащищённый endpoint.
 * recovery_hash = SHA-256 секретного токена, полученного в Streamlit.
 * payload = Fernet-токен (шифрование в Streamlit, ключ на сервере Streamlit).
 */
function temporaryResult_(p) {
  const action = String(p.action || '');
  const order = checkCode(p.order_id);
  const kind = checkCode(p.operation);
  if (!['profile','compatibility'].includes(kind)) throw Error('invalid_operation');
  const accessHash = String(p.recovery_hash || '');
  if (!/^[a-f0-9]{64}$/.test(accessHash)) throw Error('invalid_recovery_hash');
  const folder = cleanupFolder_();
  const now = Date.now();
  const prefix = CLEANUP_PREFIX;
  // Имя содержит только код заказа, тип результата и случайный UUID.
  const files = folder.getFiles();
  let matchFile = null, matchExpiry = 0;
  while (files.hasNext()) {
    const f = files.next();
    const match = /^OBR_TMP_(\d{13})_([A-Za-z0-9-]+)_(profile|compatibility)_([a-f0-9-]{36})\.txt$/i.exec(f.getName());
    if (!match || match[2] !== order || match[3] !== kind) continue;
    if (matchFile) throw Error('duplicate_result_files');
    matchFile = f; matchExpiry = Number(match[1]);
  }
  if (action === 'temp_save') {
    if (matchFile) throw Error('result_already_exists');
    const orderSheet = sheet('Заказы');
    const row = findRow(orderSheet, order);
    if (!row) throw Error('order_not_found');
    const orderData = orderSheet.getRange(row, 1, 1, 12).getValues()[0];
    if (String(orderData[8]) !== 'completed') throw Error('order_not_completed');
    const payload = String(p.ciphertext || '');
    if (!/^[A-Za-z0-9_=-]{40,250000}$/.test(payload)) throw Error('invalid_ciphertext');
    const expiry = now + CLEANUP_TEST_TTL_MS;
    const filename = prefix + expiry + '_' + order + '_' + kind + '_' + Utilities.getUuid() + '.txt';
    const file = folder.createFile(filename, JSON.stringify({accessHash, payload}), MimeType.PLAIN_TEXT);
    return {ok:true,expires_at_ms:expiry};
  }
  if (action === 'temp_get') {
    if (!matchFile || now >= matchExpiry) return {ok:true,status:'expired'};
    const data = JSON.parse(matchFile.getBlob().getDataAsString('UTF-8'));
    // Проверяем хеш без раскрытия содержимого файла.
    if (data.accessHash !== accessHash) throw Error('access_denied');
    return {ok:true,status:'available',ciphertext:data.payload,expires_at_ms:matchExpiry};
  }
  throw Error('unknown_temporary_action');
}


/**
 * Изолированная проверка temp_save/temp_get.
 * Создаёт отдельный фиктивный заказ в журнале; реальных заказов не меняет.
 * Проверяет передачу ФИКТИВНОГО шифротекста, но НЕ криптографию Fernet.
 * Запускать вручную в Apps Script: cleanupTestTemporaryResult().
 */
function cleanupTestTemporaryResult() {
  const id = 'OBR-TEST-' + Utilities.getUuid();
  const secret = Utilities.getUuid() + Utilities.getUuid();
  const hashBytes = Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256, secret);
  const hash = hashBytes.map(b => ('0' + (b & 255).toString(16)).slice(-2)).join('');
  // Допустимый по формату, но не настоящий Fernet-токен.
  const fakeCiphertext = 'gAAAAAB' + Utilities.getUuid().replace(/-/g, '') +
    Utilities.getUuid().replace(/-/g, '') + '==';

  run({action:'create_order', order_id:id, tariff:'test', amount_rub:0});
  run({action:'update_order', order_id:id, service_status:'completed'});
  const saved = run({action:'temp_save', order_id:id,
    operation:'profile', recovery_hash:hash, ciphertext:fakeCiphertext});
  const loaded = run({action:'temp_get', order_id:id,
    operation:'profile', recovery_hash:hash});
  if (!saved.ok || !loaded.ok || loaded.status !== 'available' ||
      loaded.ciphertext !== fakeCiphertext) throw Error('roundtrip_failed');

  let denied = false;
  try {
    run({action:'temp_get', order_id:id, operation:'profile',
      recovery_hash:'0'.repeat(64)});
  } catch (err) {
    denied = String(err.message || err) === 'access_denied';
  }
  if (!denied) throw Error('wrong_secret_not_denied');

  const result = {ok:true, test_order_id:id, save:'passed',
    restore:'passed', wrong_secret:'denied',
    expires_at:new Date(saved.expires_at_ms).toISOString(),
    note:'Mock ciphertext only; real encryption not tested'};
  Logger.log(JSON.stringify(result));
  return result;
}


/** Проверить истечение срока для последнего фиктивного заказа из теста. */
function cleanupTestExpiredResult() {
  const s = sheet('Заказы');
  const last = s.getLastRow();
  if (last < 2) throw Error('no_test_orders');
  const ids = s.getRange(2, 1, last - 1, 1).getValues();
  let id = '';
  for (let i = ids.length - 1; i >= 0; i--) {
    if (String(ids[i][0]).startsWith('OBR-TEST-')) {
      id = String(ids[i][0]); break;
    }
  }
  if (!id) throw Error('no_test_orders');
  // Для истёкшего файла хеш не требуется: temp_get возвращает expired
  // до проверки секрета. Для ещё действующего файла это будет access_denied.
  const response = run({action:'temp_get', order_id:id,
    operation:'profile', recovery_hash:'0'.repeat(64)});
  if (response.status !== 'expired') throw Error('expired_result_still_available');
  const result = {ok:true, test_order_id:id, expired_access:'denied'};
  Logger.log(JSON.stringify(result));
  return result;
}
