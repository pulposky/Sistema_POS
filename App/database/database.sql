-- ============================================================
-- SCRIPT DE ESTRUCTURA DE BASE DE DATOS
-- Nombre de la Base de Datos: Personalizable (ej. pos_db, mi_tienda, etc.)
-- ============================================================

-- Reemplace "pos_db" por el nombre de base de datos que prefiera:
CREATE DATABASE IF NOT EXISTS `sena_pdv` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `sena_pdv`;

-- ------------------------------------------------------------
-- Tabla: usuarios
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `usuarios` (
  `id_usuario` INT AUTO_INCREMENT PRIMARY KEY,
  `nombre` VARCHAR(100) NOT NULL,
  `usuario` VARCHAR(50) NOT NULL UNIQUE,
  `password` VARCHAR(255) NOT NULL,
  `rol` VARCHAR(50) NOT NULL DEFAULT 'Cajero'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Usuario inicial por defecto (admin / admin123)
INSERT INTO `usuarios` (`id_usuario`, `nombre`, `usuario`, `password`, `rol`)
VALUES (1, 'Administrador del Sistema', 'admin', 'admin123', 'Administrador')
ON DUPLICATE KEY UPDATE `id_usuario`=`id_usuario`;

-- ------------------------------------------------------------
-- Tabla: clientes
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `clientes` (
  `id_cliente` INT AUTO_INCREMENT PRIMARY KEY,
  `nombre` VARCHAR(100) NOT NULL,
  `documento` VARCHAR(30) DEFAULT '',
  `direccion` VARCHAR(150) DEFAULT '',
  `telefono` VARCHAR(30) DEFAULT '',
  `rol` VARCHAR(50) DEFAULT 'Cliente'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Cliente por defecto para ventas rápidas (Consumidor Final)
INSERT INTO `clientes` (`id_cliente`, `nombre`, `documento`, `direccion`, `telefono`, `rol`)
VALUES (1, 'Cliente General', '222222222222', 'Ciudad', '0000000000', 'Cliente')
ON DUPLICATE KEY UPDATE `id_cliente`=`id_cliente`;

-- ------------------------------------------------------------
-- Tabla: proveedores
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `proveedores` (
  `id_proveedor` INT AUTO_INCREMENT PRIMARY KEY,
  `nombre` VARCHAR(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO `proveedores` (`id_proveedor`, `nombre`)
VALUES (1, 'Proveedor General')
ON DUPLICATE KEY UPDATE `id_proveedor`=`id_proveedor`;

-- ------------------------------------------------------------
-- Tabla: producto
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `producto` (
  `id_producto` INT AUTO_INCREMENT PRIMARY KEY,
  `codigo` varchar(50) NOT NULL,
  `nombre` VARCHAR(100) NOT NULL,
  `unidad` VARCHAR(20) DEFAULT 'UND',
  `lugar` VARCHAR(50) DEFAULT 'Bodega Principal',
  `precio` DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
  `categoria` VARCHAR(100) DEFAULT 'Otros',
  `stock` DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
  `limite_venta` INT NOT NULL DEFAULT 0,
  `estado` VARCHAR(50) DEFAULT 'inactivo',
  `descripcion` VARCHAR(250)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Agrega columnas a producto SOLO si no existen (compatible con MySQL,
-- que no soporta "ADD COLUMN IF NOT EXISTS"). Se usa information_schema
-- + PREPARE/EXECUTE para que sea re-ejecutable sin error.
SET @db = DATABASE();

-- producto.descripcion
SET @sql = IF(
  (SELECT COUNT(*) FROM information_schema.COLUMNS
   WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'producto' AND COLUMN_NAME = 'descripcion') = 0,
  'ALTER TABLE `producto` ADD COLUMN `descripcion` TEXT DEFAULT NULL',
  'SELECT 0'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- producto.categoria
SET @sql = IF(
  (SELECT COUNT(*) FROM information_schema.COLUMNS
   WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'producto' AND COLUMN_NAME = 'categoria') = 0,
  'ALTER TABLE `producto` ADD COLUMN `categoria` VARCHAR(100) DEFAULT ''Otros''',
  'SELECT 0'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- ------------------------------------------------------------
-- Tabla: venta
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `venta` (
  `id_venta` INT AUTO_INCREMENT PRIMARY KEY,
  `fecha` DATETIME NOT NULL,
  `total` DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
  `metodo_pago` VARCHAR(50) NOT NULL,
  `estado` VARCHAR(20) DEFAULT 'ACTIVA',
  `id_cliente` INT DEFAULT 1,
  `id_usuario` INT DEFAULT 1,
  `dinero_recibido` DECIMAL(12, 2) DEFAULT 0.00,
  `cambio` DECIMAL(12, 2) DEFAULT 0.00,
  `notas` VARCHAR(150),
  `id_apartado` INT DEFAULT NULL,
  FOREIGN KEY (`id_cliente`) REFERENCES `clientes`(`id_cliente`),
  FOREIGN KEY (`id_usuario`) REFERENCES `usuarios`(`id_usuario`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ------------------------------------------------------------
-- Tabla: detalle_venta
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `detalle_venta` (
  `id_detalle` INT AUTO_INCREMENT PRIMARY KEY,
  `id_venta` INT NOT NULL,
  `id_producto` INT NOT NULL,
  `cantidad` DECIMAL(12, 2) NOT NULL,
  `precio_unitario` DECIMAL(12, 2) NOT NULL,
  `subtotal` DECIMAL(12, 2) NOT NULL,
  FOREIGN KEY (`id_venta`) REFERENCES `venta`(`id_venta`),
  FOREIGN KEY (`id_producto`) REFERENCES `producto`(`id_producto`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ------------------------------------------------------------
-- Tabla: compras
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `compras` (
  `id_compra` INT AUTO_INCREMENT PRIMARY KEY,
  `fecha` DATETIME NOT NULL,
  `total` DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
  `id_proveedor` INT DEFAULT 1,
  `id_usuario` INT DEFAULT 1,
  `estado` VARCHAR(20) DEFAULT 'ACTIVA',
  FOREIGN KEY (`id_proveedor`) REFERENCES `proveedores`(`id_proveedor`),
  FOREIGN KEY (`id_usuario`) REFERENCES `usuarios`(`id_usuario`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ------------------------------------------------------------
-- Tabla: detalle_compras
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `detalle_compras` (
  `id_detalle` INT AUTO_INCREMENT PRIMARY KEY,
  `id_compra` INT NOT NULL,
  `id_producto` INT NOT NULL,
  `cantidad` DECIMAL(12, 2) NOT NULL,
  `precio_unitario` DECIMAL(12, 2) NOT NULL,
  `subtotal` DECIMAL(12, 2) NOT NULL,
  FOREIGN KEY (`id_compra`) REFERENCES `compras`(`id_compra`),
  FOREIGN KEY (`id_producto`) REFERENCES `producto`(`id_producto`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ------------------------------------------------------------
-- Tablas: entradas de inventario
-- Una entrada agrega existencias por ajustes, devoluciones, etc.
-- No guarda ni modifica precios o costos de los productos.
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `entradas` (
  `id_entrada` INT AUTO_INCREMENT PRIMARY KEY,
  `fecha` DATETIME NOT NULL,
  `observacion` TEXT,
  `id_usuario` INT DEFAULT 1,
  `estado` VARCHAR(20) NOT NULL DEFAULT 'ACTIVA',
  FOREIGN KEY (`id_usuario`) REFERENCES `usuarios`(`id_usuario`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `detalle_entradas` (
  `id_detalle_entrada` INT AUTO_INCREMENT PRIMARY KEY,
  `id_entrada` INT NOT NULL,
  `id_producto` INT NOT NULL,
  `cantidad` DECIMAL(12, 2) NOT NULL,
  FOREIGN KEY (`id_entrada`) REFERENCES `entradas`(`id_entrada`),
  FOREIGN KEY (`id_producto`) REFERENCES `producto`(`id_producto`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ------------------------------------------------------------
-- Tabla: remision
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `remision` (
  `id_remision` INT AUTO_INCREMENT PRIMARY KEY,
  `fecha` DATETIME NOT NULL,
  `tipo_remision` VARCHAR(50) DEFAULT 'Despacho',
  `id_cliente` INT DEFAULT 1,
  `id_usuario` INT DEFAULT 1,
  `notas` TEXT,
  `estado` VARCHAR(20) DEFAULT 'ACTIVA',
  FOREIGN KEY (`id_cliente`) REFERENCES `clientes`(`id_cliente`),
  FOREIGN KEY (`id_usuario`) REFERENCES `usuarios`(`id_usuario`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ------------------------------------------------------------
-- Tabla: detalle_remision
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `detalle_remision` (
  `id_detalle_remision` INT AUTO_INCREMENT PRIMARY KEY,
  `id_remision` INT NOT NULL,
  `id_producto` INT NOT NULL,
  `cantidad` DECIMAL(12, 2) NOT NULL,
  FOREIGN KEY (`id_remision`) REFERENCES `remision`(`id_remision`),
  FOREIGN KEY (`id_producto`) REFERENCES `producto`(`id_producto`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- INTEGRACION CON MARKETPLACE WEB
-- ============================================================
-- Este bloque sincroniza la base de datos compartida con el
-- Marketplace web (https://github.com/pulposky/Marketplace).
--
-- Si la base fue creada primero por el Marketplace, estas
-- instrucciones no alteran nada (todo usa IF NOT EXISTS).
-- Si la base fue creada primero por el POS, se agregan las
-- columnas y tablas que la web necesita para funcionar.
-- ============================================================

-- Columna que la web usa para controlar el stock en linea
-- (el POS solo usa producto.stock para el inventario fisico).
-- Se agrega solo si no existe (compatible con MySQL).
SET @db = DATABASE();
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

-- =====================================================================
-- INTEGRACIÓN CON LA WEB (compatible con MySQL: todo se agrega solo si
-- no existe, usando information_schema + PREPARE/EXECUTE para poder
-- re-ejecutar este script sin errores, tanto en base nueva como existente)
-- =====================================================================
SET @db = DATABASE();

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

-- Columna venta.id_apartado (NULL = venta directa; no NULL = entrega de apartado)
SET @sql = IF(
  (SELECT COUNT(*) FROM information_schema.COLUMNS
   WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'venta' AND COLUMN_NAME = 'id_apartado') = 0,
  'ALTER TABLE `venta` ADD COLUMN `id_apartado` INT DEFAULT NULL AFTER `notas`',
  'SELECT 0'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- FK de la venta hacia el apartado (la columna/apartados ya existen aquí)
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

-- ------------------------------------------------------------
-- Tabla: notificaciones (alertas para el admin)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `notificaciones` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `titulo` VARCHAR(255) NOT NULL,
  `mensaje` TEXT NOT NULL,
  `fecha` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `leido` TINYINT(1) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ------------------------------------------------------------
-- Tabla: page_views (registro de visitas del marketplace)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `page_views` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `ruta` VARCHAR(255) NOT NULL,
  `usuario` VARCHAR(255) DEFAULT NULL,
  `ip` VARCHAR(45) DEFAULT NULL,
  `user_agent` TEXT DEFAULT NULL,
  `fecha` DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- FIN INTEGRACION MARKETPLACE WEB
-- ============================================================

-- ------------------------------------------------------------
-- Informe de inventario calculado por movimientos.
-- Se calcula desde los documentos, sin depender de producto.stock.
-- ------------------------------------------------------------
SELECT
  p.id_producto,
  p.codigo,
  p.nombre,
  p.unidad,
  COALESCE(e.entradas, 0) + COALESCE(c.compras, 0)
    - COALESCE(v.ventas, 0) - COALESCE(r.remisiones, 0) AS stock_final
FROM producto p
LEFT JOIN (
  SELECT de.id_producto, SUM(de.cantidad) AS entradas
  FROM detalle_entradas de
  INNER JOIN entradas e ON e.id_entrada = de.id_entrada
  WHERE e.estado = 'ACTIVA'
  GROUP BY de.id_producto
) e ON e.id_producto = p.id_producto
LEFT JOIN (
  SELECT dc.id_producto, SUM(dc.cantidad) AS compras
  FROM detalle_compras dc
  INNER JOIN compras c ON c.id_compra = dc.id_compra
  WHERE c.estado = 'ACTIVA'
  GROUP BY dc.id_producto
) c ON c.id_producto = p.id_producto
LEFT JOIN (
  SELECT dv.id_producto, SUM(dv.cantidad) AS ventas
  FROM detalle_venta dv
  INNER JOIN venta v ON v.id_venta = dv.id_venta
  WHERE v.estado = 'ACTIVA'
  GROUP BY dv.id_producto
) v ON v.id_producto = p.id_producto
LEFT JOIN (
  SELECT dr.id_producto, SUM(dr.cantidad) AS remisiones
  FROM detalle_remision dr
  INNER JOIN remision r ON r.id_remision = dr.id_remision
  WHERE r.estado = 'ACTIVA'
  GROUP BY dr.id_producto
) r ON r.id_producto = p.id_producto
-- Solo muestra productos que tengan al menos una entrada activa.
WHERE COALESCE(e.entradas, 0) > 0
-- Agrupa códigos con el mismo prefijo, por ejemplo todos los LAC.
ORDER BY p.codigo ASC;
