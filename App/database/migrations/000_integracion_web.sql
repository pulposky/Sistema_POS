-- =====================================================================
-- MIGRACIÓN 000 - INTEGRACIÓN CON MARKETPLACE WEB
-- ------------------------------------------------------------
-- Objetivo: sobre una base POS existente y ya en uso, agrega lo que el
-- Marketplace web (https://github.com/pulposky/Marketplace) necesita:
--   * Columnas de producto: descripcion, categoria, limite_venta
--   * Tabla: apartados (reservas de la web) + índices
--
-- Forma de uso (sobre una base POS creada antes o en una BD existente):
--   mysql -u <usuario> -p sena_pdv < 000_integracion_web.sql
--
-- Es RE-EJECUTABLE (idempotente) y compatible con MySQL: NO usa
-- `IF NOT EXISTS` en ALTER TABLE (MySQL no lo soporta), sino
-- information_schema + PREPARE/EXECUTE.
-- =====================================================================

SET @db = DATABASE();

-- Columna producto.descripcion (solo si no existe)
SET @sql = IF(
  (SELECT COUNT(*) FROM information_schema.COLUMNS
   WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'producto' AND COLUMN_NAME = 'descripcion') = 0,
  'ALTER TABLE `producto` ADD COLUMN `descripcion` TEXT DEFAULT NULL',
  'SELECT 0'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Columna producto.categoria (solo si no existe)
SET @sql = IF(
  (SELECT COUNT(*) FROM information_schema.COLUMNS
   WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'producto' AND COLUMN_NAME = 'categoria') = 0,
  'ALTER TABLE `producto` ADD COLUMN `categoria` VARCHAR(100) DEFAULT ''Otros''',
  'SELECT 0'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Columna producto.limite_venta (la web controla el stock en línea;
-- el POS solo usa producto.stock para el inventario físico)
SET @sql = IF(
  (SELECT COUNT(*) FROM information_schema.COLUMNS
   WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'producto' AND COLUMN_NAME = 'limite_venta') = 0,
  'ALTER TABLE `producto` ADD COLUMN `limite_venta` INT NOT NULL DEFAULT 0',
  'SELECT 0'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- ------------------------------------------------------------
-- Tabla: apartados (reservas de la web)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `apartados` (
  `id_apartado` INT AUTO_INCREMENT PRIMARY KEY,
  `nombre_cliente` VARCHAR(255) NOT NULL,
  `producto` INT NOT NULL,
  `cantidad` INT NOT NULL DEFAULT 1,
  `estado` ENUM('pendiente', 'confirmado', 'cancelado', 'entregado') NOT NULL DEFAULT 'pendiente',
  `cancelado_por` ENUM('admin', 'cliente') DEFAULT NULL,
  `fecha` DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`producto`) REFERENCES `producto`(`id_producto`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Índices de la tabla apartados (solo si no existen)
SET @sql = IF(
  (SELECT COUNT(*) FROM information_schema.STATISTICS
   WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'apartados' AND INDEX_NAME = 'idx_apartados_estado') = 0,
  'CREATE INDEX `idx_apartados_estado` ON `apartados`(`estado`)',
  'SELECT 0'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @sql = IF(
  (SELECT COUNT(*) FROM information_schema.STATISTICS
   WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'apartados' AND INDEX_NAME = 'idx_apartados_cliente') = 0,
  'CREATE INDEX `idx_apartados_cliente` ON `apartados`(`nombre_cliente`)',
  'SELECT 0'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;
