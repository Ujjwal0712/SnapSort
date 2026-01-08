-- Migration: Rename selfie_public_id to s3_key
-- This migration renames the column to reflect the change from Cloudinary to AWS S3

-- Rename the column
ALTER TABLE users 
RENAME COLUMN selfie_public_id TO s3_key;

-- Verify the change
-- SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'users' AND column_name = 's3_key';
