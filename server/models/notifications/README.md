# Notification model notes

Notifications now generate their UUID primary key and annotate `notification_type` with `NotificationType` rather than the unrelated read-state enum. Confirm the SQL column values and existing database schema before applying migrations.
