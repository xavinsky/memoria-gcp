#!/usr/bin/env python3
"""Compile le contenu Markdown de content/ en www/data/content.js.

Le site (www/index.html) reste un fichier statique qui s'ouvre en file:// : les données sont
chargées par <script src>, sous la forme `const SITE = {...}`, et non par fetch.

Structure lue :
  content/site.yml                        pages du menu, libellés des groupes ; une page de type
                                          `accueil` affiche content/accueil.md ;
                                          projets : autres projets IA, menu latéral de l'accueil
  content/accueil.md                      page d'accueil (front matter : title)
  content/<page>/<groupe>/<NN>-<slug>.md  une section ; le dossier donne le groupe, le nom de
                                          fichier l'ordre et l'id par défaut
  content/lexique.md                      un terme par titre `## Terme`
  content/svg/*.svg                       schémas, insérés inline via ![légende](../../svg/x.svg)

Front matter d'une section : title (obligatoire), subgroup, id, type: syntax (tableau objectif |
syntaxe | résultat), et pour une fiche produit : icon (chemin sous www/icons/, sans .svg), aka
(ancien nom), docs (libellé → URL, rendu en liste sous un titre « Documentation ») et schema
(schéma d'intégration généré par build/schema.py, placé en tête de la section), deprecie
(produit en fin de vie ou déconseillé : phrase affichée en bandeau sous le titre, fiche grisée et
renvoyée en fin de sous-groupe), captures
(image, page, legende : captures de la documentation officielle, rangées dans
www/captures/<id de la section>/).

Syntaxe propre au site dans le Markdown : encarts `> [!TIP]` / `> [!WARNING]` (alertes GitHub),
marqueurs `[!SOMMEIL]` (projet libre en sommeil), `[!PREVERSION]` (fonction en préversion) et
`[!DECONSEILLE]` (hors pratique standard ou pérennité incertaine) : badge avec infobulle à l'endroit du
marqueur ; en tête d'une puce ou d'une ligne de tableau, l'élément entier est grisé.

Pour le référencement, le build produit aussi, à partir de www/index.html pris pour gabarit, une
page par section et une pour le lexique (www/<id>.html : titre, description, URL canonique, Open
Graph, contenu statique de la section) et www/sitemap.xml. Ces fichiers ne sont pas versionnés.

Usage : python3 build/build.py
"""

import datetime
import html
import json
import re
import subprocess
import sys
import urllib.parse
import unicodedata
from pathlib import Path

import yaml
from markdown_it import MarkdownIt
from markdown_it.token import Token
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from pygments.util import ClassNotFound

import schema

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
OUTPUT = ROOT / "www" / "data" / "content.js"
ICONS = ROOT / "www" / "icons"
WWW = ROOT / "www"
SITE_URL = "https://tekio.org/memoria-gcp/"
SITE_NAME = "MemorIA GCP"
GENERATED_MARK = '<meta name="generator" content="memoria-gcp build/build.py">'
SEO_BLOCK_RE = re.compile(r"<!-- seo -->.*?<!-- /seo -->", re.S)
RESERVED_PAGES = {"index", "engine", "style", "sitemap"}
DESCRIPTION_MAX = 160

STATUS_MARKERS = {
    "SOMMEIL": ("dormant", "🧊", "Projet en sommeil : dépôt non archivé, sans développement actif depuis plus "
                "d'un an. Déconseillé pour un nouveau projet."),
    "PREVERSION": ("preview", "préversion", "Préversion : sans engagement de disponibilité ni de support. Chez "
                   "Google Cloud, une préversion peut changer ou être arrêtée avant d'atteindre la disponibilité "
                   "générale (GA) : à éviter en production."),
    "DECONSEILLE": ("discouraged", "déconseillé", "Déconseillé : hors de la pratique standard, ou pérennité "
                    "incertaine. L'explication figure dans le texte."),
}
MARKER_RE = re.compile(r"\[!(" + "|".join(STATUS_MARKERS) + r")\]\s*")
CALLOUTS = {"NOTE": "tip", "TIP": "tip", "IMPORTANT": "tip", "WARNING": "warning", "CAUTION": "warning"}
SYNTAX_COLUMNS = ["col-objectif", "col-syntaxe", "col-resultat"]
FORMATTER = HtmlFormatter(nowrap=True, classprefix="tok-")


