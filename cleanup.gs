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
  if (props.getProperty(CLEANUP_FOLDER_PROP)) {
    throw Error('Test folder already configured; refusing to create another');
  }
  const folder = DriveApp.createFolder('Образы — ТЕСТ временного хранения');
  props.setProperty(CLEANUP_FOLDER_PROP, folder.getId());
  props.setProperty(CLEANUP_DELETED_PROP, '0');
  // Триггер с периодом 1 минута; запуск не гарантирован точно по минутам.
  ScriptApp.newTrigger('cleanupExpiredFiles')
    .timeBased().everyMinutes(1).create();
  Logger.log('Test folder: ' + folder.getUrl());
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
    const match = /^OBR_TMP_(\d{13})_[0-9a-f-]+\.txt$/i.exec(file.getName());
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
    const m = /^OBR_TMP_(\d{13})_[0-9a-f-]+\.txt$/i.exec(name);
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
