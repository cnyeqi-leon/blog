# -*- coding: utf-8 -*-
"""夜航手记 · X 风格单列时间线静态站点生成器

数据（与本地后台字段兼容，后台保存后直接重建即可）：
  _data/site.json        站点信息：name / author / handle / tagline / bio / about_md / footer ...
  _data/posts/*.json     每篇文章：{id, title, slug, date, status, tags, summary, cover, body(markdown)}

产物：
  index.html             时间线首页（搜索过滤 / 深浅色切换 / 右侧栏）
  post/<slug>.html       单篇帖子页
  about.html             关于页
  posts.json             文章索引
  assets/style.css       样式
  assets/app.js          前端脚本

用法：python build.py
"""
import hashlib
import html
import json
import os
import re
import sys
from collections import Counter
from urllib.parse import quote

try:
    import mistune
    _MD = mistune.create_markdown(escape=False, plugins=['table', 'strikethrough', 'url'])
except Exception:  # 没装 mistune 也能构建
    mistune = None
    _MD = None

sys.stdout.reconfigure(encoding='utf-8')

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, '_data')
POSTS_DIR = os.path.join(DATA, 'posts')

FONT = ('-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Hiragino Sans GB",'
        '"Microsoft YaHei","Noto Sans SC",system-ui,sans-serif')

FAVICON = ("data:image/svg+xml,%3Csvg%20xmlns='http://www.w3.org/2000/svg'%20viewBox='0%200%2064%2064'%3E"
           "%3Crect%20width='64'%20height='64'%20rx='16'%20fill='%230f1419'/%3E"
           "%3Cpath%20d='M41%2010a22%2022%200%201%200%2013%2031A18%2018%200%200%201%2041%2010z'%20fill='%231d9bf0'/%3E"
           "%3C/svg%3E")

THEME_INIT = ('<script>(function(){try{var t=localStorage.getItem("theme");'
              'if(t==="dark"||(!t&&window.matchMedia&&window.matchMedia("(prefers-color-scheme: dark)").matches)){'
              'document.documentElement.setAttribute("data-theme","dark");'
              'var m=document.getElementById("themeColor");if(m)m.setAttribute("content","#000000");}'
              '}catch(e){}})();</script>')

LOGO = ('<svg class="brand-mark" viewBox="0 0 32 32" aria-hidden="true">'
        '<defs><linearGradient id="bm" x1="0" y1="0" x2="1" y2="1">'
        '<stop offset="0" stop-color="#1d9bf0"/><stop offset="1" stop-color="#7856ff"/></linearGradient></defs>'
        '<circle cx="16" cy="16" r="16" fill="url(#bm)"/>'
        '<path d="M21.7 7.2a9.6 9.6 0 1 0 2.9 14.3A8.3 8.3 0 0 1 21.7 7.2z" fill="#fff"/></svg>')

ICON_REPLY = ('<svg viewBox="0 0 24 24" aria-hidden="true">'
              '<path d="M12 3.5c5.2 0 9.5 3.7 9.5 8.2 0 4.6-4.3 8.3-9.5 8.3-1.1 0-2.2-.1-3.2-.4L4 21.5l1.1-3.8C3.6 16.2 2.5 14.1 2.5 11.7c0-4.5 4.3-8.2 9.5-8.2z" '
              'fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"/></svg>')
ICON_REPOST = ('<svg viewBox="0 0 24 24" aria-hidden="true">'
               '<path d="M4 9.5h10.5a3 3 0 0 1 3 3V17" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/>'
               '<path d="M14.5 5.5 18.5 9.5 14.5 13.5" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/>'
               '<path d="M20 14.5H9.5a3 3 0 0 1-3-3V7" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/>'
               '<path d="M9.5 18.5 5.5 14.5 9.5 10.5" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg>')
ICON_HEART = ('<svg viewBox="0 0 24 24" aria-hidden="true">'
              '<path d="M12 20.2 10.7 19C6.2 15 3 12.2 3 8.8 3 6.2 5.1 4 7.7 4c1.6 0 3.1.8 4.3 2.2C13.2 4.8 14.7 4 16.3 4 18.9 4 21 6.2 21 8.8c0 3.4-3.2 6.2-7.7 10.2L12 20.2z" '
              'fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"/></svg>')
ICON_SHARE = ('<svg viewBox="0 0 24 24" aria-hidden="true">'
              '<path d="M12 15.5V4.5" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/>'
              '<path d="M7.5 9 12 4.5 16.5 9" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/>'
              '<path d="M5 13.5v4.5A2 2 0 0 0 7 20h10a2 2 0 0 0 2-2v-4.5" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/></svg>')
ICON_SUN = ('<svg class="ic-sun" viewBox="0 0 24 24" aria-hidden="true">'
            '<circle cx="12" cy="12" r="4.3" fill="none" stroke="currentColor" stroke-width="1.7"/>'
            '<path d="M12 2.6v2.2M12 19.2v2.2M2.6 12h2.2M19.2 12h2.2M5.4 5.4l1.6 1.6M17 17l1.6 1.6M18.6 5.4 17 7M7 17l-1.6 1.6" '
            'fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/></svg>')
ICON_MOON = ('<svg class="ic-moon" viewBox="0 0 24 24" aria-hidden="true">'
             '<path d="M20.4 14.2A8.6 8.6 0 0 1 9.8 3.6a8.6 8.6 0 1 0 10.6 10.6z" fill="none" stroke="currentColor" '
             'stroke-width="1.7" stroke-linejoin="round"/></svg>')
ICON_CLEAR = ('<svg viewBox="0 0 24 24" aria-hidden="true">'
              '<path d="M6 6l12 12M18 6 6 18" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/></svg>')
ICON_SEARCH = ('<svg class="search-icon" viewBox="0 0 24 24" aria-hidden="true">'
               '<path d="M10.5 3a7.5 7.5 0 1 1-4.7 13.35l-3.32 3.32a1 1 0 1 1-1.42-1.42l3.32-3.32A7.5 7.5 0 0 1 10.5 3zm0 2a5.5 5.5 0 1 0 0 11 5.5 5.5 0 0 0 0-11z" fill="currentColor"/></svg>')
ICON_BACK = ('<svg viewBox="0 0 24 24" aria-hidden="true">'
             '<path d="M20 12H5M11 6l-6 6 6 6" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>')

AVATARS = [
    ('#1d9bf0', '#7856ff'),
    ('#00ba7c', '#1d9bf0'),
    ('#ff7854', '#f91880'),
    ('#7856ff', '#f91880'),
    ('#f5a524', '#ff7854'),
    ('#00b8d9', '#00ba7c'),
    ('#536471', '#1d9bf0'),
    ('#1d9bf0', '#f5a524'),
]

