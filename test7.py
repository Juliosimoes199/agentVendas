import google.generativeai as genai
import streamlit as st
from streamlit_chat import message
import streamlit.components.v1 as components
from prometheus_client import Counter, Histogram, generate_latest, REGISTRY
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

genai.configure(api_key="AIzaSyArTog-quWD9Tqf-CkkFAq_-UOZfK1FTtA")

# *** MOVA ESTA LINHA PARA CÁ: ***
st.set_page_config(page_title="Seu Assistente de Compras Inteligente 🧠", page_icon="🧠")

# --- Dados dos Produtos (Exemplo Hardcoded) ---
produtos = {
    "camiseta_algodao": {
        "nome": "Camiseta de Algodão Premium",
        "descricao": "Feita com algodão orgânico super macio. Disponível em diversas cores e tamanhos.",
        "preco": 5589.99,
        "disponibilidade": True,
        "variantes": {
            "cores": ["#1f77b4", "#2ca02c", "#7f7f7f", "#000000"],  # Cores em hexadecimal
            "tamanhos": ["P", "M", "G", "GG"]
        },
        "envio": "2000,00 kz para toda Luanda. Entrega em 3-7 dias úteis.",
        "devolucao": "Aceitamos devoluções em até 30 dias."
    },
    "caneca_ceramica": {
        "nome": "Caneca de Cerâmica Personalizada",
        "descricao": "Caneca de cerâmica de alta qualidade, ideal para bebidas quentes ou frias. Pode ser personalizada com sua foto ou texto.",
        "preco": 760.78,
        "disponibilidade": True,
        "envio": "1000,00 kz para toda Luanda. Entrega em 5-10 dias úteis.",
        "devolucao": "Não aceitamos devoluções de produtos personalizados."
    }
    # Adicione mais produtos aqui
}

@st.cache_resource
def initialize_metrics():
    request_count = Counter('app_requests_total', 'Total number of requests to the app')
    response_latency = Histogram('app_response_latency_seconds', 'Response latency in seconds')
    agent_interaction_count = Counter('agent_interactions_total', 'Total number of interactions with the sales agent')
    return request_count, response_latency, agent_interaction_count

REQUEST_COUNT, RESPONSE_LATENCY, AGENT_INTERACTION_COUNT = initialize_metrics()

def agente_de_vendas(pergunta_usuario, historico_conversa, produtos_conhecimento=produtos):
    """
    Agente para responder perguntas sobre produtos, lembrando do histórico da conversa.
    """
    start_time = time.time()
    model_vendas = genai.GenerativeModel('gemini-2.0-flash-exp')

    prompt_vendas = f"""Você é um agente de vendas especializado nos seguintes produtos:\n\n"""
    for nome, detalhes in produtos_conhecimento.items():
        prompt_vendas += f"- **{detalhes['nome']}**: {detalhes['descricao']} Preço:{detalhes['preco']:.2f} kz. "
        if detalhes['disponibilidade']:
            prompt_vendas += "Disponível."
        else:
            prompt_vendas += "Indisponível."
        if "variantes" in detalhes:
            prompt_vendas += f" Variantes: Cores: {', '.join([f'<span style="color:{cor}">●</span>' for cor in detalhes['variantes'].get('cores', [])])}, Tamanhos: {', '.join(detalhes['variantes'].get('tamanhos', []) )}."
        prompt_vendas += "\n"

    # Adiciona o histórico da conversa ao prompt
    prompt_vendas += "\nHistórico da Conversa:\n"
    for turno in historico_conversa:
        prompt_vendas += f"{'Usuário' if turno['is_user'] else 'Agente'}: {turno['content']}\n"

    prompt_vendas += f"""\nCom base nas informações acima e no histórico da conversa, responda à seguinte pergunta do usuário da melhor forma possível para auxiliar na venda:\n\n"{pergunta_usuario}"\n\nSe o usuário perguntar sobre um produto específico, forneça detalhes relevantes como descrição, preço, disponibilidade e variantes. Se o usuário quiser comprar, informe os próximos passos. Tente lembrar de informações ditas anteriormente na conversa para fornecer respostas mais contextuais e personalizadas. Seja amigável e persuasivo."""

    response_vendas = model_vendas.generate_content(prompt_vendas)
    latency = time.time() - start_time
    RESPONSE_LATENCY.observe(latency)
    AGENT_INTERACTION_COUNT.inc()
    return response_vendas.text

# --- Interface Streamlit Aprimorada e Mais Atraente com Memória ---
# st.set_page_config(page_title="Seu Assistente de Compras Inteligente 🧠", page_icon="🧠") # REMOVA DAQUI

