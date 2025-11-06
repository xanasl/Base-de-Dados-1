from login import abrir_janela_login
import tkinter as tk
from tkinter import ttk, messagebox

def mostrar_grelha(conn, intervalo=5000):
    """
    Abre uma janela Tkinter que mostra os tempos de edição (EventType='O')
    e faz refresh automático a cada 'intervalo' milissegundos.
    """
    janela = tk.Tk()
    janela.title("Tempos de Edição das Encomendas")
    janela.geometry("800x500")

    frame = ttk.Frame(janela, padding=10)
    frame.pack(fill="both", expand=True)

    tree = ttk.Treeview(frame, show="headings")
    tree.grid(row=0, column=0, sticky="nsew")

    scroll_y = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    scroll_x = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
    scroll_y.grid(row=0, column=1, sticky="ns")
    scroll_x.grid(row=1, column=0, sticky="ew")

    frame.rowconfigure(0, weight=1)
    frame.columnconfigure(0, weight=1)

    # === Função que lê a BD e atualiza a grelha ===
    def atualizar_grelha():
        try:
            cursor = conn.cursor()
            # Consulta: calcula o tempo entre o início e o fim de cada edição
            cursor.execute("""
                SELECT 
                    COALESCE(LO1.UserId, 'Desconhecido') AS UserId,
                    LO1.Objecto AS EncId,
                    DATEDIFF(SECOND, LO1.Valor, LO2.Valor) AS Tempo
                FROM LogOperations LO1
                JOIN LogOperations LO2 
                    ON LO1.Referencia = LO2.Referencia
                WHERE 
                    LO1.EventType = 'O' 
                    AND LO2.EventType = 'O'
                    AND LO1.DCriacao < LO2.DCriacao
            """)
            colunas = [desc[0] for desc in cursor.description]
            dados = cursor.fetchall()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao obter dados:\n\n{e}")
            return

        # Define colunas (só uma vez)
        if not tree["columns"]:
            tree["columns"] = colunas
            for col in colunas:
                tree.heading(col, text=col)
                tree.column(col, width=150, anchor="center")

        # Limpa dados antigos
        for item in tree.get_children():
            tree.delete(item)

        # Insere novos dados
        for linha in dados:
            linha_limpa = [
                str(valor).replace("'", "").replace("(", "").replace(")", "") if valor is not None else ""
                for valor in linha
            ]
            tree.insert("", "end", values=linha_limpa)

        janela.after(intervalo, atualizar_grelha)

    # Primeira atualização
    atualizar_grelha()

    janela.mainloop()


# --- Código principal ---
if __name__ == "__main__":
    conn, isolamento = abrir_janela_login()

    if conn:
        # Refresh a cada 60 segundos (60000 ms)
        mostrar_grelha(conn, intervalo=60000)
        conn.close()
    else:
        print("Ligação não estabelecida.")
