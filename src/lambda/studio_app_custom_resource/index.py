import datetime
from typing import List, TypedDict, Union
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)
sm_client = boto3.client("sagemaker")


class AppConfig(TypedDict):
    DomainId: str
    UserProfileName: str
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


class ListResponse(TypedDict):
    Apps: List[AppConfig]
    NextToken: str


def delete_studio_apps(list_response: ListResponse) -> List[AppConfig]:
    failed_apps = []
    for app_config in list_response.get("Apps", []):
        try:
            if app_config.get("Status") != "InService":
                continue
            logger.info({"status": "deleting studio app"})
            delete_response = sm_client.delete_app(
                DomainId=app_config["DomainId"],
                UserProfileName=app_config["UserProfileName"],
                AppName=app_config["AppName"],
                AppType=app_config["AppType"],
            )
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


def on_delete(user_profile_name: str, physical_resource_id: str):
    """Function to execute when deleting the custom resource

    Args:
         (str): Name of the lcc
        physical_resource_id (str): physical resource id

    Returns:
        result (json): status and physical resource id
    """

    logger.info({"status": "deleting resource"})
    try:
        list_response: ListResponse = sm_client.list_apps(
            UserProfileNameEquals=user_profile_name
        )
        logger.info({"status": "listed studio apps", "response": list_response})
    except Exception as e:
        logger.exception({"status": "failed to delete studio app", "exception": e})
        return {
            "Status": "FAILED",
            "PhysicalResourceId": physical_resource_id,
            "Reason": "failed to list studio apps",
        }

    failed_apps = delete_studio_apps(list_response)

    if failed_apps:
        return {
            "Status": "FAILED",
            "PhysicalResourceId": physical_resource_id,
            "Reason": f"failed to delete studio apps :{[(failed_app.get('UserProfileName'), failed_app.get('AppName')) for failed_app in failed_apps]}",
        }
    return {"Status": "SUCCESS", "PhysicalResourceId": physical_resource_id}


def is_delete_complete(user_profile_name: str, domain_id: str):
    logger.info({"status": "calling is_delete_complete"})
    try:
        list_response: ListResponse = sm_client.list_apps(
            UserProfileNameEquals=user_profile_name
        )
        logger.info({"status": "listed studio apps", "response": list_response})
        running_apps = [
            app
            for app in list_response.get("Apps")
            if app["Status"] in ["In-Service", "Deleting"]
        ]
        if running_apps:
            logger.info({"status": "deleting studio apps"})
            delete_studio_apps(list_response)
            return {"IsComplete": False}

        else:
            logger.info({"status": "deleted all studio apps"})
            logger.info({"status": "deleting user profile"})
            sm_client.delete_user_profile(
                DomainId=domain_id, UserProfileName=user_profile_name
            )
            logger.info({"status": "deleted user profile"})
    except Exception as e:
        logger.exception(
            {
                "status": "failed to list studio apps or to delete user profiles",
                "exception": e,
            }
        )
        return {"IsComplete": False}
    return {"IsComplete": True}


def on_event_handler(event, context):
    logger.info(event)
    user_profile_name = event.get("ResourceProperties", {}).get("user_profile_name")
    physical_resource_id = event.get("PhysicalResourceId")

    request_type = event["RequestType"]
    if request_type == "Create":
        return on_create()
    if request_type == "Update":
        return on_update()
    if request_type == "Delete":
        return on_delete(user_profile_name, physical_resource_id)
    raise Exception(f"Invalid request type: {request_type}")


def is_complete_handler(event, context):
    logger.info(event)
    user_profile_name = event.get("ResourceProperties", {}).get("user_profile_name")
    domain_id = event.get("ResourceProperties", {}).get("domain_id")
    request_type = event["RequestType"]

    if request_type == "Create":
        return is_create_complete()
    if request_type == "Update":
        return is_update_complete()
    if request_type == "Delete":
        return is_delete_complete(user_profile_name, domain_id)
    raise Exception(f"Invalid request type: {request_type}")
