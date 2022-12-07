import sqlite3

connection = sqlite3.connect("database.db")
cursor = connection.cursor()


for i in cursor.execute("SELECT * FROM users"):
    print(i)
connection.close()