DEFAULT_ABOUT = """## 关于这个站

这是一个只放文字的角落。没有算法推荐，没有时间线焦虑；写下来，就放在这里。

## 会写什么

- 读到的一句值得记下的话
- 一段路过的观察
- 折腾东西时的记录

## 不会写什么

真实姓名、学校、住址、联系方式，一概不写。这里只有文字。

## 关于我

一个喜欢在夜里写字的人。仅此而已。"""

CSS = r'''/* =========================================================
   夜航手记 · X 风格单列时间线
   ========================================================= */
:root{
  --font: __FONT__;
  --bg:#ffffff;
  --surface:#ffffff;
  --surface-2:#f7f9f9;
  --surface-3:#eff3f4;
  --line:#eff3f4;
  --line-strong:#cfd9de;
  --text:#0f1419;
  --muted:#536471;
  --faint:#8b98a5;
  --accent:#1d9bf0;
  --accent-soft:rgba(29,155,240,.10);
  --like:#f91880;
  --repost:#00ba7c;
  --header:rgba(255,255,255,.86);
  --radius:16px;
  --max:966px;
  color-scheme:light;
}
[data-theme="dark"]{
  --bg:#000000;
  --surface:#16181c;
  --surface-2:#1d1f23;
  --surface-3:#22262b;
  --line:#2f3336;
  --line-strong:#3d4247;
  --text:#e7e9ea;
  --muted:#8b98a5;
  --faint:#71767b;
  --accent:#1d9bf0;
  --accent-soft:rgba(29,155,240,.16);
  --header:rgba(0,0,0,.82);
  color-scheme:dark;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--text);font-family:var(--font);font-size:15px;
  line-height:1.5;-webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale;overflow-y:scroll}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}
button{font:inherit;color:inherit;background:none;border:0;padding:0;cursor:pointer}
img{max-width:100%}
::selection{background:rgba(29,155,240,.28)}
[hidden]{display:none !important}
.sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;
  clip:rect(0 0 0 0);white-space:nowrap;border:0}

/* ---------- 顶栏 ---------- */
.topbar{position:sticky;top:0;z-index:50;background:var(--header);
  -webkit-backdrop-filter:blur(14px) saturate(1.4);backdrop-filter:blur(14px) saturate(1.4);
  border-bottom:1px solid var(--line)}
.topbar-inner{max-width:var(--max);margin:0 auto;padding:0 18px;height:56px;
  display:flex;align-items:center;gap:12px}
.brand{display:inline-flex;align-items:center;gap:9px;color:var(--text);font-weight:800;
  font-size:17px;letter-spacing:-.01em;flex:none}
.brand:hover{text-decoration:none}
.brand-mark{width:28px;height:28px;flex:none}
.brand-name{white-space:nowrap}
.icon-btn{width:38px;height:38px;border-radius:999px;display:grid;place-items:center;
  color:var(--text);transition:background .15s,color .15s;flex:none}
.icon-btn:hover{background:var(--surface-2)}
.icon-btn svg{width:19px;height:19px}
.topbar-actions{display:flex;align-items:center;gap:4px;flex:none;margin-left:auto}
.ghost-link{font-size:14px;color:var(--muted);padding:8px 12px;border-radius:999px;
  transition:background .15s,color .15s;white-space:nowrap}
.ghost-link:hover{background:var(--surface-2);color:var(--text);text-decoration:none}
.topbar-spacer{flex:1}
.theme-btn .ic-moon{display:none}
[data-theme="dark"] .theme-btn .ic-moon{display:block}
[data-theme="dark"] .theme-btn .ic-sun{display:none}

/* 搜索框 */
.search{position:relative;display:flex;align-items:center;flex:1 1 200px;max-width:380px;margin:0 auto}
.search input{width:100%;height:38px;border:1px solid transparent;border-radius:999px;
  background:var(--surface-2);color:var(--text);padding:0 38px 0 40px;font:inherit;font-size:14px;
  outline:none;-webkit-appearance:none;appearance:none;
  transition:background .15s,border-color .15s,box-shadow .15s}
.search input::placeholder{color:var(--faint)}
.search input:focus{background:var(--bg);border-color:var(--accent);box-shadow:0 0 0 3px var(--accent-soft)}
.search-icon{position:absolute;left:14px;width:17px;height:17px;color:var(--faint);pointer-events:none}
.qclear{position:absolute;right:7px;width:26px;height:26px;border-radius:50%;
  display:grid;place-items:center;color:var(--bg);background:var(--accent)}
.qclear svg{width:14px;height:14px}

/* ---------- 页面骨架 ---------- */
.page{max-width:var(--max);margin:0 auto;padding:16px 18px 44px;display:grid;
  grid-template-columns:minmax(0,600px);justify-content:center;gap:26px}
@media(min-width:1200px){
  .page{grid-template-columns:minmax(0,600px) 300px;justify-content:space-between;padding-top:20px}
}
.timeline,.thread,.about{min-width:0}

/* ---------- 时间线 ---------- */
.timeline-head{display:flex;align-items:baseline;justify-content:space-between;gap:10px;
  padding:4px 4px 14px}
.timeline-head h1{font-size:22px;line-height:1.2;letter-spacing:-.02em;margin:0;font-weight:800}
.count{font-size:13px;color:var(--muted);white-space:nowrap}
.filter-bar{display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap;
  font-size:13px;color:var(--muted);background:var(--accent-soft);
  border:1px solid rgba(29,155,240,.25);border-radius:12px;padding:9px 12px;margin:0 0 12px}
.filter-clear{font-size:13px;color:var(--accent);font-weight:600;flex:none}
.filter-clear:hover{text-decoration:underline}

.feed{display:flex;flex-direction:column;gap:10px}
.post-card{display:flex;gap:12px;padding:15px 16px;background:var(--surface);
  border:1px solid var(--line);border-radius:var(--radius);
  transition:background .15s,border-color .15s}
.post-card:hover{background:var(--surface-2);border-color:var(--line-strong)}
.avatar{width:44px;height:44px;flex:none;border-radius:50%;display:grid;place-items:center;
  color:#fff;font-weight:700;font-size:17px;position:relative;overflow:hidden;
  background:conic-gradient(from var(--av-r,140deg),var(--av-a,#1d9bf0),var(--av-b,#7856ff),var(--av-a,#1d9bf0))}
.avatar::before{content:"";position:absolute;inset:0;
  background:radial-gradient(120% 90% at 78% 16%,rgba(255,255,255,.45),transparent 52%),
             radial-gradient(90% 90% at 18% 88%,rgba(0,0,0,.22),transparent 62%)}
.avatar span{position:relative;z-index:1;text-shadow:0 1px 2px rgba(0,0,0,.28)}
.avatar-xl{width:58px;height:58px;font-size:22px;border:3px solid var(--surface);
  box-shadow:0 0 0 1px var(--line)}
.pc-main{flex:1;min-width:0}
.pc-head{display:flex;align-items:center;gap:4px;flex-wrap:wrap;font-size:15px;min-width:0}
.pc-name{color:var(--text);font-weight:700;max-width:100%;overflow:hidden;text-overflow:ellipsis;
  white-space:nowrap}
.pc-name:hover{text-decoration:underline}
.pc-handle,.pc-time{color:var(--muted);font-size:14px}
.pc-sep{color:var(--muted)}
.pc-link{display:block;color:var(--text)}
.pc-link:hover{text-decoration:none}
.pc-title{font-size:16px;line-height:1.4;letter-spacing:-.005em;margin:3px 0 2px;font-weight:700;
  word-break:break-word}
.pc-link:hover .pc-title{text-decoration:underline}
.pc-text{margin:0;font-size:15px;line-height:1.55;color:var(--text);word-break:break-word;
  display:-webkit-box;-webkit-line-clamp:4;-webkit-box-orient:vertical;overflow:hidden}
.pc-cover{margin-top:10px;border:1px solid var(--line);border-radius:14px;overflow:hidden;
  background:var(--surface-2)}
.pc-cover img{display:block;width:100%;max-height:320px;object-fit:cover}
.pc-tags{display:flex;flex-wrap:wrap;gap:0 12px;margin-top:7px}
.tag{font-size:13.5px;color:var(--accent);padding:2px 0;line-height:1.5}
.tag:hover{text-decoration:underline}

.pc-actions{display:flex;align-items:center;gap:2px;margin:8px 0 0 -8px}
.act{width:34px;height:34px;border-radius:50%;display:grid;place-items:center;color:var(--muted);
  transition:color .15s,background .15s}
.act svg{width:18px;height:18px}
.act:hover{color:var(--accent);background:var(--accent-soft)}
.act-repost:hover{color:var(--repost);background:rgba(0,186,124,.1)}
.act-like:hover{color:var(--like);background:rgba(249,24,128,.1)}
.act-like.liked{color:var(--like)}
.act-like.liked svg path{fill:currentColor}

.empty{display:flex;flex-direction:column;align-items:center;gap:10px;padding:52px 20px;
  color:var(--muted);font-size:14.5px;text-align:center;
  border:1px dashed var(--line-strong);border-radius:var(--radius);margin-top:10px}
.empty-ico{font-size:26px;color:var(--faint);line-height:1}
.feed-end{text-align:center;font-size:12.5px;color:var(--faint);letter-spacing:.08em;margin:22px 0 0}

/* ---------- 页脚 ---------- */
.site-foot{display:flex;flex-direction:column;gap:7px;margin-top:28px;padding-top:18px;
  border-top:1px solid var(--line);font-size:13px;color:var(--muted)}
.site-foot nav{display:flex;gap:16px;flex-wrap:wrap}
.site-foot a{color:var(--muted)}
.site-foot a:hover{color:var(--accent)}
.site-foot p{margin:0}
.foot-fine{font-size:12px;color:var(--faint)}

/* ---------- 侧栏 ---------- */
.sidebar{display:none;flex-direction:column;gap:14px;min-width:0}
@media(min-width:1200px){
  .sidebar{display:flex;position:sticky;top:74px;align-self:start}
}
.side-card{background:var(--surface-2);border:1px solid var(--line);border-radius:var(--radius);
  padding:16px 18px}
.side-card h2{font-size:15px;margin:0 0 12px;font-weight:700;letter-spacing:-.01em}
.profile-card{padding:0;overflow:hidden;background:var(--surface)}
.profile-banner{height:76px;background:
  radial-gradient(1.2px 1.2px at 14% 28%,#fff 45%,transparent 55%),
  radial-gradient(1px 1px at 27% 62%,rgba(255,255,255,.85) 45%,transparent 55%),
  radial-gradient(1.6px 1.6px at 42% 24%,#fff 45%,transparent 55%),
  radial-gradient(1px 1px at 56% 68%,rgba(255,255,255,.8) 45%,transparent 55%),
  radial-gradient(1.4px 1.4px at 71% 36%,#fff 45%,transparent 55%),
  radial-gradient(1px 1px at 83% 60%,rgba(255,255,255,.75) 45%,transparent 55%),
  radial-gradient(1.2px 1.2px at 92% 26%,#fff 45%,transparent 55%),
  linear-gradient(125deg,#0b1220 0%,#132a4a 48%,#1d4f86 78%,#1d9bf0 130%)}
.profile-body{padding:0 18px 16px;margin-top:-24px;position:relative}
.p-name{font-size:18px;margin:8px 0 0;font-weight:800;letter-spacing:-.01em}
.p-handle{font-size:14px;color:var(--muted);margin-top:1px}
.p-bio{font-size:13.5px;line-height:1.6;margin:10px 0 12px;color:var(--text)}
.p-stats{display:flex;gap:16px;font-size:13px;color:var(--muted)}
.p-stats b{color:var(--text);font-weight:700}
.side-link{display:inline-block;margin-top:12px;font-size:13.5px;color:var(--accent);font-weight:600}
.tagcloud{display:flex;flex-wrap:wrap;gap:7px}
.tag-chip{display:inline-flex;align-items:center;gap:5px;font-size:13px;color:var(--text);
  background:var(--surface);border:1px solid var(--line);border-radius:999px;padding:5px 11px;
  transition:.12s;line-height:1.4}
.tag-chip:hover{background:var(--accent-soft);border-color:rgba(29,155,240,.4);
  color:var(--accent);text-decoration:none}
.tag-chip .n{font-size:11px;color:var(--faint)}
.archive{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:1px}
.archive button,.archive a{display:flex;justify-content:space-between;align-items:center;gap:10px;
  width:100%;padding:8px 9px;border-radius:10px;font-size:13.5px;color:var(--text);
  text-align:left;transition:background .12s,color .12s}
.archive :hover{background:var(--surface);color:var(--accent);text-decoration:none}
.archive .n{font-size:12px;color:var(--faint)}
.side-note{font-size:13px;color:var(--muted);line-height:1.6}
.side-foot{font-size:12px;color:var(--faint);line-height:1.6;padding:2px 4px;margin:0}

/* ---------- 帖子页 ---------- */
.thread-card{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);
  padding:18px 20px 8px}
.tp-head{display:flex;align-items:center;gap:10px}
.tp-id{display:flex;flex-direction:column;line-height:1.3;min-width:0}
.tp-name{font-weight:700;font-size:15px}
.tp-handle{font-size:14px;color:var(--muted)}
.tp-title{font-size:23px;line-height:1.32;letter-spacing:-.015em;margin:16px 0 4px;
  font-weight:800;word-break:break-word}
.tp-meta{font-size:14px;color:var(--muted);padding-bottom:14px;border-bottom:1px solid var(--line);
  margin-bottom:16px}
.tp-tags{display:flex;flex-wrap:wrap;gap:0 12px;margin:0 0 14px}
.tp-actions{display:flex;gap:6px;border-top:1px solid var(--line);margin-top:20px;
  padding:8px 0 4px;margin-left:-8px}

/* ---------- 正文排版 ---------- */
.body{font-size:16px;line-height:1.85;word-break:break-word}
.body>*:first-child{margin-top:0}
.body p{margin:14px 0}
.body h2{font-size:21px;line-height:1.35;margin:28px 0 10px;font-weight:800;letter-spacing:-.01em}
.body h3{font-size:17.5px;margin:22px 0 8px;font-weight:700}
.body ul,.body ol{margin:14px 0;padding-left:1.35em}
.body li{margin:6px 0}
.body li::marker{color:var(--faint)}
.body a{color:var(--accent);text-decoration:underline;text-underline-offset:2px}
.body blockquote{margin:18px 0;padding:2px 0 2px 16px;border-left:3px solid var(--accent);
  color:var(--muted)}
.body blockquote p{margin:6px 0}
.body code{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:.9em;
  background:var(--surface-2);border:1px solid var(--line);border-radius:6px;padding:1px 5px}
.body pre{background:var(--surface-2);border:1px solid var(--line);border-radius:12px;
  padding:14px 16px;overflow:auto;line-height:1.6}
.body pre code{background:none;border:0;padding:0;font-size:13.5px}
.body img{border-radius:14px;border:1px solid var(--line);margin:18px 0;display:block}
.body table{border-collapse:collapse;width:100%;margin:18px 0;font-size:14.5px}
.body th,.body td{border:1px solid var(--line-strong);padding:8px 10px;text-align:left}
.body th{background:var(--surface-2)}
.body hr{border:0;border-top:1px solid var(--line);margin:26px 0}

/* ---------- 上一条 / 下一条 ---------- */
.pager{display:flex;gap:10px;margin-top:14px}
.pager-link{flex:1;min-width:0;display:flex;flex-direction:column;gap:3px;background:var(--surface);
  border:1px solid var(--line);border-radius:14px;padding:11px 14px;color:var(--muted);
  font-size:12.5px;transition:.15s}
.pager-link:hover{background:var(--surface-2);border-color:var(--line-strong);text-decoration:none}
.pager-link b{display:block;color:var(--text);font-size:14px;font-weight:600;overflow:hidden;
  text-overflow:ellipsis;white-space:nowrap}
.back-home{display:inline-block;margin-top:16px;font-size:14px;color:var(--accent);font-weight:600}

/* ---------- 关于页 ---------- */
.about-card{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);
  overflow:hidden}
.about-banner{height:150px;background:
  radial-gradient(1.4px 1.4px at 10% 30%,#fff 45%,transparent 55%),
  radial-gradient(1px 1px at 22% 66%,rgba(255,255,255,.8) 45%,transparent 55%),
  radial-gradient(2px 2px at 34% 22%,#fff 45%,transparent 55%),
  radial-gradient(1.2px 1.2px at 47% 58%,rgba(255,255,255,.85) 45%,transparent 55%),
  radial-gradient(1px 1px at 58% 34%,rgba(255,255,255,.75) 45%,transparent 55%),
  radial-gradient(1.6px 1.6px at 69% 70%,#fff 45%,transparent 55%),
  radial-gradient(1px 1px at 80% 30%,rgba(255,255,255,.8) 45%,transparent 55%),
  radial-gradient(1.4px 1.4px at 91% 56%,#fff 45%,transparent 55%),
  linear-gradient(118deg,#05080f 0%,#0e1c33 55%,#153a63 100%)}
.about-body{padding:0 22px 22px;margin-top:-30px;position:relative}
.about-name{font-size:24px;font-weight:800;letter-spacing:-.02em;margin:10px 0 0}
.about-handle{font-size:14.5px;color:var(--muted);margin-top:1px}
.about-bio{font-size:15px;line-height:1.65;margin:12px 0 14px;color:var(--text)}
.about-meta{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:18px}
.about-meta span{font-size:12.5px;color:var(--muted);background:var(--surface-2);
  border:1px solid var(--line);border-radius:999px;padding:4px 10px}
.about-md{border-top:1px solid var(--line);padding-top:6px;margin-top:18px}

/* ---------- 轻提示 ---------- */
.toast{position:fixed;left:50%;bottom:26px;transform:translate(-50%,12px);
  background:#0f1419;color:#fff;padding:9px 16px;border-radius:999px;font-size:13.5px;
  opacity:0;pointer-events:none;transition:opacity .2s,transform .2s;z-index:99;
  box-shadow:0 4px 20px rgba(0,0,0,.22);max-width:86vw;text-align:center}
.toast.on{opacity:1;transform:translate(-50%,0)}
[data-theme="dark"] .toast{background:#e7e9ea;color:#0f1419}
[data-theme="dark"] .pc-cover img,[data-theme="dark"] .body img{opacity:.92}

/* ---------- 窄屏 ---------- */
@media(max-width:640px){
  .topbar-inner{height:auto;min-height:54px;flex-wrap:wrap;padding:8px 14px 10px;gap:8px 10px}
  .brand{flex:1}
  .topbar-actions{margin-left:0}
  .search{order:3;flex:1 1 100%;max-width:none;margin:0}
  .page{padding:6px 0 30px;gap:0}
  .timeline-head{padding:10px 16px 12px;border-bottom:1px solid var(--line)}
  .filter-bar{margin:10px 12px}
  .feed{gap:0}
  .post-card{border-radius:0;border-left:0;border-right:0;border-top:0;padding:14px 16px}
  .feed-end{margin:18px 0 0}
  .empty{margin:12px 14px 0}
  .site-foot{margin:26px 16px 0;padding-top:16px}
  .thread-card{border-radius:0;border-left:0;border-right:0;padding:14px 16px 4px}
  .tp-title{font-size:21px}
  .pager{margin:12px 12px 0}
  .back-home{margin:16px 16px 0}
  .about-card{border-radius:0;border-left:0;border-right:0}
  .about-body{padding:0 18px 20px}
}
@media(prefers-reduced-motion:reduce){
  *,*::before,*::after{transition-duration:.01ms !important;animation-duration:.01ms !important;
    scroll-behavior:auto !important}
}
'''.replace('__FONT__', FONT)

