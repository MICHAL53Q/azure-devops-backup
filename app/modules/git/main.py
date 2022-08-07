import os
import base64
from git import Repo


class Git:
    def __init__(self, user_name: str, user_password: str) -> None:
        # Create Basic auth header
        auth_header_bytes = (f"{user_name}:{user_password}").encode("ascii")
        auth_header_base64_bytes = base64.b64encode(auth_header_bytes)
        auth_header_base64 = auth_header_base64_bytes.decode("ascii")
        self.auth_header = f"Authorization: Basic {auth_header_base64}"

    def sync(self, remote: str, path: str) -> bool:
        has_changes = False
        if os.path.isdir(path):
            has_changes = self.__update(path)
        else:
            has_changes = True
            self.__clone(remote, path)

        return has_changes

    def __clone(self, remote: str, path: str) -> None:
        Repo.clone_from(
            url=remote,
            c=f"http.extraHeader={self.auth_header}",
            to_path=path,
            mirror=True
        )

    def __update(self, path: str) -> bool:
        has_changes = False

        repo_remote = Repo(path).remote()
        for fetch_info in repo_remote.fetch(prune=True):
            if fetch_info.flags != fetch_info.HEAD_UPTODATE:
                has_changes = True
                break
        repo_remote.update(prune=True)

        return has_changes
