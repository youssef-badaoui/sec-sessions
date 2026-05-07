# Security Training Labs

Hands-on code-level security training for client dev teams.
Built and maintained by **Youssef Badaoui**, cybersecurity consultant at **Techso Group**.

4 days, 10 labs. Each lab is a standalone Dockerized Flask app with one intentional vulnerability, a guide, and a walkthrough.

## Labs

| Day | Lab | Vulnerability | Port(s) | Directory |
|-----|-----|--------------|---------|-----------|
| 1 | Lab 1 | Broken Access Control (Wallet Tampering) | 5009 | `day1/lab1-broken-access-control/` |
| 1 | Lab 2 | IDOR Password Update | 5010 | `day1/lab2-idor-password/` |
| 2 | Lab 1 | Stored XSS | 5001 | `day2/lab1-xss/` |
| 2 | Lab 2 | SQL Injection (Auth Bypass) | 5002 | `day2/lab2-sqli/` |
| 3 | Lab 3 | Password Reset Flaw | 5003, 5013 | `day3/lab3-password-reset/` |
| 3 | Lab 4 | 2FA Bypass | 5004, 5014 | `day3/lab4-2fa-bypass/` |
| 3 | Lab 4B | Reset Link Host Header Poisoning | 5007, 5017 | `day3/lab4b-host-header-reset/` |
| 4 | Lab 5 | Store Price Manipulation | 5005 | `day4/lab5-store-price-manipulation/` |
| 4 | Lab 6 | Bank Transfer Race Condition | 5006 | `day4/lab6-bank-race-condition/` |
| 4 | Lab 7 | Weather SSRF | 5008, 7777 | `day4/lab7-weather-ssrf/` |

## Run a lab

```bash
cd <lab-directory>
docker compose up --build
```

## Credentials

| Lab | User | Password |
|-----|------|----------|
| Day 1 Lab 1 | `admin` / `user` | `admin123` / `user123` |
| Day 1 Lab 2 | `admin` / `user` | `admin123` / `user123` |
| Day 2 Lab 1 | `admin` / `user` | `adminpass` / `password` |
| Day 2 Lab 2 | `admin` / `employee` | `supersecretpassword` / `password123` |
| Day 3 Lab 3 | `admin` / `user` | `unknownpassword` / `password` |
| Day 3 Lab 4 | `admin` / `user` | `adminpass` / `password` |
| Day 3 Lab 4B | `admin` / `user` | `unknownpassword` / `password` |
| Day 4 Lab 5 | sign up | chosen at signup |
| Day 4 Lab 6 | `alice` / `bob` | `password` / `password` |

Day 3 labs use a separate mailbox UI on the second port; mailbox accounts mirror app credentials.

## Stack

Python Flask · SQLite · Docker Compose
