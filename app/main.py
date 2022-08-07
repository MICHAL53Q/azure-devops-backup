#!/usr/bin/env python3
"""
Azure DevOps Backup

Solution to extract & transport data from Azure DevOps (SaaS) 
into external file storage (SharePoint)

Script should run as CronJob with no-concurency policy,
suitable to run in container, requires persistent volume.
"""

__author__ = "MICHAL53Q@gmail.com"
__version__ = "0.1.0"
__license__ = "MIT"

import os
import sys
import shutil

from logzero import logger

from app.modules.azure_devops.main import AzureDevops
from app.modules.git.main import Git
from app.modules.sharepoint.main import SharePoint


def set_exit_code(value: int) -> None:
    global exit_code
    exit_code = value


def get_exit_code() -> int:
    global exit_code
    return exit_code


def except_hook(exctype, excvalue, exctraceback):
    import traceback

    logger.error(excvalue)
    logger.error(traceback.format_tb(exctraceback))
    sys.exit(1)


# Set initial exit code
exit_code = 0

# Set default exception handler
sys.excepthook = except_hook


def get_archive_paths(path_archive: str) -> dict:
    # Get len of path_archive to substring absolute path
    len_substring_path = len(path_archive) + 1

    dir_paths = set()
    file_paths = set()
    for subdir, dirs, files in os.walk(path_archive):
        for file in files:
            full_path = os.path.join(subdir, file)
            absolute_path = os.path.dirname(full_path)

            dir_paths.add(absolute_path[len_substring_path:])
            file_paths.add(full_path)

    return {
        "dir_paths": dir_paths,
        "file_paths": file_paths
    }


def clean_archive_path(path_archive: str) -> None:
    logger.info(f"clean_archive_path | cleaning archive path | path_archive: {path_archive}")
    if os.path.isdir(path_archive):
        shutil.rmtree(path_archive)


def get_env_vars() -> tuple:
    try:
        devops_pat = os.environ['DEVOPS_PAT']
        devops_org_url = os.environ['DEVOPS_ORGANIZATION_URL']
        path_clone = os.environ['PATH_CLONE']
        path_archive = os.environ['PATH_ARCHIVE']
        sharepoint_url = os.environ['SHAREPOINT_URL']
        sharepoint_dir = os.environ['SHAREPOINT_DIR']
        sharepoint_client_id = os.environ['SHAREPOINT_CLIENT_ID']
        sharepoint_client_secret = os.environ['SHAREPOINT_CLIENT_SECRET']
    except KeyError as exception:
        raise Exception(f"Missing ENV Variable: {exception}")

    return devops_pat, devops_org_url, path_clone, path_archive, sharepoint_url, sharepoint_dir, sharepoint_client_id, sharepoint_client_secret


def sync_data(devops_pat: str, devops_org_url, path_clone: str) -> set:
    # Initialize Azure DevOps Client
    devops = AzureDevops(devops_pat, devops_org_url)

    # Initialize Git
    git = Git("", devops_pat)

    # List DevOps Projects
    projects_name = devops.list_projects_name()

    changes = set()
    for project_name in projects_name:
        # Sync project repos
        for repo in devops.list_project_repos(project_name):
            try:
                repo_name = repo['name']
                repo_remote_url = repo['remote_url']

                has_changes = git.sync(repo_remote_url, f"{path_clone}/{project_name}/git/{repo_name}")
                if has_changes:
                    changes.add(f"{project_name}/git/{repo_name}")

                logger.info(f"sync_data | syncing repos | project: {project_name} | repo: {repo_name} | has_changes: {has_changes}")
            except Exception as exception:
                logger.error(f"sync_data | syncing repos | project: {project_name} | repo: {repo_name} | exception: {exception}")
                set_exit_code(1)
                continue

        # Sync project wikis
        for wiki in devops.list_project_wikis(project_name):
            try:
                wiki_name = wiki['name']
                wiki_remote_url = wiki['remote_url']

                has_changes = git.sync(wiki_remote_url, f"{path_clone}/{project_name}/wiki/{wiki_name}")
                if has_changes:
                    changes.add(f"{project_name}/wiki/{wiki_name}")

                logger.info(f"sync_data | syncing wikis | project: {project_name} | wiki: {wiki_name} | has_changes: {has_changes}")
            except Exception as exception:
                logger.error(f"sync_data | syncing repos | project: {project_name} | repo: {wiki_name} | exception: {exception}")
                set_exit_code(1)
                continue

    return changes


def archive_changes(path_clone: str, path_archive: str, changes: set):
    if len(changes) == 0:
        logger.info(f"archive_changes | no changes detected")
        return

    for change in changes:
        logger.info(f"archive_changes | archiving changes: {change}.zip")
        shutil.make_archive(f"{path_archive}/{change}", 'zip', f"{path_clone}/{change}")


def upload_changes_to_sharepoint(sharepoint_url: str, sharepoint_client_id: str, sharepoint_client_secret: str, path_archive: str, sharepoint_dir: str):
    # Get len of path_archive to substring absolute path
    len_substring_path = len(path_archive) + 1

    # Collect paths required to upload files to SharePoint
    archive_paths = get_archive_paths(path_archive)
    dir_paths = archive_paths['dir_paths']
    file_paths = archive_paths['file_paths']

    # Get SharePoint client
    shp = SharePoint(sharepoint_url, sharepoint_client_id, sharepoint_client_secret)

    # Ensure dir_paths exists in SharePoint
    for dir_path in dir_paths:
        logger.info(f"upload_changes_to_sharepoint | ensuring dir exists | sharepoint_dir: {sharepoint_dir} | dir_path: {dir_path}")
        shp.ensure_dir_exists(sharepoint_dir, dir_path)

    # Upload files to SharePoint
    for file_path in file_paths:
        full_dir_path = os.path.dirname(file_path)
        relative_dir_path = full_dir_path[len_substring_path:]

        logger.info(f"upload_changes_to_sharepoint | upload file | sharepoint_dir: {sharepoint_dir} | relative_dir_path: {relative_dir_path} | file_path: {file_path}")
        shp.upload_file(sharepoint_dir, relative_dir_path, file_path)

    clean_archive_path(path_archive)


def main():
    # Get ENV Variables
    devops_pat, devops_org_url, path_clone, path_archive, sharepoint_url, sharepoint_dir, sharepoint_client_id, sharepoint_client_secret = get_env_vars()

    # Sync local data with remote
    changes = sync_data(devops_pat, devops_org_url, path_clone)

    # Archive changes found during sync
    archive_changes(path_clone, path_archive, changes)

    # Upload archived changes into sharepoint
    upload_changes_to_sharepoint(sharepoint_url, sharepoint_client_id, sharepoint_client_secret, path_archive, sharepoint_dir)

    # Exit script with exit code
    sys.exit(get_exit_code())


if __name__ == "__main__":
    main()
