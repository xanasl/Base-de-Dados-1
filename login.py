import tkinter as tk
from tkinter import ttk, messagebox
import pyodbc #Faz a ligação ao SQL Server

def abrir_janela_login():
    """
    Abre uma janela de login e devolve:
      - uma conexão pyodbc válida
      - o nível de isolamento selecionado
    """
    conn = None  
    isolamento = None

    def conectar():
        nonlocal conn, isolamento  
        server = entry_server.get().strip()#Endereço do servidor (IP)
        database = entry_database.get().strip()#Nome da base de dados
        username = entry_username.get().strip()#Nome do utilizador
        password = entry_password.get().strip()#Password do utilizador
        isolamento = combo_auth.get().strip()#Nível de isolamento

        if not (server and database and username and password):
            messagebox.showwarning("Campos obrigatórios", "Por favor preencha todos os campos.")
            return

        # tenta estabelecer a conexão à base de dados
        try:
            conn_str = (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={server};"
                f"DATABASE={database};"
                f"UID={username};"
                f"PWD={password};"
            )
            conn = pyodbc.connect(conn_str)#Estabelece a ligação
            cursor = conn.cursor()
            cursor.execute(f"SET TRANSACTION ISOLATION LEVEL {isolamento};")# Define o nivel de isolamento escolhido
            root.destroy()
        except Exception as e:
            messagebox.showerror("Erro de conexão", f"Não foi possível conectar:\n\n{e}")

    # --- Interface gráfica ---
    root = tk.Tk()
    root.title("SQL Server Login")
    root.geometry("420x300")
    root.resizable(False, False)

    ttk.Label(root, text="SQL Server Management Studio", font=("Segoe UI", 14, "bold")).pack(pady=10)

    frame = ttk.Frame(root, padding=10)
    frame.pack(fill="x")

    ttk.Label(frame, text="Server:").grid(row=0, column=0, sticky="w", pady=5)
    entry_server = ttk.Entry(frame, width=30)
    entry_server.grid(row=0, column=1, padx=5)

    ttk.Label(frame, text="Database:").grid(row=1, column=0, sticky="w", pady=5)
    entry_database = ttk.Entry(frame, width=30)
    entry_database.grid(row=1, column=1, padx=5)

    ttk.Label(frame, text="User:").grid(row=2, column=0, sticky="w", pady=5)
    entry_username = ttk.Entry(frame, width=30)
    entry_username.grid(row=2, column=1, padx=5)

    ttk.Label(frame, text="Password:").grid(row=3, column=0, sticky="w", pady=5)
    entry_password = ttk.Entry(frame, width=30, show="*")
    entry_password.grid(row=3, column=1, padx=5)

    ttk.Label(frame, text="Nível de Isolamento:").grid(row=4, column=0, sticky="w", pady=5)
    
    #Combobox para selecionar o nível de isolamento
    combo_auth = ttk.Combobox(
        frame,
        values=["READ COMMITTED", "READ UNCOMMITTED", "REPEATABLE READ", "SERIALIZABLE"],
        state="readonly",
        width=27
    )
    combo_auth.current(0)
    combo_auth.grid(row=4, column=1, padx=5)

    ttk.Button(root, text="Connect", command=conectar).pack(pady=20)#Botão para conectar
    root.mainloop()#Espera pela interação do utilizador

    # devolve a ligação + o nível de isolamento
    return conn, isolamento