JS = r'''(function () {
  'use strict';
  var doc = document.documentElement;
  function $(s) { return document.querySelector(s); }
  function $$(s) { return Array.prototype.slice.call(document.querySelectorAll(s)); }

  /* ---------- 深浅色 ---------- */
  var themeBtn = $('#themeBtn');
  var themeColor = $('#themeColor');
  function currentTheme() { return doc.getAttribute('data-theme') === 'dark' ? 'dark' : 'light'; }
  function applyTheme(t, persist) {
    doc.setAttribute('data-theme', t);
    if (themeColor) themeColor.setAttribute('content', t === 'dark' ? '#000000' : '#ffffff');
    if (themeBtn) {
      var label = t === 'dark' ? '切换到浅色模式' : '切换到深色模式';
      themeBtn.setAttribute('aria-label', label);
      themeBtn.setAttribute('title', label);
      themeBtn.setAttribute('aria-pressed', t === 'dark' ? 'true' : 'false');
    }
    if (persist) { try { localStorage.setItem('theme', t); } catch (e) {} }
  }
  if (themeBtn) {
    applyTheme(currentTheme(), false);
    themeBtn.addEventListener('click', function () {
      applyTheme(currentTheme() === 'dark' ? 'light' : 'dark', true);
    });
    if (window.matchMedia) {
      var mq = window.matchMedia('(prefers-color-scheme: dark)');
      var onChange = function (e) {
        var saved = null;
        try { saved = localStorage.getItem('theme'); } catch (err) {}
        if (!saved) applyTheme(e.matches ? 'dark' : 'light', false);
      };
      if (mq.addEventListener) mq.addEventListener('change', onChange);
      else if (mq.addListener) mq.addListener(onChange);
    }
  }

  /* ---------- 轻提示 ---------- */
  var toastEl = $('#toast');
  var toastTimer = null;
  function toast(msg) {
    if (!toastEl) return;
    toastEl.textContent = msg;
    toastEl.classList.add('on');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { toastEl.classList.remove('on'); }, 2200);
  }

  /* ---------- 互动按钮（纯前端，不接真实数据） ---------- */
  document.addEventListener('click', function (e) {
    var t = e.target;
    if (!t || !t.closest) return;
    var like = t.closest('.act-like');
    if (like) {
      var liked = like.getAttribute('aria-pressed') === 'true';
      like.setAttribute('aria-pressed', liked ? 'false' : 'true');
      like.classList.toggle('liked', !liked);
      return;
    }
    var share = t.closest('.act-share');
    if (share) {
      var href = share.getAttribute('data-href') || '';
      var url = location.href;
      if (href) { try { url = new URL(href, location.href).href; } catch (err) {} }
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(url).then(
          function () { toast('链接已复制'); },
          function () { toast(url); }
        );
      } else {
        toast(url);
      }
      return;
    }
    if (t.closest('.act-reply') || t.closest('.act-repost')) {
      toast('这里只做展示，没有接入互动数据');
    }
  });

  /* ---------- 时间线搜索 / 筛选 ---------- */
  var feed = $('#feed');
  if (!feed) return;
  var cards = $$('.post-card');
  var total = cards.length;
  var input = $('#q');
  var clearSearch = $('#qclear');
  var countEl = $('#count');
  var emptyEl = $('#empty');
  var emptyText = $('#emptyText');
  var filterBar = $('#filterBar');
  var filterText = $('#filterText');
  var clearFilter = $('#clearFilter');
  var month = '';

  function norm(s) { return (s || '').toLowerCase(); }
  function apply() {
    var q = norm(input ? input.value.trim() : '');
    var shown = 0;
    cards.forEach(function (card) {
      var okQ = !q || norm(card.getAttribute('data-search')).indexOf(q) !== -1;
      var okM = !month || (card.getAttribute('data-date') || '').indexOf(month) === 0;
      var show = okQ && okM;
      card.hidden = !show;
      if (show) shown++;
    });
    if (countEl) countEl.textContent = '共 ' + total + ' 条';
    if (emptyEl) emptyEl.hidden = shown > 0;
    if (emptyText && shown === 0) {
      emptyText.textContent = total ? '没有找到匹配的帖子，换个关键词试试。' : '这里还没有帖子。';
    }
    if (filterBar) filterBar.hidden = !(q || month);
    if (filterText && (q || month)) {
      var parts = [];
      if (q) parts.push('关键词「' + input.value.trim() + '」');
      if (month) parts.push('归档 ' + month.replace('-', ' 年 ') + ' 月');
      filterText.textContent = '筛选：' + parts.join(' · ') + ' → ' + shown + ' 条';
    }
    if (clearSearch) clearSearch.hidden = !q;
  }

  if (input) input.addEventListener('input', apply);
  if (clearSearch) clearSearch.addEventListener('click', function () {
    if (input) { input.value = ''; input.focus(); }
    apply();
  });
  if (clearFilter) clearFilter.addEventListener('click', function () {
    month = '';
    if (input) input.value = '';
    apply();
  });

  feed.addEventListener('click', function (e) {
    var tag = e.target && e.target.closest ? e.target.closest('[data-tag]') : null;
    if (!tag) return;
    if (input) input.value = tag.getAttribute('data-tag') || '';
    month = '';
    apply();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });

  $$('[data-side-tag]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      if (input) input.value = btn.getAttribute('data-side-tag') || '';
      month = '';
      apply();
    });
  });
  $$('[data-side-month]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      month = btn.getAttribute('data-side-month') || '';
      apply();
    });
  });

  var params = new URLSearchParams(location.search);
  var tagParam = params.get('tag');
  var monthParam = params.get('month');
  if (tagParam && input) input.value = tagParam;
  if (monthParam) month = monthParam;
  apply();
})();
'''


