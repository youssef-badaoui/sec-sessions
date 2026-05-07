# Lab 2 — IDOR on Password Update

Open [walkthrough.html](/Users/youssefbadaoui/cdg-sessions/day1/lab2-idor-password/walkthrough.html:1) directly in your browser for the standalone walkthrough.

This lab highlights:
- a password update endpoint that authenticates one user but mutates another (IDOR via a `id` body field)
- account takeover from a low-privilege session
- the proper fix: never trust the user identifier from the request body — derive it from the session
