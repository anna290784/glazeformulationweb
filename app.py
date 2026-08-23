# -*- coding: utf-8 -*-
"""Web app Streamlit: dalla formula Seger UMF alla ricetta. Solo calcolo, nessun salvataggio."""
from __future__ import annotations

import importlib
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

import engine as e
import diagrammi as d
importlib.reload(e)
importlib.reload(d)

st.set_page_config(
    page_title="un1cum ceramica — Glaze Formulation Web",
    page_icon="logo_un1cum.png",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.session_state.materie = e.carica_materie_prime()
if "ricetta" in st.session_state:
    st.session_state.ricetta = [
        r for r in (st.session_state.ricetta or [])
        if r.get("materia") in st.session_state.materie
    ]
if "archivio" not in st.session_state:
    st.session_state.archivio = e.carica_archivio()
if "ricetta" not in st.session_state:
    st.session_state.ricetta = []
if "target" not in st.session_state:
    st.session_state.target = {}
if "totale" not in st.session_state:
    st.session_state.totale = 100.0
if "errore" not in st.session_state:
    st.session_state.errore = ""
if "info" not in st.session_state:
    st.session_state.info = ""
if "status" not in st.session_state:
    st.session_state.status = "Pronto"


def _parse_num(raw, lo=0.0, hi=5000.0):
    s = str(raw if raw is not None else "0").strip().replace(",", ".")
    if s in ("", ".", "-"):
        return 0.0
    try:
        v = float(s)
    except ValueError:
        return 0.0
    return max(lo, min(hi, v))


if st.session_state.pop("_svuota_umf", False):
    for o in e.OSSIDI_FORMULA_INPUT:
        st.session_state[f"umf_{o}"] = ""
    st.session_state.totale_batch = "100"
for o in ("K2O", "Na2O"):
    st.session_state.pop(f"umf_{o}", None)
for o in e.OSSIDI_FORMULA_INPUT:
    k = f"umf_{o}"
    if k not in st.session_state:
        st.session_state[k] = ""
    elif isinstance(st.session_state[k], (int, float)):
        st.session_state[k] = (
            "" if float(st.session_state[k]) == 0 else f"{st.session_state[k]:g}")
    elif str(st.session_state[k]).strip().replace(",", ".") in ("0", "0.0", "0.00"):
        st.session_state[k] = ""
if "totale_batch" not in st.session_state:
    st.session_state.totale_batch = "100"
elif isinstance(st.session_state.totale_batch, (int, float)):
    st.session_state.totale_batch = f"{float(st.session_state.totale_batch):g}"
if "totale_necessario" not in st.session_state:
    st.session_state.totale_necessario = f"{float(st.session_state.totale):g}"
elif isinstance(st.session_state.totale_necessario, (int, float)):
    st.session_state.totale_necessario = f"{float(st.session_state.totale_necessario):g}"

MATERIE = st.session_state.materie
NOMI_MATERIE = sorted(MATERIE.keys())
LOGO = Path(__file__).resolve().parent / "logo_un1cum.png"

CSS = """
<style>
@import url("https://fonts.googleapis.com/css2?family=Segoe+UI:wght@400;600;700&display=swap");

html, body, [data-testid="stAppViewContainer"], .stApp {
    background: #141418 !important;
    color: #E8E8EE !important;
    font-family: "Segoe UI", "Segoe UI Variable", sans-serif !important;
}
[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stToolbar"], [data-testid="stDecoration"],
#MainMenu, footer, header { visibility: hidden; height: 0; }
[data-testid="stImage"] button,
[data-testid="stPyplot"] button { display: none !important; }
[data-testid="stPyplot"] {
    max-width: 320px !important;
}
[data-testid="stPyplot"] img {
    max-width: 320px !important;
    width: 320px !important;
    height: auto !important;
}
[data-testid="stToolbar"] { display: none !important; }
.stDeployButton, [data-testid="stStatusWidget"] { display: none !important; }
[data-testid="stSidebar"] { display: none !important; }
.block-container {
    padding-top: 0.4rem !important;
    padding-bottom: 2.4rem !important;
    max-width: 1280px !important;
}

.ga-topbar {
    background: #1E1E26;
    border-bottom: 1px solid #3A3A48;
    margin: -0.4rem -1rem 1rem -1rem;
    padding: 10px 24px;
}
.ga-brand-title {
    font-family: "Segoe UI Semibold", "Segoe UI", sans-serif;
    font-size: 20px !important;
    font-weight: 600;
    color: #FFFFFF !important;
    line-height: 1.15;
    margin: 0;
}
.ga-brand-sub {
    font-size: 14px !important;
    color: #F0F0F4 !important;
    margin: 2px 0 0 0;
}
.ga-accent {
    width: 3px;
    height: 36px;
    background: #FF7A4E;
    border-radius: 2px;
    display: inline-block;
}

.ga-section {
    color: #F8D48A !important;
    font-family: "Segoe UI Semibold", "Segoe UI", sans-serif !important;
    font-size: 18px !important;
    font-weight: 600 !important;
    letter-spacing: 0.02em;
    margin: 6px 0 8px 0 !important;
}
.ga-h2-teal {
    color: #5EE0D0 !important;
    font-family: "Segoe UI Semibold", "Segoe UI", sans-serif !important;
    font-size: 15px !important;
    font-weight: 600 !important;
    margin: 0 0 8px 0 !important;
}
.ga-h2-violet {
    color: #A8B6F0 !important;
    font-family: "Segoe UI Semibold", "Segoe UI", sans-serif !important;
    font-size: 15px !important;
    font-weight: 600 !important;
    margin: 0 0 6px 0 !important;
}
.ga-h2-gold {
    color: #F8D48A !important;
    font-family: "Segoe UI Semibold", "Segoe UI", sans-serif !important;
    font-size: 15px !important;
    font-weight: 600 !important;
    margin: 0 0 6px 0 !important;
}
.ga-col-h {
    font-family: "Segoe UI Semibold", "Segoe UI", sans-serif !important;
    font-size: 14px !important;
    font-weight: 700 !important;
    letter-spacing: 0.06em;
    margin: 0 0 8px 0 !important;
    text-transform: uppercase;
}
[data-testid="stMarkdownContainer"] p.ga-col-h.ga-col-basici,
p.ga-col-h.ga-col-basici { color: #FF9A72 !important; }
[data-testid="stMarkdownContainer"] p.ga-col-h.ga-col-anfoteri,
p.ga-col-h.ga-col-anfoteri { color: #B4C0F8 !important; }
[data-testid="stMarkdownContainer"] p.ga-col-h.ga-col-acidi,
p.ga-col-h.ga-col-acidi { color: #5EE0D0 !important; }
.ga-analisi-riga {
    font-family: Consolas, "Cascadia Mono", "Courier New", monospace !important;
    font-size: 14px !important;
    color: #F4F4F8 !important;
    margin: 0 0 4px 0;
}
.ga-analisi-note {
    color: #D8D8E0;
    font-size: 13px;
    line-height: 1.45;
    margin: 6px 0 4px 0;
}
.ga-hint {
    color: #F0F0F4 !important;
    font-size: 15px !important;
    line-height: 1.5;
    margin: 0 0 4px 0;
}
.ga-mono {
    font-family: Consolas, "Cascadia Mono", "Courier New", monospace !important;
    font-size: 14px !important;
    color: #F4F4F8 !important;
    white-space: pre-wrap;
    line-height: 1.5;
    margin: 0 0 6px 0;
}
.ga-mono-dim {
    font-family: Consolas, "Cascadia Mono", "Courier New", monospace !important;
    font-size: 14px !important;
    color: #D0D0D8 !important;
    white-space: pre-wrap;
    margin: 0 0 6px 0;
}
.ga-scost-ok { color: #7AE08A !important; font-size: 14px; margin: 0 0 8px 0; }
.ga-scost-warn { color: #F8D48A !important; font-size: 14px; margin: 0 0 8px 0; }
.ga-scost-bad { color: #FF9A72 !important; font-size: 14px; margin: 0 0 8px 0; }
.ga-totale {
    color: #5EE0D0 !important;
    font-family: "Segoe UI Semibold", "Segoe UI", sans-serif !important;
    font-size: 15px !important;
    font-weight: 600 !important;
    margin: 8px 0 4px 0 !important;
}
.ga-status {
    position: fixed;
    left: 0; right: 0; bottom: 0;
    background: #1E1E26;
    border-top: 1px solid #3A3A48;
    color: #F0F0F4;
    font-size: 13px;
    padding: 8px 16px;
    z-index: 50;
}
.ga-empty {
    color: #E0E0E8;
    font-size: 15px;
    padding: 18px 8px;
}

[data-testid="stVerticalBlockBorderWrapper"] {
    background: #26262F !important;
    border: 1px solid #3A3A48 !important;
    border-radius: 12px !important;
    padding: 4px 4px 8px 4px !important;
}

[data-testid="stNumberInput"] label p,
[data-testid="stSelectbox"] label p,
[data-testid="stTextInput"] label p,
[data-testid="stWidgetLabel"] p {
    color: #F2F2F6 !important;
    font-size: 14px !important;
    font-weight: 600 !important;
}
[data-testid="stNumberInput"] input,
[data-testid="stTextInput"] input,
[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
    background: #22222C !important;
    color: #FFFFFF !important;
    border: 1px solid #5A5A68 !important;
    border-radius: 8px !important;
    font-size: 16px !important;
    font-family: Consolas, "Cascadia Mono", "Segoe UI", sans-serif !important;
}
[data-testid="stNumberInput"] button {
    background: #22222C !important;
    color: #E8E8EE !important;
    border-color: #5A5A68 !important;
}
[data-testid="InputInstructions"],
[data-testid="stFormSubmitButton"] + div {
    color: #D0D0D8 !important;
}
.stMarkdown p:not([class^="ga-"]),
.stCaption,
[data-testid="stMarkdownContainer"] p:not([class^="ga-"]) {
    color: #F4F4F8 !important;
}
[data-testid="stSelectbox"] div[data-baseweb="select"] * {
    color: #FFFFFF !important;
}

div.stButton > button,
div.stFormSubmitButton > button {
    background: transparent !important;
    border: 1px solid #5A5A68 !important;
    color: #FFFFFF !important;
    border-radius: 8px !important;
    font-family: "Segoe UI", sans-serif !important;
    font-size: 15px !important;
    font-weight: 600 !important;
    height: 38px;
    min-height: 38px;
}
div.stButton > button:hover {
    background: #1E1E26 !important;
    border-color: #3A3A48 !important;
    color: #E8E8EE !important;
}

.st-key-btn_calcola button {
    background: #3DB8A8 !important;
    border: none !important;
    color: #FFFFFF !important;
}
.st-key-btn_calcola button:hover { filter: brightness(1.08); background: #3DB8A8 !important; }
.st-key-btn_scala button {
    background: #3DB8A8 !important;
    border: none !important;
    color: #FFFFFF !important;
}
.st-key-btn_scala button:hover { filter: brightness(1.08); background: #3DB8A8 !important; }

.st-key-btn_aggiungi button,
.st-key-btn_sostituisci button {
    background: #FF7A4E !important;
    border: none !important;
    color: #FFFFFF !important;
}
.st-key-btn_aggiungi button:hover,
.st-key-btn_sostituisci button:hover { background: #FF9470 !important; }

.st-key-btn_rimuovi button,
.st-key-btn_togli button {
    background: #E05555 !important;
    border: none !important;
    color: #FFFFFF !important;
}
.st-key-btn_rimuovi button:hover,
.st-key-btn_togli button:hover { filter: brightness(1.08); background: #E05555 !important; }

[data-testid="stRadio"] {
    background: #22222C;
    border-radius: 6px;
    padding: 6px 8px;
}
[data-testid="stRadio"] label {
    font-family: Consolas, "Cascadia Mono", "Courier New", monospace !important;
    font-size: 15px !important;
    color: #FFFFFF !important;
    padding: 5px 8px !important;
    border-radius: 4px;
}
[data-testid="stRadio"] label p {
    color: #FFFFFF !important;
    font-size: 15px !important;
}
[data-testid="stRadio"] label:has(input:checked) {
    background: #FF7A4E !important;
    color: #FFFFFF !important;
}
[data-testid="stRadio"] label:has(input:checked) p {
    color: #FFFFFF !important;
}
</style>
"""


def formatta_umf_colonne(umf, per_riga=3):
    u = dict(umf or {})
    kna = (
        float(u.get("KNaO", 0) or 0)
        + float(u.get("K2O", 0) or 0)
        + float(u.get("Na2O", 0) or 0)
    )
    u["KNaO"] = kna
    items = []
    for o in e.OSSIDI_FORMULA_INPUT:
        v = float(u.get(o, 0) or 0)
        if abs(v) > 0.001:
            items.append(f"{o:<6} {v:6.3f}")
    if not items:
        return "  —"
    linee = []
    for i in range(0, len(items), per_riga):
        linee.append("  " + "   ".join(items[i:i + per_riga]))
    return "\n".join(linee)


def _target_da_form(valori, totale):
    target = {o: 0.0 for o in e.OSSIDI_TUTTI}
    for o, v in valori.items():
        try:
            target[o] = float(v or 0)
        except (TypeError, ValueError):
            target[o] = 0.0
    if totale <= 0:
        raise ValueError("Il totale batch deve essere maggiore di zero.")
    return target, float(totale)


def _valori_umf_da_stato():
    return {
        o: _parse_num(st.session_state.get(f"umf_{o}", 0), 0.0, 20.0)
        for o in e.OSSIDI_FORMULA_INPUT
    }


def calcola(valori, totale):
    st.session_state.errore = ""
    st.session_state.info = ""
    try:
        valori = {
            o: _parse_num((valori or {}).get(o, 0), 0.0, 20.0)
            for o in e.OSSIDI_FORMULA_INPUT
        }
        if not any(v > 0 for v in valori.values()):
            valori = _valori_umf_da_stato()
        tot = _parse_num(totale, 1.0, 5000.0) or 100.0
        target, tot = _target_da_form(valori, tot)
        norm = e.normalizza_umf_basici(target)
        if norm:
            target = norm
        ricetta = e.genera_ricetta_da_umf(
            target, MATERIE, totale_grammi=tot, df=st.session_state.archivio)
    except ValueError as exc:
        st.session_state.errore = str(exc)
        st.session_state.status = str(exc)
        return
    except Exception as exc:
        st.session_state.errore = f"Errore nel calcolo: {exc}"
        st.session_state.status = st.session_state.errore
        return
    if not ricetta:
        msg = "Impossibile proporre una ricetta con le materie disponibili."
        st.session_state.errore = msg
        st.session_state.status = msg
        return
    st.session_state.target = target
    st.session_state.totale = tot
    st.session_state.totale_necessario = f"{tot:g}"
    st.session_state.ricetta = ricetta
    st.session_state.sel_riga = 0
    st.session_state.info = f"Ricetta proposta: {len(ricetta)} materie, {tot:g} g"
    st.session_state.status = st.session_state.info


def ricalcola_con(materiali, grammi):
    target = st.session_state.target
    if not target:
        st.session_state.errore = "Calcola prima una ricetta dalla formula."
        st.session_state.status = st.session_state.errore
        return
    tot = st.session_state.totale or 100.0
    ricetta = e.ricalcola_ricetta_materiali(
        target, MATERIE, materiali, grammi, totale_grammi=tot)
    if not ricetta:
        st.session_state.errore = (
            "Impossibile ricalcolare la ricetta con le materie attuali.")
        st.session_state.status = st.session_state.errore
        return
    st.session_state.errore = ""
    st.session_state.ricetta = ricetta
    st.session_state.info = "Ricetta ricalcolata sulla formula"
    st.session_state.status = st.session_state.info


def svuota_formula():
    st.session_state._svuota_umf = True
    st.session_state.target = {}
    st.session_state.errore = ""
    st.session_state.info = ""
    st.session_state.status = "Formula svuotata"


def scala_ricetta_a_totale(nuovo_totale):
    ricetta = list(st.session_state.ricetta or [])
    if not ricetta:
        st.session_state.errore = "Calcola prima una ricetta dalla formula."
        st.session_state.status = st.session_state.errore
        return
    tot = _parse_num(nuovo_totale, 0.0, 50000.0)
    if tot <= 0:
        st.session_state.errore = "Inserisci i grammi totali di cui hai bisogno."
        st.session_state.status = st.session_state.errore
        return
    attuale = sum(float(r.get("grammi") or 0) for r in ricetta)
    if attuale <= 0:
        st.session_state.errore = "La ricetta non ha quantità da ricalcolare."
        st.session_state.status = st.session_state.errore
        return
    fattore = tot / attuale
    st.session_state.ricetta = [
        {**r, "grammi": round(float(r.get("grammi") or 0) * fattore, 2)}
        for r in ricetta
    ]
    st.session_state.totale = tot
    st.session_state.errore = ""
    st.session_state.info = f"Quantità ricalcolate per {tot:g} g"
    st.session_state.status = st.session_state.info


def svuota_ricetta():
    st.session_state.ricetta = []
    st.session_state.info = ""
    st.session_state.errore = ""
    st.session_state.status = "Ricetta svuotata"


def umf_da_campi(valori):
    out = {o: 0.0 for o in e.OSSIDI_TUTTI}
    for o, v in (valori or {}).items():
        out[o] = _parse_num(v, 0.0, 20.0)
    return out


def _umf_ha_valori(valori):
    fn = getattr(e, "umf_ha_valori", None)
    if callable(fn):
        return fn(valori)
    return any(float((valori or {}).get(o, 0) or 0) > 0.001 for o in e.OSSIDI_TUTTI)


def umf_per_analisi(valori_form):
    """Come nel desktop: ricetta se c'è e la formula non è cambiata, altrimenti i campi."""
    live = umf_da_campi(valori_form)
    ric = st.session_state.ricetta or []
    target = st.session_state.target or {}
    formula_cambiata = False
    if target and _umf_ha_valori(target):
        live_n = e.normalizza_umf_basici(live) or live
        for o in e.OSSIDI_FORMULA_INPUT:
            if abs(float(live_n.get(o, 0) or 0) - float(target.get(o, 0) or 0)) >= 0.001:
                formula_cambiata = True
                break
    if ric and not formula_cambiata:
        return e.umf_da_ricetta_list(ric, MATERIE), "da ricetta calcolata"
    if _umf_ha_valori(live):
        return live, "da formula target"
    return {}, ""


st.markdown(CSS, unsafe_allow_html=True)
components.html(
    """
<script>
(function () {
  const root = window.parent.document;
  if (!root || root.documentElement.dataset.gaZeroScript === "1") return;
  root.documentElement.dataset.gaZeroScript = "1";
  function isZero(raw) {
    const s = String(raw || "").trim().replace(",", ".");
    if (s === "" || s === "." || s === "-") return false;
    const n = Number(s);
    return Number.isFinite(n) && n === 0;
  }
  function bind(el) {
    if (el.dataset.gaZero === "1") return;
    el.dataset.gaZero = "1";
    el.addEventListener("focus", function () {
      if (isZero(el.value)) {
        el.value = "";
        requestAnimationFrame(function () {
          if (isZero(el.value)) {
            try { el.select(); } catch (err) {}
          }
        });
      } else if (el.value) {
        try { el.select(); } catch (err) {}
      }
    }, true);
  }
  function scan() {
    root.querySelectorAll(
      '[data-testid="stTextInput"] input, [data-testid="stNumberInput"] input'
    ).forEach(bind);
  }
  scan();
  new MutationObserver(scan).observe(root.body, {childList: true, subtree: true});
})();
</script>
""",
    height=0,
)

# —— topbar come l'originale ——
hb1, hb2, hb3 = st.columns([0.09, 0.7, 0.25])
with hb1:
    if LOGO.is_file():
        st.image(str(LOGO), width=48)
    else:
        st.markdown(
            '<div style="color:#FF7A4E;font-size:26px;padding-top:6px;">●</div>',
            unsafe_allow_html=True)
with hb2:
    st.markdown(
        '<p class="ga-brand-title">un1cum ceramica</p>'
        '<p class="ga-brand-sub">Glaze Formulation Web</p>',
        unsafe_allow_html=True)
with hb3:
    st.markdown(
        '<p class="ga-brand-sub" style="text-align:right;padding-top:14px;">'
        "solo calcolo · nessun salvataggio</p>",
        unsafe_allow_html=True)

col_form, col_ric = st.columns([1, 1.08], gap="large")

with col_form:
    st.markdown(
        '<p class="ga-section">= &nbsp; FORMULA SEGER DESIDERATA (UMF)</p>',
        unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown('<p class="ga-h2-teal">OSSIDI UMF</p>', unsafe_allow_html=True)
        campi = {o: 0.0 for o in e.OSSIDI_FORMULA_INPUT}
        gruppi = (
            ("BASICI", "ga-col-basici", e.OSSIDI_BASICI_INPUT),
            ("ANFOTERI", "ga-col-anfoteri", e.OSSIDI_ANFOTERI_INPUT),
            ("ACIDI", "ga-col-acidi", e.OSSIDI_ACIDI_INPUT),
        )
        with st.form("form_umf", border=False, clear_on_submit=False):
            col_b, col_an, col_ac = st.columns(3, gap="medium")
            for col, (titolo, cls, ossidi) in zip((col_b, col_an, col_ac), gruppi):
                with col:
                    st.markdown(
                        f'<p class="ga-col-h {cls}">{titolo}</p>',
                        unsafe_allow_html=True)
                    for ossido in ossidi:
                        campi[ossido] = st.text_input(
                            ossido, key=f"umf_{ossido}", placeholder="0")
            act1, act2 = st.columns([1.15, 1.85])
            with act1:
                totale = st.text_input("Totale batch (g)", key="totale_batch")
            with act2:
                st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                inviato = st.form_submit_button(
                    "CALCOLA RICETTA", width="stretch", key="btn_calcola")
        if inviato:
            calcola(campi, totale)
        if st.button("Svuota formula", key="btn_svuota_form", width="stretch"):
            svuota_formula()
            st.rerun()

    with st.container(border=True):
        st.markdown('<p class="ga-h2-violet">CONFRONTO FORMULA</p>', unsafe_allow_html=True)
        target = st.session_state.target
        ric = st.session_state.ricetta
        if not target or not any(float(target.get(o, 0) or 0) > 0 for o in e.OSSIDI_TUTTI):
            st.markdown('<p class="ga-mono-dim">  Target: —</p>', unsafe_allow_html=True)
            st.markdown('<p class="ga-mono-dim">  Da ricetta: —</p>', unsafe_allow_html=True)
            st.markdown('<p class="ga-mono-dim">  Scostamento: —</p>', unsafe_allow_html=True)
        else:
            st.markdown(
                '<p class="ga-mono">  Target:\n' + formatta_umf_colonne(target) + "</p>",
                unsafe_allow_html=True)
            if not ric:
                st.markdown(
                    '<p class="ga-mono-dim">  Da ricetta: —</p>', unsafe_allow_html=True)
                st.markdown(
                    '<p class="ga-mono-dim">  Scostamento: —</p>', unsafe_allow_html=True)
            else:
                umf = e.umf_da_ricetta_list(ric, MATERIE)
                calc_al, tgt_al, delta, err = e.scostamento_umf(umf, target)
                st.markdown(
                    '<p class="ga-mono">  Da ricetta:\n'
                    + formatta_umf_colonne(calc_al) + "</p>",
                    unsafe_allow_html=True)
                if delta:
                    msg = "  Scostamento: " + ", ".join(
                        f"{o} {d:+.3f}" for o, d in delta[:8])
                    if len(delta) > 8:
                        msg += f" (+{len(delta) - 8})"
                    cls = "ga-scost-warn" if err < 2 else "ga-scost-bad"
                else:
                    msg = "  Scostamento: buon accordo con la formula target."
                    cls = "ga-scost-ok"
                st.markdown(f'<p class="{cls}">{msg}</p>', unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown(
            '<p class="ga-h2-gold">ANALISI IN TEMPO REALE</p>',
            unsafe_allow_html=True)
        umf_an, fonte = umf_per_analisi(campi)
        an = e.analisi_da_umf(umf_an) if umf_an else None
        if not an:
            st.markdown(
                '<p class="ga-mono-dim">  Inserisci gli ossidi: l\'analisi si aggiorna subito.</p>',
                unsafe_allow_html=True)
        else:
            st.markdown(
                f'<p class="ga-hint">  ({fonte})</p>', unsafe_allow_html=True)
            st.markdown(
                f'<p class="ga-analisi-riga">SiO2/Al2O3 -&gt; {an["si_al"]}</p>'
                f'<p class="ga-analisi-riga">Al2O3/SiO2 -&gt; {an["al_si"]}</p>'
                f'<p class="ga-analisi-riga">Somma R2O -&gt; {an["somma_r2o"]}</p>'
                f'<p class="ga-analisi-riga">Somma RO -&gt; {an["somma_ro"]}</p>'
                f'<p class="ga-analisi-riga">COE Teorico -&gt; {an["coe"]}</p>'
                f'<p class="ga-analisi-riga">Rapporto di Acidità RA -&gt; {an["ra"]}'
                f' &nbsp; {an["ra_zona"]}</p>',
                unsafe_allow_html=True)
            st.markdown(
                f'<p class="ga-analisi-riga" style="color:{an["zona_stull_colore"]};">'
                f'Zona Stull -&gt; {an["zona_stull"]}</p>',
                unsafe_allow_html=True)
            st.markdown(
                f'<p class="ga-analisi-riga" style="color:{an["ra_colore"]};">'
                f'{an["ra_indicazione"]}</p>',
                unsafe_allow_html=True)
            if an.get("ra_causa"):
                st.markdown(
                    f'<p class="ga-analisi-note">{an["ra_causa"]}</p>',
                    unsafe_allow_html=True)
            if an.get("ra_effetti"):
                st.markdown(
                    f'<p class="ga-analisi-note">{an["ra_effetti"]}</p>',
                    unsafe_allow_html=True)

with col_ric:
    st.markdown(
        '<p class="ga-section">~ &nbsp; RICETTA PROPOSTA (MODIFICABILE)</p>',
        unsafe_allow_html=True)

    with st.container(border=True):
        with st.form("form_add", border=False, clear_on_submit=False):
            a1, a2, a3 = st.columns([2.4, 1.0, 1.1])
            with a1:
                extra = st.selectbox(
                    "Materia", NOMI_MATERIE or [""],
                    key="add_mat", label_visibility="collapsed")
            with a2:
                extra_g = st.number_input(
                    "grammi", min_value=0.0, max_value=5000.0, value=1.0,
                    step=0.5, format="%.2f", key="add_g",
                    label_visibility="collapsed")
            with a3:
                add_ok = st.form_submit_button(
                    "AGGIUNGI", width="stretch", key="btn_aggiungi")
        if add_ok:
            ricetta = list(st.session_state.ricetta or [])
            if not st.session_state.target:
                st.session_state.errore = "Calcola prima una ricetta dalla formula."
                st.session_state.status = st.session_state.errore
            elif extra in {x["materia"] for x in ricetta}:
                st.session_state.errore = (
                    "Materia già presente. Usala dal menu per sostituirla.")
                st.session_state.status = st.session_state.errore
            else:
                mats = [x["materia"] for x in ricetta] + [extra]
                grams = [float(x["grammi"]) for x in ricetta] + [float(extra_g or 1)]
                ricalcola_con(mats, grams)
            st.rerun()

        ricetta = list(st.session_state.ricetta or [])
        if not ricetta:
            st.markdown(
                '<p class="ga-empty">Imposta la formula e premi CALCOLA RICETTA.</p>',
                unsafe_allow_html=True)
        else:
            if "sel_riga" not in st.session_state:
                st.session_state.sel_riga = 0
            nomi_righe = [
                f"{r['materia']}  —  {float(r['grammi']):g} g" for r in ricetta]
            idx0 = min(int(st.session_state.sel_riga or 0), len(nomi_righe) - 1)
            scelta = st.radio(
                "Seleziona riga", nomi_righe, index=idx0,
                key="radio_riga", label_visibility="collapsed")
            st.session_state.sel_riga = nomi_righe.index(scelta)

            i = st.session_state.sel_riga
            altre = [n for n in NOMI_MATERIE if n != ricetta[i]["materia"]]
            with st.form("form_sost", border=False, clear_on_submit=False):
                s1, s2 = st.columns([2.6, 1.2])
                with s1:
                    sost = st.selectbox(
                        "Sostituisci con", altre,
                        key=f"sost_{i}_{ricetta[i]['materia']}")
                with s2:
                    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                    sost_ok = st.form_submit_button(
                        "SOSTITUISCI", width="stretch", key="btn_sostituisci")
            if sost_ok:
                mats = [x["materia"] for x in ricetta]
                grams = [float(x["grammi"]) for x in ricetta]
                mats[i] = sost
                ricalcola_con(mats, grams)
                st.rerun()

        b1, b2, _ = st.columns([1, 1, 2.2])
        with b1:
            if st.button("SVUOTA", key="btn_svuota_ric", width="stretch"):
                svuota_ricetta()
                st.rerun()
        with b2:
            if st.button("RIMUOVI", key="btn_rimuovi", width="stretch"):
                ricetta = list(st.session_state.ricetta or [])
                if ricetta:
                    i = int(st.session_state.get("sel_riga", 0))
                    i = max(0, min(i, len(ricetta) - 1))
                    rest = [x for j, x in enumerate(ricetta) if j != i]
                    if rest:
                        ricalcola_con(
                            [x["materia"] for x in rest],
                            [float(x["grammi"]) for x in rest])
                    else:
                        svuota_ricetta()
                    st.session_state.sel_riga = 0
                    st.rerun()

        tot_g = sum(float(r.get("grammi") or 0) for r in (st.session_state.ricetta or []))
        if ricetta:
            with st.form("form_scala", border=False, clear_on_submit=False):
                sc1, sc2 = st.columns([1.35, 1.15])
                with sc1:
                    tot_need = st.text_input(
                        "Grammi di cui ho bisogno", key="totale_necessario")
                with sc2:
                    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                    scala_ok = st.form_submit_button(
                        "RICALCOLA QUANTITÀ", width="stretch", key="btn_scala")
            if scala_ok:
                scala_ricetta_a_totale(tot_need)
                st.rerun()
        tot_g = sum(float(r.get("grammi") or 0) for r in (st.session_state.ricetta or []))
        st.markdown(
            f'<p class="ga-totale">Totale ricetta: {tot_g:.3f} g</p>',
            unsafe_allow_html=True)

    st.markdown(
        '<p class="ga-section">* &nbsp; DIAGRAMMI GLAZE FORMULATION</p>',
        unsafe_allow_html=True)
    with st.container(border=True):
        umf_diag, fonte_diag = umf_per_analisi(campi)
        stato_d = d.stato_diagramma(umf_diag)
        if stato_d.get("ok"):
            extra = "in zona" if stato_d.get("in_zona") else "fuori zona"
            st.markdown(
                f'<p class="ga-hint">n.{stato_d["meta"]["n"]}  ·  {fonte_diag}  ·  {extra}</p>',
                unsafe_allow_html=True)
        else:
            st.markdown(
                f'<p class="ga-mono-dim">  {stato_d.get("info", "—")}</p>',
                unsafe_allow_html=True)
        fig = d.disegna_diagramma(stato_d, compatto=True)
        c_diag, _ = st.columns([0.78, 0.22])
        with c_diag:
            st.pyplot(fig, width="content", clear_figure=True)

if st.session_state.errore:
    st.session_state.status = st.session_state.errore

st.markdown(
    f'<div class="ga-status">{st.session_state.status}</div>',
    unsafe_allow_html=True)