# Custom CSS para estilos (mantido)
st.markdown(
    """
    <style>
        .stChatInputContainer {
            position: fixed;
            bottom: 0;
            background-color: white;
            padding: 16px;
            border-top: 1px solid #eee;
        }
        .streamlit-expander header:first-child {
            font-size: 16px;
            font-weight: bold;
        }
        .user-message {
            background-color: #e1f5fe !important; /* Azul claro */
            color: black !important;
            border-radius: 8px;
            padding: 8px 12px;
            margin-bottom: 8px;
            width: fit-content;
            float: right;
            clear: both;
        }
        .agent-message {
            background-color: #f0f4c3 !important; /* Amarelo claro */
            color: black !important;
            border-radius: 8px;
            padding: 8px 12px;
            margin-bottom: 8px;
            width: fit-content;
            float: left;
            clear: both;
        }
        .sidebar .sidebar-content {
            padding-top: 1rem;
        }
        .sidebar-subheader {
            font-size: 14px;
            font-weight: bold;
            margin-top: 10px;
        }
        .sidebar-item {
            font-size: 12px;
            margin-bottom: 5px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Seu Assistente de Compras Inteligente 🧠")
st.markdown("Olá! 👋 Estou aqui para te ajudar com suas compras.")

# Inicializa o histórico de mensagens
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# Exibe o histórico de mensagens com estilos personalizados
for msg in st.session_state["messages"]:
    if msg["is_user"]:
        st.markdown(f'<div class="user-message"><i class="fa fa-user-circle"></i> {msg["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="agent-message"><i class="fa fa-robot"></i> {msg["content"]}</div>', unsafe_allow_html=True)

# Caixa de entrada para o usuário
if prompt := st.chat_input("Digite sua pergunta aqui..."):
    REQUEST_COUNT.inc()
    st.session_state["messages"].append({"content": prompt, "is_user": True})
    st.markdown(f'<div class="user-message"><i class="fa fa-user-circle"></i> {prompt}</div>', unsafe_allow_html=True)

    # Obtém a resposta do agente, passando o histórico da conversa
    resposta_do_agente = agente_de_vendas(prompt, st.session_state["messages"])
    st.session_state["messages"].append({"content": resposta_do_agente, "is_user": False})
    st.markdown(f'<div class="agent-message"><i class="fa fa-robot"></i> {resposta_do_agente}</div>', unsafe_allow_html=True)

# Barra Lateral com visual aprimorado (mantido)
with st.sidebar:
    st.header("Detalhes dos Produtos")
    for nome, detalhes in produtos.items():
        with st.expander(f"**{detalhes['nome']}**", expanded=False):
            st.markdown(f"<p class='sidebar-item'>Preço: {detalhes['preco']:.2f} kz</p>", unsafe_allow_html=True)
            st.markdown(f"<p class='sidebar-item'>Disponibilidade: {'<span style=\"color:green\">✅ Disponível</span>' if detalhes['disponibilidade'] else '<span style=\"color:red\">❌ Indisponível</span>'}</p>", unsafe_allow_html=True)
            if "variantes" in detalhes:
                if "cores" in detalhes['variantes']:
                    cores_html = " ".join([f'<span style="color:{cor}">●</span>' for cor in detalhes['variantes']['cores']])
                    st.markdown(f"<p class='sidebar-item'>Cores: {cores_html}</p>", unsafe_allow_html=True)
                if "tamanhos" in detalhes['variantes']:
                    st.markdown(f"<p class='sidebar-item'>Tamanhos: {', '.join(detalhes['variantes']['tamanhos'])}</p>", unsafe_allow_html=True)
            st.markdown(f"<p class='sidebar-item'>Envio: {detalhes['envio']}</p>", unsafe_allow_html=True)
            st.markdown(f"<p class='sidebar-item'>Devolução: {detalhes['devolucao']}</p>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("Sua Compra Inteligente❤️")

# Adiciona a biblioteca Font Awesome para os ícones (mantido)
components.html(
    """
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" integrity="sha512-9usAa10IRO0HhonpyAIVpjrylPvoDwiPUiKdWk5t3PyolY1cOd4DSE0Ga+ri4AuTroPR5aQvXU9xC6qOPnzFeg==" crossorigin="anonymous" referrerpolicy="no-referrer" />
    """,
    height=0,
)

# Exponha as métricas em uma rota HTTP
class MetricsHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/metrics':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.wfile.write(generate_latest(REGISTRY))
        else:
            self.send_response(404)
            self.end_headers()

def run_metrics_server(port=8000):
    httpd = HTTPServer(('0.0.0.0', port), MetricsHandler)
    httpd.serve_forever()

if __name__ == '__main__':
    metrics_thread = threading.Thread(target=run_metrics_server)
    metrics_thread.daemon = True
    metrics_thread.start()
    # O loop principal do Streamlit continua rodando aqui
