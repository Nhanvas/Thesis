"""v5 helpers (deck v5, 21/10): the author's Canva style, full deck. Re-uses table/card/img/span of lib (D4g)."""
from lib import FB, FH, BLUE, INK, MUTED, RED, ORANGE, GREEN, PALE, LINE, e, footer, table, img, card, span

HL = "#DC433A"      # the author's highlight red in Canva
BLK = "#000000"


def hl(t, bold=True):
    return span(t, HL, bold)


def slide(sid, title, body, page, nav=None, sub=None, cite=None, notes=None, gap=16, sub_fs=34, pad_b=116):
    parts = [f'<section id="{sid}" data-transition="fade" style="background:#FFFFFF;color:{INK};font-family:{FB};'
             f'padding:26px 40px {pad_b}px;display:flex;flex-direction:column;gap:{gap}px">']
    parts.append(footer(page, nav))
    parts.append(f'<h2 style="font-family:{FH};font-size:53px;font-weight:700;line-height:1.15;color:{BLUE}">{title}</h2>')
    if sub:
        parts.append(f'<p style="font-size:{sub_fs}px;line-height:1.3;color:{BLK}">{sub}</p>')
    parts.append(body)
    if cite:
        parts.append(f'<p style="position:absolute;left:40px;bottom:96px;width:1840px;font-size:22px;font-style:italic;'
                     f'color:{MUTED}">{cite}</p>')
    if notes:
        parts.append(f"<aside>{e(notes)}</aside>")
    parts.append("</section>")
    return "\n".join(parts)


def cap(t, fs=30, align="left"):
    return f'<p style="font-size:{fs}px;font-style:italic;color:{INK};text-align:{align}">{t}</p>'


def ul(items, fs=34, lh=1.4, w=None, extra=""):
    ws = f"width:{w}px;" if w else ""
    return f'<ul style="{ws}font-size:{fs}px;line-height:{lh}{extra}">' + "".join(f"<li>{i}</li>" for i in items) + "</ul>"


def row(*cols, gap=30, align="start", extra=""):
    return f'<div style="display:flex;flex-direction:row;gap:{gap}px;align-items:{align}{extra}">' + "".join(cols) + "</div>"


def colm(*items, w=None, gap=12, extra=""):
    ws = f"width:{w}px;" if w else "flex:1;"
    return f'<div style="{ws}display:flex;flex-direction:column;gap:{gap}px{extra}">' + "".join(items) + "</div>"


def p(t, fs=34, extra=""):
    return f'<p style="font-size:{fs}px;line-height:1.3{extra}">{t}</p>'


def fig(name, alt, w, h, caption=None, cfs=28):
    c = cap(caption, cfs, "center") if caption else ""
    return (f'<div style="display:flex;flex-direction:column;align-items:center;gap:6px">'
            f'{img(name, alt, w, h)}{c}</div>')


def dashed(inner, w=None, pad="16px 22px", extra="", fill=False):
    ws = f"width:{w}px;" if w else ("flex:1;" if fill else "")
    return (f'<div style="{ws}display:flex;flex-direction:column;gap:8px;border:3px dashed {INK};border-radius:10px;'
            f'padding:{pad}{extra}">{inner}</div>')
