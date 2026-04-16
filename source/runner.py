from source.app.databases.database import Get_Connection

conn = Get_Connection()
cur = conn.cursor()

cur.execute("DELETE FROM Users WHERE username = ?", ("admin1",))
conn.commit()
conn.close()

print("Deleted old admin1")