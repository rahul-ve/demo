#!/bin/bash

#####
: '
This script creates the GNAF DB.

STEPS:

1. Download the GNAF GDA2020 zip file from data.gov.au and extract the contents to a location that is accessible to the PostgreSQL server
2. Map the table names to file names  (Authority Code & Standard files), output from this step is used in STEP 5
3. Create the schema
4. Create the tables
5. Load the data from PSV files
6. Add FK constraints
7. Create the Address View

'
#####

set -euxo pipefail

##
DB_="geo"
SCHEMA_="gnaf202011"
GNAF_DATA_FOLDER_ROOT="/mnt"

## 
DATA_FILES_PATH="$GNAF_DATA_FOLDER_ROOT/nov20_gnaf_pipeseparatedvalue_gda2020/G-NAF/G-NAF NOVEMBER 2020"
PROVIDED_SCRIPTS_PATH="$GNAF_DATA_FOLDER_ROOT/nov20_gnaf_pipeseparatedvalue_gda2020/G-NAF/Extras"

## STEP 2

## Authority Code tables
## Extract Authority Code table names from the psv file names
ls "$DATA_FILES_PATH/Authority Code/" | awk  'BEGIN{OFS=","} v_ = match($1, /(Authority_Code_)(.*)(_psv.psv)/, arr){print $1,arr[2]}' > "$DATA_FILES_PATH/ac_tables.csv"

## Standard tables
## Extract Standard table names from the psv file names
ls "$DATA_FILES_PATH/Standard/" | awk  'BEGIN{OFS=","} v_ = match($1, /([A-Z]+)_(.*)(_psv.psv)/, arr){print $1,arr[2]}' > "$DATA_FILES_PATH/std_tables.csv"


## STEP 3
psql -d $DB_ -c "CREATE SCHEMA $SCHEMA_;"

## STEP 4
psql -d $DB_ -c "SET SCHEMA '$SCHEMA_';"  -f "$PROVIDED_SCRIPTS_PATH/GNAF_TableCreation_Scripts/create_tables_ansi.sql"

## STEP 5
psql -d $DB_ -c "SET SCHEMA '$SCHEMA_';"  -f "./load_data.sql"

## STEP 6
psql -d $DB_ -c "SET SCHEMA '$SCHEMA_';" -f "$PROVIDED_SCRIPTS_PATH/GNAF_TableCreation_Scripts/add_fk_constraints.sql"

## STEP 7
psql -d $DB_ -c "SET SCHEMA '$SCHEMA_';" -f "$PROVIDED_SCRIPTS_PATH/GNAF_View_Scripts/address_view.sql"
