from pathlib import Path
import crypt

from llxgvagate.user import User, Group
from llxgvagate.base_plugin import BasePlugin
from llxgvagate.error import GvaGateError

class Easy(BasePlugin):
    def __init__(self):
        self.passwd_file = Path("/var/lib/adf/passwd")
        self.shadow_file = Path("/var/lib/adf/shadow")

    @property
    def name(self):
        return "adf"

    def authenticate(self, username, password, callback):
        if self.passwd_file.exists() and self.shadow_file.exists():
            with self.passwd_file.open("r") as passwd_file:
                for line in passwd_file:
                    if line.startswith(f"{username}:"):
                        user_info = line.strip().split(":")
                        if len(user_info) < 5:
                            return None, GvaGateError.Error
                        result = {
                            'login': user_info[0],
                            'uid': int(user_info[1]),
                            'name': user_info[2],
                            'surname': user_info[3],
                            'user_type': user_info[4]
                        }
                        break
                else:
                    return None, GvaGateError.UserNotFound
            with self.shadow_file.open("r") as shadow_file:
                for line in shadow_file:
                    if line.startswith(f"{username}:"):
                        shadow_info = line.strip().split(":")
                        if len(shadow_info) < 2:
                            return None, GvaGateError.Error
                        stored_password_hash = shadow_info[1]
                        break
                else:
                    return None, GvaGateError.UserNotFound
            if not crypt.crypt(password, stored_password_hash) == stored_password_hash:
                return None, GvaGateError.InvalidPassword
        else:
            return None, GvaGateError.ServerNotFound
        user = User(result['login'])
        user.name = result['name']
        user.surname = result['surname']
        user.uid = result['uid']
        if result['user_type'] == "s":
            user.groups.append(Group("Alumno", 70001))
        elif result['user_type'] == "t":
            user.groups.append(Group("Profesor", 70002))
        elif result['user_type'] == "a":
            user.groups.append(Group("Administrador", 70003))
        elif result['user_type'] == "n":
            user.groups.append(Group("NoDocente", 70004))
        user.populate_user()
        return user, GvaGateError.Allowed
