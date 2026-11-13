"""Helpers: Canva-style slide sections for the Slides artifact (format.md subset)."""
import html

FB = "'Carlito', Arial, sans-serif"          # body (Calibri metric twin; set Calibri in Canva)
FH = "'Cabin', Arial, sans-serif"            # titles and nav (as the author's Canva deck)
BLUE, INK, MUTED, RED, ORANGE, GREEN = "#1F6FB2", "#1E2430", "#5F6B7A", "#C62828", "#C8641E", "#1B7F5B"
PALE, LINE = "#EEF4FA", "#D5DCE4"
NAV = [("Introduction", 40, 214), ("Methodology", 268, 206), ("Results", 498, 124),
       ("Discussion", 646, 170), ("Conclusion", 840, 170)]


def e(s):
    return html.escape(s, quote=False)


def footer(page, nav=None):
    out = ['<div style="position:absolute;left:0;bottom:0;width:1920px;height:89px;'
           'background:linear-gradient(90deg, #D8E6F3 0%, #8DB6DD 40%, #2C67AE 100%)"></div>']
    if nav:
        for name, x, w in NAV:
            if name == nav:
                out.append(f'<p style="position:absolute;left:{x}px;bottom:16px;width:{w}px;height:56px;'
                           f'font-family:{FH};font-size:32px;line-height:1.6;text-align:center;color:#FFFFFF;'
                           f'background:{BLUE};border-radius:28px">{name}</p>')
            else:
                out.append(f'<p style="position:absolute;left:{x}px;bottom:16px;width:{w}px;height:56px;'
                           f'font-family:{FH};font-size:32px;line-height:1.6;text-align:center;color:{INK}">{name}</p>')
    out.append(f'<p style="position:absolute;right:40px;bottom:22px;width:90px;font-family:{FH};font-size:32px;'
               f'font-weight:700;color:#FFFFFF;text-align:right">{page}</p>')
    return "\n".join(out)


def section(sid, title, body, page, nav=None, sub=None, cite=None, notes=None, gap=16):
    parts = [f'<section id="{sid}" data-transition="fade" style="background:#FFFFFF;color:{INK};font-family:{FB};'
             f'padding:30px 40px 116px;display:flex;flex-direction:column;gap:{gap}px">']
    # rev 4 (20/10): References now one page, so every appendix page shifts by -1 (Thank you = 27, A1 = 28)
    if page >= 29:
        page -= 1
    parts.append(footer(page, nav))
    parts.append(f'<h2 style="font-family:{FH};font-size:54px;font-weight:600;line-height:1.15;color:{BLUE}">{title}</h2>')
    if sub:
        parts.append(f'<p style="font-size:30px;line-height:1.3;color:{INK}">{sub}</p>')
    parts.append(body)
    if cite:
        parts.append(f'<p style="position:absolute;left:40px;bottom:96px;width:1840px;font-size:22px;font-style:italic;'
                     f'color:{MUTED}">{cite}</p>')
    if notes:
        parts.append(f"<aside>{e(notes)}</aside>")
    parts.append("</section>")
    return "\n".join(parts)


def table(head, rows, widths, fs=27, hl=(), bold_first=False, colors=None, width=None):
    """head: list of str; rows: list of lists (str, may hold inline html); widths: % per column."""
    w = f"width:{width}px;" if width else ""
    t = [f'<table style="{w}font-size:{fs}px;line-height:1.25;color:{INK}">']
    t.append('<tr style="background:#E9EEF4">' + "".join(
        f'<th style="width:{wd}%">{h}</th>' for h, wd in zip(head, widths)) + "</tr>")
    for i, r in enumerate(rows):
        bg = ' style="background:#DCEBF8"' if i in hl else ""
        cells = []
        for j, c in enumerate(r):
            st = []
            if colors and (i, j) in colors:
                st.append(f"color:{colors[(i, j)]}")
            cells.append(f'<td style="{";".join(st)}">{c}</td>' if st else f"<td>{c}</td>")
        t.append(f"<tr{bg}>" + "".join(cells) + "</tr>")
    t.append("</table>")
    return "\n".join(t)


def img(src, alt, w, h, extra=""):
    return f'<img src="{{{{{src}}}}}" alt="{e(alt)}" style="width:{w}px;height:{h}px;object-fit:contain{extra}">'


def card(title, lines, w=None, bg=PALE, border=BLUE, fs=27, tfs=29, extra=""):
    ws = f"width:{w}px;" if w else "flex:1;"
    inner = "".join(f'<p style="font-size:{fs}px;line-height:1.3">{l}</p>' for l in lines)
    t = f'<p style="font-size:{tfs}px;font-weight:700;color:{border}">{title}</p>' if title else ""
    return (f'<div style="{ws}display:flex;flex-direction:column;gap:6px;background:{bg};'
            f'border-top:5px solid {border};padding:14px 18px{extra}">{t}{inner}</div>')


def span(text, color, bold=False):
    s = f'<span style="color:{color}">{text}</span>'
    return f"<b>{s}</b>" if bold else s