# --------------------------------------------------------------------------- #
# 工具函数
# --------------------------------------------------------------------------- #
def esc(s):
    return html.escape(str(s if s is not None else ''))


def attr(s):
    return html.escape(str(s if s is not None else ''), quote=True)


def write(path, content):
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)


def read_json(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def site_conf(site):
    site = site or {}

    def s(key, fallback=''):
        return str(site.get(key) or fallback).strip()

    name = s('name', '夜航手记') or '夜航手记'
    author = s('author') or s('nickname') or name
    handle = s('handle') or '@notes'
    if not handle.startswith('@'):
        handle = '@' + handle
    bio = s('bio') or s('tagline')
    links = []
    for item in site.get('links') or []:
        if isinstance(item, dict) and item.get('url'):
            links.append({'label': str(item.get('label') or item['url']),
                          'url': str(item['url'])})
    return {
        'name': name,
        'author': author,
        'handle': handle,
        'bio': bio,
        'tagline': s('tagline'),
        'avatar_text': (s('avatar_text') or author or '夜')[:1],
        'hero_title': s('hero_title') or '时间线',
        'title': s('title') or name,
        'description': s('description') or bio or s('tagline') or '一个只放文字的角落。',
        'footer': s('footer') or '自己写的字，自己搭的站。',
        'links': links,
    }


def avatar_style(seed):
    digest = hashlib.sha1(('avatar|' + str(seed or 'x')).encode('utf-8')).digest()
    index = int.from_bytes(digest[0:2], 'big') % len(AVATARS)
    a, b = AVATARS[index]
    rotation = int.from_bytes(digest[2:4], 'big') % 360
    return '--av-a:%s;--av-b:%s;--av-r:%ddeg' % (a, b, rotation)


def fmt_short(date):
    m = re.match(r'^(\d{4})-(\d{1,2})-(\d{1,2})', (date or '').strip())
    if not m:
        return (date or '').strip() or '未标日期'
    return '%d月%d日' % (int(m.group(2)), int(m.group(3)))


def fmt_long(date):
    m = re.match(r'^(\d{4})-(\d{1,2})-(\d{1,2})', (date or '').strip())
    if not m:
        return (date or '').strip() or '未标日期'
    return '%d年%d月%d日' % (int(m.group(1)), int(m.group(2)), int(m.group(3)))


def fmt_month(key):
    m = re.match(r'^(\d{4})-(\d{1,2})$', key or '')
    if not m:
        return key or ''
    return '%d年%d月' % (int(m.group(1)), int(m.group(2)))


def plain_text(text, limit=None):
    s = text or ''
    s = re.sub(r'```.*?```', ' ', s, flags=re.S)
    s = re.sub(r'!\[[^\]]*\]\([^)]*\)', ' ', s)
    s = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', s)
    s = re.sub(r'(?m)^\s{0,3}#{1,6}\s*', '', s)
    s = re.sub(r'(?m)^\s*[-*+]\s+', '', s)
    s = re.sub(r'(?m)^\s*\d+\.\s+', '', s)
    s = re.sub(r'(?m)^\s*>\s?', '', s)
    s = re.sub(r'[`*_~]', '', s)
    s = re.sub(r'\s+', ' ', s).strip()
    if limit and len(s) > limit:
        s = s[:limit].rstrip() + '…'
    return s


def _fallback_inline(s):
    s = html.escape(s)
    s = re.sub(r'!\[([^\]]*)\]\(([^)\s]+)\)', r'<img src="\2" alt="\1">', s)
    s = re.sub(r'\[([^\]]+)\]\(([^)\s]+)\)', r'<a href="\2">\1</a>', s)
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
    s = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'(?<!\*)\*([^*\n]+)\*(?!\*)', r'<em>\1</em>', s)
    return s


