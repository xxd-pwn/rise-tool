import os
import re
import subprocess

import pyodbc
import mysql.connector
import psycopg2
from psycopg2 import OperationalError
from loguru import logger

# TODO: Modify the parameters
def connectOracle():
    conn = pyodbc.connect(
        "DRIVER="
        "DBQ="
        "UID="
        "PWD="
    )
    return conn

def connectMySQL():
    conn = mysql.connector.connect(
        host='',
        user='',
        password='',
        database='',
        charset='utf8mb4'
    )
    return conn

def connectMariaDB():
    conn = mysql.connector.connect(
        host='',
        port='',
        user='',
        password='',
        database='',
        charset='utf8mb4'
    )
    return conn

def connectPostgres():
    conn = None
    try:
        conn = psycopg2.connect(
            host='',
            database='',
            user='',
            password='',
            port=''
        )
    except OperationalError as e:
        print(f"The error '{e}' occurred")
    return conn

def SQLExecuteWithRollback(conn, sql):
    cursor = conn.cursor()
    try:
        cursor.execute(sql)
        if cursor.description:
            listRS = cursor.fetchall()
            conn.commit()
            return listRS
        else:
            conn.commit()
            return
    except Exception as e:
        conn.rollback()
        raise
    finally:
        cursor.close()

def execute_plpgsql(sql):
    try:
        conn = connectPostgres()
        cursor = conn.cursor()
        cursor.execute(sql)
        conn.commit()
        return True, 'pass!'
    except Exception as e:
        pattern = r"LINE\s+\d+"
        return False, re.sub(pattern, "", str(e)).strip()

def execute_plsql(sql: str):
    initial_sql = """
    BEGIN
    FOR item IN (SELECT object_name, object_type FROM user_objects WHERE object_type IN ('PROCEDURE', 'FUNCTION'))
    LOOP
        EXECUTE IMMEDIATE 'DROP ' || item.object_type || ' ' || item.object_name;
    END LOOP;
END;
    """
    __run_sqlplus(initial_sql)
    return __run_sqlplus(sql)

def __run_sqlplus(sql: str):
    #TODO: Modify the connect_str of Oracle
    connect_str = ''

    os.environ['NLS_LANG'] = 'AMERICAN_AMERICA.AL32UTF8'

    input_script = f"""
    SET PAGESIZE 0 FEEDBACK OFF VERIFY OFF HEADING OFF ECHO OFF TRIMSPOOL ON LINESIZE 32767
    WHENEVER SQLERROR EXIT SQL.SQLCODE
    {sql}\n /
    show errors;
    EXIT;
    """

    try:
        proc = subprocess.Popen(
            ["sqlplus", connect_str],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",
            text=True
        )

        stdout, stderr = proc.communicate(input=input_script)

        if stderr:
            print(f"SQL*Plus errors: {stderr}")
            return False, stderr.strip()

        if stdout:
            # print(f"Input SQL:\n{sql}")
            # print(f"SQL*Plus original output: {stdout}")
            pattern = r"Connected to:[\s\S]*?Disconnected from Oracle Database 19c Enterprise Edition Release 19\.0\.0\.0\.0"
            match = re.search(pattern, stdout.strip()).group()
            match = match.replace("Connected to:", "")
            match = match.replace("Oracle Database 19c Enterprise Edition Release 19.0.0.0.0 - Production", "")
            match = match.replace("Version 19.3.0.0.0", "")
            match = match.replace("Disconnected from Oracle Database 19c Enterprise Edition Release 19.0.0.0.0", "")
            match = match.replace("\n", " ")
            while "  " in match:
                match = match.replace("  ", " ")
            if proc.returncode != 0:
                pattern_err = r"ORA-[0-9]{5}:.*"
                return False, re.search(pattern_err, match).group()
            else:
                match = match.replace("\t", "")
                match = match.replace("SQL>", "")
                while "  " in match:
                    match = match.replace("  ", " ")
                # print(f"SQL*Plus output: {match}")
                if 'Warning:' not in match:
                    return True, match
                else:
                    warning_pattern = r"Warning:.*"
                    if 'SQL> No errors.' in match:
                        return False, re.search(warning_pattern, match).group()
                    else:
                        return False, __getTheFirstErrMsg(match)

    except Exception as e:
        print(f"Error: {e}")
        return False, e

def __getTheFirstErrMsg(msg: str):
    start_index = msg.find('Errors for PROCEDURE')
    complete_msg = msg[start_index + len('Errors for PROCEDURE'):].strip()
    # print(f"Complete message: {complete_msg}")
    pattern = r"PLS-\d{5}"
    matches = re.finditer(pattern, complete_msg)
    match_positions = [match.start() for match in matches]
    if len(match_positions) < 2:
        return re.sub(r"\b\d+/\d+\b", "", complete_msg).strip()

    start_index = match_positions[0]
    end_index = match_positions[1]

    result = complete_msg[start_index:end_index].strip()

    plsql_index = result.find("PL/SQL")
    if plsql_index != -1:
        result = result[:plsql_index].strip()

    result = re.sub(r"\b\d+/\d+\b", "", result).strip()

    return result

def getConnbyName(dbName: str):
    if dbName.lower() == 'mysql':
        return connectMySQL()
    elif dbName.lower() == 'postgresql':
        return connectPostgres()
    elif dbName.lower() == 'oracle':
        return connectOracle()
    elif dbName.lower() == 'mariadb':
        return connectMariaDB()
    else:
        return None

def verify(s_db: str, s_sql: str, t_db: str, t_sql: str):
    s_conn = getConnbyName(s_db)
    t_conn = getConnbyName(t_db)
    try:
        s_result = SQLExecuteWithRollback(s_conn, s_sql)
    except Exception as e:
        s_result = None
        print(f'Error: {e}')
    try:
        t_result = SQLExecuteWithRollback(t_conn, t_sql)
    except Exception as e:
        logger.error(f'Error: {e}')
        return False, str(e)
    if s_result is not None and s_result != t_result:
        return False, f'These two sql are different! Result of the source sql is {s_result}, but the result of the converted sql is {t_result}'
    return True, 'pass!'