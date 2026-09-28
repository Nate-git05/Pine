# SQLAlchemy models handoff

The subdirectories define customer/merchant identities, agents and hires, job requests and jobs, payment records, and notifications. Newly created records now receive UUIDs for the edited models, and job ratings can be absent until a customer rates the completed job.

`Customer` is mapped to `customers` to match foreign keys in the rest of the model tree. Confirm the live schema and migrate it if it currently uses a singular table name before deployment. The broader model layer still needs a full schema audit for nullability, enums, relationships, and migrations.
