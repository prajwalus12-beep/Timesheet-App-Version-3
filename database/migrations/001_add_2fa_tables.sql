-- Migration: 001_add_2fa_tables.sql
-- Purpose: Add Two-Factor Authentication (TOTP) support for Employees and Admins

CREATE TABLE IF NOT EXISTS public.user_2fa (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    username TEXT UNIQUE NOT NULL,
    user_type TEXT NOT NULL CHECK (user_type IN ('admin', 'employee')),
    two_fa_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    setup_verified BOOLEAN NOT NULL DEFAULT FALSE,
    encrypted_secret TEXT,
    recovery_codes_hashed JSONB NOT NULL DEFAULT '[]'::jsonb,
    last_used_timestep BIGINT,
    failed_attempts INTEGER NOT NULL DEFAULT 0,
    locked_until TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_verified_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_user_2fa_username ON public.user_2fa (username);
CREATE INDEX IF NOT EXISTS idx_user_2fa_user_id ON public.user_2fa (user_id);

CREATE TABLE IF NOT EXISTS public.two_factor_audit_logs (
    id BIGSERIAL PRIMARY KEY,
    event_type TEXT NOT NULL,
    actor_username TEXT NOT NULL,
    target_username TEXT NOT NULL,
    user_type TEXT NOT NULL,
    details TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_2fa_audit_target ON public.two_factor_audit_logs (target_username);
CREATE INDEX IF NOT EXISTS idx_2fa_audit_created ON public.two_factor_audit_logs (created_at DESC);
