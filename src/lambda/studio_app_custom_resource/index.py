import datetime
from typing import List, TypedDict, Union, Dict
import boto3
import logging
from typing import Dict

logger = logging.getLogger()
logger.setLevel(logging.INFO)
sm_client = boto3.client("sagemaker")


class SpaceConfig(TypedDict):
    DomainId: str
    SpaceName: str
    Status: Union["Deleted", "Deleting", "Failed", "InService", "Pending"]
    CreationTime: datetime.datetime
    LastModifiedTime: datetime.datetime
    SpaceSettingsSummary: Dict
    SpaceSharingSettingsSummary: Dict
    OwnershipSettingsSummary: Dict
    SpaceDisplayName: str


class AppConfig(TypedDict):
    DomainId: str
    UserProfileName: str
    SpaceName: str
    AppType: Union[
        "JupyterLab",
        "CodeEditor",
        "DetailedProfiler",
        "TensorBoard",
        "RStudioServerPro",
        "RSessionGateway",
        "Canvas",
    ]
    AppName: str
    Status: Union["Deleted", "Deleting", "Failed", "InService", "Pending"]
    CreationTime: datetime.datetime


class ListAppsResponse(TypedDict):
    Apps: List[AppConfig]
    NextToken: str


class ListSpacesResponse(TypedDict):
    Spaces: List[SpaceConfig]
    NextToken: str


def delete_studio_apps(list_response: ListAppsResponse) -> List[AppConfig]:
    failed_apps = []
    for app_config in list_response.get("Apps", []):
        try:
            if app_config.get("Status") != "InService":
                continue
            logger.info({"status": "deleting studio app"})

            delete_app_kwargs = {
                "DomainId": app_config["DomainId"],
                "AppName": app_config["AppName"],
                "AppType": app_config["AppType"],
            }

            if app_config.get("UserProfileName"):
                delete_app_kwargs.update(
                    {"UserProfileName": app_config["UserProfileName"]}
                )
            else:
                delete_app_kwargs.update({"SpaceName": app_config["SpaceName"]})

            delete_response = sm_client.delete_app(**delete_app_kwargs)
            logger.info({"status": "deleted studio app", "response": delete_response})
        except Exception as e:
            logger.exception({"status": "failed to delete studio app", "exception": e})
            failed_apps.append(app_config)
    return failed_apps


def on_create():
    """Function to execute when creating a new custom resource

    Args:

    Returns:
        result (json): status
    """

    logger.info({"status": "create resource not needed for studio app custom resource"})

    return {"Status": "SUCCESS"}


def is_create_complete():
    logger.info({"status": "calling is_create_complete"})
    return {"IsComplete": True}


def on_update():
    """Function to execute when updating the custom resource

    Args:

    Returns:
        result (json): status
    """

    logger.info({"status": "update resource not needed for studio app custom resource"})

    return {"Status": "SUCCESS"}


def is_update_complete():
    logger.info({"status": "calling is_update_complete"})
    return {"IsComplete": True}


def on_delete(
    domain_id: str, user_profile_name: str, space_name: str, physical_resource_id: str
):
    """Function to execute when deleting the custom resource

    Args:
         (str): Name of the lcc
        physical_resource_id (str): physical resource id

    Returns:
        result (json): status and physical resource id
    """

    logger.info({"status": "deleting studio apps and spaces"})

    # list all sagemaker apps and delete
    try:
        list_apps_response: ListAppsResponse = sm_client.list_apps(
            DomainIdEquals=domain_id
        )
        list_apps_response["Apps"] = [
            app
            for app in list_apps_response["Apps"]
            if app.get("UserProfileName") == user_profile_name
            or app.get("SpaceName") == space_name
        ]
        logger.info(
            {
                "status": "listed studio apps",
                "response": list_apps_response,
            }
        )

    except Exception as e:
        logger.exception({"status": "failed to delete studio app", "exception": e})
        return {
            "Status": "FAILED",
            "PhysicalResourceId": physical_resource_id,
            "Reason": "failed to list studio apps",
        }
    failed_apps = delete_studio_apps(list_apps_response)

    if failed_apps:

        return {
            "Status": "FAILED",
            "PhysicalResourceId": physical_resource_id,
            "Reason": f"failed to delete studio resources:\n apps: {[(failed_app.get('UserProfileName'), failed_app.get('SpaceName'), failed_app.get('AppName')) for failed_app in failed_apps]}",
        }
    return {"Status": "SUCCESS", "PhysicalResourceId": physical_resource_id}


