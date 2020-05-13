'''
Created on Feb 12, 2020

@author: Tim Kreuzer
'''

from contextlib import closing
import psycopg2

def get_user_id(app_logger, uuidcode, database, email):
    email = email.replace("@", "_at_")
    with closing(psycopg2.connect(host=database.get('host'),
                                  port=database.get('port'),
                                  user=database.get('user'),
                                  password=database.get('password'),
                                  database=database.get('database'))) as con: # auto closes
        with closing(con.cursor()) as cur: # auto closes
            with con: # auto commit
                cmd = "SELECT \"id\" FROM \"User\" WHERE \"email\" = %s"
                app_logger.trace("uuidcode={} - Execute: {}, email={}".format(uuidcode, cmd, email))
                cur.execute(cmd,
                            (email, ))
                results = cur.fetchall()
                app_logger.trace("uuidcode={} - Results: {}".format(uuidcode, results))
    if len(results) > 0:
        return results[0][0]
    else:
        return 0


def create_user(app_logger, uuidcode, database, email):
    email = email.replace("@", "_at_")
    with closing(psycopg2.connect(host=database.get('host'),
                                  port=database.get('port'),
                                  user=database.get('user'),
                                  password=database.get('password'),
                                  database=database.get('database'))) as con: # auto closes
        with closing(con.cursor()) as cur: # auto closes
            with con: # auto commit
                cmd = "INSERT INTO \"User\" (\"email\") VALUES (%s)"
                app_logger.trace("uuidcode={} - Execute: {}, email={}".format(uuidcode, cmd, email))
                cur.execute(cmd,
                            (email, ))


def get_next_slave(app_logger, uuidcode, database):
    with closing(psycopg2.connect(host=database.get('host'),
                                  port=database.get('port'),
                                  user=database.get('user'),
                                  password=database.get('password'),
                                  database=database.get('database'))) as con: # auto closes
        with closing(con.cursor()) as cur: # auto closes
            with con: # auto commit
                cmd = "SELECT \"id\", \"Hostname\" FROM \"DockerSpawner\" WHERE \"Active\" = 1 ORDER BY \"Running\" LIMIT 1"
                app_logger.trace("uuidcode={} - Execute: {}".format(uuidcode, cmd))
                cur.execute(cmd)
                results = cur.fetchall()
                app_logger.trace("uuidcode={} - Results: {}".format(uuidcode, results))
    if len(results) > 0:
        return results[0][0], results[0][1]
    else:
        return 0, ""

def insert_container(app_logger, uuidcode, database, userid, slaveid, servername):
    with closing(psycopg2.connect(host=database.get('host'),
                                  port=database.get('port'),
                                  user=database.get('user'),
                                  password=database.get('password'),
                                  database=database.get('database'))) as con: # auto closes
        with closing(con.cursor()) as cur: # auto closes
            with con: # auto commit
                cmd = "INSERT INTO \"Containers\" (\"user_id\", \"slave_id\", \"uuid\", \"name\") VALUES (%s, %s, %s, %s)"
                app_logger.trace("uuidcode={} - Execute: {} with {} {} {} {}".format(uuidcode, cmd, userid, slaveid, uuidcode, servername))
                cur.execute(cmd,
                            (userid,
                             slaveid,
                             uuidcode,
                             servername))

def get_user_running(app_logger, uuidcode, database, user_id):
    with closing(psycopg2.connect(host=database.get('host'),
                                  port=database.get('port'),
                                  user=database.get('user'),
                                  password=database.get('password'),
                                  database=database.get('database'))) as con: # auto closes
        with closing(con.cursor()) as cur: # auto closes
            with con: # auto commit
                cmd = "SELECT COUNT(\"id\") FROM \"Containers\" WHERE \"user_id\" = %s"
                app_logger.trace("uuidcode={} - Execute: {} with {}".format(uuidcode, cmd, user_id))
                cur.execute(cmd,
                            (user_id, ))
                results = cur.fetchall()
                app_logger.trace("uuidcode={} - Results: {}".format(uuidcode, results))
    if len(results) > 0:
        return results[0][0]
    else:
        return 0

