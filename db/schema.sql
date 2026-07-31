-- BASE DE DATOS DEL PROYECTO INTEGRADOR
-- ESTUDIANTE: EDWIN STEBAN PULIDO ROJAS
-- PROOGRAMA: PROGRAMACIÓN BÁSICA - 442226-02 [2026-2C]
-- UNIVERSIDAD INCCA DE COLOMBIA - 2026

-- 1. CREACIÓN Y USO DE LA BASE DE DATOS
CREATE DATABASE IF NOT EXISTS inventario_calzado CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE inventario_calzado;

-- 2. Tabla: user (Unificada para autenticación y lógica de negocio)
CREATE TABLE user (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(20) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    fullname VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    role VARCHAR(30) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Inserta un usuario administrador con una contraseña hasheada ('admin')
INSERT INTO user (username, password, fullname, email, role) VALUES ('admin', 'scrypt:32768:8:1$pw1MY0jjQ2cw0HTw$4c65905189cbe24572e077c6f4f6ad4f506533260b393a4f5e6333156211bededbe5030cb7a4caa4a1a7b85c46a9d01761302a2fa4c74390071acf7f6cf90cbd', 'Administrador del Sistema', 'admin@inventory.com', 'Administrador');
INSERT INTO user (username, password, fullname, email, role) VALUES ('bodeguero', 'scrypt:32768:8:1$pw1MY0jjQ2cw0HTw$4c65905189cbe24572e077c6f4f6ad4f506533260b393a4f5e6333156211bededbe5030cb7a4caa4a1a7b85c46a9d01761302a2fa4c74390071acf7f6cf90cbd', 'Carlos Mendoza', 'carlos@bodega.com', 'Bodeguero');

-- 3. Tabla: suppliers (proveedores)
CREATE TABLE suppliers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tax_id VARCHAR(20) NOT NULL UNIQUE,
    company_name VARCHAR(120) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    address VARCHAR(150) NOT NULL,
    city VARCHAR(50) DEFAULT 'Bogotá'
);

-- 4. Tabla: materials (materias primas/insumos)
-- Incluye la clave foránea supplier_id que enlaza con suppliers
CREATE TABLE materials (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    stock_quantity DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    unit_of_measure VARCHAR(20) NOT NULL,
    supplier_id INT,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE SET NULL
);

-- 5. Tabla: finished_products (productos terminados)
CREATE TABLE finished_products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    reference VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(150) NOT NULL,
    size INT NOT NULL,
    stock_available INT NOT NULL DEFAULT 0
);

-- 6. Tabla: inventory_movements (movimientos de inventario)
-- Incluye las claves foráneas material_id y user_id
CREATE TABLE inventory_movements (
    id INT AUTO_INCREMENT PRIMARY KEY,
    material_id INT NOT NULL,
    user_id INT DEFAULT NULL,
    movement_type VARCHAR(15) NOT NULL, -- ej: 'Entrada', 'Salida'
    quantity DECIMAL(10,2) NOT NULL,
    movement_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    notes VARCHAR(255) DEFAULT NULL,
    FOREIGN KEY (material_id) REFERENCES materials(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE SET NULL
);

-- 7. Tabla: audit_log (Para el Módulo de Auditoría)
CREATE TABLE IF NOT EXISTS audit_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_name VARCHAR(50) NOT NULL,
    action VARCHAR(50) NOT NULL,
    table_name VARCHAR(50) NOT NULL,
    record_id INT,
    old_data JSON DEFAULT NULL,
    new_data JSON DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ====================================================================
-- DATOS DE PRUEBA (5 REGISTROS DE EJEMPLO PARA CADA TABLA PRINCIPAL)
-- ====================================================================


-- Inserción en: suppliers
INSERT INTO suppliers (tax_id, company_name, phone, address, city) VALUES
('900123456-1', 'Cueros del Restrepo S.A.S', '6012345678', 'Calle 18 Sur # 15-20', 'Bogotá'),
('800987654-2', 'Suelas y Tacones Bogotá', '6019876543', 'Carrera 24 # 12-45', 'Bogotá'),
('700111222-3', 'Pegantes y Sintéticos Alba', '3105556677', 'Av. Primero de Mayo # 28-10', 'Bogotá'),
('901333444-5', 'Hilos y Herrajes del Calzado', '6014445566', 'Calle 15 Sur # 14-05', 'Bogotá'),
('802555666-7', 'Distribuidora de Plantillas S.A.', '3158889900', 'Carrera 10 # 3-15', 'Bogotá');

-- Inserción en: materials
INSERT INTO materials (name, stock_quantity, unit_of_measure, supplier_id) VALUES
('Cuero napa negro', 150.50, 'Metros', 1),
('Suela de caucho Talla 40', 80.00, 'Unidades', 2),
('Pegante Boxer industrial', 25.00, 'Litros', 3),
('Hilo nylon de alta resistencia', 12.00, 'Rollos', 4),
('Herraje metálico decorativo', 500.00, 'Unidades', 4);

-- Inserción en: finished_products
INSERT INTO finished_products (reference, description, size, stock_available) VALUES
('BOT-01', 'Bota de cuero formal clásica', 38, 25),
('TEN-02', 'Tenis deportivo urbano blanco', 40, 14),
('ZAP-03', 'Zapato ejecutivo elegante negro', 41, 30),
('SAN-04', 'Sandalia de descanso para dama', 36, 18),
('MOC-05', 'Mocasín casual de gamuza café', 39, 22);

-- Inserción en: inventory_movements
INSERT INTO inventory_movements (material_id, user_id, movement_type, quantity, notes) VALUES
(1, 2, 'Entrada', 50.00, 'Compra según Factura 405'), -- user_id 2 es 'bodeguero'
(3, 2, 'Entrada', 10.00, 'Reabastecimiento local'), -- user_id 2 es 'bodeguero'
(1, 1, 'Salida', 15.50, 'Despacho a lote de producción BOT-01 por admin'), -- user_id 1 es 'admin'
(2, 2, 'Salida', 20.00, 'Entrega de suelas a taller de armado'), -- user_id 2 es 'bodeguero'
(4, 1, 'Entrada', 5.00, 'Ingreso por caja menor por admin'); -- user_id 1 es 'admin'