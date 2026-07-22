from nicegui import ui
from database import conectar, devolver_conexao, excluir_cliente
import asyncio
import os
import urllib.parse

# Pasta para salvar as artes/PDFs enviadas no painel
PASTA_PROMOCOES = "promocoes"
os.makedirs(PASTA_PROMOCOES, exist_ok=True)

# ==========================================================
# MODELOS E DADOS
# ==========================================================

modelos = {
    "Volvo": ["FH", "FM", "FMX", "VM", "NH"],
    "Scania": ["R", "S", "P", "G", "T", "L"],
    "Mercedes-Benz": ["Actros", "Atego", "Axor", "Accelo"],
    "Volkswagen": ["Constellation", "Delivery", "Meteor"],
    "Iveco": ["Hi-Way", "S-Way", "Tector", "Daily"],
    "DAF": ["XF", "CF", "LF", "XG"],
    "Ford": ["Cargo", "F-4000"]
}

marcas = list(modelos.keys())
anos = [str(i) for i in range(2026, 1989, -1)]

arquivo_promocao_path = None

# ==========================================================
# BANCO DE DADOS (Busca Síncrona Interna)
# ==========================================================

def _buscar_clientes_db(marca_filtro=None, modelo_filtro=None, ano_inicio_filtro=None, ano_fim_filtro=None):
    conn = conectar()
    try:
        with conn.cursor() as cursor:
            query = """
            SELECT id, nome, whatsapp, cidade, marca, modelo, ano, data_cadastro
            FROM clientes
            WHERE 1=1
            """
            parametros = []

            if marca_filtro:
                query += " AND marca=%s"
                parametros.append(marca_filtro)

            if modelo_filtro:
                query += " AND modelo=%s"
                parametros.append(modelo_filtro)

            if ano_inicio_filtro:
                query += " AND CAST(ano AS INTEGER) >= %s"
                parametros.append(int(ano_inicio_filtro))

            if ano_fim_filtro:
                query += " AND CAST(ano AS INTEGER) <= %s"
                parametros.append(int(ano_fim_filtro))

            query += " ORDER BY id DESC"
            cursor.execute(query, parametros)
            return cursor.fetchall()
    finally:
        devolver_conexao(conn)

# ==========================================================
# FUNÇÕES DA TABELA E FILTROS
# ==========================================================

async def carregar_tabela():
    tabela.selected = []
    atualizar_painel_campanha()

    dados = await asyncio.to_thread(
        _buscar_clientes_db,
        marca.value,
        modelo.value,
        ano_inicio.value,
        ano_fim.value
    )

    tabela.rows = [
        {
            "id": c[0],
            "nome": c[1],
            "whatsapp": c[2],
            "cidade": c[3],
            "marca": c[4],
            "modelo": c[5],
            "ano": c[6],
            "data": c[7].strftime("%d/%m/%Y %H:%M") if c[7] else ""
        }
        for c in dados
    ]

    tabela.update()
    contador.text = f"🚛 Total de registros localizados: {len(dados)}"

def mudou_marca():
    modelo.set_options(modelos.get(marca.value, []))
    modelo.value = None

async def limpar_filtros():
    marca.value = None
    modelo.value = None
    ano_inicio.value = None
    ano_fim.value = None
    await carregar_tabela()

# ==========================================================
# GERENCIAMENTO DE CAMPANHA E UPLOAD
# ==========================================================

def salvar_arquivo(e):
    global arquivo_promocao_path
    caminho = os.path.join(PASTA_PROMOCOES, e.name)
    
    with open(caminho, 'wb') as f:
        f.write(e.content.read())
        
    arquivo_promocao_path = caminho
    status_arquivo.text = f"📎 Arquivo pronto: {e.name}"
    ui.notify(f"Arquivo '{e.name}' pronto para a promoção!", color="positive")

def atualizar_painel_campanha(e=None):
    qtd = len(tabela.selected)
    info_selecionados.text = f"🎯 {qtd} cliente(s) selecionado(s) para a campanha."

def gerar_link_wa(cliente):
    numero = "".join(filter(str.isdigit, cliente["whatsapp"]))
    if not numero.startswith("55"):
        numero = "55" + numero

    # Substituição das variáveis dinâmicas na mensagem
    texto = texto_mensagem.value.format(
        nome=cliente.get("nome", ""),
        marca=cliente.get("marca", ""),
        modelo=cliente.get("modelo", ""),
        ano=cliente.get("ano", "")
    )

    texto_encoded = urllib.parse.quote(texto)
    return f"https://wa.me/{numero}?text={texto_encoded}"

def abrir_campanha():
    if not tabela.selected:
        ui.notify("Selecione pelo menos um cliente na tabela!", color="warning")
        return

    dialog = ui.dialog()
    with dialog, ui.card().classes("w-full max-w-2xl"):
        ui.label("🚀 Fila de Envio da Campanha").classes("text-h6 font-bold")
        ui.label("Clique no botão de cada cliente para abrir a conversa com a mensagem pronta.").classes("text-sm text-gray-600 mb-2")

        with ui.scroll_area().classes("h-64 border rounded p-2 w-full"):
            for c in tabela.selected:
                with ui.row().classes("items-center justify-between w-full border-b py-2"):
                    ui.label(f"{c['nome']} ({c['marca']} {c['modelo']} - {c['ano']})").classes("font-semibold text-sm")
                    link = gerar_link_wa(c)
                    ui.button("Enviar WhatsApp 📲", on_click=lambda l=link: ui.navigate.to(l, new_tab=True)).props("color=positive size=sm")

        ui.button("Fechar", on_click=dialog.close).classes("mt-4 align-right")
    
    dialog.open()

