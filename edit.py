import tkinter as tk
from tkinter import ttk, messagebox
import pyodbc
import datetime
from login import abrir_janela_login
from decimal import Decimal

# ============================================================
# Função principal da aplicação de edição de encomendas
# Permite editar a morada e as quantidades dos produtos
# Regista logs de início e fim e mede o tempo total da operação
# ============================================================
def app_edit():
    # === Liga à base de dados através da janela de login ===
    conn, isolamento = abrir_janela_login()

    # Se a conexão falhar, sai da aplicação
    if not conn:
        return

    cursor = conn.cursor()
    cursor.execute("SELECT DB_NAME()")

    # === Janela principal ===
    root = tk.Tk()
    root.title("Editar Encomenda")
    root.geometry("800x600")

    # === Linha superior: ID da encomenda + botão carregar ===
    frame_top = ttk.Frame(root, padding=10)
    frame_top.pack(fill="x")

    ttk.Label(frame_top, text="ID da Encomenda:").grid(row=0, column=0, sticky="w", padx=5)
    entry_encid = ttk.Entry(frame_top, width=10)
    entry_encid.grid(row=0, column=1, padx=5)

    btn_carregar = ttk.Button(frame_top, text="Carregar Encomenda")
    btn_carregar.grid(row=0, column=2, padx=10)

    # === Cabeçalho da encomenda (Cliente, Nome, Morada) ===
    frame_info = ttk.Frame(root, padding=10)
    frame_info.pack(fill="x", pady=10)

    ttk.Label(frame_info, text="Cliente ID:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
    cliente_var = tk.StringVar()
    ttk.Entry(frame_info, textvariable=cliente_var, width=20, state="readonly").grid(row=0, column=1, sticky="w")

    ttk.Label(frame_info, text="Nome:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
    nome_var = tk.StringVar()
    ttk.Entry(frame_info, textvariable=nome_var, width=40, state="readonly").grid(row=1, column=1, sticky="w")

    ttk.Label(frame_info, text="Morada:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
    morada_var = tk.StringVar()
    entry_morada = ttk.Entry(frame_info, textvariable=morada_var, width=60)
    entry_morada.grid(row=2, column=1, sticky="w")

    # === Tabela de linhas da encomenda ===
    frame_tabela = ttk.Frame(root, padding=10)
    frame_tabela.pack(fill="both", expand=True)

    cols = ("ProdutoId", "Designacao", "Preco", "Qtd")
    tree_linhas = ttk.Treeview(frame_tabela, columns=cols, show="headings", height=10)
    for col in cols:
        tree_linhas.heading(col, text=col)
        tree_linhas.column(col, width=120, anchor="center")
    tree_linhas.pack(fill="both", expand=True)

    # === Permitir editar apenas a coluna "Qtd" ===
    def editar_qtd(event):
        item = tree_linhas.identify_row(event.y)
        coluna = tree_linhas.identify_column(event.x)
        if coluna != "#4":  # só a coluna 4 (Qtd)
            return

        x, y, width, height = tree_linhas.bbox(item, coluna)
        valor_atual = tree_linhas.item(item, "values")[3]
        entry_edit = ttk.Entry(tree_linhas)
        entry_edit.place(x=x, y=y, width=width, height=height)
        entry_edit.insert(0, valor_atual)
        entry_edit.focus()

        def salvar_edicao(event):
            novo_valor = entry_edit.get()
            valores = list(tree_linhas.item(item, "values"))
            valores[3] = novo_valor
            tree_linhas.item(item, values=valores)
            entry_edit.destroy()

        entry_edit.bind("<Return>", salvar_edicao)
        entry_edit.bind("<FocusOut>", lambda e: entry_edit.destroy())

    tree_linhas.bind("<Double-1>", editar_qtd)

    # Identificador único da operação (referência no LogOperations)
    user_ref = f"G1-{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    start_time = None  # tempo de início da edição

    # === Função: Carregar encomenda ===
    def carregar_encomenda():
        nonlocal start_time
        try:
            encid = int(entry_encid.get().strip())  # Valida o ID introduzido
        except ValueError:
            messagebox.showwarning("Aviso", "O ID da encomenda deve ser um número.")
            return

        try:
            # Aplica o nível de isolamento escolhido
            cursor.execute(f"SET TRANSACTION ISOLATION LEVEL {isolamento}")

            # Registar início da operação no log
            start_time = datetime.datetime.now()
            cursor.execute("""
                INSERT INTO LogOperations (EventType, Objecto, Valor, Referencia)
                VALUES ('O', ?, ?, ?)
            """, (f"Encomenda {encid}", start_time, user_ref))
            conn.commit()

            # Ler cabeçalho da encomenda
            cursor.execute("""
                SELECT ClienteId, Nome, Morada FROM Encomenda WHERE EncId = ?
            """, (encid,))
            encomenda = cursor.fetchone()

            if not encomenda:
                messagebox.showerror("Erro", f"Encomenda com ID {encid} não encontrada.")
                return

            cliente_var.set(encomenda[0])
            nome_var.set(encomenda[1])
            morada_var.set(encomenda[2])

            # Carregar linhas
            cursor.execute("""
                SELECT ProdutoId, Designacao, Preco, Qtd
                FROM EncLinha WHERE EncId = ?
            """, (encid,))
            rows = cursor.fetchall()

            # Limpar e preencher a tabela
            for item in tree_linhas.get_children():
                tree_linhas.delete(item)
            for row in rows:
                valores_limp = []
                for v in row:
                    if isinstance(v, Decimal):
                        v = f"{v:.2f}"
                    elif isinstance(v, (int, float)):
                        v = str(v)
                    elif isinstance(v, str):
                        v = v.strip()
                    valores_limp.append(v)
                tree_linhas.insert("", "end", values=tuple(valores_limp))


        except Exception as e:
            messagebox.showerror("Erro", str(e))

    # === Função: Guardar alterações ===
    def guardar_alteracoes():
        try:
            encid = int(entry_encid.get().strip())
        except ValueError:
            messagebox.showwarning("Aviso", "O ID da encomenda deve ser um número válido.")
            return

        nova_morada = morada_var.get()

        try:
            cursor.execute(f"SET TRANSACTION ISOLATION LEVEL {isolamento}")

            # Atualizar morada
            cursor.execute("UPDATE Encomenda SET Morada = ? WHERE EncId = ?", (nova_morada, encid))

            # Atualizar as quantidades
            for item in tree_linhas.get_children():
                produto_id, designacao, preco, qtd = tree_linhas.item(item, "values")
                cursor.execute("""
                    UPDATE EncLinha SET Qtd = ? WHERE EncId = ? AND ProdutoId = ?
                """, (qtd, encid, produto_id))

            conn.commit()

            # Calcular o tempo decorrido
            end_time = datetime.datetime.now()
            tempo_total = None
            if start_time:
                tempo_total = end_time - start_time

            # Log do fim da edição
            cursor.execute("""
                INSERT INTO LogOperations (EventType, Objecto, Valor, Referencia)
                VALUES ('O', ?, ?, ?)
            """, (f"Encomenda {encid}", end_time, user_ref))
            conn.commit()

            msg = "Alterações guardadas com sucesso!"

        except Exception as e:
            conn.rollback()
            messagebox.showerror("Erro", f"Ocorreu um erro: {e}")

    # Ligar o botão de carregar à função
    btn_carregar.config(command=carregar_encomenda)

    # Botão final para guardar alterações
    ttk.Button(root, text="Guardar Alterações", command=guardar_alteracoes).pack(pady=15)

    root.mainloop()


if __name__ == "__main__":
    app_edit()
