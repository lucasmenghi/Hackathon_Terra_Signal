"""
config/theme.py
Tema visual e componentes HTML compartilhados entre todas as páginas.
Segue o padrão dos painéis do André (header com logo, títulos de seção, cards) com a paleta do projeto Terra Signal.
"""

import base64
from pathlib import Path

import streamlit as st

BASE_DIR = Path(__file__).parent.parent
ASSETS = BASE_DIR / "assets"

# Paleta do projeto (a mesma dos notebooks: COR, DESTAQUE, CINZA, TEXTO do _comum)
COR = "#1f6f8b"          # cor principal: o dado em foco
COR_ESCURA = "#174f63"
COR_CLARA = "#E6F1F5"
DESTAQUE = "#d9822b"     # destaque: o que pede atenção
CINZA = "#B0B0B0"        # contexto: o que serve de comparação
CINZA_CLARO = "#E5E7EB"
TEXTO = "#333333"
TEXTO_2 = "#4B5563"       # texto secundário: contraste de 7,5:1 no branco

# Segmentos do notebook 07 (K-means no comportamento), quadrantes e faixas de risco: a legenda do app inteiro
SEGMENTOS = {
    "S1": ("Fibra no mensal, pouca proteção", "fibra, contrato mensal, quase sem suporte e segurança; 55% de churn, 41% da receita"),
    "S2": ("DSL no mensal, clientes novos", "DSL, contrato mensal, até cerca de 1 ano de casa; 32% de churn"),
    "S3": ("Contrato anual", "contrato de um ano; 15% de churn"),
    "S4": ("Só telefonia", "sem internet, mensalidade baixa; 7% de churn"),
    "S5": ("Fiéis de dois anos", "contrato de dois anos e pacote completo; 5% de churn"),
}
QUADRANTES = {
    "Salvar já": "risco alto e mensalidade alta: oferta forte",
    "Ação barata": "risco alto e mensalidade baixa: e-mail ou aviso no app",
    "Fidelizar": "risco baixo e mensalidade alta: relacionamento, sem incomodar",
    "Manter": "risco baixo e mensalidade baixa: nenhuma ação",
}

# Semáforo do monitoramento
STATUS_COR = {"estável": "#3A7D44", "atenção": "#E0A100", "alerta": "#C0392B", "aguardando": "#9CA3AF"}
STATUS_FUNDO = {"estável": "#E8F3EA", "atenção": "#FDF4D9", "alerta": "#F9E3E0", "aguardando": "#F3F4F6"}