def increase_slave_running(app_logger, uuidcode, database, slave_id):
    with closing(psycopg2.connect(host=database.get('host'),
                                  port=database.get('port'),
                                  user=database.get('user'),
                                  password=database.get('password'),
                                  database=database.get('database'))) as con: # auto closes
        with closing(con.cursor()) as cur: # auto closes
            with con: # auto commit
                cmd = "UPDATE \"DockerSpawner\" SET \"Running\" = \"Running\" + 1 WHERE \"id\" = %s"
                app_logger.trace("uuidcode={} - Execute: {} with {}".format(uuidcode, cmd, slave_id))
                cur.execute(cmd,
                            (slave_id, ))


def get_container_info(app_logger, uuidcode, database, user_id, servername):
    with closing(psycopg2.connect(host=database.get('host'),
                                  port=database.get('port'),
                                  user=database.get('user'),
                                  password=database.get('password'),
                                  database=database.get('database'))) as con: # auto closes
        with closing(con.cursor()) as cur: # auto closes
            with con: # auto commit
                cmd = "SELECT \"slave_id\", \"uuid\" FROM \"Containers\" WHERE \"user_id\" = %s AND \"name\" = %s"
                app_logger.trace("uuidcode={} - Execute: {} with {} {}".format(uuidcode, cmd, user_id, servername))
                cur.execute(cmd,
                            (user_id, servername))
                results = cur.fetchall()
                app_logger.trace("uuidcode={} - Results: {}".format(uuidcode, results))
    if len(results) > 1:
        app_logger.error("uuidcode={} - More than one Result found. Please clean up database".format(uuidcode))
    if len(results) > 0:
        return results[0][0], results[0][1]
    else:
        return []
    
def get_slave_hostname(app_logger, uuidcode, database, slave_id):
    with closing(psycopg2.connect(host=database.get('host'),
                                  port=database.get('port'),
                                  user=database.get('user'),
                                  password=database.get('password'),
                                  database=database.get('database'))) as con: # auto closes
        with closing(con.cursor()) as cur: # auto closes
            with con: # auto commit
                cmd = "SELECT \"Hostname\" FROM \"DockerSpawner\" WHERE \"id\" = %s"
                app_logger.trace("uuidcode={} - Execute: {} with {}".format(uuidcode, cmd, slave_id))
                cur.execute(cmd,
                            (slave_id, ))
                results = cur.fetchall()
                app_logger.trace("uuidcode={} - Results: {}".format(uuidcode, results))
    if len(results) > 1:
        app_logger.error("uuidcode={} - More than one Result found. Please clean up database".format(uuidcode))
    if len(results) > 0:
        return results[0][0]
    else:
        app_logger.error("uuidcode={} - Result from Database get_slave_hostname: {}".format(uuidcode, results))
        return 0
    

def decrease_slave_running(app_logger, uuidcode, database, slave_id):
    with closing(psycopg2.connect(host=database.get('host'),
                                  port=database.get('port'),
                                  user=database.get('user'),
                                  password=database.get('password'),
                                  database=database.get('database'))) as con: # auto closes
        with closing(con.cursor()) as cur: # auto closes
            with con: # auto commit
                cmd = "UPDATE \"DockerSpawner\" SET \"Running\" = \"Running\" - 1 WHERE \"id\" = %s"
                app_logger.trace("uuidcode={} - Execute: {} with {}".format(uuidcode, cmd, slave_id))
                cur.execute(cmd,
                            (slave_id, ))
                
def remove_container(app_logger, uuidcode, database, user_id, servername):
    with closing(psycopg2.connect(host=database.get('host'),
                                  port=database.get('port'),
                                  user=database.get('user'),
                                  password=database.get('password'),
                                  database=database.get('database'))) as con: # auto closes
        with closing(con.cursor()) as cur: # auto closes
            with con: # auto commit
                cmd = "DELETE FROM \"Containers\" WHERE \"user_id\" = %s AND \"name\" = %s"
                app_logger.trace("uuidcode={} - Execute: {} with {} {}".format(uuidcode, cmd, user_id, servername))
                cur.execute(cmd,
                            (user_id, servername ))

