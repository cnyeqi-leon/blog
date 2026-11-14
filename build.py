# -*- coding: utf-8 -*-
"""夜骑leon 博客 · 静态站点生成器

数据结构（都提交在仓库里）：
  _data/site.json          站点信息（昵称/签名/微信/GitHub/链接）
  _data/posts/*.json       每篇文章：{id,title,slug,date,tags,summary,cover,status,body(md)}
产物：
  index.html, post/<slug>.html, about.html, posts.json
用法：python build.py
"""
import html
import json
import os
import re
import sys

import mistune

sys.stdout.reconfigure(encoding='utf-8')

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, '_data')
POSTS_DIR = os.path.join(DATA, 'posts')

md = mistune.create_markdown(escape=False, plugins=['table', 'strikethrough', 'url'])

FONT = ("-apple-system,BlinkMacSystemFont,'PingFang SC','Microsoft YaHei',"
        "'Noto Sans SC',system-ui,sans-serif")

CSS = r'''
:root{--cream:#fff9ec;--cream2:#fff3d6;--ink:#1b1b1b;--ink2:#5b5346;--yellow:#ffd84d;
--pink:#f7a8c4;--mint:#a8e6cf;--line:#1b1b1b;--card:#fffdf8;--grid:#efe4cd}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--cream);color:var(--ink);font-family:__FONT__;
 background-image:radial-gradient(var(--grid) 1px,transparent 1px);background-size:22px 22px;
 font-size:16px;line-height:1.75}
a{color:var(--ink);text-decoration:none}
a:hover{color:#8a5a00}
.wrap{max-width:1040px;margin:0 auto;padding:0 20px 64px}
header.top{display:flex;align-items:center;justify-content:space-between;gap:16px;
 padding:22px 0 10px;flex-wrap:wrap}
.brand{display:flex;align-items:baseline;gap:10px;font-weight:800;font-size:20px;letter-spacing:.01em}
.brand .dot{width:10px;height:10px;border-radius:50%;background:var(--yellow);
 border:2px solid var(--ink);display:inline-block;transform:translateY(-2px)}
nav{display:flex;gap:8px;flex-wrap:wrap}
nav a{font-size:14px;padding:7px 13px;border:2px solid var(--ink);border-radius:999px;background:#fff;
 transition:.15s}
nav a:hover{background:var(--yellow);color:var(--ink)}
.hero{padding:26px 0 8px}
.hero h1{font-size:clamp(34px,6.4vw,62px);line-height:1.12;margin:0 0 12px;font-weight:800;letter-spacing:-.01em}
.hl{position:relative;display:inline-block;z-index:0}
.hl::after{content:"";position:absolute;left:-6px;right:-6px;bottom:6%;height:38%;
 background:var(--yellow);border-radius:6px;z-index:-1;transform:rotate(-1.2deg)}
.hero p{margin:10px 0 0;color:var(--ink2);font-size:17px;max-width:44em}
.chips{display:flex;gap:8px;flex-wrap:wrap;margin-top:16px}
.chip{font-size:13px;border:2px solid var(--ink);border-radius:999px;padding:4px 12px;background:#fff}
.chip.y{background:var(--yellow)}.chip.p{background:var(--pink)}.chip.m{background:var(--mint)}
.layout{display:grid;grid-template-columns:minmax(0,1fr) 300px;gap:26px;margin-top:30px;align-items:start}
@media(max-width:820px){.layout{grid-template-columns:1fr}}
.card{background:var(--card);border:2.5px solid var(--ink);border-radius:18px;
 box-shadow:6px 6px 0 rgba(27,27,27,.12);overflow:hidden}
.post-card{display:block;padding:20px 22px;margin-bottom:18px;transition:transform .14s}
.post-card:hover{transform:translate(-2px,-2px);box-shadow:8px 8px 0 rgba(27,27,27,.16)}
.post-card .meta{font-size:13px;color:var(--ink2);display:flex;gap:10px;flex-wrap:wrap;align-items:center}
.tag{font-size:12px;border:1.5px solid var(--ink);border-radius:999px;padding:2px 9px;background:var(--cream2)}
.post-card h2{margin:8px 0 6px;font-size:24px;line-height:1.35;font-weight:800}
.post-card p{margin:0;color:var(--ink2);font-size:15px}
.post-card .cover{margin:14px -22px -20px;border-top:2.5px solid var(--ink);display:block}
.post-card .cover img{display:block;width:100%;max-height:260px;object-fit:cover}
.side{position:sticky;top:18px;display:grid;gap:18px}
.side .card{padding:18px}
.me{display:flex;align-items:center;gap:14px}
.avatar{width:56px;height:56px;border-radius:50%;background:var(--yellow);border:2.5px solid var(--ink);
 display:grid;place-items:center;font-weight:800;font-size:22px;flex:none}
.me b{display:block;font-size:16px}
.me span{font-size:13px;color:var(--ink2)}
.side h3{margin:18px 0 8px;font-size:14px;letter-spacing:.06em;color:var(--ink2);text-transform:uppercase}
.qr{display:block;width:100%;border:2.5px solid var(--ink);border-radius:14px;background:#fff}
.links{display:grid;gap:8px;margin-top:6px}
.links a{border:2px solid var(--ink);border-radius:12px;padding:8px 12px;background:#fff;font-size:14px}
.links a:hover{background:var(--yellow)}
.note{font-size:12.5px;color:var(--ink2);margin-top:8px}
footer{margin-top:44px;padding-top:18px;border-top:2px dashed var(--ink);font-size:13px;color:var(--ink2);
 display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap}
/* ---------- 文章页 ---------- */
article.post{background:var(--card);border:2.5px solid var(--ink);border-radius:20px;
 box-shadow:6px 6px 0 rgba(27,27,27,.12);padding:34px clamp(20px,4vw,52px);margin-top:22px}
article.post h1{font-size:clamp(28px,4.6vw,42px);line-height:1.25;margin:6px 0 14px;font-weight:800}
.postmeta{display:flex;gap:10px;flex-wrap:wrap;align-items:center;font-size:13.5px;color:var(--ink2);
 padding-bottom:16px;border-bottom:2px dashed var(--ink);margin-bottom:22px}
.body{font-size:16.5px;line-height:1.9}
.body h2{font-size:26px;margin:34px 0 12px;font-weight:800}
.body h2 .mk{background:linear-gradient(transparent 62%,var(--yellow) 62%)}
.body h3{font-size:20px;margin:26px 0 10px}
.body p{margin:14px 0}
.body ul,.body ol{margin:14px 0;padding-left:1.5em}
.body li{margin:6px 0}
.body img{max-width:100%;border:2.5px solid var(--ink);border-radius:14px;display:block;margin:18px auto;
 box-shadow:5px 5px 0 rgba(27,27,27,.12)}
.body blockquote{margin:18px 0;padding:12px 18px;background:var(--cream2);border-left:6px solid var(--yellow);
 border-radius:0 12px 12px 0;color:var(--ink)}
.body code{background:#f0e7d6;border:1px solid #d8cbb1;border-radius:6px;padding:1px 6px;font-size:.92em}
.body pre{background:#1b1b1b;color:#f7f3e8;padding:16px 18px;border-radius:14px;overflow:auto}
.body pre code{background:none;border:0;color:inherit;padding:0}
.body a{border-bottom:2px solid var(--yellow);font-weight:600}
.body table{border-collapse:collapse;width:100%;margin:18px 0;font-size:15px}
.body th,.body td{border:1.5px solid var(--ink);padding:8px 10px;text-align:left}
.body th{background:var(--cream2)}
.body hr{border:0;border-top:2px dashed var(--ink);margin:28px 0}
.pager{display:flex;justify-content:space-between;gap:14px;margin-top:26px;flex-wrap:wrap}
.empty{padding:40px;text-align:center;color:var(--ink2)}
'''.replace('__FONT__', FONT)


