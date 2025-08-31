-- name: GetOrCreateUser :one
INSERT INTO users (email)
VALUES ($1)
ON CONFLICT (email) DO UPDATE SET email = EXCLUDED.email
RETURNING *;

-- name: CreateOTP :one
INSERT INTO otps (user_id, otp_code, expires_at)
VALUES ($1, $2, $3)
RETURNING *;

-- name: VerifyOTP :one
UPDATE otps
SET used = TRUE
WHERE id = (
    SELECT id FROM otps
    WHERE user_id = $1
      AND otp_code = $2
      AND used = FALSE
      AND expires_at > now()
    ORDER BY expires_at DESC
    LIMIT 1
)
RETURNING *;