def _fallback_md(text):
    lines = (text or '').replace('\r\n', '\n').replace('\r', '\n').split('\n')
    out = []
    stack = []

    def close_list():
        while stack:
            out.append('</%s>' % stack.pop())

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if stripped.startswith('```'):
            close_list()
            code = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                code.append(lines[i])
                i += 1
            out.append('<pre><code>%s</code></pre>' % html.escape('\n'.join(code)))
            i += 1
            continue
        if not stripped:
            close_list()
            i += 1
            continue
        m = re.match(r'^(#{1,4})\s+(.*)$', stripped)
        if m:
            close_list()
            level = len(m.group(1))
            out.append('<h%d>%s</h%d>' % (level, _fallback_inline(m.group(2)), level))
            i += 1
            continue
        if re.match(r'^>\s?', stripped):
            close_list()
            quotes = []
            while i < len(lines) and re.match(r'^>\s?', lines[i].strip()):
                quotes.append(re.sub(r'^>\s?', '', lines[i].strip()))
                i += 1
            out.append('<blockquote>%s</blockquote>'
                       % '<br>'.join(_fallback_inline(q) for q in quotes))
            continue
        m = re.match(r'^[-*+]\s+(.*)$', stripped)
        if m:
            if not stack or stack[-1] != 'ul':
                close_list()
                out.append('<ul>')
                stack.append('ul')
            out.append('<li>%s</li>' % _fallback_inline(m.group(1)))
            i += 1
            continue
        m = re.match(r'^\d+\.\s+(.*)$', stripped)
        if m:
            if not stack or stack[-1] != 'ol':
                close_list()
                out.append('<ol>')
                stack.append('ol')
            out.append('<li>%s</li>' % _fallback_inline(m.group(1)))
            i += 1
            continue
        close_list()
        para = [stripped]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(
                r'^(#{1,4}\s|>\s?|[-*+]\s|\d+\.\s|```)', lines[i].strip()):
            para.append(lines[i].strip())
            i += 1
        out.append('<p>%s</p>' % '<br>'.join(_fallback_inline(p) for p in para))
    close_list()
    return '\n'.join(out)