class BuildError(Exception):
    pass


def slugify(text):
    text = unicodedata.normalize("NFD", text.lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


def split_front_matter(text, path):
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end < 0:
        raise BuildError(f"{path}: front matter non fermé")
    meta = yaml.safe_load(text[4:end]) or {}
    return meta, text[end + 5:]


def highlight_code(code, lang, _attrs):
    lang = (lang or "").strip()
    try:
        body = highlight(code, get_lexer_by_name(lang), FORMATTER) if lang else html.escape(code)
    except ClassNotFound:
        body = html.escape(code)
    cls = f' class="language-{lang}"' if lang else ""
    return f'<pre class="block-code"><code{cls}>{body}</code></pre>\n'


def make_parser():
    md = MarkdownIt("commonmark", {"html": True, "highlight": highlight_code})
    md.enable(["table", "strikethrough"])
    return md


def read_svg(path):
    """Contenu d'un schéma à insérer inline. Ses id sont préfixés par le nom du fichier : tous les
    SVG partagent le même document, et une référence (marqueur, dégradé) ne doit pas se résoudre
    vers l'élément homonyme d'un autre schéma, éventuellement masqué."""
    svg = path.read_text(encoding="utf-8")
    svg = re.sub(r"<\?xml[^>]*\?>", "", svg)
    svg = re.sub(r"<!DOCTYPE[^>]*>", "", svg)
    prefix = slugify(path.stem) + "-"
    svg = re.sub(r'\bid="([^"]+)"', lambda m: f'id="{prefix}{m.group(1)}"', svg)
    svg = re.sub(r'url\(#([^)]+)\)', lambda m: f"url(#{prefix}{m.group(1)})", svg)
    svg = re.sub(r'href="#([^"]+)"', lambda m: f'href="#{prefix}{m.group(1)}"', svg)
    return svg.strip()


class Renderer:
    """Rend un fichier Markdown en HTML et relève ses liens internes et ses ancres."""

    def __init__(self):
        self.md = make_parser()
        self.links = []  # (fichier source, cible #id)

    def render(self, text, source, section_id=None, syntax=False):
        tokens = self.md.parse(text)
        anchors = []
        self._callouts(tokens)
        self._status_markers(tokens)
        self._tables(tokens, syntax)
        if section_id:
            anchors = self._headings(tokens, section_id)
        tokens = self._figures(tokens, source)
        self._links(tokens, source)
        return self.md.renderer.render(tokens, self.md.options, {}), anchors

    @staticmethod
    def _callouts(tokens):
        # > [!WARNING] ... → encart coloré (syntaxe des alertes GitHub)
        for i, tok in enumerate(tokens):
            if tok.type != "blockquote_open" or i + 2 >= len(tokens):
                continue
            inline = tokens[i + 2]
            if inline.type != "inline" or not inline.children:
                continue
            first = inline.children[0]
            m = re.match(r"\[!(\w+)\]\s*", first.content) if first.type == "text" else None
            if not m or m.group(1).upper() not in CALLOUTS:
                continue
            tok.attrSet("class", "block-note " + CALLOUTS[m.group(1).upper()])
            first.content = first.content[m.end():]
            if not first.content and len(inline.children) > 1 and inline.children[1].type == "softbreak":
                del inline.children[:2]

    @staticmethod
    def _status_markers(tokens):
        # [!SOMMEIL], [!PREVERSION], [!DECONSEILLE] : badge à l'endroit du marqueur ; en tête d'une puce
        # ou de la première cellule d'une ligne de tableau, l'élément entier est en plus grisé.
        for j, tok in enumerate(tokens):
            if tok.type != "inline" or not tok.children:
                continue
            container = None
            if j >= 2 and tokens[j - 1].type == "paragraph_open" and tokens[j - 2].type == "list_item_open":
                container = tokens[j - 2]
            elif j >= 2 and tokens[j - 1].type in ("td_open", "th_open") and tokens[j - 2].type == "tr_open":
                container = tokens[j - 2]
            children = []
            for k, child in enumerate(tok.children):
                if child.type != "text" or "[!" not in child.content:
                    children.append(child)
                    continue
                parts = MARKER_RE.split(child.content)
                for n, part in enumerate(parts):
                    if n % 2 == 0:
                        if part:
                            text = Token("text", "", 0)
                            text.content = part
                            children.append(text)
                        continue
                    css, label, title = STATUS_MARKERS[part]
                    if container is not None and k == 0 and n == 1 and not parts[0].strip():
                        container.attrSet("class", css)
                        container.attrSet("title", title)
                    badge = Token("html_inline", "", 0)
                    badge.content = f'<span class="status-badge {css}" title="{html.escape(title)}">{label}</span> '
                    children.append(badge)
            tok.children = children
            if children and children[0].type == "text":
                children[0].content = children[0].content.lstrip()

    @staticmethod
    def _tables(tokens, syntax):
        col = 0
        for tok in tokens:
            if tok.type == "table_open":
                tok.attrSet("class", "syntax-table" if syntax else "md-table")
            elif tok.type == "tr_open":
                col = 0
            elif tok.type in ("td_open", "th_open"):
                if syntax and col < len(SYNTAX_COLUMNS):
                    tok.attrSet("class", SYNTAX_COLUMNS[col])
                col += 1

    @staticmethod
    def _headings(tokens, section_id):
        anchors = []
        for i, tok in enumerate(tokens):
            if tok.type == "heading_open":
                anchor = f"{section_id}--{slugify(tokens[i + 1].content)}"
                tok.attrSet("id", anchor)
                anchors.append(anchor)
        return anchors

    @staticmethod
    def _figures(tokens, source):
        # Paragraphe réduit à une image .svg → schéma inséré inline, légende = texte alternatif
        out = []
        i = 0
        while i < len(tokens):
            tok = tokens[i]
            children = tokens[i + 1].children if tok.type == "paragraph_open" else None
            if children and len(children) == 1 and children[0].type == "image" \
                    and children[0].attrGet("src").endswith(".svg"):
                img = children[0]
                svg_path = (source.parent / img.attrGet("src")).resolve()
                if not svg_path.is_file():
                    raise BuildError(f"{source}: schéma introuvable {img.attrGet('src')}")
                caption = img.content
                figure = Token("html_block", "", 0)
                figure.content = (
                    f'<figure class="block-diagram">{read_svg(svg_path)}'
                    + (f"<figcaption>{html.escape(caption)}</figcaption>" if caption else "")
                    + "</figure>\n"
                )
                out.append(figure)
                i += 3
                continue
            out.append(tok)
            i += 1
        return out

    def _links(self, tokens, source):
        for tok in tokens:
            for child in tok.children or []:
                if child.type != "link_open":
                    continue
                href = child.attrGet("href") or ""
                if href.startswith("#"):
                    self.links.append((source, href[1:]))
                elif re.match(r"https?://", href):
                    child.attrSet("target", "_blank")
                    child.attrSet("rel", "noopener")


def insert_captures(body, captures, section_id, path):
    """Section « Dans la console » : captures de la documentation officielle (CC BY 4.0), placée
    avant les alternatives en logiciel libre, ou en fin de texte."""
    figures = []
    for cap in captures:
        # La documentation Google Cloud est sous CC BY 4.0 ; une autre source est seulement citée
        host = urllib.parse.urlparse(cap["page"]).hostname or ""
        google_docs = host in ("cloud.google.com", "docs.cloud.google.com")
        credit = "documentation Google Cloud" if google_docs else f"documentation {host}"
        licence = ", licence CC BY 4.0" if google_docs else ""
        local = ROOT / "www" / "captures" / section_id / cap["image"].rsplit("/", 1)[-1]
        if not local.is_file():
            raise BuildError(f"{path}: capture absente {local.relative_to(ROOT)}")
        src = local.relative_to(ROOT / "www").as_posix()
        figures.append(
            f'<figure class="capture"><a href="{src}" target="_blank" rel="noopener">'
            f'<img src="{src}" alt="{html.escape(cap["legende"])}" loading="lazy"></a>'
            f'<figcaption>{html.escape(cap["legende"])}. Source : <a href="{html.escape(cap["page"])}" '
            f'target="_blank" rel="noopener">{credit}</a>{licence}.</figcaption></figure>'
        )
    section = "## Dans la console\n\n" + "\n\n".join(figures) + "\n\n"
    marker = "## Alternatives en logiciel libre"
    if marker in body:
        return body.replace(marker, section + marker, 1)
    return body + "\n\n" + section


def load_site():
    site = yaml.safe_load((CONTENT / "site.yml").read_text(encoding="utf-8"))
    for page in site["pages"]:
        page.setdefault("type", "sections")
        page.setdefault("groups", {})
    return site


def load_sections(site, renderer):
    sections = []
    for page in site["pages"]:
        if page["type"] != "sections":
            continue
        page_dir = CONTENT / page["key"]
        for group in page["groups"]:
            group_sections = []
            for path in sorted((page_dir / group).glob("*.md")):
                meta, body = split_front_matter(path.read_text(encoding="utf-8"), path)
                if "title" not in meta:
                    raise BuildError(f"{path}: `title` manquant dans le front matter")
                sec_id = meta.get("id") or re.sub(r"^[a-z]?\d+-", "", path.stem)
                syntax = meta.get("type") == "syntax"
                if meta.get("captures"):
                    body = insert_captures(body, meta["captures"], sec_id, path)
                if meta.get("docs"):
                    body += "\n\n## Documentation\n\n" + "".join(
                        f"- [{label}]({url})\n" for label, url in meta["docs"].items())
                body_html, anchors = renderer.render(body, path, sec_id, syntax)
                description = describe(body_html)
                if meta.get("schema"):
                    for node in meta["schema"].get("nodes", {}).values():
                        if node.get("icon") and not (ICONS / f"{node['icon']}.svg").is_file():
                            raise BuildError(f"{path}: icône de schéma introuvable www/icons/{node['icon']}.svg")
                    try:
                        body_html = schema.render(meta["schema"], sec_id, path) + body_html
                    except ValueError as err:
                        raise BuildError(str(err)) from None
                if meta.get("deprecie"):
                    body_html = (
                        '<div class="deprecated-banner"><span class="deprecated-tag">Déconseillé</span>'
                        + renderer.md.renderInline(meta["deprecie"]) + "</div>\n" + body_html
                    )
                icon = meta.get("icon")
                if icon and not (ICONS / f"{icon}.svg").is_file():
                    raise BuildError(f"{path}: icône introuvable www/icons/{icon}.svg")
                group_sections.append({
                    "id": sec_id,
                    "page": page["key"],
                    "group": group,
                    "subgroup": meta.get("subgroup"),
                    "title": meta["title"],
                    "icon": f"icons/{icon}.svg" if icon else None,
                    "aka": meta.get("aka"),
                    "deprecie": bool(meta.get("deprecie")),
                    "html": body_html,
                    "anchors": anchors,
                    "source": str(path.relative_to(ROOT)),
                    "description": description,
                })
            unknown = {p.name for p in page_dir.glob("*/") if p.is_dir()} - set(page["groups"])
            if unknown:
                raise BuildError(f"{page_dir}: dossiers absents de site.yml : {sorted(unknown)}")
            sections.extend(order_by_subgroup(group_sections))
    return sections


def order_by_subgroup(group_sections):
    # Les sections d'un même sous-groupe doivent être contiguës pour le menu latéral :
    # regroupement dans l'ordre de première apparition, ordre des fichiers conservé. Les produits
    # déconseillés passent en fin de leur sous-groupe.
    order = []
    for sec in group_sections:
        if sec["subgroup"] not in order:
            order.append(sec["subgroup"])
    return sorted(group_sections, key=lambda s: (order.index(s["subgroup"]), s["deprecie"]))


def load_lexique(renderer):
    path = CONTENT / "lexique.md"
    if not path.exists():
        return []
    terms = []
    parts = re.split(r"^## +(.+)$", path.read_text(encoding="utf-8"), flags=re.M)
    for term, body in zip(parts[1::2], parts[2::2]):
        term = term.strip()
        body_html, _ = renderer.render(body.strip(), path)
        target = re.search(r'href="#([\w-]+)"', body_html)
        terms.append({
            "t": term,
            "id": "lexterm-" + slugify(term),
            "html": body_html,
            "target": target.group(1) if target else None,
        })
    return sorted(terms, key=lambda e: slugify(e["t"]))


def load_accueil(site, renderer):
    """Page d'accueil (content/accueil.md), si site.yml déclare une page de type `accueil`."""
    pages = [p for p in site["pages"] if p["type"] == "accueil"]
    if not pages:
        return None
    path = CONTENT / "accueil.md"
    if not path.is_file():
        raise BuildError(f"{path}: fichier absent, requis par la page `{pages[0]['key']}` de site.yml")
    meta, body = split_front_matter(path.read_text(encoding="utf-8"), path)
    body_html, anchors = renderer.render(body, path, pages[0]["key"])
    return {"title": meta.get("title", pages[0]["label"]), "html": body_html, "anchors": anchors}


def check_ids_and_links(site, sections, lexique, accueil, renderer):
    known = {}
    for page in site["pages"]:
        known[page["key"]] = "page"
    for anchor in accueil["anchors"] if accueil else []:
        known[anchor] = "accueil"
    for sec in sections:
        for anchor in [sec["id"], *sec["anchors"]]:
            if anchor in known:
                raise BuildError(f"{sec['source']}: id `{anchor}` déjà utilisé")
            known[anchor] = sec["source"]
    for entry in lexique:
        known[entry["id"]] = "lexique"
    broken = [f"{src.relative_to(ROOT)}: lien vers #{target} introuvable"
              for src, target in renderer.links if target not in known]
    if broken:
        raise BuildError("\n".join(broken))


def last_updated():
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%cd", "--date=format:%d/%m/%Y", "--", "content"],
            cwd=ROOT, capture_output=True, text=True, check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        out = ""
    return out or datetime.date.today().strftime("%d/%m/%Y")


def describe(body_html):
    """Texte du premier paragraphe, sans balises, coupé à DESCRIPTION_MAX caractères."""
    m = re.search(r"<p>(.*?)</p>", body_html, re.S)
    if not m:
        return ""
    text = html.unescape(re.sub(r"<[^>]+>", "", m.group(1)))
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= DESCRIPTION_MAX:
        return text
    head = text[:DESCRIPTION_MAX]
    sentence = head.rfind(". ")
    if sentence >= DESCRIPTION_MAX // 2:
        return head[:sentence + 1]
    cut = head[:DESCRIPTION_MAX - 1].rsplit(" ", 1)[0].rstrip(" ,;:.(")
    return cut + "…"


def content_dates():
    """Date du dernier commit de chaque fichier de content/ (AAAA-MM-JJ), d'un seul git log."""
    try:
        out = subprocess.run(
            ["git", "log", "--format=@%cs", "--name-only", "--", "content"],
            cwd=ROOT, capture_output=True, text=True, check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        return {}
    dates, current = {}, None
    for line in out.splitlines():
        if line.startswith("@"):
            current = line[1:]
        elif line.strip():
            dates.setdefault(line.strip(), current)
    return dates


def seo_head(title, description, url):
    title, description, url = (html.escape(v, quote=False).replace('"', "&quot;")
                               for v in (title, description, url))
    return (
        f"{GENERATED_MARK}\n"
        f"<title>{title}</title>\n"
        f'<meta name="description" content="{description}">\n'
        f'<link rel="canonical" href="{url}">\n'
        '<meta property="og:type" content="article">\n'
        '<meta property="og:site_name" content="tekio.org">\n'
        f'<meta property="og:title" content="{title}">\n'
        f'<meta property="og:description" content="{description}">\n'
        f'<meta property="og:url" content="{url}">\n'
        '<meta property="og:locale" content="fr_FR">\n'
        '<meta name="twitter:card" content="summary">'
    )


def write_pages(site, sections, lexique):
    """Une page HTML par section et pour le lexique, puis sitemap.xml. Chaque page est le site
    complet (gabarit www/index.html) ouvert sur sa section, avec ses propres métadonnées et le
    contenu de la section en HTML statique, lisible sans JavaScript."""
    template = (WWW / "index.html").read_text(encoding="utf-8")
    if not SEO_BLOCK_RE.search(template) or '<main id="main-root"></main>' not in template:
        raise BuildError("www/index.html : bloc <!-- seo --> ou <main id=\"main-root\"> introuvable")
    for old in WWW.glob("*.html"):
        if old.name != "index.html" and GENERATED_MARK in old.read_text(encoding="utf-8"):
            old.unlink()

    dates = content_dates()
    today = datetime.date.today().isoformat()
    labels = {p["key"]: p["label"] for p in site["pages"]}
    pages = []
    for sec in sections:
        label = labels[sec["page"]]
        if sec["page"] == "produits":
            title = f"{sec['title']} : fiche produit Google Cloud | {SITE_NAME}"
        else:
            title = f"{sec['title']} : {label} sur Google Cloud | {SITE_NAME}"
        description = sec["description"] or f"{sec['title']} : {label} sur Google Cloud, dans l'aide-mémoire {SITE_NAME}."
        icon = f'<img class="panel-icon" src="{sec["icon"]}" alt="">' if sec["icon"] else ""
        body = (
            f'<section class="panel active"><div class="panel-header">{icon}<div class="panel-titles">'
            f'<h1>{html.escape(sec["title"])}</h1></div></div><div class="md">{sec["html"]}</div></section>'
        )
        pages.append((sec["id"], title, description, body, dates.get(sec["source"], today)))
    if lexique and "lexique" in labels:
        entries = "".join(
            f'<div class="lex-entry" id="{e["id"]}"><div class="lex-term">{html.escape(e["t"])}</div>'
            f'<div class="lex-def">{e["html"]}</div></div>' for e in lexique)
        body = f'<div class="page-main active"><div class="page-header"><h1>Lexique</h1></div>{entries}</div>'
        pages.append(("lexique", f"Lexique Google Cloud : termes, sigles et anciens noms | {SITE_NAME}",
                      f"Lexique Google Cloud en français : {len(lexique)} termes, sigles et anciens noms de "
                      "produits, chacun relié à la section qui le détaille.",
                      body, dates.get("content/lexique.md", today)))

    titles = [p[1] for p in pages]
    for page_id, title, description, body, _ in pages:
        if page_id in RESERVED_PAGES:
            raise BuildError(f"id `{page_id}` réservé : il donnerait la page www/{page_id}.html")
        if titles.count(title) > 1:
            raise BuildError(f"titre de page en double : {title}")
        out = SEO_BLOCK_RE.sub(lambda _: seo_head(title, description, f"{SITE_URL}{page_id}.html"), template)
        out = out.replace('<html lang="fr">', f'<html lang="fr" data-route="{page_id}">', 1)
        out = out.replace('<main id="main-root"></main>', f'<main id="main-root">{body}</main>', 1)
        (WWW / f"{page_id}.html").write_text(out, encoding="utf-8")

    urls = [(SITE_URL, max(dates.values(), default=today))]
    urls += [(f"{SITE_URL}{p[0]}.html", p[4]) for p in pages]
    (WWW / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"  <url><loc>{html.escape(u)}</loc><lastmod>{d}</lastmod></url>\n" for u, d in urls)
        + "</urlset>\n",
        encoding="utf-8",
    )
    return len(pages)


def main():
    site = load_site()
    renderer = Renderer()
    sections = load_sections(site, renderer)
    lexique = load_lexique(renderer)
    accueil = load_accueil(site, renderer)
    check_ids_and_links(site, sections, lexique, accueil, renderer)
    if accueil:
        del accueil["anchors"]
    for sec in sections:
        del sec["anchors"]
    page_count = write_pages(site, sections, lexique)
    for sec in sections:
        del sec["description"]
    data = {
        "title": site["title"],
        "updated": last_updated(),
        "pages": site["pages"],
        "sections": sections,
        "lexique": lexique,
        "accueil": accueil,
        "projets": site.get("projets", []),
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        "// Généré par build/build.py depuis content/ : ne pas éditer à la main.\n"
        "const SITE = " + json.dumps(data, ensure_ascii=False, indent=1) + ";\n",
        encoding="utf-8",
    )
    print(f"{OUTPUT.relative_to(ROOT)} : {len(sections)} sections, {len(lexique)} termes")
    print(f"www/*.html : {page_count} pages de section et lexique, www/sitemap.xml : {page_count + 1} URL")


if __name__ == "__main__":
    try:
        main()
    except BuildError as err:
        sys.exit(f"Erreur de build :\n{err}")