# ==========================================================
# EXCLUSÃO EM LOTE
# ==========================================================

def confirmar_exclusao():
    if not tabela.selected:
        ui.notify("Selecione pelo menos um cliente para excluir.", color="warning")
        return

    qtd = len(tabela.selected)
    dialog = ui.dialog()

    with dialog, ui.card():
        ui.label(f"Deseja excluir os {qtd} cliente(s) selecionado(s)?").classes("font-bold")

        with ui.row().classes("mt-4"):
            async def deletar():
                for c in tabela.selected:
                    await asyncio.to_thread(excluir_cliente, c["id"])
                dialog.close()
                await carregar_tabela()
                ui.notify(f"{qtd} cliente(s) excluído(s)!", color="positive")

            ui.button("Sim, Excluir", on_click=deletar).props("color=negative")
            ui.button("Cancelar", on_click=dialog.close)

    dialog.open()

# ==========================================================
# INTERFACE GRÁFICA
# ==========================================================

ui.label("🚛 Painel Administrativo - Auto Peças Estilo").classes("text-h5 font-bold mb-1")
contador = ui.label("🚛 Total de registros localizados: 0").classes("text-subtitle1 text-gray-600 mb-4")

# FILTROS
with ui.card().classes("w-full p-4 mb-4"):
    ui.label("🔍 Filtros de Busca").classes("font-bold text-gray-700")
    with ui.row().classes("w-full items-center gap-4 mt-2"):
        marca = ui.select(marcas, label="Marca", clearable=True, on_change=mudou_marca).classes("w-40")
        modelo = ui.select([], label="Modelo", clearable=True).classes("w-40")
        ano_inicio = ui.select(anos, label="Ano inicial", clearable=True).classes("w-32")
        ano_fim = ui.select(anos, label="Ano final", clearable=True).classes("w-32")

        ui.button("Filtrar", on_click=carregar_tabela).props("color=primary icon=search")
        ui.button("Limpar", on_click=limpar_filtros).props("outline icon=cleaning_services")

# ÁREA DE CAMPANHAS DE WHATSAPP
with ui.card().classes("w-full p-4 mb-4 bg-blue-50 border-blue-200 border"):
    ui.label("📢 Criar Campanha de Promoção").classes("font-bold text-blue-900 text-lg")
    
    with ui.row().classes("w-full items-start gap-6 mt-2"):
        # Mensagem Customizada
        with ui.column().classes("flex-1"):
            ui.label("Mensagem (use {nome}, {marca}, {modelo}, {ano}):").classes("text-xs text-gray-600")
            texto_mensagem = ui.textarea(
                value="Olá {nome}! Tudo bem?\n\nTemos ofertas especiais de peças para o seu caminhão {marca} {modelo} ({ano})! Confira em anexo nossa promoção da semana."
            ).classes("w-full bg-white border rounded p-1").props("rows=4")

        # Anexo de Imagem/PDF
        with ui.column().classes("w-80"):
            ui.label("Anexar Arte / Catálogo PDF:").classes("text-xs text-gray-600")
            ui.upload(on_upload=salvar_arquivo, max_files=1).props("accept='.jpg,.png,.pdf' flat bordered").classes("w-full bg-white")
            status_arquivo = ui.label("Nenhum arquivo anexado").classes("text-xs text-gray-500 italic")

    # Ações da Campanha
    with ui.row().classes("w-full items-center justify-between mt-4 border-t pt-3"):
        info_selecionados = ui.label("🎯 0 cliente(s) selecionado(s) para a campanha.").classes("font-semibold text-blue-800")
        
        with ui.row().classes("gap-2"):
            ui.button("🗑️ Excluir Selecionados", on_click=confirmar_exclusao).props("color=negative flat")
            ui.button("🚀 Iniciar Envio das Promoções", on_click=abrir_campanha).props("color=positive icon=send")

# TABELA COM SELEÇÃO MÚLTIPLA
colunas = [
    {"name": "nome", "label": "Nome", "field": "nome", "align": "left"},
    {"name": "whatsapp", "label": "WhatsApp", "field": "whatsapp", "align": "left"},
    {"name": "marca", "label": "Marca", "field": "marca", "align": "left"},
    {"name": "modelo", "label": "Modelo", "field": "modelo", "align": "left"},
    {"name": "ano", "label": "Ano", "field": "ano", "align": "center"},
    {"name": "data", "label": "Cadastro", "field": "data", "align": "center"}
]

tabela = ui.table(
    columns=colunas,
    rows=[],
    row_key="id",
    selection="multiple",
    on_select=atualizar_painel_campanha
).classes("w-full")

# Inicialização assíncrona da tabela
ui.timer(0.1, carregar_tabela, once=True)

# START
ui.run(
    title="Admin Auto Peças Estilo",
    host="0.0.0.0",
    port=8081
)