def is_delete_complete(user_profile_name: str, space_name: str, domain_id: str):
    logger.info({"status": "calling is_delete_complete"})

    try:
        list_apps_profile_response: ListAppsResponse = sm_client.list_apps(
            DomainIdEquals=domain_id, UserProfileNameEquals=user_profile_name
        )
        list_apps_space_response: ListAppsResponse = sm_client.list_apps(
            DomainIdEquals=domain_id, SpaceNameEquals=space_name
        )

        list_apps_response = {
            "Apps": list_apps_profile_response.get("Apps", [])
            + list_apps_space_response.get("Apps", [])
        }

        list_spaces_response: ListSpacesResponse = sm_client.list_spaces(
            DomainIdEquals=domain_id, SpaceNameContains=space_name
        )
        logger.info({"status": "listed studio apps", "response": list_apps_response})
        logger.info(
            {"status": "listed studio spaces", "response": list_spaces_response}
        )

        running_apps = [
            app
            for app in list_apps_response.get("Apps")
            if app["Status"] in ["InService", "Deleting"]
        ]

        running_spaces = [
            space
            for space in list_spaces_response.get("Spaces")
            if space["Status"] in ["InService", "Deleting"]
        ]

        if running_apps:
            logger.info({"status": "deleting studio apps"})
            delete_studio_apps(list_apps_response)
            return {"IsComplete": False}
        else:
            logger.info({"status": "deleted all studio apps"})
            if running_spaces:
                logger.info({"status": "waiting for deletion of studio spaces"})
                return {"IsComplete": False}
            else:
                logger.info({"status": "deleted all studio spaces"})
                logger.info({"status": "deleting user profile"})
                sm_client.delete_user_profile(
                    DomainId=domain_id, UserProfileName=user_profile_name
                )
                logger.info({"status": "deleted user profile"})

    except Exception as e:
        logger.exception(
            {
                "status": "failed to delete studio spaces or apps",
                "exception": e,
            }
        )
        return {"IsComplete": False}
    return {"IsComplete": True}


def on_event_handler(event, context):
    logger.info(event)
    user_profile_name = event.get("ResourceProperties", {}).get("user_profile_name")
    domain_id = event.get("ResourceProperties", {}).get("domain_id")
    space_name = event.get("ResourceProperties", {}).get("space_name")
    physical_resource_id = event.get("PhysicalResourceId")

    request_type = event["RequestType"]
    if request_type == "Create":
        return on_create()
    if request_type == "Update":
        return on_update()
    if request_type == "Delete":
        return on_delete(domain_id, user_profile_name, space_name, physical_resource_id)
    raise Exception(f"Invalid request type: {request_type}")


def is_complete_handler(event, context):
    logger.info(event)
    user_profile_name = event.get("ResourceProperties", {}).get("user_profile_name")
    domain_id = event.get("ResourceProperties", {}).get("domain_id")
    space_name = event.get("ResourceProperties", {}).get("space_name")
    request_type = event["RequestType"]

    if request_type == "Create":
        return is_create_complete()
    if request_type == "Update":
        return is_update_complete()
    if request_type == "Delete":
        return is_delete_complete(user_profile_name, space_name, domain_id)
    raise Exception(f"Invalid request type: {request_type}")
