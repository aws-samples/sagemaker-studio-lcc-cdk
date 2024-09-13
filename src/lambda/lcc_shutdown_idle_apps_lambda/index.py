import base64
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)
sm_client = boto3.client("sagemaker")


def on_create(domain_id: str, app_shutdown_lifecycle_config: str):
    """Function to execute when creating a new custom resource

    Args:
        domain_id (str): SageMaker Studio Domain ID
        app_shutdown_lifecycle_config (str): Name of the lcc

    Returns:
        result (json): status and physical resource id
    """
    logger.info({"status": "create new resource"})

    with open("shutdown-idle-apps.sh", "rb") as f:
        script_content = f.read()
    encoded_script_content = base64.b64encode(script_content).decode()

    try:
        response = sm_client.create_studio_lifecycle_config(
            StudioLifecycleConfigName=app_shutdown_lifecycle_config,
            StudioLifecycleConfigContent=encoded_script_content,
            StudioLifecycleConfigAppType="JupyterLab",
        )

        lcc_arn = response["StudioLifecycleConfigArn"]

        list_lcc_response = sm_client.list_studio_lifecycle_configs(
            AppTypeEquals="JupyterLab"
        ).get("StudioLifecycleConfigs", [])

        logger.info(
            {"status": "listed studio lifecycle configs", "response": list_lcc_response}
        )

        if list_lcc_response:
            existing_lcc_arns = [
                elem["StudioLifecycleConfigArn"] for elem in list_lcc_response
            ]
            lcc_arns = existing_lcc_arns + [lcc_arn]
        else:
            lcc_arns = [lcc_arn]
        logger.info(
            {
                "status": "prepared lifecycle config arns for domain update",
                "lcc_arns": lcc_arns,
            }
        )

        sm_client.update_domain(
            DomainId=domain_id,
            DefaultUserSettings={
                "JupyterLabAppSettings": {
                    "DefaultResourceSpec": {
                        "LifecycleConfigArn": lcc_arn,
                        "InstanceType": "ml.t3.medium",
                    },
                    "LifecycleConfigArns": lcc_arns,
                }
            },
        )
        return {"Status": "SUCCESS", "PhysicalResourceId": lcc_arn}

    except Exception as e:
        logger.exception(
            {"status": "failed to create lifecycle config", "exception": e}
        )
        return {
            "Status": "FAILED",
        }


def is_create_complete():
    logger.info({"status": "calling is_create_complete"})
    return {"IsComplete": True}


def on_update(
    domain_id: str, app_shutdown_lifecycle_config: str, physical_resource_id: str
):
    """Function to execute when updating the custom resource

    Args:
        domain_id (str): SageMaker Studio Domain ID
        app_shutdown_lifecycle_config (str): Name of the lcc
        physical_resource_id (str): physical resource id

    Returns:
        result (json): status and physical resource id
    """
    logger.info({"status": "updating resource"})

    on_delete(app_shutdown_lifecycle_config, physical_resource_id)

    return on_create(domain_id, app_shutdown_lifecycle_config)


def is_update_complete():
    logger.info({"status": "calling is_update_complete"})
    return {"IsComplete": True}


def on_delete(app_shutdown_lifecycle_config: str, physical_resource_id: str):
    """Function to execute when deleting the custom resource

    Args:
        domain_id (str): SageMaker Studio Domain ID
        app_shutdown_lifecycle_config (str): Name of the lcc

    Returns:
        result (json): status and physical resource id
    """

    logger.info({"status": "deleting resource"})

    try:
        sm_client.delete_studio_lifecycle_config(
            StudioLifecycleConfigName=app_shutdown_lifecycle_config
        )
        return {"Status": "SUCCESS", "PhysicalResourceId": physical_resource_id}

    except:
        logger.exception(
            {"status": "failed to delete lifecycle config", "exception": e}
        )
        return {"Status": "FAILED", "PhysicalResourceId": physical_resource_id}


def is_delete_complete(app_shutdown_lifecycle_config: str):
    logger.info({"status": "calling is_delete_complete"})

    try:
        # check if studio lifecycle is deleted
        lifecycle_config = sm_client.describe_studio_lifecycle_config(
            StudioLifecycleConfigName=app_shutdown_lifecycle_config
        )

        if lifecycle_config:
            sm_client.delete_studio_lifecycle_config(
                StudioLifecycleConfigName=app_shutdown_lifecycle_config
            )
            return {"IsComplete": False}

    except Exception as e:

        logger.exception(
            {"status": "studio lifecylce config does not exist anymore", "exception": e}
        )
        return {"IsComplete": True}


def on_event_handler(event, context):
    logger.info(event)
    domain_id = event["ResourceProperties"]["domain_id"]
    app_shutdown_lifecycle_config = event["ResourceProperties"][
        "app_shutdown_lifecycle_config"
    ]
    physical_resource_id = event.get("PhysicalResourceId")

    request_type = event["RequestType"]
    if request_type == "Create":
        return on_create(domain_id, app_shutdown_lifecycle_config)
    if request_type == "Update":
        return on_update(domain_id, app_shutdown_lifecycle_config, physical_resource_id)
    if request_type == "Delete":
        return on_delete(app_shutdown_lifecycle_config, physical_resource_id)
    raise Exception(f"Invalid request type: {request_type}")


def is_complete_handler(event, context):
    logger.info(event)
    app_shutdown_lifecycle_config = event.get("ResourceProperties", {}).get(
        "app_shutdown_lifecycle_config"
    )
    request_type = event["RequestType"]

    if request_type == "Create":
        return is_create_complete()
    if request_type == "Update":
        return is_update_complete()
    if request_type == "Delete":
        return is_delete_complete(app_shutdown_lifecycle_config)
    raise Exception(f"Invalid request type: {request_type}")
