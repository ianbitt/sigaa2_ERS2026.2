-- Um database e um usuário por serviço, na mesma instância (ver ADR-002).
-- Senhas de desenvolvimento: em produção viriam de um cofre de segredos.

CREATE USER vagas_user WITH PASSWORD 'vagas';
CREATE DATABASE vagas OWNER vagas_user;

CREATE USER consulta_user WITH PASSWORD 'consulta';
CREATE DATABASE consulta OWNER consulta_user;

-- Cada usuário só conecta no próprio database.
REVOKE CONNECT ON DATABASE vagas FROM PUBLIC;
REVOKE CONNECT ON DATABASE consulta FROM PUBLIC;
GRANT CONNECT ON DATABASE vagas TO vagas_user;
GRANT CONNECT ON DATABASE consulta TO consulta_user;
