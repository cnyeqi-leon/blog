# 夜航手记 · blog

X（Twitter）风格单列时间线的静态博客，部署在 GitHub Pages。

- `_data/site.json` 站点信息：站点名 / 化名 / handle / 简介 / 关于页
- `_data/posts/*.json` 文章：`{id, title, slug, date, status, tags, summary, cover, body}`，正文 Markdown
- `build.py` 生成 `index.html` / `post/` / `about.html` / `posts.json` / `assets`
- 本地后台 `../admin_server.py`：写文章、传图、一键重建并发布

## 构建

```
python build.py
```

## 本地预览

```
python -m http.server 8895 --bind 127.0.0.1 --directory .
```

打开 http://127.0.0.1:8895/ 。

## 说明

- 首页：600px 单列时间线，顶部吸顶栏（搜索 + 深浅色），≥1200px 显示右侧栏（简介 / 标签云 / 归档）。
- 搜索与标签、归档筛选全部在前端完成；互动按钮只做视觉展示，不接真实数据。
- 站点内容不含真实姓名、学校、地区、联系方式等个人信息；作者名只使用化名。
- 旧文章页面在重建时自动清理，不会残留到线上。
