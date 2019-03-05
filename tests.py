#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  tests.py
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

import unittest
import mysql.connector
import re
from dbconnector import *

class Test_dbconnector(unittest.TestCase):
    
    conn = getConnectionToMySQL()
    curs = getCursorFromConnection(conn)
    cursindb = enterBudgetDB(curs)
    

    def test_connectToMySQL(self):
        cnx = getConnectionToMySQL()
        self.assertIsInstance(cnx, mysql.connector.connection.MySQLConnection)
        cnx.close()

    def test_getCursorFromConnection(self):
        conn = getConnectionToMySQL()
        curs = getCursorFromConnection(conn)
        self.assertIsInstance(curs, mysql.connector.cursor.MySQLCursor)
        curs.close()
        conn.close()

    
    def test_enterBudgetDB(self):
        conn = getConnectionToMySQL()
        curs = getCursorFromConnection(conn)
        enterBudgetDB(curs)
        
        curs.execute("SHOW DATABASES")
        # show databases returns a tuple where the second element in the array
        # contains the db name...
        db = curs.fetchall()[1]
        # ...as the first element...
        self.assertEqual(db[0], "BUDGET")
        curs.close()
        conn.close()
    
    def test_createTables(self):
        conn = getConnectionToMySQL()
        curs = getCursorFromConnection(conn)
        cursor = enterBudgetDB(curs)
        self.assertEqual(createTables(cursor), "table created")
        
    curs.close()
    cursindb.close()
    conn.close()

if __name__ == '__main__':
    unittest.main()
