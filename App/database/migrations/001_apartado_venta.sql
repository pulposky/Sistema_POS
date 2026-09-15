-- =====================================================================
-- MIGRACIÓN 001 - ENTREGA DE APARTADOS EN EL POS
-- ------------------------------------------------------------
-- Objetivo: sobre una base existente, agrega la columna venta.id_apartado
-- que vincula una venta con la reserva (apartado) hecha en la web y cuya
-- entrega se realiza en el POS. NULL = venta directa; valor = entrega de
-- apartado (no descuenta limite_venta, y marca el apartado 'entregado').
-- Requiere que haya corrido antes la migración 000 (tabla apartados).
--
-- Forma de uso:
--   mysql -u <usuario> -p sena_pdv < 001_apartado_venta.sql
--
-- Es RE-EJECUTABLE (idempotente) y compatible con MySQL (information_schema
-- + PREPARE/EXECUTE; MySQL no admite IF NOT EXISTS en ALTER/CREATE INDEX).
-- =====================================================================

SET @db = DATABASE();

-- Columna venta.id_apartado (NULL = venta directa; no NULL = entrega de apartado)
SET @sql = IF(
  (SELECT COUNT(*) FROM information_schema.COLUMNS
   WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'venta' AND COLUMN_NAME = 'id_apartado') = 0,
  'ALTER TABLE `venta` ADD COLUMN `id_apartado` INT DEFAULT NULL AFTER `notas`',
  'SELECT 0'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- FK de la venta hacia el apartado (la columna y la tabla ya deben existir)
SET @sql = IF(
  (SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS
   WHERE CONSTRAINT_SCHEMA = @db AND TABLE_NAME = 'venta'
     AND CONSTRAINT_NAME = 'fk_venta_apartado' AND CONSTRAINT_TYPE = 'FOREIGN KEY') = 0,
  'ALTER TABLE `venta` ADD CONSTRAINT `fk_venta_apartado` FOREIGN KEY (`id_apartado`) REFERENCES `apartados`(`id_apartado`) ON DELETE SET NULL ON UPDATE CASCADE',
  'SELECT 0'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Índice para acelerar la búsqueda por apartado
SET @sql = IF(
  (SELECT COUNT(*) FROM information_schema.STATISTICS
   WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'venta' AND INDEX_NAME = 'idx_venta_apartado') = 0,
  'CREATE INDEX `idx_venta_apartado` ON `venta`(`id_apartado`)',
  'SELECT 0'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;
