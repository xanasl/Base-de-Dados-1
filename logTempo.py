
from login import abrir_janela_login
import tkinter as tk
from tkinter import ttk, messagebox

def mostrar_grelha(conn, nome_tabela, intervalo=5000):
    """Abre uma janela Tkinter que mostra todos os dados de uma tabela e faz refresh automático."""
    janela = tk.Tk()
    janela.title(f"Tabela: {nome_tabela}")
    janela.geometry("900x500")

    frame = ttk.Frame(janela, padding=10)
    frame.pack(fill="both", expand=True)

    tree = ttk.Treeview(frame, show="headings")
    tree.grid(row=0, column=0, sticky="nsew")

    scroll_y = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    scroll_x = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
    tree.configure(yscroll=scroll_y.set, xscroll=scroll_x.set)
    scroll_y.grid(row=0, column=1, sticky="ns")
    scroll_x.grid(row=1, column=0, sticky="ew")

    frame.rowconfigure(0, weight=1)
    frame.columnconfigure(0, weight=1)

    def atualizar_grelha():
        """Atualiza o conteúdo da grelha a partir da base de dados."""
        try:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT *
                FROM {nome_tabela}
                WHERE EventType = 'O'
            """)
            colunas = [desc[0] for desc in cursor.description]
            dados = cursor.fetchall()
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível obter os dados da tabela:\n\n{e}")
            return

        # Atualiza colunas (só se mudarem)
        if not tree["columns"]:
            tree["columns"] = colunas
            for col in colunas:
                tree.heading(col, text=col)
                tree.column(col, width=150, anchor="center")

        # Limpa os dados antigos
        for item in tree.get_children():
            tree.delete(item)

        # Insere os novos dados
        for linha in dados:
            tree.insert("", "end", values=linha)

        # Agenda a próxima atualização (em milissegundos)
        janela.after(intervalo, atualizar_grelha)

    # Primeira atualização imediata
    atualizar_grelha()

    janela.mainloop()


# --- Código principal ---
conn, isolamento = abrir_janela_login()

if conn:
    mostrar_grelha(conn, "LogOperations", intervalo=60000)  # refresh a cada minuto
    conn.close()
else:
    print("Ligação não estabelecida.")
