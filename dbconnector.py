#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  dbconnector.py
#  
#  Copyright 2019 Joe Westra <me@joewestra.ca>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  

import mysql.connector
import queue

host = "localhost"
user = "root"
passwd = "AmanitaMuscaria"
database = "BUDGET"
TABLE_LIST = ['assignment','category','description_one','description_two','domain','investment','transaction','type']


def getConnectionToMySQL():
    mydb = mysql.connector.connect(
    host = host,
    user = user,
    passwd=passwd
    )
    return mydb

def getCursorFromConnection(db):
    return db.cursor()

def createDatabase(cursor):
    try:
        cursor.execute(
        "CREATE DATABASE {} DEFAULT CHARACTER SET 'utf8'".format(database))
        cursor.fetchall()
    except mysql.connector.Error as err:
        print("Failed creating database {}".format(database))
        cursor.close()
        # exit(1)

def enterBudgetDB(cursor):
    try:
        cursor.execute("USE {}".format(database))
        # cursor.fetchall()
        return cursor
    except mysql.connector.Error as err:
        print("Database {} does not exist.".format(database))
        if err == mysql.connector.errorcode.ER_BAD_DB_ERROR:
            createDatabase(cursor)
            print("Database {} created".format(database))
            enterBudgetDB()
        else:
            print(err)
            cursor.close()
            # exit(1)

def getCursorInsideDB():
    cnx = getConnectionToMySQL()
    cursor = getCursorFromConnection(cnx)
    return enterBudgetDB(cursor)
    

def dropTables(cursor):
    q = queue.Queue()
    for table in TABLE_LIST:
        q.put(table)
        
    while (not q.empty()):
        tname = q.get()
        try:
            cursor.execute("DROP TABLE %s" % tname)
            
            #if forgiegn key constraints fail, just add the table to the queue again
        except mysql.connector.Error as err:
            print(err)
            q.put(tname)
            
    return True
    


def createTables(cursor):
    # used to show potential errors encountered
    #cursor.execute("SHOW ENGINE INNODB STATUS")
    #print(cursor.fetchall())    
    
    #create the tables for the transaction logging
    cursor.execute("CREATE TABLE domain (name VARCHAR(255) UNIQUE NOT NULL PRIMARY KEY)")
    cursor.execute("CREATE TABLE category (name VARCHAR(255) UNIQUE NOT NULL PRIMARY KEY)")
    cursor.execute("CREATE TABLE type (id mediumint(5) unsigned AUTO_INCREMENT not null primary key, category VARCHAR(255) not null, domain VARCHAR(255) not null,  FOREIGN KEY(category) REFERENCES category(name) ON DELETE CASCADE ON UPDATE CASCADE, FOREIGN KEY(domain) REFERENCES domain(name) ON DELETE CASCADE ON UPDATE CASCADE)")
    cursor.execute("CREATE TABLE investment (id mediumint(5) unsigned AUTO_INCREMENT not null primary key, type mediumint(5) unsigned not null, amount FLOAT(5,2) not null, FOREIGN KEY(type) REFERENCES type(id) ON DELETE CASCADE ON UPDATE CASCADE)")
    #dateformat: YYYY-MM-DD
    cursor.execute("CREATE TABLE transaction (id mediumint(5) unsigned AUTO_INCREMENT primary key, date DATE not null, account VARCHAR(10) NOT NULL, amount FLOAT(5,2) not null, descr1 VARCHAR(80) NOT NULL, descr2 VARCHAR(80))")
 
    #create the tables for mapping Transaction Description Names to categories and percentages
    cursor.execute("CREATE TABLE description_one (name VARCHAR(255) UNIQUE NOT NULL PRIMARY KEY)")
    cursor.execute("CREATE TABLE description_two (name VARCHAR(255) UNIQUE NOT NULL PRIMARY KEY)")
    cursor.execute("CREATE TABLE assignment (descrone VARCHAR(255)NOT NULL, descrtwo VARCHAR(255), percentage FLOAT(3,2) not null, type mediumint(5) unsigned, FOREIGN KEY(type) REFERENCES type(id) ON DELETE CASCADE ON UPDATE CASCADE, FOREIGN KEY(descrone) REFERENCES description_one(name) ON DELETE CASCADE ON UPDATE CASCADE, FOREIGN KEY(descrtwo) REFERENCES description_two(name) ON DELETE CASCADE ON UPDATE CASCADE, PRIMARY KEY (descrone, type))")
    return cursor



def addNameElementToTable(cursor, table, name):
    try:
        cursor.execute("INSERT INTO %s VALUES ('%s')" % (table, name))
        return True
    except mysql.connector.Error as err:
        print(err)
        return False
        
        
def addToDomain(cursor, name):
    return addNameElementToTable(cursor, "domain", name)

def addToCategory(cursor, name):
    return addNameElementToTable(cursor, "category", name)
    
def elementIsInTable(cursor, table, field, element):
    cursor.execute("SELECT * FROM %s WHERE %s = '%s'" % (table, field, element))
    results = cursor.fetchall()
    if (not results):
        return False
    return True


def isInDescOneTable(cursor, desc):
    return elementIsInTable(cursor, "description_one", "name", desc)

def isInDescTwoTable(cursor, desc):
    return elementIsInTable(cursor, "description_two", "name", desc)

#https://dev.mysql.com/doc/connector-python/en/connector-python-example-ddl.html

