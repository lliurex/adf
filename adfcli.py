#!/usr/bin/env python3

import sys
import argparse
from pathlib import Path

class User:

    EQVALENT_USER_TYPES = {
        "s": "student",
        "t": "teacher",
        "a": "admin",
        "n": "noDocente"
    }

    def __init__(self, login, username, surname, user_type, password=None):
        self.login = login
        self.username = username
        self.surname = surname
        self.user_type = user_type
        self.password = None
        self.uid = None

    def require_username(self):
        self.username = input(f"Enter username for {self.login}: ").strip()

    def require_surname(self):
        self.surname = input(f"Enter surname for {self.login}: ").strip()

    def require_user_type(self):
        user_t = input("Enter user type [s]tudent|[t]eacher|[a]dmin|[n]oDocente: ").strip().lower()[0].lower()
        if user_t in User.EQVALENT_USER_TYPES:
            self.user_type = user_t
        else:
            self.user_type = "s"

    def require_password(self):
        import getpass
        password = getpass.getpass(prompt=f"Enter password for {self.login}: ")
        password2 = getpass.getpass(prompt=f"Retype password for {self.login}: ")
        return password, password2

    def require_unique_password(self):
        retry = True
        password = None
        password2 = 1
        while retry and password != password2:
            password, password2 = self.require_password()
            if password == password2:
                break
            response = input("Passwords do not match. Do you want retry [Y]/n: ").lower()
            retry = response == "yes" or response == "y" or response == ""
        if password != password2:
            password = None
        self.password = password

    def print(self):
        print(f"Username: {self.username}")
        print(f"Surname: {self.surname}")
        print(f"User Type: {User.EQVALENT_USER_TYPES[self.user_type]}")
        if self.password:
            print(f"Password is {self.password}")
        else:
            print("Password is not set.")

    def get_hash_password(self):
        import crypt
        import random
        import string
        salt = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        return crypt.crypt(self.password, salt)

    def serialize(self):
        # Serialize the user object to a string for storage in the passwd file
        # Format: login:uid:username:surname:user_type
        return f"{self.login}:{self.uid}:{self.username}:{self.surname}:{self.user_type}"

class ADFCLI:
    def __init__(self):
        self.passwd = Path("/var/lib/adf/passwd")
        self.shadow = Path("/var/lib/adf/shadow")
        if not self.passwd.exists():
            self.passwd.parent.mkdir(parents=True, exist_ok=True)
            self.passwd.touch()
        if not self.shadow.exists():
            self.shadow.parent.mkdir(parents=True, exist_ok=True)
            self.shadow.touch()

    def check_user_exists(self, user):
        if self.passwd.exists():
            with self.passwd.open("r") as passwd_file:
                for line in passwd_file:
                    if line.startswith(f"{user}:"):
                        return True
        return False

    def add_user(self, user):
        # Check if user already exists
        if self.check_user_exists(user):
            print(f"User {user} already exists.")
            sys.exit(1)

        # require password input hidden
        user = User(user, "", "", "", "")
        user.require_username()
        user.require_surname()
        user.require_user_type()
        user.require_unique_password()
        correct = False
        while not correct:
            print("")
            user.print()
            print("")
            response = input("Is this information correct? [Y]es/[n]o/[c]ancel: ").lower()

            if response == "yes" or response == "y" or response == "":
                correct = True
                break
            elif response == "cancel" or response == "c":
                print("User creation cancelled.")
                sys.exit(0)
            elif response == "no" or response == "n":
                correct = False
                raw_wrong_info = input("What information is wrong? [u]sername|[s]urname|[t]ype|[p]assword|[a]ll: ").lower()
                wrong_info = [ x[0] for x in raw_wrong_info.split(" ") ]
                if "u" in wrong_info:
                    user.require_username()
                if "s" in wrong_info:
                    user.require_surname()
                if "t" in wrong_info:
                    user.require_user_type()
                if "p" in wrong_info:
                    user.require_unique_password()
                if "a" in wrong_info:
                    user.require_username()
                    user.require_surname()
                    user.require_user_type()
                    user.require_unique_password()
            # Save user to passwd and shadow files
        with self.passwd.open("a") as passwd_file:
            with self.shadow.open("a") as shadow_file:
                user.uid = self.get_next_uid()
                passwd_file.write(f"{user.serialize()}\n")
                shadow_file.write(f"{user.login}:{user.get_hash_password()}\n")
            
    def remove_user(self, login):
        if not self.passwd.exists():
            print("No users to remove.")
            sys.exit(1)
        with self.passwd.open("r") as passwd_file:
            lines = passwd_file.readlines()
        with self.shadow.open("r") as shadow_file:
            shadow_lines = shadow_file.readlines()
        with self.passwd.open("w") as passwd_file:
            with self.shadow.open("w") as shadow_file:
                for line in lines:
                    if not line.startswith(f"{login}:"):
                        passwd_file.write(line)
                for line in shadow_lines:
                    if not line.startswith(f"{login}:"):
                        shadow_file.write(line)

    def get_next_uid(self):
        if not self.passwd.exists():
            return 100000
        with self.passwd.open("r") as passwd_file:
            lines = passwd_file.readlines()
            if not lines:
                return 100000
            last_line = lines[-1]
            last_uid = int(last_line.split(":")[1])
            return last_uid + 1

    def unatended_add_user(self, login, username, surname, user_type, password):
        user = User(login, username, surname, user_type, password)
        if self.check_user_exists(user.login):
            print(f"User {user.login} already exists.")
            sys.exit(1)
        user.uid = self.get_next_uid()
        with self.passwd.open("a") as passwd_file:
            with self.shadow.open("a") as shadow_file:
                passwd_file.write(f"{user.serialize()}\n")
                shadow_file.write(f"{user.login}:{user.get_hash_password()}\n")

    def run(self, action, user):
        if action == "add":
            self.add_user(user)
        elif action == "remove":
            self.remove_user(user)
        else:
            print(f"Unknown action: {action}")
            sys.exit(1)



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ADF CLI")
    # add optional argument for unattended user creation with username, surname, type and password 
    parser.add_argument("--unattended", action="store_true", help="Unattended user creation")
    parser.add_argument("action", choices=["add", "remove"])
    parser.add_argument("login")
    parser.add_argument("--username","-u", help="Username for unattended user creation")
    parser.add_argument("--surname","-s", help="Surname for unattended user creation")
    parser.add_argument("--type","-t", choices=["s", "t", "a", "n"], help="User type for unattended user creation")
    parser.add_argument("--password","-p", help="Password for unattended user creation")
    args = parser.parse_args()
    adf_cli = ADFCLI()
    adf_cli.run(args.action, args.login)
    sys.exit(0)
