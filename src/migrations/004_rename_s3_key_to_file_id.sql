-- Migration: Rename s3_key to file_id
-- This migration renames the column to reflect the change from AWS S3 to ImageKit

ALTER TABLE users
RENAME COLUMN s3_key TO file_id;

-- Verify migration:
-- SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'file_id';