def esc(s):
    return html.escape(s or '')


def read_json(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def load_posts():
    posts = []
    if os.path.isdir(POSTS_DIR):
        for fn in sorted(os.listdir(POSTS_DIR)):
            if not fn.endswith('.json'):
                continue
            p = read_json(os.path.join(POSTS_DIR, fn))
            if not p:
                continue
            if p.get('status') != 'published':
                continue
            posts.append(p)
    posts.sort(key=lambda x: (x.get('date') or '', x.get('id') or ''), reverse=True)
    return posts


def render_md(text, prefix=''):
    out = md(text or '')
    if prefix:
        out = re.sub(r'(src|href)="(?!https?:|/|#|mailto:)', r'\1="' + prefix, out)
    # h2 加荧光笔
    out = re.sub(r'<h2>(.*?)</h2>', r'<h2><span class="mk">\1</span></h2>', out, flags=re.S)
    return out


def page_shell(site, title, body, extra_head=''):
    return f'''<!doctype html>
<html lang="zh-CN"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(site.get('bio') or site.get('tagline') or '')}">
<meta name="theme-color" content="#fff9ec">
<link rel="stylesheet" href="{{ROOT}}assets/style.css">
{extra_head}
</head><body>
<div class="wrap">
{body}
<footer>
  <span>{esc(site.get('name',''))} · {esc(site.get('tagline',''))}</span>
  <span>{esc(site.get('footer',''))}</span>
</footer>
</div>
</body></html>'''


def header(site, root):
    items = [('文章', root + 'index.html'), ('关于', root + 'about.html')]
    for l in site.get('nav_extra') or []:
        items.append((l['label'], l['url']))
    nav = ''.join('<a href="%s">%s</a>' % (esc(u), esc(t)) for t, u in items)
    return f'''<header class="top">
  <div class="brand"><span class="dot"></span>{esc(site.get('name',''))} · {esc(site.get('site_title',''))}</div>
  <nav>{nav}</nav>
</header>'''


def about_card(site):
    qr = site.get('qr') or ''
    q = f'<img class="qr" src="{{ROOT}}{esc(qr)}" alt="微信二维码">' if qr else ''
    links = ''.join('<a href="%s">%s</a>' % (esc(l['url']), esc(l['label'])) for l in site.get('links') or [])
    return f'''<div class="card">
  <div class="me">
    <div class="avatar">{esc(site.get('avatar_text','L'))}</div>
    <div><b>{esc(site.get('name',''))}</b><span>{esc(site.get('tagline',''))}</span></div>
  </div>
  <h3>加我</h3>
  {q}
  <div class="note">微信：{esc(site.get('wechat',''))}</div>
  <div class="note">{esc(site.get('bio',''))}</div>
  <h3>链接</h3>
  <div class="links">{links}</div>
</div>'''


def build_index(site, posts):
    cards = []
    for p in posts:
        cover = ''
        if p.get('cover'):
            cover = f'<span class="cover"><img src="{{ROOT}}{esc(p["cover"])}" alt=""></span>'
        tags = ''.join('<span class="tag">%s</span>' % esc(t) for t in p.get('tags') or [])
        cards.append(f'''<a class="card post-card" href="{{ROOT}}post/{esc(p['slug'])}.html">
  <div class="meta"><span>{esc(p.get('date',''))}</span>{tags}</div>
  <h2>{esc(p.get('title',''))}</h2>
  <p>{esc(p.get('summary',''))}</p>
  {cover}
</a>''')
    body = header(site, '{ROOT}') + f'''
<section class="hero">
  <h1><span class="hl">{esc(site.get('hero_title','我的博客'))}</span></h1>
  <p>{esc(site.get('hero_sub',''))}</p>
  <div class="chips">{''.join('<span class="chip %s">%s</span>' % (esc(c.get('color','')), esc(c.get('text',''))) for c in site.get('chips') or [])}</div>
</section>
<div class="layout">
  <div>{''.join(cards) or '<div class="card empty">还没有文章</div>'}</div>
  <aside class="side">{about_card(site)}</aside>
</div>'''
    out = page_shell(site, site.get('title') or site.get('name'), body).replace('{ROOT}', '')
    open(os.path.join(ROOT, 'index.html'), 'w', encoding='utf-8').write(out)
    print('index.html', len(out))


def build_posts(site, posts):
    os.makedirs(os.path.join(ROOT, 'post'), exist_ok=True)
    for i, p in enumerate(posts):
        body_html = render_md(p.get('body') or '', prefix='../')
        tags = ''.join('<span class="tag">%s</span>' % esc(t) for t in p.get('tags') or [])
        prev_p = posts[i + 1] if i + 1 < len(posts) else None
        next_p = posts[i - 1] if i > 0 else None
        pager = '<div class="pager">'
        pager += (f'<a class="chip" href="../post/{esc(prev_p["slug"])}.html">← {esc(prev_p["title"])}</a>' if prev_p else '<span></span>')
        pager += (f'<a class="chip" href="../post/{esc(next_p["slug"])}.html">{esc(next_p["title"])} →</a>' if next_p else '<span></span>')
        pager += '</div>'
        body = header(site, '../') + f'''
<article class="post">
  <div class="postmeta"><span>{esc(p.get('date',''))}</span>{tags}</div>
  <h1>{esc(p.get('title',''))}</h1>
  <div class="body">{body_html}</div>
  {pager}
</article>'''
        out = page_shell(site, '%s · %s' % (p.get('title', ''), site.get('name', '')), body).replace('{ROOT}', '../')
        open(os.path.join(ROOT, 'post', p['slug'] + '.html'), 'w', encoding='utf-8').write(out)
    print('posts built', len(posts))


def build_about(site):
    body = header(site, '') + f'''
<section class="hero"><h1><span class="hl">关于我</span></h1></section>
<div class="layout">
  <div class="card" style="padding:26px 28px">
    <div class="body">{render_md(site.get('about_md') or '')}</div>
  </div>
  <aside class="side">{about_card(site)}</aside>
</div>'''
    out = page_shell(site, '关于 · ' + site.get('name', ''), body).replace('{ROOT}', '')
    open(os.path.join(ROOT, 'about.html'), 'w', encoding='utf-8').write(out)
    print('about.html', len(out))


def build_feed(site, posts):
    feed = [{'slug': p['slug'], 'title': p.get('title', ''), 'date': p.get('date', ''),
             'tags': p.get('tags') or [], 'summary': p.get('summary', ''),
             'cover': p.get('cover', '')} for p in posts]
    json.dump({'site': {'name': site.get('name'), 'tagline': site.get('tagline')}, 'posts': feed},
              open(os.path.join(ROOT, 'posts.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('posts.json', len(feed))


def main():
    site = read_json(os.path.join(DATA, 'site.json'), {}) or {}
    os.makedirs(os.path.join(ROOT, 'assets'), exist_ok=True)
    open(os.path.join(ROOT, 'assets', 'style.css'), 'w', encoding='utf-8').write(CSS)
    posts = load_posts()
    build_index(site, posts)
    build_posts(site, posts)
    build_about(site)
    build_feed(site, posts)
    print('done')


if __name__ == '__main__':
    main()
