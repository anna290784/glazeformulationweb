# -*- coding: utf-8 -*-
"""Diagrammi Glaze Formulation (Daniel, 60 carte KNaO/CaO/MgO). Copiati dal desktop, senza modificarlo."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
import numpy as np

BASE_DIR = Path(__file__).resolve().parent
DIAG_DIR = BASE_DIR / "diagrammi_esposito"

_INDICE = None
_ZONE = None
_ZONE_REF = None

FREER_ZONES_MANUAL = {
    1: [
        [0.00, 1.50], [0.30, 1.50], [0.36, 1.95], [0.44, 2.45], [0.48, 3.00], [0.00, 2.00],
    ],
    19: [
        [0.05, 2.50], [0.85, 7.10], [0.65, 6.00], [0.45, 4.00], [0.35, 2.50],
        [0.40, 1.00], [0.15, 1.00], [0.05, 2.50],
    ],
    25: [
        [0.00, 2.50], [0.85, 8.50], [0.72, 6.70], [0.58, 5.10], [0.47, 4.10],
        [0.35, 3.00], [0.43, 2.30], [0.56, 1.90], [0.68, 1.50], [0.42, 1.50], [0.00, 2.20],
    ],
    33: [
        [0.00, 3.00], [1.05, 9.80], [1.05, 8.80], [0.65, 3.80],
        [0.95, 1.80], [0.85, 1.50], [0.00, 1.50],
    ],
    40: [
        [0.40, 7.00], [0.85, 11.80], [0.80, 8.50], [0.70, 7.00],
    ],
    60: [
        [0.00, 5.50], [1.45, 17.50], [1.05, 3.00], [1.00, 3.00],
        [0.80, 2.50], [0.60, 1.50], [0.00, 1.50],
    ],
}

FREER_WEDGE_ANCHORS = [
    {"kna": 0.0, "ca": 1.0, "mg": 0.0,
     "si_left": 1.5, "al_apex": 0.48, "si_apex": 3.0, "al_bl": 0.0, "al_br": 0.30,
     "al_nose": 0.36, "si_nose": 1.9, "si_base": 1.5},
    {"kna": 0.2, "ca": 0.6, "mg": 0.2,
     "si_left": 2.5, "al_apex": 0.85, "si_apex": 7.1, "al_bl": 0.15, "al_br": 0.40,
     "al_nose": 0.35, "si_nose": 2.5, "si_base": 1.0, "hook": True,
     "al_hook": 0.05, "si_hook": 2.5},
    {"kna": 0.3, "ca": 0.7, "mg": 0.0,
     "si_left": 2.5, "al_apex": 0.85, "si_apex": 8.5, "al_bl": 0.42, "al_br": 0.68,
     "al_nose": 0.35, "si_nose": 3.0, "si_base": 1.5},
    {"kna": 0.5, "ca": 0.5, "mg": 0.0,
     "si_left": 7.0, "al_apex": 0.85, "si_apex": 11.8, "al_bl": 0.40, "al_br": 0.70,
     "al_nose": 0.80, "si_nose": 8.5, "si_base": 7.0, "floating": True},
]

FREER_QUAD_ANCHORS = [
    {"kna": 0.4, "ca": 0.6, "mg": 0.0,
     "al_lo": 0.55, "si_lo": 5.5, "al_br": 0.85, "si_br": 5.5,
     "al_tr": 1.10, "si_tr": 8.8, "al_tl": 1.10, "si_tl": 9.8, "al_sl": 0.78, "si_sl": 7.5},
]


def _load_json(path, default):
    if not path.is_file():
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def carica_indice():
    global _INDICE
    if _INDICE is None:
        _INDICE = _load_json(DIAG_DIR / "index.json", [])
    return _INDICE


def carica_zone():
    global _ZONE
    if _ZONE is None:
        _ZONE = _load_json(DIAG_DIR / "zone.json", {})
    return _ZONE


def carica_zone_ref():
    global _ZONE_REF
    if _ZONE_REF is None:
        raw = _load_json(DIAG_DIR / "zones_ref.json", {})
        _ZONE_REF = {int(k): v for k, v in raw.items()}
    return _ZONE_REF


def profilo_diagramma_daniel(umf):
    umf = umf or {}
    kna = sum(float(umf.get(o, 0) or 0) for o in ("KNaO", "K2O", "Na2O"))
    ca = float(umf.get("CaO", 0) or 0)
    mg = float(umf.get("MgO", 0) or 0)
    tot = kna + ca + mg
    if tot < 0.02:
        return None
    return {"k": kna / tot, "ca": ca / tot, "mg": mg / tot, "modo": "daniel_flux"}


def trova_diagramma(prof):
    if not prof:
        return None
    idx = carica_indice()
    if not idx:
        return None
    kna = float(prof.get("k", 0) or 0)
    ca = float(prof.get("ca", 0) or 0)
    mg = float(prof.get("mg", 0) or 0)
    best, best_d = None, 1e9
    for item in idx:
        err = (item["kna"] - kna) ** 2 + (item["ca"] - ca) ** 2 + (item["mg"] - mg) ** 2
        if err < best_d:
            best_d, best = err, item
    return dict(best) if best else None


def testo_mix(item):
    if not item:
        return "—"
    parti = []
    if item.get("kna", 0) > 0:
        parti.append(f"KNaO {item['kna']:.1f}")
    if item.get("ca", 0) > 0:
        parti.append(f"CaO {item['ca']:.1f}")
    if item.get("mg", 0) > 0:
        parti.append(f"MgO {item['mg']:.1f}")
    return "  ".join(parti) if parti else "—"


def _clip_pt(al, si, al_max, si_max):
    return [round(max(0.0, min(al_max, al)), 3), round(max(0.0, min(si_max, si)), 3)]


def _densify_ring(zone, steps=6):
    if len(zone) < 3:
        return zone
    out = []
    n = len(zone)
    for i in range(n):
        a0, s0 = zone[i]
        a1, s1 = zone[(i + 1) % n]
        out.append([a0, s0])
        for t in range(1, steps):
            f = t / steps
            out.append([a0 + (a1 - a0) * f, s0 + (s1 - s0) * f])
    return out


def _zona_plausibile(zone, meta):
    if not zone or len(zone) < 4:
        return False
    al_max = float(meta.get("al_max", 1.2))
    si_max = float(meta.get("si_max", 10.0))
    als = [p[0] for p in zone]
    sis = [p[1] for p in zone]
    if max(als) > al_max * 1.05 or max(sis) > si_max * 1.05:
        return False
    if max(als) - min(als) > al_max * 0.92 and max(sis) - min(sis) > si_max * 0.85:
        return False
    return True


def _adatta_zona_scala(zone, meta_src, meta_dst):
    if not zone or not meta_src or not meta_dst:
        return zone
    sa = float(meta_src.get("al_max", 1.0))
    ss = float(meta_src.get("si_max", 10.0))
    da = float(meta_dst.get("al_max", 1.0))
    ds = float(meta_dst.get("si_max", 10.0))
    if abs(sa - da) < 0.02 and abs(ss - ds) < 0.2:
        return zone
    return [_clip_pt(al * da / max(sa, 0.01), si * ds / max(ss, 0.01), da, ds)
            for al, si in zone]


def _trova_zona_ref_vicina(meta):
    refs = carica_zone_ref()
    if not refs:
        return None, []
    n = int(meta.get("n", 0) or 0)
    if n in refs:
        return n, refs[n]
    idx = {item["n"]: item for item in carica_indice()}
    kna = float(meta.get("kna", 0) or 0)
    ca = float(meta.get("ca", 0) or 0)
    mg = float(meta.get("mg", 0) or 0)
    best_n, best_d = None, 1e9
    for rn in refs:
        item = idx.get(rn)
        if not item:
            continue
        d = (item["kna"] - kna) ** 2 + (item["ca"] - ca) ** 2 + (item["mg"] - mg) ** 2
        if kna >= 0.05 and item["kna"] < 0.05:
            d += 0.04
        elif kna < 0.05 and item["kna"] >= 0.15:
            d += 0.04
        if abs(item["kna"] - kna) > 0.12:
            d += 0.02
        if d < best_d:
            best_d, best_n = d, rn
    if best_n is None:
        return None, []
    return best_n, refs[best_n]


def _idw_blend(kna, ca, mg, anchors, keys):
    wsum = 0.0
    out = {k: 0.0 for k in keys}
    for a in anchors:
        d = (a["kna"] - kna) ** 2 + (a["ca"] - ca) ** 2 + (a["mg"] - mg) ** 2
        w = 1.0 / (d + 0.008)
        wsum += w
        for k in keys:
            if k in a:
                out[k] += w * float(a[k])
    if wsum <= 0:
        return out
    return {k: out[k] / wsum for k in keys}


def _daniel_curva_destra(al_apex, si_apex, al_nose, si_nose, al_br, si_base, al_bl):
    return [
        [al_apex * 0.96, si_apex * 0.96],
        [al_apex * 0.88, si_apex * 0.88],
        [al_apex * 0.80, si_apex * 0.80],
        [al_apex * 0.72, si_apex * 0.72],
        [al_apex * 0.64, si_apex * 0.64],
        [al_nose + 0.14, si_nose + 1.4],
        [al_nose + 0.08, si_nose + 0.8],
        [al_nose, si_nose],
        [al_nose + 0.06, si_base + 0.65],
        [al_nose + 0.12, si_base + 0.40],
        [al_nose + 0.18, si_base + 0.20],
        [al_br - 0.02, si_base],
        [al_br, si_base],
    ]


def _build_daniel_wedge(p, al_max, si_max):
    curve = _daniel_curva_destra(
        p["al_apex"], p["si_apex"], p["al_nose"], p["si_nose"],
        p["al_br"], p["si_base"], p["al_bl"],
    )
    if p.get("floating"):
        pts = [
            [p["al_bl"], p["si_base"]],
            [p["al_apex"], p["si_apex"]],
            *curve,
            [p["al_br"], p["si_base"]],
        ]
    elif p.get("hook"):
        pts = [
            [p["al_bl"], p["si_base"]],
            [p["al_br"], p["si_base"]],
            *curve,
            [p["al_apex"], p["si_apex"]],
            [p.get("al_hook", 0.05), p.get("si_hook", 2.5)],
            [p["al_bl"], p["si_base"] + 0.35],
        ]
    else:
        pts = [
            [0.0, p["si_left"]],
            [p["al_apex"], p["si_apex"]],
            *curve,
            [p["al_br"], p["si_base"]],
            [p["al_bl"], p["si_base"]],
        ]
    return [_clip_pt(al, si, al_max, si_max) for al, si in pts]


def _build_daniel_quad(p, al_max, si_max):
    pts = [
        [p["al_lo"], p["si_lo"]],
        [p["al_br"], p["si_br"]],
        [p["al_tr"], p["si_tr"]],
        [p["al_tl"], p["si_tl"]],
        [p.get("al_sl", p["al_lo"]), p.get("si_sl", p["si_lo"])],
    ]
    return [_clip_pt(al, si, al_max, si_max) for al, si in pts]


def genera_zona(meta):
    if not meta:
        return []
    kna = float(meta.get("kna", 0) or 0)
    ca = float(meta.get("ca", 0) or 0)
    mg = float(meta.get("mg", 0) or 0)
    al_max = float(meta.get("al_max", 1.0))
    si_max = float(meta.get("si_max", 10.0))
    n = int(meta.get("n", 0) or 0)
    if 33 <= n <= 39:
        keys = ["al_lo", "si_lo", "al_br", "si_br", "al_tr", "si_tr", "al_tl", "si_tl", "al_sl", "si_sl"]
        p = _idw_blend(kna, ca, mg, FREER_QUAD_ANCHORS, keys)
        return _build_daniel_quad(p, al_max, si_max)
    keys = [
        "si_left", "al_apex", "si_apex", "al_bl", "al_br", "al_nose", "si_nose", "si_base",
    ]
    p = _idw_blend(kna, ca, mg, FREER_WEDGE_ANCHORS, keys)
    p["al_apex"] = min(al_max * 0.95, p["al_apex"])
    p["si_apex"] = min(si_max * 0.95, p["si_apex"])
    p["al_br"] = min(p["al_br"], p["al_apex"] - 0.05)
    p["al_bl"] = min(p["al_bl"], p["al_br"] - 0.02)
    if n >= 40 and si_max > 11.5:
        p["floating"] = True
        p["si_base"] = max(6.5, p["si_base"])
        p["si_left"] = p["si_base"]
    if mg >= 0.12 and kna >= 0.12 and ca >= 0.25 and n < 40:
        p["hook"] = True
        p["al_hook"] = 0.05 + 0.02 * mg + 0.01 * kna
        p["si_hook"] = 2.35 + 0.25 * kna + 0.10 * mg
    if kna >= 0.85 and ca < 0.12:
        return _build_daniel_wedge({
            "si_left": 0.0, "al_apex": min(al_max * 0.85, 0.72 + 0.12 * kna),
            "si_apex": min(si_max * 0.85, 7.0 + 0.6 * kna),
            "al_bl": 0.18 + 0.04 * kna, "al_br": 0.68 + 0.04 * kna,
            "al_nose": 0.40, "si_nose": 2.0, "si_base": 0.0, "floating": True,
        }, al_max, si_max)
    return _build_daniel_wedge(p, al_max, si_max)


def carica_zona(meta):
    if not meta:
        return []
    n = int(meta.get("n", 0) or 0)
    al_max = float(meta.get("al_max", 1.0))
    si_max = float(meta.get("si_max", 10.0))
    ref_n, ref_zone = _trova_zona_ref_vicina(meta)
    if ref_zone and len(ref_zone) >= 3:
        idx = {item["n"]: item for item in carica_indice()}
        meta_src = idx.get(ref_n, meta)
        zone = _adatta_zona_scala(ref_zone, meta_src, meta)
        zone = [_clip_pt(al, si, al_max, si_max) for al, si in zone]
        return _densify_ring(zone, steps=10)
    if n in FREER_ZONES_MANUAL:
        zone = [_clip_pt(al, si, al_max, si_max) for al, si in FREER_ZONES_MANUAL[n]]
        return _densify_ring(zone, steps=10)
    z = carica_zone().get(str(n)) or []
    if z and len(z) >= 4 and _zona_plausibile(z, meta):
        return _densify_ring(z, steps=10)
    return _densify_ring(genera_zona(meta), steps=10)


def punto_in_zona(zone, al, si):
    if not zone or len(zone) < 3:
        return False
    n = len(zone)
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = zone[i]
        xj, yj = zone[j]
        if ((yi > si) != (yj > si)) and (
            al < (xj - xi) * (si - yi) / (yj - yi + 1e-12) + xi
        ):
            inside = not inside
        j = i
    return inside


def testo_profilo(prof):
    if not prof:
        return "—"
    return (
        f"KNa {prof['k'] * 100:.0f}%  "
        f"Ca {prof['ca'] * 100:.0f}%  "
        f"Mg {prof['mg'] * 100:.0f}%"
    )


def stato_diagramma(umf):
    """Seleziona carta, zona e punto dalla formula UMF."""
    prof = profilo_diagramma_daniel(umf)
    meta = trova_diagramma(prof)
    al = float((umf or {}).get("Al2O3", 0) or 0)
    si = float((umf or {}).get("SiO2", 0) or 0)
    if not meta:
        return {
            "ok": False,
            "info": "Inserisci fondenti KNaO + CaO o MgO",
            "meta": None, "zone": [], "al": al, "si": si,
            "in_zona": False, "prof": prof,
        }
    zone = carica_zona(meta)
    in_z = punto_in_zona(zone, al, si) if al > 0 or si > 0 else False
    return {
        "ok": True,
        "info": (
            f"n.{meta['n']}  {testo_mix(meta)}  ·  {testo_profilo(prof)}  ·  "
            f"SiO2 {si:.3f}  Al2O3 {al:.3f}"
        ),
        "meta": meta, "zone": zone, "al": al, "si": si,
        "in_zona": in_z, "prof": prof,
    }


def disegna_diagramma(stato, compatto=True):
    """Figura scura come la carta Daniel del desktop."""
    if compatto:
        fig, ax = plt.subplots(figsize=(3.8, 3.5), dpi=100)
        fs_tick, fs_lab, fs_title, fs_empty = 6.5, 8, 9, 9
        ms_dot, ms_pt = 3.2, (10, 6.5, 3.5)
        pad_title = 4
    else:
        fig, ax = plt.subplots(figsize=(6.4, 5.6), dpi=110)
        fs_tick, fs_lab, fs_title, fs_empty = 8, 10, 11, 12
        ms_dot, ms_pt = 6, (14, 9, 5)
        pad_title = 8
    fig.patch.set_facecolor("#2A2A31")
    ax.set_facecolor("#2A2A31")
    meta = (stato or {}).get("meta")
    if not meta:
        ax.set_xticks([])
        ax.set_yticks([])
        for sp in ax.spines.values():
            sp.set_visible(False)
        ax.text(0.5, 0.5, "Inserisci fondenti nella formula",
                ha="center", va="center", color="#8A8A93", fontsize=fs_empty)
        fig.tight_layout(pad=0.4)
        return fig

    al_max = float(meta.get("al_max", 1.0))
    si_max = float(meta.get("si_max", 10.0))
    ax.set_xlim(0, al_max)
    ax.set_ylim(0, si_max)
    ax.set_aspect(al_max / si_max * 0.92)

    al_minor, si_minor = 0.05, 0.5
    al_major, si_major = 0.2, 2.0
    ax.set_xticks(np.arange(0, al_max + 1e-6, al_minor), minor=True)
    ax.set_yticks(np.arange(0, si_max + 1e-6, si_minor), minor=True)
    ax.set_xticks(np.arange(0, al_max + 1e-6, al_major))
    ax.set_yticks(np.arange(0, si_max + 1e-6, si_major))
    ax.grid(True, which="minor", color="#38383F", linewidth=0.45)
    ax.grid(True, which="major", color="#4C4C56", linewidth=0.7)
    ax.tick_params(colors="#F1F1F2", labelsize=fs_tick, length=3)
    for sp in ax.spines.values():
        sp.set_color("#F1F1F2")
        sp.set_linewidth(1.2)
    ax.set_xlabel("Al2O3", color="#F1F1F2", fontsize=fs_lab, fontweight="bold")
    ax.set_ylabel("SiO2", color="#F1F1F2", fontsize=fs_lab, fontweight="bold")

    zone = stato.get("zone") or []
    if len(zone) >= 3:
        poly = Polygon(
            [(p[0], p[1]) for p in zone],
            closed=True, facecolor="#3A3A42", edgecolor="none", zorder=2)
        ax.add_patch(poly)
        closed = zone + [zone[0]]
        segs = []
        step = 0.11 if compatto else 0.08
        for i in range(len(closed) - 1):
            x0, y0 = closed[i]
            x1, y1 = closed[i + 1]
            dx, dy = x1 - x0, y1 - y0
            length = (dx * dx + dy * dy) ** 0.5
            steps = max(1, int(length / step))
            for j in range(steps + 1):
                t = j / steps
                segs.append((x0 + dx * t, y0 + dy * t))
        if segs:
            xs, ys = zip(*segs)
            ax.scatter(xs, ys, s=ms_dot, c="#F1F1F2", zorder=3, linewidths=0)

    al, si = float(stato.get("al") or 0), float(stato.get("si") or 0)
    if al > 0 or si > 0:
        in_z = bool(stato.get("in_zona"))
        ax.plot(al, si, "o", ms=ms_pt[0], mfc="#5A5A64", mec="none", zorder=5)
        ax.plot(al, si, "o", ms=ms_pt[1], mfc="#8A8A93", mec="none", zorder=6)
        ax.plot(al, si, "o", ms=ms_pt[2], mfc="#FFFFFF", mec="#2A2A31", mew=1.1, zorder=7)
        stato_txt = "in zona" if in_z else "fuori zona"
        ax.annotate(
            f"Al={al:.2f}  Si={si:.2f}\n{stato_txt}",
            xy=(al, si), xytext=(8, 8), textcoords="offset points",
            color="#F1F1F2", fontsize=fs_tick,
            bbox=dict(boxstyle="round,pad=0.2", fc="#35353C",
                      ec="#F1F1F2" if in_z else "#6A6A72", lw=0.8),
            zorder=8,
        )

    n = meta.get("n", "?")
    mix = testo_mix(meta)
    ax.set_title(f"{n}     {mix}", color="#F1F1F2", fontsize=fs_title, pad=pad_title)
    fig.tight_layout(pad=0.35)
    return fig
