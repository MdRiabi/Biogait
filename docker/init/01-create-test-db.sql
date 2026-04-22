-- Exécuté au premier démarrage du volume Postgres (docker-entrypoint-initdb.d)
CREATE DATABASE biogait_test;
GRANT ALL PRIVILEGES ON DATABASE biogait_test TO biogait;
