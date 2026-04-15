# Security Training Labs

Hands-on security training platform — 3 days, 7 vulnerability labs. Each lab is a standalone Docker containerized web app with an intentional vulnerability.

## Labs

| Day | Lab | Vulnerability | Port(s) | Directory |
|-----|-----|--------------|---------|-----------|
| 1 | Lab 1 | Stored XSS | 5001 | `day1/lab1-xss/` |
| 1 | Lab 2 | SQL Injection (Auth Bypass) | 5002 | `day1/lab2-sqli/` |
| 2 | Lab 3 | Password Reset Flaw | 5003, 5013 (mailbox) | `day2/lab3-password-reset/` |
| 2 | Lab 4 | 2FA Bypass | 5004, 5014 (mailbox) | `day2/lab4-2fa-bypass/` |
| 2 | Lab 4B | Reset Link Host Header Poisoning | 5007, 5017 (mailbox) | `day2/lab4b-host-header-reset/` |
| 3 | Lab 5 | Price Manipulation | 5005 | `day3/lab5-price-manipulation/` |
| 3 | Lab 6 | SSRF | 5006 | `day3/lab6-ssrf/` |

## Quick Start

Each lab runs independently with a single command:

```bash
# Day 1
cd day1/lab1-xss && docker compose up --build
cd day1/lab2-sqli && docker compose up --build

# Day 2
cd day2/lab3-password-reset && docker compose up --build
cd day2/lab4-2fa-bypass && docker compose up --build
cd day2/lab4b-host-header-reset && docker compose up --build

# Day 3
cd day3/lab5-price-manipulation && docker compose up --build
cd day3/lab6-ssrf && docker compose up --build
```

## Tech Stack

- **Backend:** Python Flask
- **Frontend:** Plain HTML/CSS
- **Database:** SQLite
- **Containerization:** Docker + Docker Compose

## Training Materials

Training material now follows two patterns:
- Day 1 and Day 2 labs include a short `guide.md` that points to a standalone `walkthrough.html`
- The standalone walkthroughs cover the code path, exploitation flow, and fix
- Day 1 Lab 1 also includes a French walkthrough: `walkthrough-fr.html`

Available standalone walkthroughs:
- `day1/lab1-xss/walkthrough.html`
- `day1/lab1-xss/walkthrough-fr.html`
- `day1/lab2-sqli/walkthrough.html`
- `day2/lab3-password-reset/walkthrough.html`
- `day2/lab4-2fa-bypass/walkthrough.html`
- `day2/lab4b-host-header-reset/walkthrough.html`

## Test Credentials

| Lab | User | Password | Role |
|-----|------|----------|------|
| Lab 1 | `user` | `password` | user |
| Lab 1 | `admin` | `adminpass` | admin |
| Lab 2 | `admin` | `supersecretpassword` | admin |
| Lab 2 | `employee` | `password123` | employee |
| Lab 3 | `user` | `password` | user |
| Lab 3 | `admin` | `unknownpassword` | admin |
| Lab 4 | `user` | `password` | user |
| Lab 4 | `admin` | `adminpass` | admin |
| Lab 4B | `user` | `password` | user |
| Lab 4B | `admin` | `unknownpassword` | admin |

## Mailbox Accounts

Day 2 mailbox-enabled labs now use separate mailbox accounts per user:

| Lab | Mailbox User | Password |
|-----|--------------|----------|
| Lab 3 | `user` | `password` |
| Lab 3 | `admin` | `unknownpassword` |
| Lab 4 | `user` | `password` |
| Lab 4 | `admin` | `adminpass` |
| Lab 4B | `user` | `password` |
| Lab 4B | `admin` | `unknownpassword` |