def aplicar_tema():
    """Aplica o CSS global do app. Chamar no início de cada página."""
    st.markdown(f"""
<style>
:root {{
    --cor:            {COR};
    --cor-escura:     {COR_ESCURA};
    --cor-clara:      {COR_CLARA};
    --destaque:       {DESTAQUE};
    --text-primary:   #1A1A1A;
    --text-secondary: {TEXTO_2};
    --bg-main:        #F8FAFA;
    --bg-white:       #FFFFFF;
    --border:         {CINZA_CLARO};
    --shadow:         0 1px 4px rgba(0,0,0,0.07);
}}

html, body {{
    font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif !important;
    background-color: var(--bg-main) !important;
    color: var(--text-primary) !important;
}}
[class*="css"] {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif !important; }}
.block-container {{ padding-top: 1.6rem; padding-bottom: 2rem; }}

/* ── Sidebar ── */
[data-testid="stSidebar"] {{
    background-color: var(--bg-white) !important;
    border-right: 1px solid var(--border) !important;
}}
[data-testid="stSidebarNav"] {{ padding-top: 1.2rem !important; }}
[data-testid="stSidebarNav"] a {{
    padding: 9px 16px !important;
    border-radius: 8px !important;
    font-size: 14px !important;
    font-weight: 500 !important;
}}
[data-testid="stSidebarNav"] a:hover {{ background: var(--cor-clara) !important; }}
[data-testid="stSidebarNav"] a[aria-current="page"] {{
    background: var(--cor-clara) !important;
    font-weight: 600 !important;
}}

/* ── Header com logo ── */
.ts-header {{
    display: flex; align-items: center; gap: 1.2rem;
    padding: 0.4rem 0 1.1rem; border-bottom: 1px solid var(--border); margin-bottom: 1.4rem;
}}
.ts-header img {{ height: 130px; width: auto; max-width: 260px; object-fit: contain; }}
.ts-header-divider {{ width: 1px; height: 96px; background: var(--border); }}
.ts-header-text h1 {{ font-size: 2rem; font-weight: 700; margin: 0; color: var(--text-primary); }}
.ts-header-text p {{ font-size: 13px; color: var(--text-secondary); margin: 4px 0 0; }}

/* ── Títulos de seção (editorial) ── */
.ts-label {{ font-size:13px; font-weight: 600; color: var(--text-secondary); text-transform: uppercase;
             letter-spacing: 0.08em; margin: 1.6rem 0 4px; }}
.ts-titulo {{ font-size: 1.35rem; font-weight: 700; color: var(--text-primary); margin: 0 0 4px; }}
.ts-desc {{ font-size: 14px; color: var(--text-secondary); margin: 0 0 0.9rem; line-height: 1.55; }}

/* ── Cards da Home ── */
.ts-card {{
    background: var(--bg-white); border: 1px solid var(--border); border-radius: 12px;
    padding: 1.2rem 1.3rem; box-shadow: var(--shadow); min-height: 175px;
    display: flex; flex-direction: column;
}}
.ts-card:hover {{ border-color: var(--cor); box-shadow: 0 4px 12px rgba(31,111,139,0.12); }}
.ts-card-title {{ font-size: 1.05rem; font-weight: 700; color: var(--text-primary); margin: 0 0 4px; }}
.ts-card-subtitle {{ font-size: 13px; color: var(--text-secondary); margin: 0 0 10px; }}
.ts-card-desc {{ font-size: 13.5px; color: var(--text-primary); line-height: 1.5; margin: 0 0 12px; flex-grow: 1; }}
.ts-tag {{
    display: inline-block; background: var(--cor-clara); color: var(--cor-escura); font-size:13px; font-weight: 600;
    padding: 3px 10px; border-radius: 12px; margin: 0 5px 4px 0;
}}

/* ── Cartões de número (KPI) ── */
.ts-kpi {{
    background: var(--bg-white); border: 1px solid var(--border); border-radius: 12px; padding: 1rem 1.1rem;
    box-shadow: var(--shadow); height: 100%; min-height: 150px;
}}
.ts-kpi-label {{ font-size:13px; font-weight: 600; color: var(--text-secondary); text-transform: uppercase;
                 letter-spacing: 0.05em; margin: 0; }}
.ts-kpi-valor {{ font-size: 2rem; font-weight: 700; margin: 6px 0 2px; line-height: 1.1; }}
.ts-kpi-nota {{ font-size:13.5px; color: var(--text-secondary); margin: 0; }}
.ts-pill {{ display: inline-block; font-size:13px; font-weight: 700; padding: 2px 9px; border-radius: 10px;
            text-transform: uppercase; letter-spacing: 0.04em; }}

/* ── Caixa "Como ler" ── */
.ts-leitura {{
    background: var(--bg-white); border: 1px solid var(--border); border-left: 4px solid var(--cor);
    border-radius: 8px; padding: 0.8rem 1rem; margin: 0.4rem 0 1.2rem; font-size: 13.5px; line-height: 1.55;
}}
.ts-leitura b {{ color: var(--cor-escura); }}

hr {{ border-color: var(--border) !important; }}
[data-testid="stCaptionContainer"] {{ color: #4B5563 !important; font-size:13px !important; }}
</style>
""", unsafe_allow_html=True)


def imagem_base64(nome_arquivo: str):
    """Lê uma imagem de assets/ e devolve como data URI (base64). Sem o arquivo, devolve None."""
    path = ASSETS / nome_arquivo
    if not path.exists():
        return None
    ext = path.suffix.lower().lstrip(".")
    mime = "image/svg+xml" if ext == "svg" else f"image/{'jpeg' if ext == 'jpg' else ext}"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode()}"


def logo_base64():
    for ext in ["png", "svg", "jpg", "jpeg"]:
        src = imagem_base64(f"logo.{ext}")
        if src:
            return src
    return None


def page_header(titulo: str, subtitulo: str = "", imagem: str = ""):
    """Header padrão de cada página: [logo ou imagem da página] | [título / subtítulo]."""
    src = imagem_base64(imagem) if imagem else None
    src = src or logo_base64()
    logo_html = (f'<img src="{src}" />' if src else
                 f'<span style="font-size:1.3rem;font-weight:700;color:{COR};">Terra Signal</span>')
    sub_html = f"<p>{subtitulo}</p>" if subtitulo else ""
    st.markdown(f"""
<div class="ts-header">
    {logo_html}
    <div class="ts-header-divider"></div>
    <div class="ts-header-text"><h1>{titulo}</h1>{sub_html}</div>
</div>
""", unsafe_allow_html=True)


