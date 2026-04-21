# Claude Instructions

## Data Persistence

Always use the Supabase MCP tools to save and retrieve data. Never store data locally or suggest manual database operations when a Supabase tool exists.

### Supabase
Use the Supabase MCP tools for all data operations:
- `list_projects`, `get_project`, `get_project_url` — find and connect to the project
- `list_tables` — inspect available tables before querying
- `execute_sql` — run queries to read or write data
- `apply_migration` — apply schema changes
- `list_migrations` — check migration history
- `generate_typescript_types` — generate types from the database schema
- `get_logs` — debug edge functions or database issues
- `list_edge_functions`, `deploy_edge_function`, `get_edge_function` — manage serverless functions

### Rules
- Always use Supabase to persist any data the user wants saved.
- Before writing data, check existing tables with `list_tables` to avoid duplication.
- Use `apply_migration` for schema changes, never raw DDL via `execute_sql` in production.
- If the project is ambiguous, use `list_projects` first and confirm with the user.

## General Rules

- Do NOT use Google Home, Sonos, or any smart home MCP tools in this project.
- Focus exclusively on application data and backend logic via Supabase.
