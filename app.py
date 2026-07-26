from nicegui import ui
from database import salvar_cliente, cliente_existe
import re
import asyncio

# ==========================================================
# CSS
# ==========================================================

ui.add_head_html("""
<style>
body {
    margin: 0;
    font-family: Arial, Helvetica, sans-serif;
    background: linear-gradient(135deg, #000000, #1c1c1c, #ff2d7a);
}

.card {
    width: 90%;
    max-width: 430px;
    background: white;
    border-radius: 20px;
    padding: 30px;
    box-sizing: border-box;
    box-shadow: 0px 15px 35px rgba(0,0,0,.35);
}

.subtitulo {
    text-align: center;
    color: #666;
    font-size: 18px;
    font-weight: bold;
    margin-bottom: 25px;
    line-height: 1.4;
}

.q-btn {
    background: #ff2d7a !important;
    color: white !important;
    width: 100%;
    height: 52px;
    font-size: 17px;
    font-weight: bold;
    border-radius: 10px;
}

.q-btn:hover {
    background: #e60073 !important;
}
</style>
""")

# ==========================================================
# MODELOS
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

# ==========================================================
# FUNÇÕES
# ==========================================================

def limpar_telefone(numero):
    return re.sub(r'\D', '', numero or '')

def telefone_valido(numero):
    return len(limpar_telefone(numero)) == 11

def limpar_formulario():
    nome.value = ""
    whatsapp.value = ""
    cidade.value = ""
    marca.value = None
    modelo.value = None
    ano.value = None
    aceite.value = False
    modelo.set_options([])

def mudou_marca():
    modelo.set_options(modelos.get(marca.value, []))
    modelo.value = None

# ==========================================================
# CADASTRO
# ==========================================================

async def cadastrar_cliente():
    btn_cadastrar.disable()
    btn_cadastrar.text = "Salvando..."

    try:
        nome_cliente = (nome.value or "").strip()
        telefone = limpar_telefone(whatsapp.value)
        cidade_cliente = (cidade.value or "").strip()

        # -------------------------
        # VALIDAÇÕES
        # -------------------------
        if len(nome_cliente) < 3:
            ui.notify("Informe seu nome completo.", color="negative")
            return

        if not telefone_valido(whatsapp.value):
            ui.notify("Informe um WhatsApp válido.", color="negative")
            return

        if len(cidade_cliente) < 2:
            ui.notify("Informe sua cidade.", color="negative")
            return

        if not marca.value:
            ui.notify("Selecione a marca.", color="negative")
            return

        if not modelo.value:
            ui.notify("Selecione o modelo.", color="negative")
            return

        if not ano.value:
            ui.notify("Selecione o ano.", color="negative")
            return

        if not aceite.value:
            ui.notify("Aceite receber promoções.", color="negative")
            return

        # -------------------------
        # VERIFICAR DUPLICIDADE EM THREAD SEPARADA (Rápido / Não Trava)
        # -------------------------
        existe = await asyncio.to_thread(
            cliente_existe, 
            telefone, 
            marca.value, 
            modelo.value, 
            ano.value
        )

        if existe:
            ui.notify(
                "Você já cadastrou este exato caminhão anteriormente!", 
                color="warning"
            )
            return

        # -------------------------
        # SALVAR EM THREAD SEPARADA (Sem travamento de UI)
        # -------------------------
        await asyncio.to_thread(
            salvar_cliente,
            nome_cliente,
            telefone,
            cidade_cliente,
            marca.value,
            modelo.value,
            ano.value
        )

        ui.notify("✅ Cadastro realizado com sucesso!", color="positive")

        container_form.set_visibility(False)
        container_sucesso.set_visibility(True)

    except Exception as e:
        print(e)
        ui.notify("Erro ao realizar cadastro.", color="negative")

    finally:
        btn_cadastrar.enable()
        btn_cadastrar.text = "🚛 QUERO RECEBER PROMOÇÕES"

def novo_cadastro():
    limpar_formulario()
    container_sucesso.set_visibility(False)
    container_form.set_visibility(True)

# ==========================================================
# INTERFACE
# ==========================================================

with ui.column().classes("items-center justify-center w-full min-h-screen"):
    with ui.card().classes("card"):
        ui.image("static/logo.png").style("width:180px;margin:auto;display:block;")

        with ui.column().classes("w-full") as container_form:
            ui.html("""
            <div class="subtitulo">
            Cadastre seu caminhão e receba promoções exclusivas.
            </div>
            """)

            nome = ui.input(label="Nome completo").props("maxlength=80").classes("w-full")
            whatsapp = ui.input(label="WhatsApp", placeholder="(14) 99999-9999").props('mask="(##) #####-####" maxlength=15').classes("w-full")
            cidade = ui.input(label="Cidade / UF").props("maxlength=50").classes("w-full")

            marca = ui.select(
                options=list(modelos.keys()), 
                label="Marca", 
                clearable=True, 
                on_change=mudou_marca
            ).classes("w-full")

            modelo = ui.select(
                options=[], 
                label="Modelo", 
                clearable=True
            ).classes("w-full")

            ano = ui.select(
                options=[str(i) for i in range(2026, 1989, -1)], 
                label="Ano", 
                clearable=True
            ).classes("w-full")

            aceite = ui.checkbox("Quero receber promoções e ofertas exclusivas pelo WhatsApp.")

            btn_cadastrar = ui.button(
                "🚛 QUERO RECEBER PROMOÇÕES", 
                on_click=cadastrar_cliente
            ).classes("q-btn mt-2")

        with ui.column().classes("w-full text-center items-center py-4") as container_sucesso:
            container_sucesso.set_visibility(False)

            ui.icon("check_circle", size="64px", color="positive")
            ui.label("Cadastro Realizado!").classes("text-h6 font-bold text-gray-800 mt-2")
            ui.label("Em breve você receberá ofertas e promoções exclusivas diretamente no seu WhatsApp.").classes("text-body2 text-gray-600 mb-6")

            ui.button("Cadastrar outro caminhão", on_click=novo_cadastro).props("outline color=primary").classes("w-full")

# ==========================================================
# START
# ==========================================================

ui.run(
    title="Auto Peças Estilo",
    host="0.0.0.0",
    port=8080
)