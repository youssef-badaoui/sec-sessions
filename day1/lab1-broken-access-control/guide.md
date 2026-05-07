# Lab 1 — Broken Access Control (Wallet Tampering)

Open [walkthrough.html](/Users/youssefbadaoui/cdg-sessions/day1/lab1-broken-access-control/walkthrough.html:1) directly in your browser for the standalone walkthrough.

This lab highlights:
- an "admin" endpoint (`/admin/update_wallet`) that ships with no server-side authorization check
- the gap between UI hiding and real access control
- the proper fix: enforce role on the server, not on the form
