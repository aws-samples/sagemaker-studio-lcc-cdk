import base64
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)
sm_client = boto3.client("sagemaker")


def on_create(domain_id: str, package_lifecycle_config: str):
    """Function to execute when creating a new custom resource

    Args:
        domain_id (str): SageMaker Studio Domain ID
        package_lifecycle_config (str): Name of the lcc

    Returns:
        result (json): status and physical resource id
    """

    logger.info("create new resource")

    with open("install-packages.sh", "rb") as f:
        script_content = f.read()
    encoded_script_content = base64.b64encode(script_content).decode()

    try:
        response = sm_client.create_studio_lifecycle_config(
            StudioLifecycleConfigName=package_lifecycle_config,
            StudioLifecycleConfigContent=encoded_script_content,
            StudioLifecycleConfigAppType="KernelGateway",
        )

        lcc_arn = response["StudioLifecycleConfigArn"]

        sm_client.update_domain(
            DomainId=domain_id,
            DefaultUserSettings={
                "KernelGatewayAppSettings": {
                    "LifecycleConfigArns": [lcc_arn],
                }
            },
        )
        return {"Status": "SUCCESS", "PhysicalResourceId": lcc_arn}

    except:
        logger.exception("failed to create lifecycle config")
        return {"Status": "FAILED"}


def is_create_complete():
    logger.info("calling is_create_complete")
    return {"IsComplete": True}


def on_update(domain_id: str, package_lifecycle_config: str, physical_resource_id: str):
    """Function to execute when updating the custom resource

    Args:
        domain_id (str): SageMaker Studio Domain ID
        package_lifecycle_config (str): Name of the lcc
        physical_resource_id (str): physical resource id

    Returns:
        result (json): status and physical resource id
    """

    logger.info("update resource")

    on_delete(package_lifecycle_config, physical_resource_id)

    return on_create(domain_id, package_lifecycle_config)


def is_update_complete():
    logger.info("calling is_update_complete")
    return {"IsComplete": True}


def on_delete(package_lifecycle_config: str, physical_resource_id: str):
    """Function to execute when deleting the custom resource

    Args:
        package_lifecycle_config (str): Name of the lcc
        physical_resource_id (str): physical resource id

    Returns:
        result (json): status and physical resource id
    """

    logger.info("delete resource")
    try:
        sm_client.delete_studio_lifecycle_config(
            StudioLifecycleConfigName=package_lifecycle_config
        )
        return {"Status": "SUCCESS", "PhysicalResourceId": physical_resource_id}

    except:
        logger.exception("failed to delete lifecycle config")
        return {"Status": "FAILED", "PhysicalResourceId": physical_resource_id}


def is_delete_complete(package_lifecycle_config: str):
    logger.info("calling is_delete_complete")

    try:
        # check if studio lifecycle is deleted
        lifecycle_config = sm_client.describe_studio_lifecycle_config(
            StudioLifecycleConfigName=package_lifecycle_config
        )

        if lifecycle_config:
            sm_client.delete_studio_lifecycle_config(
                StudioLifecycleConfigName=package_lifecycle_config
            )
            return {"IsComplete": False}

    except:
        logger.exception("studio lifecycle config does not exist anymore")
        return {"IsComplete": True}


def on_event_handler(event, context):
    logger.info(event)
    domain_id = event["ResourceProperties"]["domain_id"]
    package_lifecycle_config = event["ResourceProperties"]["package_lifecycle_config"]
    physical_resource_id = event.get("PhysicalResourceId")

    request_type = event["RequestType"]
    if request_type == "Create":
        return on_create(domain_id, package_lifecycle_config)
    if request_type == "Update":
        return on_update(domain_id, package_lifecycle_config, physical_resource_id)
    if request_type == "Delete":
        return on_delete(package_lifecycle_config, physical_resource_id)
    raise Exception(f"Invalid request type: {request_type}")


def is_complete_handler(event, context):
    logger.info(event)
    package_lifecycle_config = event.get("ResourceProperties", {}).get(
        "package_lifecycle_config"
    )
    request_type = event["RequestType"]

    if request_type == "Create":
        return is_create_complete()
    if request_type == "Update":
        return is_update_complete()
    if request_type == "Delete":
        return is_delete_complete(package_lifecycle_config)
    raise Exception(f"Invalid request type: {request_type}")