def render_md(text, prefix=''):
    source = text or ''
    if _MD is not None:
        try:
            out = _MD(source)
        except Exception:
            out = _fallback_md(source)
    else:
        out = _fallback_md(source)
    if prefix:
        out = re.sub(r'(src|href)="(?!https?:|/|#|mailto:|data:)', r'\1="' + prefix, out)
    return out


def load_posts():
    posts = []
    if not os.path.isdir(POSTS_DIR):
        return posts
    for fn in sorted(os.listdir(POSTS_DIR)):
        if not fn.endswith('.json'):
            continue
        post = read_json(os.path.join(POSTS_DIR, fn))
        if not isinstance(post, dict):
            continue
        if (post.get('status') or 'published') != 'published':
            continue
        if not post.get('slug'):
            post['slug'] = re.sub(r'[^a-z0-9\u4e00-\u9fff-]+', '-',
                                  str(post.get('id') or 'post')).strip('-') or 'post'
        posts.append(post)
    posts.sort(key=lambda p: ((p.get('date') or ''), (p.get('id') or '')), reverse=True)
    return posts


# --------------------------------------------------------------------------- #
# HTML 组件
# --------------------------------------------------------------------------- #
def page_shell(site, title, body, root='', desc=''):
    c = site_conf(site)
    return f'''<!doctype html>
<html lang="zh-CN" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{attr(desc or c['description'])}">
<meta name="color-scheme" content="light dark">
<meta name="theme-color" content="#ffffff" id="themeColor">
<meta property="og:title" content="{attr(title)}">
<meta property="og:description" content="{attr(desc or c['description'])}">
<meta property="og:type" content="website">
<link rel="icon" href="{FAVICON}">
<link rel="stylesheet" href="{root}assets/style.css">
{THEME_INIT}
</head>
<body>
{body}
<div class="toast" id="toast" role="status" aria-live="polite"></div>
<script src="{root}assets/app.js" defer></script>
</body>
</html>
'''


def topbar(site, root='', mode='home'):
    c = site_conf(site)
    back = ''
    if mode != 'home':
        back = ('<a class="icon-btn back-btn" href="%sindex.html" aria-label="返回时间线" '
                'title="返回时间线">%s</a>' % (root, ICON_BACK))
    if mode == 'home':
        middle = f'''<div class="search" role="search">
  {ICON_SEARCH}
  <input id="q" type="search" placeholder="搜索帖子或标签" autocomplete="off" enterkeyhint="search" aria-label="搜索帖子">
  <button class="qclear" id="qclear" type="button" aria-label="清空搜索" title="清空搜索" hidden>{ICON_CLEAR}</button>
</div>'''
    else:
        middle = '<div class="topbar-spacer"></div>'
    return f'''<header class="topbar">
  <div class="topbar-inner">
    {back}
    <a class="brand" href="{root}index.html" aria-label="{attr(c['name'])} 时间线">
      {LOGO}
      <span class="brand-name">{esc(c['name'])}</span>
    </a>
    {middle}
    <div class="topbar-actions">
      <a class="ghost-link" href="{root}about.html">关于</a>
      <button class="icon-btn theme-btn" id="themeBtn" type="button" aria-label="切换深浅色" title="切换深浅色" aria-pressed="false">
        {ICON_SUN}
        {ICON_MOON}
      </button>
    </div>
  </div>
</header>'''


