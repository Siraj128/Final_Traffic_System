# Migration to Real Database (PostgreSQL)

## Goal Description
The goal is to migrate the **SafeDrive Rewards** backend from a file-based SQLite database (`reward_app.db`) to a robust, server-based **PostgreSQL** database. This will improve data integrity, concurrency, and scalability, making the application production-ready.

## User Review Required
> [!IMPORTANT]
> **PostgreSQL Installation Required**: Since PostgreSQL is not detected on your system, you will need to install it manually. I will provide a script/guide to help you, but you must download the installer from the official website.

> [!WARNING]
> **Data Migration**: The current data in `reward_app.db` will **NOT** be automatically transferred to PostgreSQL with this plan (unless we add a specific data migration step). We will start with a fresh database schema. If you need existing data moved, please let me know.

## Proposed Changes

### Backend Configuration
#### [MODIFY] [requirements.txt](file:///d:/Antigravity/reward%20app/reward_backend/requirements.txt)
- Add `asyncpg` dependency (the async driver for PostgreSQL).
- Add `python-dotenv` (already there, but ensuring).

#### [MODIFY] [config.py](file:///d:/Antigravity/reward%20app/reward_backend/utils/config.py)
- Update `SQLITE_URL` (or rename to `DATABASE_URL`) to support PostgreSQL connection strings.
- Add defaults for `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_SERVER`, `POSTGRES_DB`.

#### [MODIFY] [connection.py](file:///d:/Antigravity/reward%20app/reward_backend/database/connection.py)
- Update code to handle PostgreSQL connection string format (replace `postgresql://` with `postgresql+asyncpg://` if needed).
- Remove SQLite-specific `check_same_thread` argument in `connect_args` for Postgres.

#### [NEW] [create_tables.py](file:///d:/Antigravity/reward%20app/reward_backend/create_tables.py)
- A new script to create all tables in the database using SQLAlchemy metadata. This replaces the manual `migrate_db.py` which was hardcoded for SQLite.

### Database Setup
- **Manual Step**: Install PostgreSQL 16 (or latest) for Windows.
- **Manual Step**: Create a database named `safedrive` and a user `admin` (or use default `postgres`).

## Verification Plan

### Automated Tests
- Run `create_tables.py` to verify schema creation without errors.
- Run the backend server (`uvicorn main:app`) and ensure it connects to the database.

### Manual Verification
- **Step 1**: Install PostgreSQL.
- **Step 2**: Configuration backend with DB credentials.
- **Step 3**: Start server.
- **Step 4**: Trigger an API endpoint (e.g., login or register) to verify data is written to the new database (using `pgAdmin` or command line if available).
