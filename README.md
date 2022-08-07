# Azure DevOps Backup

Solution to extract & transport data from Azure DevOps (SaaS)
into external file storage (SharePoint)

Script should run as CronJob with no-concurency policy,
suitable to run in container, requires persistent volume.

Through Azure DevOps REST API application get all Git repos & wikis which are mirrored into file storage.
If there are incremental changes, they are later packed into .zip files and trasported into external storage (SharePoint)

If non-critical error happen, script will keep running but exit code will be 1,
if run is without error exit code is 0

# Requirements

## Linux container with persitent volume

Application is running in container with mounted peristent volume as file storage

## Azure DevOps organization

Azure DevOps organization with account PAT Token with following permissions:

| Name        | Permissions |
| ----------- | ----------- |
| <b>Wiki</b> | Read        |
| <b>Code</b> | Read        |

[Azure DevOps PAT Token Docs](https://docs.microsoft.com/en-us/azure/devops/organizations/accounts/use-personal-access-tokens-to-authenticate?view=azure-devops&tabs=Windows)

## SharePoint

SharePoint site with App-Only service account with following permissions:

```
<AppPermissionRequests AllowAppOnlyPolicy="true">
  <AppPermissionRequest Scope="http://sharepoint/content/tenant" Right="FullControl" />
</AppPermissionRequests>
```

[SharePoint App-Only Docs](https://docs.microsoft.com/en-us/sharepoint/dev/solution-guidance/security-apponly-azureacs)

# Configs

| Name                     | Example                                        | Description                |
| ------------------------ | ---------------------------------------------- | -------------------------- |
| DEVOPS_PAT               | xxxxxxxxxxxxxxxxxxxxxxxxx                      | Azure DevOps PAT Token     |
| DEVOPS_ORGANIZATION_URL  | https://dev.azure.com/myOrganization           | Azure DevOps URL           |
| SHAREPOINT_URL           | https://myCompany.sharepoint.com/sites/backups | Full Sharepoint target URL |
| SHAREPOINT_DIR           | Documents/DevOps                               | Sharepoint Directory name  |
| SHAREPOINT_CLIENT_ID     | 00000000-0000-0000-0000-000000000000           | Sharepoint Client ID       |
| SHAREPOINT_CLIENT_SECRET | xxxxxxxxxxxxxxxxxxxxxxxxx                      | Sharepoint Client Secret   |
| PATH_CLONE               | /mnt/backup/clone                              | Path where store clone     |
| PATH_ARCHIVE             | /mnt/backup/archive                            | Path where store archives  |

# File structure

```
.
├── app                                 # App folder
├── configs                             # Contains environment files (for local development)
│   └── test.env                        # Contains sensitive data which are injected into docker-compose.yaml
├── tests                               # App tests folder
└── tmp                                 # Mounted storage for application data
    ├── archive                         # Contains backup archives (cleaned after every success run)
    └── clone                           # Contains git mirror data
```

# Installation

## Requirements

- Docker running Linux containers (for local development)
- Service Principal for Azure Key Vault
- Sharepoint App-Only credentials

## Create configs

### ./configs/test.env

```bash
cat << EOF > ./configs/test.env
DEVOPS_PAT=xxxxxxxxxxxxxxxxxxxxxxxxx
DEVOPS_ORGANIZATION_URL=https://dev.azure.com/organization

SHAREPOINT_URL=https://organization.sharepoint.com/sites/backups
SHAREPOINT_DIR=Documents/DevOps
SHAREPOINT_CLIENT_ID=00000000-0000-0000-0000-000000000000
SHAREPOINT_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxx
EOF
```

## Run container

```
docker-compose --env-file ./configs/test.env up --build
```

## Run container inactivelly & attach to it

You will need uncomment following section in <i>docker-compose.yaml</i>

```
    # stdin_open: true
    # tty: true
    # command: tail -f /dev/null
```

and run following command

```
docker-compose --env-file ./configs/test.env up --build -d && docker exec -it git-backup sh
```
