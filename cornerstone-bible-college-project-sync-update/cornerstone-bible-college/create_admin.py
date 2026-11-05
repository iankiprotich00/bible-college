#!/usr/bin/env python3
"""Create a college administrator account (for the bursar or registrar).

Usage:   python3 create_admin.py
Admins sign in on the staff page (the 'Tutor login' link) and get the admin portal.
"""
import getpass, sys
import portal_db as p

conn = p.connect()
p.migrate(conn)
name = input("Full name: ").strip()
email = input("Email: ").strip()
pw = getpass.getpass("Password (at least 8 characters): ")
if pw != getpass.getpass("Type it again: "):
    sys.exit("The passwords don't match. Nothing was created.")
ok, msg = p.create_admin(conn, name, email, pw)
print(msg)
sys.exit(0 if ok else 1)
