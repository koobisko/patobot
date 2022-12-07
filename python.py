import sqlite3

connection = sqlite3.connect("database.db")
cursor = connection.cursor()


cursor.execute("create table gta (release_year integer, release_name text, city text)")

release_list = [
    (1969, "HOvo 1", "woody town"),
    (1980, "yah", "kaka")
]

cursor.executemany("insert into gta values (?,?,?)", release_list)

for row in cursor.execute("select * from gta"):
    print(row)

cursor.execute("select * from gta where city=:c", {"c": "kaka"})
search = cursor.fetchall()
print(search)
connection.close()