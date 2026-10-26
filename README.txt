CUSTOMERVAULT - setup and change notes

SETUP
1. In backend/.env add (the server will not start without it):
   SECRET_KEY=<64 random characters>
   Make one with:  python -c "import secrets; print(secrets.token_hex(32))"
   Use a NEW key; the old one was shared in a chat. Everyone signs in again afterwards.
2. Optional, only behind your own reverse proxy:  TRUST_PROXY=true
3. Replace your backend and frontend folders with these, then restart.
   The database upgrades itself on start (new columns only, no data is touched).

PHASE 1 - roles, security, new columns
 admin = everything | standard = everything except admin screens |
 limited = view, add, edit, upload; no delete, no bin, no direct customer add.
 Login throttle: 8 wrong passwords per ID or 30 per IP in 5 minutes -> wait.
 New device columns: Dispatched Date, Model, SIM Provider, Activation Plan, Firmware, Flash, SIM Type.

PHASE 2 - customer management (Customers tab)
 Rename, rename several, merge: admin + standard.
 Delete customer and delete forever: admin only. Deleting sends the customer and its devices
 to Deleted Customers; admin + standard can restore them.
 Search the cards, hide/show cards.
 Adding devices under the name of a deleted customer brings that customer back.