def secao_titulo(label: str, titulo: str, descricao: str = ""):
    """Bloco editorial: rótulo em caixa alta + título (a conclusão) + descrição."""
    desc = f'<p class="ts-desc">{descricao}</p>' if descricao else ""
    st.markdown(f'<p class="ts-label">{label}</p><p class="ts-titulo">{titulo}</p>{desc}', unsafe_allow_html=True)


def card(titulo: str, subtitulo: str, descricao: str, tags: list):
    tags_html = "".join(f'<span class="ts-tag">{t}</span>' for t in tags)
    st.markdown(f"""
<div class="ts-card">
    <p class="ts-card-title">{titulo}</p>
    <p class="ts-card-subtitle">{subtitulo}</p>
    <p class="ts-card-desc">{descricao}</p>
    <div>{tags_html}</div>
</div>
""", unsafe_allow_html=True)


def pill(status: str) -> str:
    return (f'<span class="ts-pill" style="background:{STATUS_FUNDO.get(status, "#F3F4F6")};'
            f'color:{STATUS_COR.get(status, TEXTO_2)};">{status}</span>')


def kpi(label: str, valor: str, nota: str = "", status: str = "", cor_valor: str = ""):
    cor = cor_valor or (STATUS_COR.get(status) if status else "#1A1A1A")
    pill_html = f" {pill(status)}" if status else ""
    st.markdown(f"""
<div class="ts-kpi">
    <p class="ts-kpi-label">{label}{pill_html}</p>
    <p class="ts-kpi-valor" style="color:{cor};">{valor}</p>
    <p class="ts-kpi-nota">{nota}</p>
</div>
""", unsafe_allow_html=True)


def legenda(itens: list):
    """Legenda de cores visível embaixo de um gráfico. itens = [(cor, texto, forma)]; forma: barra, ponto, linha,
    tracejado ou zona."""
    def marca(cor, forma):
        if forma == "ponto":
            return f'<span style="display:inline-block;width:11px;height:11px;border-radius:50%;background:{cor};"></span>'
        if forma == "linha":
            return f'<span style="display:inline-block;width:20px;height:3px;background:{cor};vertical-align:middle;"></span>'
        if forma == "tracejado":
            return f'<span style="display:inline-block;width:20px;border-top:2px dashed {cor};vertical-align:middle;"></span>'
        if forma == "zona":
            return (f'<span style="display:inline-block;width:18px;height:12px;background:{cor};border:1px solid #D1D5DB;'
                    f'border-radius:2px;"></span>')
        return f'<span style="display:inline-block;width:14px;height:11px;background:{cor};border-radius:2px;"></span>'
    partes = "".join(f'<span style="display:inline-flex;align-items:center;gap:6px;margin:0 16px 4px 0;">{marca(c, f)}'
                     f'<span>{t}</span></span>' for c, t, f in itens)
    st.markdown(f'<div style="font-size:13px;color:#1A1A1A;margin:-0.2rem 0 0.4rem;line-height:1.9;">'
                f'<b style="color:{TEXTO_2};margin-right:10px;">Legenda</b>{partes}</div>', unsafe_allow_html=True)


def explicar(conteudo_md: str, rotulo: str = "Como interpretar"):
    """Botão que abre um quadro sobreposto com a explicação (popover), para não ocupar a página."""
    with st.popover(rotulo):
        st.markdown(conteudo_md)


def como_ler(onde: str, observar: str, comparar: str, achado: str, termos: dict | None = None,
             itens_legenda: list | None = None):
    """Legenda visível e o botão "Como interpretar": onde olhar, o que observar, o que comparar, o achado e os termos."""
    if itens_legenda:
        legenda(itens_legenda)
    texto = (f"**Onde olhar:** {onde}\n\n**O que observar:** {observar}\n\n**O que comparar:** {comparar}\n\n"
             f"**Achado:** {achado}")
    if termos:
        texto += "\n\n---\n\n" + "\n\n".join(f"**{t}:** {d}" for t, d in termos.items())
    explicar(texto)


def virg(x, d=1) -> str:
    """Número no padrão brasileiro: 1.234,5."""
    if x is None:
        return "—"
    try:
        if x != x:          # NaN
            return "—"
    except TypeError:
        return str(x)
    return f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")
