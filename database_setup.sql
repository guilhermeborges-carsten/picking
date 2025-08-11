-- =====================================================
-- SCRIPT DE CRIAÇÃO DO BANCO DE DADOS - SISTEMA PICKING
-- =====================================================

-- 1. Criar tabela de usuários
CREATE TABLE usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(100) NOT NULL,
    nome VARCHAR(100),
    cargo VARCHAR(50),
    admin BOOLEAN DEFAULT 0,
    ativo BOOLEAN DEFAULT 1
);

-- 2. Criar tabela de clientes
CREATE TABLE clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome VARCHAR(100) NOT NULL,
    codigo VARCHAR(20) UNIQUE,
    ativo BOOLEAN DEFAULT 1,
    data_cadastro DATE DEFAULT CURRENT_DATE
);

-- 3. Criar tabela de colaboradores Carsten
CREATE TABLE colaboradores_carsten (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome VARCHAR(100) NOT NULL,
    cargo VARCHAR(100) NOT NULL,
    departamento VARCHAR(100) NOT NULL,
    data_contratacao DATE NOT NULL,
    ativo BOOLEAN DEFAULT 1,
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Criar tabela de cadastros
CREATE TABLE tb_pck_arm (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data DATE NOT NULL,
    cliente_id INTEGER,
    mod_carsten VARCHAR(20),
    mod_3 VARCHAR(20),
    total_volumes VARCHAR(20),
    vol_pessoas VARCHAR(20),
    usuario_id INTEGER,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
    FOREIGN KEY (cliente_id) REFERENCES clientes(id)
);

-- 5. Criar tabela de logs do sistema
CREATE TABLE sistema_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usuario_id INTEGER,
    usuario_nome VARCHAR(100),
    acao VARCHAR(100) NOT NULL,
    modulo VARCHAR(100) NOT NULL,
    detalhes TEXT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

-- 6. Inserir clientes padrão
INSERT INTO clientes (nome) VALUES 
    ('YPÊ'),
    ('LIDER'),
    ('SELMI'),
    ('BRITVIC'),
    ('MARS'),
    ('FUGINI'),
    ('BAUDUCCO'),
    ('BARILLA'),
    ('MOCOCA'),
    ('J MACEDO'),
    ('CEPERA'),
    ('MDIAS'),
    ('RECKITT');

-- 7. Inserir usuário administrador padrão
-- Senha: admin123 (deve ser alterada em produção)
INSERT INTO usuarios (username, password, nome, cargo, admin, ativo) VALUES 
    ('admin', 'scrypt:32768:8:1$wNoS9iyiNK3225iE$c444de67170d3f289eadf28469525ddf203dfcd6717b9dc4dbc8e4c13125081a1a403e48980820884c89dfccfd19942fbdb33cc918a5a7ac961370d9bcc76b52', 'Administrador', 'Administrador', 1, 1);

-- 8. Inserir alguns colaboradores Carsten de exemplo
INSERT INTO colaboradores_carsten (nome, cargo, departamento, data_contratacao, ativo) VALUES 
    ('João Silva', 'Operador', 'Logística', '2023-01-15', 1),
    ('Maria Santos', 'Supervisor', 'Logística', '2022-06-10', 1),
    ('Pedro Costa', 'Auxiliar', 'Logística', '2023-03-20', 1);

-- 9. Criar índices para melhor performance
CREATE INDEX IF NOT EXISTS idx_tb_pck_arm_data ON tb_pck_arm(data);
CREATE INDEX IF NOT EXISTS idx_tb_pck_arm_cliente ON tb_pck_arm(cliente_id);
CREATE INDEX IF NOT EXISTS idx_tb_pck_arm_usuario ON tb_pck_arm(usuario_id);
CREATE INDEX IF NOT EXISTS idx_sistema_logs_timestamp ON sistema_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_usuarios_username ON usuarios(username);
CREATE INDEX IF NOT EXISTS idx_clientes_nome ON clientes(nome);
CREATE INDEX IF NOT EXISTS idx_colaboradores_nome ON colaboradores_carsten(nome);
