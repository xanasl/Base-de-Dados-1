from login import abrir_janela_login
import tkinter as tk
from tkinter import ttk, messagebox

def mostrar_grelha(conn, nome_tabela):
    """Abre uma janela Tkinter que mostra todos os dados de uma tabela."""
    try:
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT *
            FROM {nome_tabela}
            WHERE EventType <> 'O'
            ORDER BY EventType DESC
            OFFSET 0 ROWS FETCH NEXT 10 ROWS ONLY
        """)
        colunas = [desc[0] for desc in cursor.description]
        dados = cursor.fetchall()
    except Exception as e:
        messagebox.showerror("Erro", f"Não foi possível obter os dados da tabela:\n\n{e}")
        return

    # Cria a janela principal
    janela = tk.Tk()
    janela.title(f"Tabela: {nome_tabela}")
    janela.geometry("900x500")

    frame = ttk.Frame(janela, padding=10)
    frame.pack(fill="both", expand=True)

    # Cria a grelha (Treeview)
    tree = ttk.Treeview(frame, columns=colunas, show="headings")
    for col in colunas:
        tree.heading(col, text=col)
        tree.column(col, width=150, anchor="center")

    # Adiciona os dados
    for linha in dados:
        tree.insert("", "end", values=linha)

    # Scrollbars
    scroll_y = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    scroll_x = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
    tree.configure(yscroll=scroll_y.set, xscroll=scroll_x.set)

    # Layout
    tree.grid(row=0, column=0, sticky="nsew")
    scroll_y.grid(row=0, column=1, sticky="ns")
    scroll_x.grid(row=1, column=0, sticky="ew")
    frame.rowconfigure(0, weight=1)
    frame.columnconfigure(0, weight=1)

    janela.mainloop()


# --- Código principal ---
conn, isolamento = abrir_janela_login()  # já define o nível de isolamento na conexão

if conn:
    mostrar_grelha(conn, "LogOperations")
    conn.close()
else:
    print("Ligação não estabelecida.")
