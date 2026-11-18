"""Builds assets/card.svg: the profile card (ASCII otter from otterminal, terminal panel, selected work, stack, live GitHub numbers).

Standard library only, so the daily GitHub Action needs no installs.

    python scripts/build_card.py            # GITHUB_TOKEN optional: with it, the yearly contributions are included
"""
import json
import os
import urllib.request
from datetime import datetime, timezone
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
USER = "Lautiri"
W = 1000

BG, CARD, LINE, TEXT, MUTED = "#0A0A0A", "#141414", "#272727", "#FFFFFF", "#8F8F8F"
ORANGE, CYAN, GREEN = "#FF7A1A", "#2EE6E6", "#3DDC97"
FONT = "'SF Mono',ui-monospace,Menlo,Consolas,'DejaVu Sans Mono','Liberation Mono',monospace"
SANS = "-apple-system,'Segoe UI',Helvetica,Arial,sans-serif"
MONTHS = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]

PANEL = [
    ("head", "lautaro@gcp"),
    ("row", "Rol", "BI Analyst · MarTech · Analytics"),
    ("row", "Base", "Buenos Aires, Argentina"),
    ("row", "Cloud", "GCP · BigQuery · Cloud Run"),
    ("row", "Datos", "dbt · Airflow · SQL · Python"),
    ("row", "MarTech", "GA4 · GTM · Braze · Amplitude"),
    ("row", "IA", "Vertex AI · LLM · agentes"),
    ("row", "Estado", "disponible para tu proyecto"),
    ("head", "Contacto"),
    ("row", "Mail", "lautarovillalbafabricio@gmail.com"),
    ("row", "LinkedIn", "in/lautaro-villalba"),
    ("row", "Web", "lautaro-villalba-portfolio.web.app"),
]

WORK = [
    ("#E5484D", "Veko Producciones", "Productora de eventos: web, tracking,", "un bot que cotiza y diseños automáticos.", "Next.js · GA4 · Vertex AI"),
    ("#2D6BFF", "Tracking de punta a punta", "Del primer tag al tablero: medir", "para entender el negocio y decidir.", "GTM · GA4 · BigQuery"),
    ("#FF5A36", "itti", "Equipo interno de datos y MarTech", "para un grupo de negocios digitales.", "dbt · Airflow · Braze"),
    ("#00B37A", "Rubik Cloud", "Datos, analítica y producto para", "clientes de distintos rubros.", "BigQuery ML · FastAPI · React"),
]

STACK = [
    ("Modelado", "dbt · BigQuery · SQL"),
    ("Orquestación", "Airflow · Cloud Run · GCS · CI/CD"),
    ("MarTech", "GA4 · GTM · Google Ads · Meta Ads"),
    ("", "Braze · Amplitude · Looker Studio"),
    ("Apps e IA", "Python · FastAPI · React · Vertex AI"),
]


