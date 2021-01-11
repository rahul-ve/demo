## GNAF Database


**For Docker build, please refer to [this repo](https://github.com/rahul-ve/gnaf_container).**
####  Prerequisites
- GNAF data files from [data.gov.au](https://data.gov.au/dataset/ds-dga-19432f89-dc3a-4ef3-b943-5326ef1dbecc/details?q=gnaf)
    - Extract the zip file to a location that is accessible from the PostgreSQL instance. (e.g. /mnt/  OR bind mount into the docker container)
- PostgreSQL instance on Linux OS
- Either add unix user account to the database and give permissions on the target database OR modify the psql commands in "gnaf_db_setup.sh" to explicitly specify username (**-U db_username**) and password via **~/.pgpass** or **PGPASSWORD**
- Install gawk, awk commands use gawk extensions!
    - apt-get install -y gawk 
- Non-Default Database (Optional)
- Install PostGIS extension (Optional)


#### Instructions
- Update the variables (where necessary) in the code files:
    - load_data.sql
        - **file_path_prefix**
    - gnaf_db_setup.sh
        - **DB_**
        - **SCHEMA_**
        - **GNAF_DATA_FOLDER_ROOT**
        - **DATA_FILES_PATH**
        - **PROVIDED_SCRIPTS_PATH**
- run gnaf_db_setup.sh