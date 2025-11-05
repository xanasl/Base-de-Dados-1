import tkinter
from tkinter import ttk, messagebox
import pyodbc
import datetime
from login import abrir_janela_login


#Função principal da aplicação browser ==>Mostra as encomendas e as linhas da encomenda selecionada
def app_browser():
    # === Liga à base de dados através da janela de login ===
    conn, isolamento = abrir_janela_login()

    # Se a conexão falhar, sai da aplicação
    if not conn:
        return
    cursor = conn.cursor()

    # === Janela principal ===
    root = tkinter.Tk()
    root.title("Browser de Encomendas")
    root.geometry("800x600")

    #Estado do auto refresh==>Atualização automática
    auto_running={"active":False,"after_id":None}#after_id==>guarda o id do evento agendado com root.after() para permitir cancelar o temporizador 

    #=== Topo: Controlo de refresh e estado ===
    top=ttk.Frame(root,padding=10)
    top.pack(fill="x")

    lbl_isolation=ttk.Label(top,text=f"Nivel de isolamento: {isolamento}")
    lbl_isolation.grid(row=0,column=0,sticky="w")

    btn_refresh=ttk.Button(top,text="Refresh agora")
    btn_refresh.grid(row=0,column=1,sticky="e",padx=(10,0))

    ttk.Label(top,text="Intervalo Auto-Refresh (s):").grid(row=0,column=2,padx=(20,5))
    combo_interval=ttk.Combobox(top,state="readonly",width=12, values=["1 ms", "10 ms", "100 ms", "250 ms", "500 ms", "1 s", "2 s", "5 s", "10 s"])
    
    combo_interval.current(5)#Seleciona 1 s por defeito
    combo_interval.grid(row=0,column=3)
    
    toggle_auto=ttk.Button(top,text="Iniciar Auto-Refresh")
    toggle_auto.grid(row=0,column=4,padx=(10,0))

    lbl_last_refresh=ttk.Label(top,text="Último Refresh:---")
    lbl_last_refresh.grid(row=0,column=5,padx=(20,0))

    #Controlo do layout do Topo
    for i in range(6):
        top.columnconfigure(i,weight=0)
    top.columnconfigure(5,weight=1)

    # === Grelha Superior:Encomendas  ===
    frame_orders=ttk.LabelFrame(root,text="Encomendas",padding=8)
    frame_orders.pack(fill="both",expand=True,padx=10,pady=(0,6))

    columns_orders=("EncID","ClienteID","Nome","Morada")
    tree_orders=ttk.Treeview(frame_orders,columns=columns_orders,show="headings",height=12)
    vbs_orders=ttk.Scrollbar(frame_orders,orient="vertical",command=tree_orders.yview)
    hsb_orders=ttk.Scrollbar(frame_orders,orient="horizontal",command=tree_orders.xview)
    tree_orders.configure(yscrollcommand=vbs_orders.set,xscrollcommand=hsb_orders.set)

    for col,width in [("EncID",90),("ClienteID",90),("Nome",220),("Morada",480)]:
        tree_orders.heading(col,text=col)#Define o cabeçalho da coluna
        tree_orders.column(col,width=width,anchor="w")#Define a largura e o alinhamento da coluna==>w=esquerda

    tree_orders.grid(row=0,column=0,sticky="nsew")#sticky=nsew ==> expande em todas as direcções
    vbs_orders.grid(row=0,column=1,sticky="ns")#Coloca a scrollbar vertical ao lado direito da grelha
    hsb_orders.grid(row=1,column=0,sticky="ew")#Coloca a scrollbar horizontal em baixo da grelha
    frame_orders.rowconfigure(0,weight=1)#Permite que a grelha expanda verticalmente
    frame_orders.columnconfigure(0,weight=1)#Permite que a grelha expanda horizontalmente

    # === Grelha Inferior:Linhas da encomenda selecionada  ===
    frame_lines=ttk.LabelFrame(root,text="Linhas da Encomenda",padding=8)
    frame_lines.pack(fill="both",expand=True,padx=10,pady=(6,10))

    columns_lines=("ProdutoID","Designacao","Preco","Qtd")
    tree_lines=ttk.Treeview(frame_lines,columns=columns_lines,show="headings",height=10)
    vbs_lines=ttk.Scrollbar(frame_lines,orient="vertical",command=tree_lines.yview)
    hsb_lines=ttk.Scrollbar(frame_lines,orient="horizontal",command=tree_lines.xview)
    tree_lines.configure(yscrollcommand=vbs_lines.set,xscrollcommand=hsb_lines.set)

    for col,width in [("ProdutoID",100),("Designacao",300),("Preco",120),("Qtd",80)]:
        tree_lines.heading(col,text=col)
        anchor="e" if col=="Preco" else "w"#Alinha à direita a coluna Preco
        tree_lines.column(col,width=width,anchor=anchor)

    tree_lines.grid(row=0,column=0,sticky="nsew")
    vbs_lines.grid(row=0,column=1,sticky="ns")
    hsb_lines.grid(row=1,column=0,sticky="ew")

    frame_lines.rowconfigure(0,weight=1)
    frame_lines.columnconfigure(0,weight=1)

    # === Função: Converte o valor da combo para milissegundos ===
    def combo_to_ms(text: str)->int:
        text=text.strip().lower()
        if text.endswith("ms"):
            return max(1,int(text.replace("ms","").strip()))
        if text.endswith("s"):
            sec=float(text.replace("s","").strip())
            return max(1000,int(sec*1000))
        return 1000#Default 1 segundo

        


    # === Função: Obtém o EncID da encomenda selecionada ===
    def current_encid_selected():
        selection=tree_orders.selection()
        if not selection:
            return None
        item_id=selection[0]
        values=tree_orders.item(item_id,"values")
        if not values:
            return None
        return values[0]#Retorna o EncID da encomenda selecionada
    
    
    # === Função: Carrega as encomendas na grelha superior ===
    def load_orders():
        try:
            keep=current_encid_selected()#Mentém o EncID selecionado se possivel

            #Carregar encomendas
            tree_orders.delete(*tree_orders.get_children())#Limpa a grelha
            cursor.execute("""
                SELECT EncID, ClienteID,Nome,Morada
                FROM Encomenda
                ORDER BY EncID DESC
                """)
            
            for row in cursor.fetchall():
                tree_orders.insert("",tkinter.END,values=(row[0],row[1],row[2],row[3]))

            #Restaurar seleção
            if keep is not None:
                for item_id in tree_orders.get_children():
                    values=tree_orders.item(item_id,"values")
                    if values and values[0]==keep:
                        tree_orders.selection_set(item_id)
                        tree_orders.see(item_id)
                        break
            
            #Atualiza linhas em baixo para o EncID selecionado ou limpa
            encid=current_encid_selected()
            if encid is not None:
                load_lines(encid)
            else:
                tree_lines.delete(*tree_lines.get_children())#Limpa a grelha de linhas
        
        except Exception as e:
            messagebox.showerror("Erro ao carregar as encomendas", str(e))

    # === Função: Carrega as linhas da encomenda selecionada na grelha inferior ===
    def load_lines(encid):
        try:
            tree_lines.delete(*tree_lines.get_children())#Limpa a grelha de linhas
            cursor.execute("""
                SELECT ProdutoID, Designacao, Preco, Qtd
                FROM EncLinha 
                WHERE EncId = ?
                ORDER BY ProdutoID
            """, (encid,))  
            for row in cursor.fetchall():
                prod_id,design,preco,qtd=row
                tree_lines.insert("",tkinter.END,values=(prod_id,design,preco,qtd))
        except Exception as e:
            messagebox.showerror("Erro ao carregar linhas", str(e))

    # === Função: Evento de seleção de encomenda ===        
    def on_order_select(event):
        encid=current_encid_selected()
        if encid is not None:
            load_lines(encid)
        else:
            tree_lines.delete(*tree_lines.get_children())#Limpa a grelha de linhas
    
    # === Função: Atualiza as encomendas (botão refresh) ===
    def do_refresh():
        load_orders()
    
    # === Funções: Alterna o estado do auto-refresh ===
    
    #Funcão de auto-tick
    def auto_tick():
        if not auto_running["active"]:
            return
        do_refresh()
        interval_ms=combo_to_ms(combo_interval.get())
        auto_running["after_id"]=root.after(interval_ms,auto_tick)

    def toggle_auto_refresh():
        if auto_running["active"]:
            #Desativa o auto-refresh
            auto_running["active"]=False
            if auto_running["after_id"] is not None:
                root.after_cancel(auto_running["after_id"])
                auto_running["after_id"]=None
            toggle_auto.config(text="Iniciar Auto-Refresh")
        else:
            #Ativa o auto-refresh
            auto_running["active"]=True
            toggle_auto.config(text="Parar Auto-Refresh")
            auto_tick()
    
    # === Função: Fecha a aplicação limpando recursos ===
    def on_close():
        try:
            if auto_running["after_id"] is not None:
                root.after_cancel(auto_running["after_id"])
        except Exception:
            pass
        try:
            cursor.close()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass
        root.destroy()
    

    #Bindings e callbacks
    tree_orders.bind("<<TreeviewSelect>>",on_order_select)
    btn_refresh.config(command=do_refresh)
    toggle_auto.config(command=toggle_auto_refresh)
    root.protocol("WM_DELETE_WINDOW",on_close)

    #Carrega as encomendas inniciais
    do_refresh()
    root.mainloop()


if __name__ == "__main__":
    app_browser()