def action_buttons(href=''):
    return f'''<button class="act act-reply" type="button" aria-label="回复（仅展示）" title="回复（仅展示）">{ICON_REPLY}</button>
      <button class="act act-repost" type="button" aria-label="转发（仅展示）" title="转发（仅展示）">{ICON_REPOST}</button>
      <button class="act act-like" type="button" aria-label="喜欢（仅展示）" title="喜欢（仅展示）" aria-pressed="false">{ICON_HEART}</button>
      <button class="act act-share" type="button" aria-label="复制链接" title="复制链接" data-href="{attr(href)}">{ICON_SHARE}</button>'''


def tag_buttons(tags):
    return ''.join('<button class="tag" type="button" data-tag="%s">#%s</button>'
                   % (attr(t), esc(t)) for t in tags)


def tag_links(tags, root):
    return ''.join('<a class="tag" href="%sindex.html?tag=%s">#%s</a>'
                   % (root, attr(quote(str(t))), esc(t)) for t in tags)


def post_tags(p):
    return [str(t) for t in (p.get('tags') or []) if str(t).strip()]


def post_card(site, post, root=''):
    c = site_conf(site)
    slug = str(post.get('slug') or post.get('id') or 'post')
    href = root + 'post/' + slug + '.html'
    date = str(post.get('date') or '').strip()
    tags = post_tags(post)
    title = str(post.get('title') or '').strip() or '无标题'
    excerpt = str(post.get('summary') or '').strip() or plain_text(post.get('body') or '', 170)
    cover_path = str(post.get('cover') or '').strip()
    cover = ''
    if cover_path:
        cover = ('<div class="pc-cover"><img src="%s" alt="" loading="lazy"></div>'
                 % attr(root + cover_path))
    tags_block = ('<div class="pc-tags">%s</div>' % tag_buttons(tags)) if tags else ''
    search_blob = ' '.join([title, excerpt, date, ' '.join(tags),
                            plain_text(post.get('body') or '', 1600)]).lower()
    avatar = avatar_style(post.get('id') or slug)
    initial = (c['avatar_text'] or '夜')[:1]
    return f'''<article class="post-card" data-search="{attr(search_blob)}" data-date="{attr(date)}">
  <div class="avatar" style="{avatar}" aria-hidden="true"><span>{esc(initial)}</span></div>
  <div class="pc-main">
    <div class="pc-head">
      <a class="pc-name" href="{href}">{esc(c['author'])}</a>
      <span class="pc-handle">{esc(c['handle'])}</span>
      <span class="pc-sep" aria-hidden="true">·</span>
      <time class="pc-time" datetime="{attr(date)}" title="{attr(fmt_long(date))}">{esc(fmt_short(date))}</time>
    </div>
    <a class="pc-link" href="{href}">
      <h2 class="pc-title">{esc(title)}</h2>
      <p class="pc-text">{esc(excerpt)}</p>
      {cover}
    </a>
    {tags_block}
    <div class="pc-actions" role="group" aria-label="互动（仅展示）">
      {action_buttons(href)}
    </div>
  </div>
</article>'''


def sidebar(site, posts, root='', interactive=True):
    c = site_conf(site)
    tag_counts = Counter()
    month_counts = Counter()
    for post in posts:
        for tag in post_tags(post):
            tag_counts[tag] += 1
        month = str(post.get('date') or '')[:7]
        if re.match(r'^\d{4}-\d{2}$', month):
            month_counts[month] += 1

    tag_parts = []
    for tag, n in sorted(tag_counts.items(), key=lambda kv: (-kv[1], kv[0])):
        if interactive:
            tag_parts.append('<button class="tag-chip" type="button" data-side-tag="%s">#%s<span class="n">%d</span></button>'
                             % (attr(tag), esc(tag), n))
        else:
            tag_parts.append('<a class="tag-chip" href="%sindex.html?tag=%s">#%s<span class="n">%d</span></a>'
                             % (root, attr(quote(tag)), esc(tag), n))
    tag_cloud = ''.join(tag_parts) or '<span class="side-note">还没有标签。</span>'

    archive_parts = []
    for month, n in sorted(month_counts.items(), reverse=True):
        if interactive:
            archive_parts.append('<li><button type="button" data-side-month="%s"><span>%s</span><span class="n">%d</span></button></li>'
                                 % (attr(month), esc(fmt_month(month)), n))
        else:
            archive_parts.append('<li><a href="%sindex.html?month=%s"><span>%s</span><span class="n">%d</span></a></li>'
                                 % (root, attr(month), esc(fmt_month(month)), n))
    archive = ('<ul class="archive">%s</ul>' % ''.join(archive_parts)) if archive_parts \
        else '<span class="side-note">还没有帖子。</span>'

    return f'''<aside class="sidebar" aria-label="站点侧栏">
  <section class="side-card profile-card">
    <div class="profile-banner" aria-hidden="true"></div>
    <div class="profile-body">
      <div class="avatar avatar-xl" style="{avatar_style('site-' + c['name'])}" aria-hidden="true"><span>{esc(c['avatar_text'])}</span></div>
      <h2 class="p-name">{esc(c['name'])}</h2>
      <div class="p-handle">{esc(c['handle'])}</div>
      <p class="p-bio">{esc(c['bio'])}</p>
      <div class="p-stats"><span><b>{len(posts)}</b> 帖子</span><span><b>{len(tag_counts)}</b> 标签</span></div>
      <a class="side-link" href="{root}about.html">关于这个站 →</a>
    </div>
  </section>
  <section class="side-card">
    <h2>标签</h2>
    <div class="tagcloud">{tag_cloud}</div>
  </section>
  <section class="side-card">
    <h2>归档</h2>
    {archive}
  </section>
  <p class="side-foot">没有追踪、没有广告、没有后台统计。</p>
</aside>'''


def site_footer(site, root=''):
    c = site_conf(site)
    extra = ''.join('<a href="%s" target="_blank" rel="noopener noreferrer">%s</a>'
                    % (attr(link['url']), esc(link['label'])) for link in c['links'])
    return f'''<footer class="site-foot">
  <nav><a href="{root}index.html">时间线</a><a href="{root}about.html">关于</a>{extra}</nav>
  <p>{esc(c['footer'])}</p>
  <p class="foot-fine">没有追踪、没有广告、没有后台统计。</p>
</footer>'''


