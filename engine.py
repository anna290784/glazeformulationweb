# -*- coding: utf-8 -*-
"""
Motore formula Seger UMF → ricetta.

Logica copiata dal progetto desktop Glaze AI (senza modificarlo):
- umf_da_ricetta_list / ricetta_pesi_seger / accumula_pesi_ossido_ricetta
- genera_ricetta_da_umf e raffinamento grammi
- sostituzione materie: ricalcola_ricetta_materiali
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
MATERIE_FILE = BASE_DIR / "materie_prime.json"
CSV_FILE = BASE_DIR / "database_test_smalti_seger.csv"

OSSIDI_UMF = [
    "SiO2", "Al2O3", "B2O3", "Fe2O3", "TiO2", "CaO", "MgO", "K2O", "Na2O",
    "ZnO", "BaO", "Li2O", "PbO", "SrO", "P2O5", "MnO", "CuO", "CoO", "Cr2O3",
    "NiO", "SnO2", "ZrO2", "V2O5",
]
OSSIDI_BASICI_INPUT = ["KNaO", "CaO", "MgO"]
OSSIDI_ANFOTERI_INPUT = ["Al2O3"]
OSSIDI_ACIDI_INPUT = ["SiO2"]
OSSIDI_FORMULA_INPUT = (
    OSSIDI_BASICI_INPUT + OSSIDI_ANFOTERI_INPUT + OSSIDI_ACIDI_INPUT
)
OSSIDI_FONDENTI = ["KNaO", "K2O", "Na2O", "Li2O", "CaO", "MgO"]
MATERIE_CONSENTITE = [
    "Marmo", "Feldspato", "Caolino", "Wollastonite",
    "Dolomite", "Talco", "Carbonato di Magnesio", "Quarzo",
]
OSSIDI_R2O = ["K2O", "Na2O", "Li2O"]
OSSIDI_RO = ["CaO", "MgO", "ZnO", "BaO", "PbO", "SrO"]
OSSIDI_TUTTI = list(OSSIDI_UMF) + ["KNaO"]

PESI_MOLARI = {
    "SiO2": 60.08, "Al2O3": 101.96, "B2O3": 69.62, "Fe2O3": 159.69,
    "TiO2": 79.87, "CaO": 56.08, "MgO": 40.30, "K2O": 94.20,
    "Na2O": 61.98, "ZnO": 81.39, "BaO": 153.33, "Li2O": 29.88,
    "PbO": 223.20, "SrO": 103.62, "P2O5": 141.94, "MnO": 70.94,
    "MnO2": 86.94, "CuO": 79.55, "CoO": 74.93, "Cr2O3": 151.99,
    "NiO": 74.69, "SnO2": 150.71, "ZrO2": 123.22, "V2O5": 181.88,
    "KNaO": 78.09,
}

# Preferenze materie: solo le 8 materie dello schema web.
PREFERENZE_OSSIDO_MATERIALE = {
    "SiO2": ["Quarzo"],
    "Al2O3": ["Caolino"],
    "CaO": ["Marmo", "Wollastonite"],
    "MgO": ["Talco", "Dolomite", "Carbonato di Magnesio"],
    "K2O": ["Feldspato"],
    "Na2O": ["Feldspato"],
    "KNaO": ["Feldspato"],
}


def _scheda_materia(comp):
    """Formula Seger (coeff. molari) e peso molare della foto, senza ferro."""
    comp = comp or {}
    seger = comp.get("seger")
    if isinstance(seger, dict):
        coeffs = {o: float(seger.get(o, 0) or 0) for o in OSSIDI_FORMULA_INPUT}
    else:
        coeffs = {o: float(comp.get(o, 0) or 0) for o in OSSIDI_FORMULA_INPUT}
        coeffs["KNaO"] = (
            coeffs.get("KNaO", 0.0)
            + float(comp.get("K2O", 0) or 0)
            + float(comp.get("Na2O", 0) or 0)
        )
    try:
        pm = float(comp.get("pm") or 0)
    except (TypeError, ValueError):
        pm = 0.0
    if pm <= 0:
        pm = 100.0
    return coeffs, pm


def carica_materie_prime():
    if not MATERIE_FILE.is_file():
        return {}
    with open(MATERIE_FILE, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        return {}
    return {n: data[n] for n in MATERIE_CONSENTITE if n in data}


def carica_archivio():
    if not CSV_FILE.is_file():
        return pd.DataFrame()
    try:
        return pd.read_csv(CSV_FILE, sep=";")
    except Exception:
        return pd.DataFrame()


def normalizza_nome_materia(nome, materie_prime):
    nome = str(nome or "").strip()
    if nome in materie_prime:
        return nome
    alias = {
        "Talc": "Talco", "talc": "Talco", "TALC": "Talco",
        "Silice": "Quarzo", "Quartz": "Quarzo",
        "Carbonato di Calcio": "Marmo", "Calcite": "Marmo",
        "Feldspato Potassico": "Feldspato", "Feldspato Sodico": "Feldspato",
    }
    alt = alias.get(nome)
    if alt and alt in materie_prime:
        return alt
    low = nome.lower()
    for k in materie_prime:
        if k.lower() == low:
            return k
    return nome


def parse_ricetta_salvata(ricetta_json):
    if pd.isna(ricetta_json) or not str(ricetta_json).strip():
        return []
    try:
        data = json.loads(ricetta_json)
    except Exception:
        return []
    if isinstance(data, dict):
        righe = data.get("righe", data.get("componenti", []))
        if not isinstance(righe, list):
            return []
        if str(data.get("unita", "")).lower() in ("percentuale", "percent", "pct", "%"):
            for r in righe:
                if isinstance(r, dict):
                    r["percentuale"] = True
        return righe
    if isinstance(data, list):
        return data
    return []


def ricetta_pesi_seger(ricetta):
    if not ricetta:
        return ricetta
    righe = [dict(r) for r in ricetta]
    gram_sum = sum(
        float(r.get("grammi", 0) or 0)
        for r in righe if not r.get("percentuale", False)
    )
    pct_sum = sum(
        float(r.get("grammi", 0) or 0)
        for r in righe if r.get("percentuale", False)
    )
    has_gram = gram_sum > 0
    has_pct = pct_sum > 0

    if has_pct and not has_gram:
        if pct_sum <= 0:
            return righe
        fattore = 100.0 / pct_sum
        for r in righe:
            r["grammi"] = float(r.get("grammi", 0) or 0) * fattore
            r["percentuale"] = False
        return righe

    if has_gram and has_pct:
        convertite = []
        for r in righe:
            val = float(r.get("grammi", 0) or 0)
            if r.get("percentuale", False):
                convertite.append({
                    **r,
                    "grammi": val / 100.0 * gram_sum,
                    "percentuale": False,
                })
            else:
                convertite.append({**r, "grammi": val, "percentuale": False})
        return convertite

    return righe


def accumula_pesi_ossido_ricetta(ricetta_calc, materie_prime):
    pesi_ossido = {o: 0.0 for o in OSSIDI_TUTTI}
    peso_loi = 0.0
    for r in ricetta_calc:
        comp = materie_prime.get(
            normalizza_nome_materia(r["materia"], materie_prime), {})
        grammi = float(r.get("grammi", 0) or 0)
        for ossido, perc in comp.items():
            if ossido == "LOI":
                peso_loi += grammi * float(perc) / 100.0
            elif ossido == "MnO2":
                pesi_ossido["MnO"] = pesi_ossido.get("MnO", 0.0) + grammi * float(perc) / 100.0
            elif ossido in pesi_ossido:
                pesi_ossido[ossido] += grammi * float(perc) / 100.0
    return pesi_ossido, peso_loi


def umf_da_ricetta_list(ricetta, materie_prime):
    if not ricetta or not materie_prime:
        return {o: 0.0 for o in OSSIDI_TUTTI}
    ricetta_calc = ricetta_pesi_seger([dict(r) for r in ricetta])
    moli = {o: 0.0 for o in OSSIDI_TUTTI}
    for r in ricetta_calc:
        nome = normalizza_nome_materia(r.get("materia", ""), materie_prime)
        coeffs, pm = _scheda_materia(materie_prime.get(nome))
        n = float(r.get("grammi", 0) or 0) / pm
        for o, c in coeffs.items():
            moli[o] = moli.get(o, 0.0) + n * c
    moli["KNaO"] = moli.get("KNaO", 0.0) + moli.get("K2O", 0.0) + moli.get("Na2O", 0.0)
    moli["K2O"] = 0.0
    moli["Na2O"] = 0.0
    somma_fondenti = moli["KNaO"] + moli.get("CaO", 0.0) + moli.get("MgO", 0.0)
    if somma_fondenti > 0:
        return {o: moli[o] / somma_fondenti for o in OSSIDI_TUTTI}
    return {o: 0.0 for o in OSSIDI_TUTTI}


def _valore_ossido_riga(riga, ossido):
    try:
        if ossido not in riga.index:
            return 0.0
        valore = riga[ossido]
    except Exception:
        return 0.0
    if pd.isna(valore) or str(valore).strip().lower() in ("", "nan", "none"):
        return 0.0
    try:
        return float(valore)
    except Exception:
        return 0.0


def valori_umf_da_riga(riga):
    return {o: _valore_ossido_riga(riga, o) for o in OSSIDI_TUTTI}


def _materia_preferita_per_ossido(ossido, materie_prime):
    for nome in PREFERENZE_OSSIDO_MATERIALE.get(ossido, []):
        if nome in materie_prime:
            return nome
    best = None
    best_pct = 0.0
    for nome, comp in materie_prime.items():
        pct = _pct_ossido_in_materia(comp, ossido)
        if pct > best_pct:
            best_pct = pct
            best = nome
    return best


def _pct_ossido_in_materia(comp, ossido):
    coeffs, _pm = _scheda_materia(comp)
    if ossido == "KNaO":
        return coeffs.get("KNaO", 0.0)
    return float(coeffs.get(ossido, 0) or 0)


def _allinea_alcali_umf(computed, target):
    c = {o: float((computed or {}).get(o, 0) or 0) for o in OSSIDI_TUTTI}
    t = {o: float((target or {}).get(o, 0) or 0) for o in OSSIDI_TUTTI}
    t_kna = t.get("KNaO", 0.0)
    t_k = t.get("K2O", 0.0)
    t_na = t.get("Na2O", 0.0)
    if t_kna > 1e-6 and t_k <= 1e-6 and t_na <= 1e-6:
        c["KNaO"] = c.get("KNaO", 0.0) + c.get("K2O", 0.0) + c.get("Na2O", 0.0)
        c["K2O"] = 0.0
        c["Na2O"] = 0.0
    elif t_k > 1e-6 or t_na > 1e-6:
        t["KNaO"] = 0.0
        c["KNaO"] = 0.0
    return c, t


def _errore_umf_ricetta(computed, target):
    c, t = _allinea_alcali_umf(computed, target)
    err = 0.0
    for o in OSSIDI_TUTTI:
        tv = t.get(o, 0.0)
        cv = c.get(o, 0.0)
        if tv > 0:
            w = 3.0 if o in OSSIDI_FONDENTI + ["SiO2", "Al2O3"] else 1.0
            err += w * ((cv - tv) / max(tv, 0.01)) ** 2
        elif cv > 0.02:
            w = 4.0 if o in ("Fe2O3", "TiO2", "MnO", "CuO", "CoO", "Cr2O3", "NiO",
                             "SnO2", "ZrO2") else 2.0
            err += w * (cv / 0.05) ** 2
    return err


def _raffina_grammi_ricetta(materiali, grammi, target_umf, materie_prime,
                            totale_grammi, mantieni_materiali=False):
    n = len(materiali)
    if n == 0:
        return []

    def ricetta_da_g(gvals):
        return [
            {"materia": materiali[i], "grammi": gvals[i], "percentuale": False}
            for i in range(n) if gvals[i] > 0.01
        ]

    def score(gvals):
        ric = ricetta_da_g(gvals)
        if not ric:
            return 1e18
        return _errore_umf_ricetta(
            umf_da_ricetta_list(ric, materie_prime), target_umf)

    best_g = [max(0.0, float(g)) for g in grammi]
    if len(best_g) != n:
        best_g = [float(totale_grammi) / n] * n
    best_s = score(best_g)
    fattori = (1.35, 0.74, 1.2, 0.83, 1.1, 0.91, 1.5, 0.67, 0.4, 0.2, 0.0)
    for _ in range(160):
        migliorato = False
        for i in range(n):
            for f in fattori:
                prova = best_g[:]
                prova[i] = max(0.0, prova[i] * f) if f > 0 else 0.0
                s = score(prova)
                if s < best_s - 1e-12:
                    best_s = s
                    best_g = prova
                    migliorato = True
        if not migliorato:
            break

    somma = sum(best_g) or 1.0
    best_g = [g * float(totale_grammi) / somma for g in best_g]
    ricetta = []
    for i, materia in enumerate(materiali):
        g = best_g[i]
        if g >= 0.05 or (mantieni_materiali and g > 0.01):
            ricetta.append({
                "materia": materia,
                "grammi": round(max(g, 0.01), 2),
                "percentuale": False,
            })
    return ricetta


def _materia_per_ossido_ok(ossido, materie_prime):
    if ossido == "KNaO":
        for cand in ("Feldspato",):
            if cand in materie_prime and _pct_ossido_in_materia(
                    materie_prime.get(cand), "KNaO") > 1.0:
                return cand
        best, best_pct = None, 0.0
        for n, comp in materie_prime.items():
            if n == "Acido Borico":
                continue
            pct = _pct_ossido_in_materia(comp, "KNaO")
            if pct > best_pct:
                best_pct = pct
                best = n
        return best
    nome = _materia_preferita_per_ossido(ossido, materie_prime)
    if nome == "Acido Borico":
        for cand in PREFERENZE_OSSIDO_MATERIALE.get(ossido, []):
            if cand != "Acido Borico" and cand in materie_prime:
                return cand
        best, best_pct = None, 0.0
        for n, comp in materie_prime.items():
            if n == "Acido Borico":
                continue
            pct = float(comp.get(ossido, 0) or 0)
            if pct > best_pct:
                best_pct = pct
                best = n
        return best
    return nome


def _ricetta_simile_da_archivio(target_umf, df, materie_prime):
    if df is None or getattr(df, "empty", True):
        return None
    best_ricetta = None
    best_dist = 1e18
    ossidi_extra = [
        o for o in OSSIDI_TUTTI
        if o not in OSSIDI_FORMULA_INPUT and o not in ("KNaO", "K2O", "Na2O")
    ]
    for _, riga in df.iterrows():
        valori = valori_umf_da_riga(riga)
        if any(float(valori.get(o, 0) or 0) > 0.02 for o in ossidi_extra):
            continue
        dist = 0.0
        v_al, t_al = _allinea_alcali_umf(valori, target_umf)
        for o in OSSIDI_TUTTI:
            t = float(t_al.get(o, 0) or 0)
            v = float(v_al.get(o, 0) or 0)
            if t > 0:
                dist += (v - t) ** 2
            elif v > 0.05:
                dist += (v ** 2) * 2.5
        if dist < best_dist:
            ric = parse_ricetta_salvata(riga.get("Ricetta", "[]"))
            if ric:
                best_dist = dist
                best_ricetta = ric
    if not best_ricetta or best_dist > 2.5:
        return None
    out = []
    for r in best_ricetta:
        materia = normalizza_nome_materia(
            str(r.get("materia", "")).strip(), materie_prime)
        if not materia or materia not in materie_prime:
            continue
        try:
            grammi = float(r.get("grammi", 0) or 0)
        except (TypeError, ValueError):
            continue
        if grammi <= 0:
            continue
        out.append({"materia": materia, "grammi": grammi, "percentuale": False})
    return out or None


def _moli_per_grammo(comp):
    coeffs, pm = _scheda_materia(comp)
    mpg = {o: 0.0 for o in OSSIDI_TUTTI}
    for o, c in coeffs.items():
        mpg[o] = float(c or 0) / pm
    return mpg


def _n_ossidi_in_formula(comp, ossidi_formula):
    mpg = _moli_per_grammo(comp)
    return sum(1 for o in ossidi_formula if mpg.get(o, 0.0) > 1e-6)


def normalizza_umf_basici(target):
    """Formula Seger: i basici (KNaO+CaO+MgO) sommano sempre a 1. Al2O3 e SiO2 restano."""
    tgt = {o: float((target or {}).get(o, 0) or 0) for o in OSSIDI_TUTTI}
    tgt["KNaO"] = tgt.get("KNaO", 0.0) + tgt.get("K2O", 0.0) + tgt.get("Na2O", 0.0)
    tgt["K2O"] = 0.0
    tgt["Na2O"] = 0.0
    flux = tgt["KNaO"] + tgt["CaO"] + tgt["MgO"]
    if flux <= 1e-9:
        return None
    out = dict(tgt)
    out["KNaO"] = tgt["KNaO"] / flux
    out["CaO"] = tgt["CaO"] / flux
    out["MgO"] = tgt["MgO"] / flux
    return out


def _target_seger_normalizzato(target):
    tgt = normalizza_umf_basici(target)
    if not tgt:
        return None
    return {
        "KNaO": tgt["KNaO"],
        "CaO": tgt["CaO"],
        "MgO": tgt["MgO"],
        "Al2O3": tgt["Al2O3"],
        "SiO2": tgt["SiO2"],
    }


def _ricetta_se_un_materiale(target, materie_prime, totale_grammi):
    """Se la formula coincide con una sola materia (es. solo Feldspato), usa il 100%."""
    need = _target_seger_normalizzato(target)
    if not need:
        return None
    migliore = None
    migliore_score = None
    for nome in materie_prime:
        umf = umf_da_ricetta_list(
            [{"materia": nome, "grammi": 100.0, "percentuale": False}],
            materie_prime,
        )
        scarta = False
        for o in ("KNaO", "CaO", "MgO"):
            if need[o] <= 0.001 and umf.get(o, 0.0) > 0.03:
                scarta = True
                break
            if need[o] > 0.001 and umf.get(o, 0.0) <= 0.03:
                scarta = True
                break
            if abs(umf.get(o, 0.0) - need[o]) > 0.03:
                scarta = True
                break
        if scarta:
            continue

        def _rel(ossido):
            tv = need[ossido]
            cv = float(umf.get(ossido, 0.0) or 0.0)
            if tv <= 0.001:
                return 0.0 if cv <= 0.08 else 99.0
            return abs(cv - tv) / tv

        if _rel("Al2O3") > 0.03 or _rel("SiO2") > 0.03:
            continue
        score = _rel("Al2O3") + _rel("SiO2")
        if migliore_score is None or score < migliore_score:
            migliore_score = score
            migliore = nome
    if not migliore:
        return None
    return [{
        "materia": migliore,
        "grammi": round(float(totale_grammi), 2),
        "percentuale": False,
    }]


def _primo_disponibile(nomi, materie_prime):
    for nome in nomi:
        if nome in materie_prime:
            return nome
    return None


def _ricetta_seger_basici_prima(target, materie_prime, totale_grammi):
    """Basici (somma 1), poi Caolino per Al2O3 e Quarzo per SiO2 se mancano."""
    una = _ricetta_se_un_materiale(target, materie_prime, totale_grammi)
    if una:
        return una
    need = _target_seger_normalizzato(target)
    if not need:
        return []
    grammi = {}

    def portato(ossido):
        tot = 0.0
        for mat, g in grammi.items():
            tot += g * _moli_per_grammo(materie_prime.get(mat)).get(ossido, 0.0)
        return tot

    def resto_di(ossido):
        return need[ossido] - portato(ossido)

    def aggiungi(nome, ossido, resto=None):
        if not nome or nome not in materie_prime:
            return 0.0
        if resto is None:
            resto = resto_di(ossido)
        if resto <= 0.001:
            return 0.0
        mpg = _moli_per_grammo(materie_prime.get(nome))
        resa = mpg.get(ossido, 0.0)
        if resa <= 1e-12:
            return 0.0
        g_add = resto / resa
        for o in ("KNaO", "CaO", "MgO"):
            if o == ossido:
                continue
            mo = mpg.get(o, 0.0)
            if mo <= 1e-9:
                continue
            r = resto_di(o)
            if r <= 0.001:
                return 0.0
            g_add = min(g_add, r / mo)
        if g_add <= 1e-9:
            return 0.0
        grammi[nome] = grammi.get(nome, 0.0) + g_add
        return g_add

    aggiungi(_primo_disponibile(("Feldspato",), materie_prime), "KNaO")

    ca_left = resto_di("CaO")
    mg_left = resto_di("MgO")
    if ca_left > 0.001 and mg_left > 0.001:
        aggiungi(_primo_disponibile(("Dolomite",), materie_prime), "CaO",
                 min(ca_left, mg_left))

    aggiungi(_primo_disponibile(
        ("Marmo", "Wollastonite", "Dolomite"), materie_prime), "CaO")
    aggiungi(_primo_disponibile(
        ("Carbonato di Magnesio", "Talco", "Dolomite"), materie_prime), "MgO")

    if resto_di("Al2O3") > 0.001:
        aggiungi(_primo_disponibile(("Caolino",), materie_prime), "Al2O3")
    if resto_di("SiO2") > 0.001:
        aggiungi(_primo_disponibile(
            ("Quarzo", "Wollastonite", "Talco", "Caolino"), materie_prime), "SiO2")

    if not grammi:
        return []
    tot = sum(grammi.values()) or 1.0
    return [
        {"materia": m, "grammi": round(g * float(totale_grammi) / tot, 2),
         "percentuale": False}
        for m, g in grammi.items() if g * float(totale_grammi) / tot >= 0.05
    ]


def _ricetta_da_ossidi_target(target, materie_prime, totale_grammi):
    basici = list(OSSIDI_FONDENTI)
    secondari = [o for o in OSSIDI_TUTTI if o not in basici]
    priorita_sec = ["Al2O3", "SiO2", "B2O3", "P2O5", "F", "TiO2", "ZrO2", "SnO2"]
    rest = [o for o in secondari if o not in priorita_sec]
    ordine_ossidi = (
        [o for o in basici if float(target.get(o, 0) or 0) > 0.001]
        + [o for o in priorita_sec if float(target.get(o, 0) or 0) > 0.001]
        + [o for o in rest if float(target.get(o, 0) or 0) > 0.001]
    )

    materiali = []
    visti = set()
    ruolo = {}

    for o in ordine_ossidi:
        nomi = []
        if o in ("KNaO", "K2O", "Na2O"):
            if "Feldspato" in materie_prime:
                nomi.append("Feldspato")
        nome = _materia_per_ossido_ok(o, materie_prime)
        if nome:
            nomi.append(nome)
        for nome in nomi:
            if not nome or nome in visti or nome == "Acido Borico":
                continue
            materiali.append(nome)
            visti.add(nome)
            ruolo[nome] = "basico" if o in basici else "altro"

    if float(target.get("B2O3", 0) or 0) > 0.1:
        for frit in ("Fritta 3134", "Fritta 3124", "Gerstley Borate"):
            if frit in materie_prime and frit not in visti:
                materiali.append(frit)
                visti.add(frit)
                ruolo[frit] = "altro"
                break

    for extra in ("Quarzo", "Caolino"):
        if extra in materie_prime and extra not in visti:
            if target.get("SiO2", 0) > 0 or target.get("Al2O3", 0) > 0:
                materiali.append(extra)
                visti.add(extra)
                ruolo[extra] = "altro"

    if not materiali:
        return []

    pesi_init = []
    for materia in materiali:
        comp = materie_prime.get(materia, {})
        if ruolo.get(materia) == "basico":
            copertura = 0.0
            for o in basici:
                t = float(target.get(o, 0) or 0)
                if t <= 0:
                    continue
                copertura += t * _pct_ossido_in_materia(comp, o)
            pesi_init.append(max(copertura, 0.35))
        else:
            dom = max(
                ((o, float(comp.get(o, 0) or 0)) for o in OSSIDI_TUTTI),
                key=lambda x: x[1],
                default=("SiO2", 1.0),
            )[0]
            tgt = max(float(target.get(dom, 0.05) or 0.05), 0.05)
            pesi_init.append(max(tgt * 0.45, 0.15))

    s = sum(pesi_init) or 1.0
    grammi = [float(totale_grammi) * p / s for p in pesi_init]
    return _raffina_grammi_ricetta(
        materiali, grammi, target, materie_prime, totale_grammi)


def genera_ricetta_da_umf(target_umf, materie_prime, totale_grammi=100.0, df=None):
    if not materie_prime:
        return []
    target = {o: float(target_umf.get(o, 0) or 0) for o in OSSIDI_TUTTI}
    if sum(target.get(o, 0) for o in OSSIDI_FONDENTI) <= 0:
        raise ValueError(
            "Inserisci almeno un fondente (R2O o RO) nella formula.")
    target = normalizza_umf_basici(target) or target

    seger = _ricetta_seger_basici_prima(target, materie_prime, totale_grammi)
    if seger:
        return seger
    raff_ossidi = _ricetta_da_ossidi_target(target, materie_prime, totale_grammi)
    if raff_ossidi:
        return raff_ossidi
    raise ValueError(
        "Nessuna materia prima disponibile per questa formula.")


def ricalcola_ricetta_materiali(target_umf, materie_prime, materiali, grammi_iniziali,
                                totale_grammi=100.0):
    materiali = [m for m in materiali if m in materie_prime]
    if not materiali:
        return []
    n = len(materiali)
    if not grammi_iniziali or len(grammi_iniziali) != n:
        grammi_iniziali = [totale_grammi / n] * n
    target = {o: float(target_umf.get(o, 0) or 0) for o in OSSIDI_TUTTI}
    target = normalizza_umf_basici(target) or target
    subset = {n: materie_prime[n] for n in materiali if n in materie_prime}
    seger = _ricetta_seger_basici_prima(target, subset, totale_grammi)
    if seger:
        return seger
    return _raffina_grammi_ricetta(
        materiali, list(grammi_iniziali), target, materie_prime, totale_grammi,
        mantieni_materiali=True)


def scostamento_umf(computed, target):
    target = normalizza_umf_basici(target) or target
    calc_al, tgt_al = _allinea_alcali_umf(computed, target)
    delta = []
    for o in OSSIDI_TUTTI:
        tv = float(tgt_al.get(o, 0) or 0)
        if tv <= 0:
            continue
        d = float(calc_al.get(o, 0) or 0) - tv
        if abs(d) >= 0.02:
            delta.append((o, d))
    err = _errore_umf_ricetta(computed, target)
    return calc_al, tgt_al, delta, err


# Analisi in tempo reale (stessa logica del desktop: RA Esposito, COE UMF, Stull).
OSSIDI_BASICI_RA = list(OSSIDI_R2O) + list(OSSIDI_RO) + [
    "KNaO", "MnO", "CuO", "CoO", "NiO",
]
OSSIDI_ANFOTERI_RA = ["Al2O3", "Fe2O3", "TiO2", "ZrO2"]
FATTORI_COE = {
    "SiO2": 0.8, "Al2O3": 5.0, "B2O3": 0.8, "Fe2O3": 12.0,
    "TiO2": 4.1, "CaO": 15.0, "MgO": 6.0, "K2O": 33.3,
    "Na2O": 38.0, "ZnO": 10.0, "BaO": 20.0, "Li2O": 27.0,
    "PbO": 10.6, "SrO": 16.0, "P2O5": 13.5, "MnO": 10.5,
    "CuO": 7.5, "CoO": 5.5, "Cr2O3": 5.2, "NiO": 5.0,
    "SnO2": 2.0, "ZrO2": 2.1, "V2O5": 15.0, "KNaO": 35.6,
}


def umf_senza_alcali_duplicati(valori):
    out = {o: float((valori or {}).get(o, 0) or 0) for o in OSSIDI_TUTTI}
    if out.get("KNaO", 0) > 0 and (out.get("K2O", 0) > 0 or out.get("Na2O", 0) > 0):
        out["KNaO"] = 0.0
    return out


def umf_ha_valori(valori):
    return any(float((valori or {}).get(o, 0) or 0) > 0.001 for o in OSSIDI_TUTTI)


def classifica_zona_stull(al, si):
    al = float(al or 0)
    si = float(si or 0)
    if si < 0.6 + 1.8 * al:
        return "INFUSO", "#A89898"
    ratio = (si / al) if al > 0 else 99
    if ratio < 5:
        return "MATT", "#F4D08A"
    return "LUCIDO", "#7B8CDE"


def calcola_rapporto_acidita(valori):
    """RA Esposito: (2 SiO2 + 2 SnO2 + 6 B2O3 + 2 F2) / (2 basici + 6 anfoteri)."""
    v = umf_senza_alcali_duplicati(valori)
    si = float(v.get("SiO2", 0) or 0)
    sn = float(v.get("SnO2", 0) or 0)
    b2o = float(v.get("B2O3", 0) or 0)
    f2 = float(v.get("F2", 0) or 0)
    f = float(v.get("F", 0) or 0)
    if f2 <= 0 and f > 0:
        f2 = f / 2.0
    num = 2.0 * si + 2.0 * sn + 6.0 * b2o + 2.0 * f2
    basici = sum(float(v.get(o, 0) or 0) for o in OSSIDI_BASICI_RA)
    anf = sum(float(v.get(o, 0) or 0) for o in OSSIDI_ANFOTERI_RA)
    den = 2.0 * basici + 6.0 * anf
    if den <= 1e-9:
        return None, {"num": num, "den": den, "basici": basici, "anfoteri": anf}
    return num / den, {"num": num, "den": den, "basici": basici, "anfoteri": anf}


def interpreta_rapporto_acidita(ra):
    if ra is None:
        return {
            "causa": "Dati insufficienti per calcolare il rapporto.",
            "effetti": "",
            "indicazione": "—",
            "colore": "#9A9AA8",
            "zona": "—",
        }
    if ra < 1.5:
        return {
            "causa": (
                "Troppi ossidi basici (Na2O, K2O, CaO, ...) e/o pochi ossidi acidi "
                "(SiO2, B2O3)."
            ),
            "effetti": (
                "Fusibilità più alta, ma bassa stabilità chimica, scarsa resistenza "
                "alla corrosione, struttura vitrea debole."
            ),
            "indicazione": "Aumentare SiO2",
            "colore": "#FF7A4E",
            "zona": "RA basso (< 1,5)",
        }
    if ra <= 3.0:
        return {
            "causa": "Buon equilibrio tra ossidi acidi e basici; composizione controllata.",
            "effetti": (
                "Cristallizzabilità controllata, buona stabilità chimica e meccanica, "
                "elevata resistenza agli shock termici."
            ),
            "indicazione": "Composizione equilibrata — nessun intervento necessario",
            "colore": "#5CBF7A",
            "zona": "RA ottimale (1,5 – 3)",
        }
    return {
        "causa": (
            "Eccesso di ossidi acidi (troppo SiO2 o B2O3) e/o carenza di ossidi basici."
        ),
        "effetti": (
            "Difficoltà di cristallizzazione, reticolo vitreo troppo rigido, "
            "viscosità elevata."
        ),
        "indicazione": "Diminuire SiO2",
        "colore": "#7B8CDE",
        "zona": "RA alto (> 3)",
    }


def dati_rapporto_acidita(valori):
    ra, _ = calcola_rapporto_acidita(valori)
    info = interpreta_rapporto_acidita(ra)
    return {"ra": ra, **info}


def analisi_da_umf(valori):
    """Campi del pannello Analisi in tempo reale."""
    v = umf_senza_alcali_duplicati(valori)
    if not umf_ha_valori(v):
        return None
    al = float(v.get("Al2O3", 0) or 0)
    si = float(v.get("SiO2", 0) or 0)
    somma_r2o = sum(float(v.get(o, 0) or 0) for o in OSSIDI_R2O)
    somma_ro = sum(float(v.get(o, 0) or 0) for o in OSSIDI_RO)
    if v.get("KNaO", 0) > 0:
        somma_r2o += float(v.get("KNaO", 0) or 0)
    si_al = f"{si / al:.3f}" if al > 0 else "--"
    al_si = f"{al / si:.3f}" if si > 0 else "--"
    coe = sum(float(v.get(o, 0) or 0) * FATTORI_COE.get(o, 0.0) for o in OSSIDI_TUTTI)
    ra, _ = calcola_rapporto_acidita(v)
    ra_info = interpreta_rapporto_acidita(ra)
    zona_stull, col_stull = classifica_zona_stull(al, si)
    return {
        "si_al": si_al,
        "al_si": al_si,
        "somma_r2o": f"{somma_r2o:.3f}" if somma_r2o > 0 else "--",
        "somma_ro": f"{somma_ro:.3f}" if somma_ro > 0 else "--",
        "coe": f"{coe:.3f}" if coe > 0 else "--",
        "ra": f"{ra:.3f}" if ra is not None else "--",
        "ra_zona": ra_info.get("zona", "—"),
        "ra_indicazione": ra_info.get("indicazione", "—"),
        "ra_causa": ra_info.get("causa", ""),
        "ra_effetti": ra_info.get("effetti", ""),
        "ra_colore": ra_info.get("colore", "#9A9AA8"),
        "zona_stull": zona_stull,
        "zona_stull_colore": col_stull,
    }
