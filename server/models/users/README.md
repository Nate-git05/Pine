# User model notes

Customer table mapping is `customers`, matching foreign keys in the job, payment, and hire models. Customer and merchant UUIDs are generated in Python for new records. Check the deployed table name before rollout; a database migration may be needed.