# --------------------------------------------------------------------------- #
# 页面构建
# --------------------------------------------------------------------------- #
def build_index(site, posts):
    c = site_conf(site)
    cards = '\n'.join(post_card(site, post) for post in posts)
    feed_end = '<p class="feed-end">— 到底了 —</p>' if posts else ''
    body = topbar(site, '', mode='home') + f'''
<div class="page">
  <main class="timeline" id="main">
    <div class="timeline-head">
      <h1>{esc(c['hero_title'])}</h1>
      <span class="count" id="count">共 {len(posts)} 条</span>
    </div>
    <div class="filter-bar" id="filterBar" hidden>
      <span id="filterText">筛选</span>
      <button class="filter-clear" id="clearFilter" type="button">清除筛选</button>
    </div>
    <div class="feed" id="feed">
{cards}
    </div>
    <div class="empty" id="empty" hidden>
      <span class="empty-ico" aria-hidden="true">✦</span>
      <span id="emptyText">没有找到匹配的帖子。</span>
    </div>
    {feed_end}
    {site_footer(site, '')}
  </main>
  {sidebar(site, posts, '', interactive=True)}
</div>'''
    out = page_shell(site, c['title'], body, '', c['description'])
    write(os.path.join(ROOT, 'index.html'), out)
    print('index.html', len(out), 'posts=%d' % len(posts))


def pager_link(post, root, label):
    href = root + 'post/' + str(post.get('slug') or post.get('id') or 'post') + '.html'
    return ('<a class="pager-link" href="%s"><span>%s</span><b>%s</b></a>'
            % (attr(href), esc(label), esc(post.get('title') or '无标题')))


def build_posts(site, posts):
    c = site_conf(site)
    root = '../'
    keep = set()
    for index, post in enumerate(posts):
        slug = str(post.get('slug') or post.get('id') or ('post-%d' % index))
        keep.add(slug + '.html')
        title = str(post.get('title') or '').strip() or '无标题'
        body_html = render_md(post.get('body') or '', prefix=root)
        tags = post_tags(post)
        tags_block = ('<div class="tp-tags">%s</div>' % tag_links(tags, root)) if tags else ''
        pager = ''
        older = posts[index + 1] if index + 1 < len(posts) else None
        newer = posts[index - 1] if index > 0 else None
        if older or newer:
            pager = '<nav class="pager" aria-label="上一条 / 下一条">'
            if older:
                pager += pager_link(older, root, '← 上一条')
            if newer:
                pager += pager_link(newer, root, '下一条 →')
            pager += '</nav>'
        excerpt = str(post.get('summary') or '').strip() or plain_text(post.get('body') or '', 160)
        body = topbar(site, root, mode='post') + f'''
<div class="page">
  <main class="thread" id="main">
    <article class="thread-card">
      <div class="tp-head">
        <div class="avatar" style="{avatar_style(post.get('id') or slug)}" aria-hidden="true"><span>{esc(c['avatar_text'])}</span></div>
        <div class="tp-id">
          <span class="tp-name">{esc(c['author'])}</span>
          <span class="tp-handle">{esc(c['handle'])}</span>
        </div>
      </div>
      <h1 class="tp-title">{esc(title)}</h1>
      <div class="tp-meta"><time datetime="{attr(post.get('date') or '')}">{esc(fmt_long(post.get('date')))}</time></div>
      {tags_block}
      <div class="body">{body_html}</div>
      <div class="tp-actions" role="group" aria-label="互动（仅展示）">
        {action_buttons('')}
      </div>
    </article>
    {pager}
    <a class="back-home" href="{root}index.html">← 返回时间线</a>
    {site_footer(site, root)}
  </main>
  {sidebar(site, posts, root, interactive=False)}
</div>'''
        out = page_shell(site, '%s · %s' % (title, c['name']), body, root, excerpt)
        write(os.path.join(ROOT, 'post', slug + '.html'), out)

    post_dir = os.path.join(ROOT, 'post')
    if os.path.isdir(post_dir):
        for fn in sorted(os.listdir(post_dir)):
            if fn.endswith('.html') and fn not in keep:
                os.remove(os.path.join(post_dir, fn))
                print('stale removed: post/%s' % fn)
    print('posts built', len(posts))


def build_about(site, posts):
    c = site_conf(site)
    about_md = str(site.get('about_md') or '').strip() or DEFAULT_ABOUT
    years = sorted({str(post.get('date') or '')[:4] for post in posts
                    if re.match(r'^\d{4}', str(post.get('date') or ''))})
    meta = ['%d 篇帖子' % len(posts)]
    if years:
        meta.append('自 %s 年开始写' % years[0])
    meta.append('纯静态 · 无追踪')
    meta_html = ''.join('<span>%s</span>' % esc(item) for item in meta)
    body = topbar(site, '', mode='about') + f'''
<div class="page">
  <main class="about" id="main">
    <article class="about-card">
      <div class="about-banner" aria-hidden="true"></div>
      <div class="about-body">
        <div class="avatar avatar-xl" style="{avatar_style('site-' + c['name'])}" aria-hidden="true"><span>{esc(c['avatar_text'])}</span></div>
        <h1 class="about-name">{esc(c['name'])}</h1>
        <div class="about-handle">{esc(c['handle'])}</div>
        <p class="about-bio">{esc(c['bio'])}</p>
        <div class="about-meta">{meta_html}</div>
        <div class="body about-md">{render_md(about_md)}</div>
        <a class="back-home" href="index.html">← 返回时间线</a>
      </div>
    </article>
    {site_footer(site, '')}
  </main>
  {sidebar(site, posts, '', interactive=False)}
</div>'''
    out = page_shell(site, '关于 · %s' % c['name'], body, '', c['description'])
    write(os.path.join(ROOT, 'about.html'), out)
    print('about.html', len(out))


def build_feed(site, posts):
    c = site_conf(site)
    feed = []
    for post in posts:
        slug = str(post.get('slug') or post.get('id') or 'post')
        feed.append({
            'id': post.get('id') or slug,
            'slug': slug,
            'title': post.get('title') or '',
            'date': post.get('date') or '',
            'tags': post_tags(post),
            'summary': post.get('summary') or '',
            'cover': post.get('cover') or '',
            'url': 'post/%s.html' % slug,
        })
    payload = {'site': {'name': c['name'], 'tagline': c['tagline'] or c['bio']},
               'posts': feed}
    write(os.path.join(ROOT, 'posts.json'),
          json.dumps(payload, ensure_ascii=False, indent=1) + '\n')
    print('posts.json', len(feed))


def main():
    site = read_json(os.path.join(DATA, 'site.json'), {}) or {}
    posts = load_posts()
    write(os.path.join(ROOT, 'assets', 'style.css'), CSS)
    write(os.path.join(ROOT, 'assets', 'app.js'), JS)
    build_index(site, posts)
    build_posts(site, posts)
    build_about(site, posts)
    build_feed(site, posts)
    print('done')


if __name__ == '__main__':
    main()
