## GNAF Database

####  Prerequisites
- GNAF data files from data.gov.au
    - Extract the zip file to a location that is accessible from the PostgreSQL instance. (e.g. /mnt/)
- PostgreSQL instance on Linux OS (Container/VM)
- Either add unix user account to the database and give permissions on the target database OR modify the psql commands in "gnaf_db_setup.sh" to explicitly specify username (-U db_username) and password via ~/.pgpass or PGPASSWORD
- Non-Default Database (Optional)
- Install PostGIS extension (Optional)


#### Instructions
- Update the variables in the code files:
    - load_data.sql
        - **Variables to change:**
            - file_path_prefix
    - gnaf_db_setup.sh
        - **Variables to change:**
            - DB_
            - SCHEMA_
            - GNAF_DATA_FOLDER_ROOT
- run gnaf_db_setup.sh