CREATE USER server_user WITH PASSWORD __PASSWORD__;
ALTER ROLE server_user SET client_encoding TO 'utf8';
ALTER ROLE server_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE server_user SET TIMEZONE TO 'UTC';

ALTER ROLE server_user WITH SUPERUSER;

CREATE DATABASE server_db;
GRANT ALL PRIVILEGES ON DATABASE server_db TO server_user;

CREATE EXTENSION intarray;