def api(url, token=None, body=None):
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body else None)
    req.add_header("User-Agent", "profile-card")
    req.add_header("Accept", "application/vnd.github+json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def github_numbers():
    """Live numbers from the GitHub API. The contributions need a token (GraphQL); without one they are left out."""
    token = os.environ.get("GITHUB_TOKEN")
    out = {}
    try:
        u = api(f"https://api.github.com/users/{USER}", token)
        out.update(repos=u["public_repos"], followers=u["followers"], since=u["created_at"])
    except Exception as e:  # the card still builds offline
        print("REST failed:", e)
    if token:
        try:
            q = 'query{user(login:"%s"){contributionsCollection{contributionCalendar{totalContributions}}}}' % USER
            d = api("https://api.github.com/graphql", token, {"query": q})
            out["contrib"] = d["data"]["user"]["contributionsCollection"]["contributionCalendar"]["totalContributions"]
        except Exception as e:
            print("GraphQL failed:", e)
    return out


def since_label(iso):
    d = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    years = now.year - d.year - ((now.month, now.day) < (d.month, d.day))
    return f"{MONTHS[d.month - 1]} {d.year} ({years} años)" if years > 0 else f"{MONTHS[d.month - 1]} {d.year}"


def t(x, y, s, size=14, fill=TEXT, anchor="start", weight=400, font=FONT, extra=""):
    return f'<text x="{x}" y="{y}" font-family="{font}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" font-weight="{weight}" {extra}>{escape(s)}</text>'


def dotted(x1, x2, y):
    return f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="#3A3A3A" stroke-width="1.5" stroke-dasharray="1.5 5" stroke-linecap="round"/>'


def section_title(x, y, s):
    return t(x, y, f"[ {s} ]", 12, MUTED, extra='letter-spacing="3"')


def otter(x, y, width):
    """The otter coding at its desk, from otterminal: 80 ASCII frames played in a loop with pure CSS.

    Every frame is a group; a shared keyframe shows each one for a single step, offset by a negative delay,
    so the loop needs no script (SVGs inside a README cannot run JavaScript)."""
    data = json.loads((ROOT / "assets/otter_coding.json").read_text())
    frames, cols = data["frames"], data["cols"]
    cw = width / cols  # textLength pins every glyph to this advance, whatever monospace font GitHub ends up using
    lh = cw * 1.62
    size = cw * 1.68
    n = len(frames)
    dt = 1 / data["fps"]
    loop = n * dt
    out = []
    for i, f in enumerate(frames):
        lines = []
        for r, line in enumerate(f):
            if not line.strip():
                continue
            # the leading blank becomes an x offset, the rest keeps its spaces through white-space:pre
            lead = len(line) - len(line.lstrip())
            body = escape(line.lstrip())
            lines.append(f'<text x="{x + lead * cw:.1f}" y="{y + r * lh:.1f}" textLength="{(len(line) - lead) * cw:.1f}" lengthAdjust="spacingAndGlyphs">{body}</text>')
        out.append(f'<g class="of" style="animation-delay:{i * dt - loop:.3f}s">{"".join(lines)}</g>')
    group = (f'<g font-family="{FONT}" font-size="{size:.2f}" fill="{ORANGE}">' + "".join(out) + "</g>")
    css = (f".of text{{white-space:pre}}.of{{opacity:0;animation:of {loop:.2f}s steps(1,end) infinite}}"
           f"@keyframes of{{0%{{opacity:1}}{100 / n:.4f}%{{opacity:0}}100%{{opacity:0}}}}"
           "@media (prefers-reduced-motion:reduce){.of{animation:none}.of:first-child{opacity:1}}")
    return group, len(f) * lh, css


def build():
    gh = github_numbers()
    parts = []
    # header
    parts.append(t(32, 58, "Lautaro Villalba", 34, TEXT, weight=600))
    parts.append(t(32, 88, f"@{USER}", 15, ORANGE))
    parts.append(t(W - 32, 58, "datos · cloud · marketing", 14, MUTED, "end"))
    parts.append(t(W - 32, 88, "Buenos Aires, Argentina", 14, MUTED, "end"))
    parts.append(f'<line x1="0" y1="116" x2="{W}" y2="116" stroke="{LINE}"/>')

    # the otter + terminal panel
    ot, rh, otter_css = otter(24, 172, 520)
    parts.append(ot)
    px, py, pw = 564, 140, W - 564 - 24
    ph = 30 + len(PANEL) * 27 + 6
    parts.append(f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="10" fill="{CARD}" stroke="{LINE}"/>')
    y = py + 32
    for i, item in enumerate(PANEL):
        delay = f'style="animation-delay:{0.4 + i * 0.12:.2f}s"'
        if item[0] == "head":
            if i:
                y += 6
            w = len(item[1]) * 9 + 14
            parts.append(f'<g class="ln" {delay}><line x1="{px + 16}" y1="{y - 5}" x2="{px + 26}" y2="{y - 5}" stroke="{LINE}"/>'
                         + t(px + 34, y, item[1], 14, GREEN if i == 0 else ORANGE, weight=600)
                         + f'<line x1="{px + 34 + w}" y1="{y - 5}" x2="{px + pw - 16}" y2="{y - 5}" stroke="{LINE}"/></g>')
        else:
            _, k, v = item
            parts.append(f'<g class="ln" {delay}>' + t(px + 16, y, "·", 14, MUTED) + t(px + 28, y, f"{k}:", 12.5, CYAN)
                         + dotted(px + 34 + len(k) * 7.6 + 8, px + pw - 22 - len(v) * 7.6, y - 4)
                         + t(px + pw - 16, y, v, 12.5, TEXT, "end") + "</g>")
        y += 27
    top = max(172 + rh, py + ph) + 26
    parts.append(f'<line x1="0" y1="{top}" x2="{W}" y2="{top}" stroke="{LINE}"/>')

    # selected work
    y = top + 40
    parts.append(section_title(32, y, "TRABAJO DESTACADO"))
    cw, chh = (W - 32 * 2 - 16) / 2, 108
    for i, (c, name, l1, l2, tech) in enumerate(WORK):
        cx = 32 + (i % 2) * (cw + 16)
        cy = y + 18 + (i // 2) * (chh + 14)
        parts.append(f'<g class="ln" style="animation-delay:{1.4 + i * 0.12:.2f}s">'
                     f'<rect x="{cx}" y="{cy}" width="{cw}" height="{chh}" rx="10" fill="{CARD}" stroke="{LINE}"/>'
                     f'<circle cx="{cx + 22}" cy="{cy + 25}" r="5" fill="{c}"/>'
                     + t(cx + 36, cy + 30, name, 15, TEXT, weight=600)
                     + t(cx + 20, cy + 56, l1, 13, MUTED, font=SANS) + t(cx + 20, cy + 74, l2, 13, MUTED, font=SANS)
                     + t(cx + 20, cy + 96, tech, 12, c) + "</g>")
    y = y + 18 + 2 * (chh + 14) + 16
    parts.append(f'<line x1="0" y1="{y}" x2="{W}" y2="{y}" stroke="{LINE}"/>')

    # stack + live GitHub numbers
    y0 = y + 40
    parts.append(section_title(32, y0, "STACK"))
    for i, (k, v) in enumerate(STACK):
        yy = y0 + 32 + i * 26
        if k:
            parts.append(t(32, yy, k, 13, CYAN))
        parts.append(t(170, yy, v, 13, TEXT))
    gx = 600
    parts.append(section_title(gx, y0, "GITHUB"))
    stats = []
    if "since" in gh:
        stats.append(("En GitHub desde", since_label(gh["since"])))
    # most of the work lives in private repos: the count only shows once private contributions are
    # enabled on the profile, otherwise a near zero number would misrepresent the activity
    if gh.get("contrib", 0) >= 30:
        stats.append(("Contribuciones · 12 meses", f'{gh["contrib"]:,}'.replace(",", ".")))
    if "repos" in gh:
        stats.append(("Repos públicos", str(gh["repos"])))
    stats.append(("Actualizado", datetime.now(timezone.utc).strftime("%d/%m/%Y")))
    for i, (k, v) in enumerate(stats):
        yy = y0 + 32 + i * 26
        parts.append(t(gx, yy, k, 13, MUTED) + dotted(gx + len(k) * 7.9 + 10, W - 40 - len(v) * 8.2, yy - 4) + t(W - 32, yy, v, 13, ORANGE, "end"))
    h = int(y0 + 32 + max(len(STACK), len(stats)) * 26 + 18)

    css = f"""
.ln{{opacity:0;animation:in .5s ease-out forwards}}
@keyframes in{{to{{opacity:1}}}}
@media (prefers-reduced-motion:reduce){{.ln{{opacity:1;animation:none}}}}""" + otter_css
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}" role="img" '
           f'aria-label="Lautaro Villalba: datos, cloud y marketing. Nutria en ASCII programando, stack y trabajo destacado.">'
           f"<title>Lautaro Villalba · @{USER}</title><style>{css}</style>"
           f'<rect width="{W}" height="{h}" rx="14" fill="{BG}" stroke="{LINE}"/>' + "\n".join(parts) + "</svg>")
    (ROOT / "assets/card.svg").write_text(svg, encoding="utf-8")
    print("card.svg", W, "x", h, gh)


if __name__ == "__main__":
    build()
