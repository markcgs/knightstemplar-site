# knightstemplar.dev

A working demonstration of a redesigned website for the Grand Encampment of Knights Templar of the U.S.A. (today's site: usagekt.org), built by Creative Technology Partners from the Grand Encampment's own public content.

```
python3 build/fetch.py   # read usagekt.org into build/data/
python3 build/build.py   # write public/
```

Cloudflare Workers Builds (Templar Ed account, Worker `knightstemplar-site`) serves `public/` as static assets whenever `main` changes. A GitHub Action refreshes the content from usagekt.org every morning.
