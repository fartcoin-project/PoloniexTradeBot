import json
import sqlite3

try: # Setup try to connect to sqlite database
    sqliteConnection = sqlite3.connect('./data.sqlite3')
    cursor = sqliteConnection.cursor()
    sqlite_select_Query = "select sqlite_version();"
    cursor.execute(sqlite_select_Query)
    record = cursor.fetchall()
    print("Connected to SQLite Database Version: ", record)
    cursor.close()
except sqlite3.Error as error:
    print("Error while connecting to sqlite", error)
    exit(1)
finally:
    sqliteConnection.close()



def insert_volume_sqlite(list): # Insert list into db
    connection = sqlite3.connect("../db.sqlite3")
    cursor = connection.cursor()
    x=1
    y=2
    z=3
    f=4
    g=5
    table_name = "table"
    counter = 0
    max_index = len(list) - 1  # Length coinlist
    while counter <= max_index:  # while = loop through PoloniexCoins List until max_index
        item = list[counter]  # Every loop change variable AltCoin to counter (0=AMP, 1=ARDR, 2=BAT...)

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name="+table_name)
        table = cursor.fetchone()
        if not table:
            cursor.execute('CREATE TABLE '+table_name+' ("date" TEXT, "close" INTEGER, "high" INTEGER, "low" INTEGER, "open" INTEGER, "volume" INTEGER, "symbol" TEXT)');
        cursor.execute('SELECT EXISTS(SELECT 1 FROM '+table_name+' WHERE item=?)',(item))
        check = cursor.fetchone()
        if check is None: # Market does not yet exist in Database
            cursor.execute('INSERT INTO '+table_name+' VALUES (?, ?, ?, ?, ?, ?)',
                           (item, x, y, z, f, g))
            connection.commit()
            print("----")
        else: # Market does exist in Database, needs Update
            cursor.execute('UPDATE '+table_name+' SET x = ?, y = ?, z = ?, f = ?, g = ? WHERE item = ?',
                           (x, y, z, f, g, item))
            connection.commit()
            print("----")
        counter = counter + 1
    cursor.close()
    sqliteConnection.close()


def get_my_jsonified_data(sel, frm, whr, key):
    with sqlite3.connect('../db.sqlite3') as sqliteConnection:
        cursor = sqliteConnection.cursor()
        cursor.execute('SELECT %s FROM "%s" WHERE "%s"=?;' % (sel, frm, whr,), [key])
        pair = cursor.fetchall()
        sqliteJson = '{"' + pair[0][1] + '": {"' + pair[0][2] + '": "' + pair[0][3] + '", "' + pair[0][4] + '": "' + pair[0][5] + '"}}'
        json2 = json.loads(sqliteJson)
        return json2


