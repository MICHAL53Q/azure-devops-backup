from azure.devops.released.core.core_client import CoreClient
from azure.devops.released.git.git_client import GitClient
from azure.devops.released.wiki.wiki_client import WikiClient
from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication


class AzureDevops:
    def __init__(self, personal_access_token: str, organization_url: str) -> None:
        credentials = BasicAuthentication('', personal_access_token)
        connection = Connection(base_url=organization_url, creds=credentials)
        self.__core_client: CoreClient = connection.clients.get_core_client()
        self.__git_client: GitClient = connection.clients.get_git_client()
        self.__wiki_client: WikiClient = connection.clients.get_wiki_client()

    def list_projects_name(self) -> set:
        response = self.__core_client.get_projects()

        result = set()
        while response is not None:
            for project in response.value:
                # Add project name to result set
                result.add(project.name)
            if response.continuation_token is not None and response.continuation_token != "":
                # Get the next page of projects
                response = self.__core_client.get_projects(continuation_token=response.continuation_token)
            else:
                # All projects have been retrieved
                response = None

        return result

    def list_project_repos(self, project_name: str) -> list:
        response = self.__git_client.get_repositories(project_name)

        result = list()
        for repo in response:
            result.append({
                'name': repo.name,
                'remote_url': repo.remote_url,
                'ssh_url': repo.ssh_url
            })

        return result

    def list_project_wikis(self, project_name: str) -> list:
        response = self.__wiki_client.get_all_wikis(project_name)

        result = list()
        for wiki in response:
            repo = self.__git_client.get_repository(wiki.repository_id, project_name)
            result.append({
                'name': repo.name,
                'remote_url': repo.remote_url,
                'ssh_url': repo.ssh_url
            })

        return result
