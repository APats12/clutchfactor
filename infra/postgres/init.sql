-- Database is already created by POSTGRES_DB env var.
-- This script runs once on first container start.

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
