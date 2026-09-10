# Opaque payload bounds

Vexmera stores a small number of intentionally flexible JSON payloads for approvals, queued jobs, and Core actions. These fields are bounded to 64 KiB after compact UTF-8 JSON encoding before they can be persisted.

The limit is a storage and resilience guard, not a business-data quota. Normal campaign identifiers, recommendation metadata, budgets, flags, and nested action context remain well below the boundary.

Do not place credentials, access tokens, secrets, raw provider responses, or large documents in these payloads. Provider secrets belong only in the existing encrypted connector storage paths.
