from login import abrir_janela_login

conn = abrir_janela_login()

if conn:
    cursor = conn.cursor()
    cursor.execute("SELECT @@VERSION;")
    print(cursor.fetchone())
    conn.close()
else:
    print("Ligação não estabelecida.")
