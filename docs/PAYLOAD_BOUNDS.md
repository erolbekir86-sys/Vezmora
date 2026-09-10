# Opaque payload bounds

Vexmera accepts a small number of intentionally flexible JSON payloads for approval requests, queued jobs and Core actions. API models bound these payloads to 64 KiB after compact UTF-8 JSON encoding before they can enter normal persistence flows.

The limit is a resilience boundary, not a business-data quota. Normal campaign identifiers, recommendation metadata, budgets, flags and nested action context remain well below the limit.

Do not place credentials, access tokens, secrets, raw provider responses or large documents in opaque payloads. Provider secrets belong only in the existing encrypted connector storage paths.
