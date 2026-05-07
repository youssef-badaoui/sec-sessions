# Lab 6: Bank Transfer Race Condition (TOCTOU)

## Setup
- Create two accounts. Each one starts with `$100`.
- Log in as one user, copy the other user's 20-digit account ID.

## The bug
Inside `/transfer` the server does:

1. `SELECT balance` for the sender
2. Look up recipient
3. **Check**: `sender.balance < amount`?
4. Insert an audit log entry
5. **Use**: `UPDATE balance = balance - amount`

Steps 3 and 5 are separated by another query, and the check uses the value read
in step 1 — not the current row. Two requests can both pass step 3 before either
reaches step 5, and both updates go through.

## Exploit
Send several transfer requests in parallel. Using curl with backgrounded jobs,
replace `<COOKIE>` with your `session` cookie and `<RECIPIENT_ACCOUNT>` with the
other user's account ID:

```bash
for i in $(seq 1 5); do
  curl -s -X POST http://localhost:5006/transfer \
    -H "Cookie: session=<COOKIE>" \
    -d "target_account_id=<RECIPIENT_ACCOUNT>&amount=100" > /dev/null &
done
wait
```

Reload the dashboard. The sender's balance will be negative, the recipient's
balance will be well over `$200`, and multiple transfers of `$100` are in the
history — even though the sender only ever had `$100` to spend.

Burp Repeater's "Send group in parallel" (single-packet attack) works too.
Stay under ~10 concurrent requests — the Flask dev server is single-process
and heavy bursts can make SQLite return `database is locked` on some
requests. One or two extra successful transfers is already proof of the bug.

## Fix
Combine the check and the update into a single atomic statement:

```sql
UPDATE users SET balance = balance - ?
  WHERE username = ? AND balance >= ?;
```

Then verify `rowcount == 1` before crediting the recipient — or wrap the whole
flow in an explicit transaction with `SELECT ... FOR UPDATE` on a DB that
supports it.
