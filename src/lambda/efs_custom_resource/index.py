import datetime
from typing import List, Optional, TypedDict, Union
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)
efs_client = boto3.client("efs")


class EfsConfig(TypedDict):
    OwnerId: str
    CreationToken: str
    FileSystemId: str
    FileSystemArn: str
    CreationTime: datetime.datetime
    LifeCycleState: Union[
        "creating", "available", "updating", "deleting", "deleted", "error"
    ]
    Name: str
    NumberOfMountTargets: float
    SizeInBytes: TypedDict
    PerformanceMode: Union["generalPurpose", "maxIO"]
    Encrypted: bool
    KmsKeyId: str
    ThroughputMode: Union["bursting", "provisioned", "elastic"]
    ProvisionedThroughputInMibps: float
    AvailabilityZoneName: str
    AvailabilityZoneId: str
    Tags: List


class DescribeResponse(TypedDict):
    Efs: List[EfsConfig]
    NextMarker: str


def delete_file_system(fs_id: str) -> None:
    if not fs_id:
        raise ValueError("fs_id not provided")
    logger.info({"status": "calling delete_file_systems"})

    mount_targets = efs_client.describe_mount_targets(FileSystemId=fs_id).get(
        "MountTargets", []
    )

    logger.info(
        {
            "status": "getting mount targets",
            "response": mount_targets,
        }
    )
    if not mount_targets:
        delete_response = efs_client.delete_file_system(FileSystemId=fs_id)

        logger.info(
            {
                "status": "deleted file system",
                "response": delete_response,
            }
        )
        return

    for mount_target in mount_targets:
        logger.info(
            {
                "status": "deleting mount target",
                "mount_target": mount_target,
            }
        )
        try:
            efs_client.delete_mount_target(
                MountTargetId=mount_target.get("MountTargetId")
            )
        except Exception as e:
            logger.exception({"status": "failed to delete file system", "exception": e})


def describe_file_system(fs_id: str) -> Optional[EfsConfig]:
    if not fs_id:
        raise ValueError("fs_id not provided")

    logger.info(
        {
            "status": "calling describe_file_systems",
        }
    )

    try:
        # fails if fs is already deleted
        describe_response = efs_client.describe_file_systems(FileSystemId=fs_id)
    except Exception as e:
        logger.exception({"status": "failed to describe file systems", "exception": e})
        return None

    logger.info({"status": "described file systems", "response": describe_response})

    if describe_response.get("FileSystems"):
        return describe_response.get("FileSystems")[0]
    return None


def on_create():
    """Function to execute when creating a new custom resource"""
    logger.info({"status": "create resource not needed for efs custom resource"})
    return {"Status": "SUCCESS"}


def is_create_complete():
    logger.info({"status": "calling is_create_complete"})
    return {"IsComplete": True}


def on_update():
    """Function to execute when updating the custom resource"""
    logger.info({"status": "update resource not needed for efs custom resource"})
    return {"Status": "SUCCESS"}


def is_update_complete():
    logger.info({"status": "calling is_update_complete"})
    return {"IsComplete": True}


def on_delete(fs_id: str, physical_resource_id: str):
    """Function to execute when deleting the custom resource

    Args:
        fs_id (str): Name of the lcc
        physical_resource_id (str): physical resource id

    Returns:
        result (json): status and physical resource id
    """
    logger.info({"status": "deleting resource"})
    try:
        esf_config: EfsConfig = describe_file_system(fs_id)
        # if fs doesnt exist anymore, return SUCCESS
        if not esf_config or esf_config.get("LifeCycleState") == "deleted":
            return {"Status": "SUCCESS", "PhysicalResourceId": physical_resource_id}
        delete_file_system(esf_config.get("FileSystemId"))
        return {"Status": "SUCCESS", "PhysicalResourceId": physical_resource_id}
    except Exception as e:
        logger.exception({"status": "failed to describe file systems", "exception": e})
        return {
            "Status": "FAILED",
            "PhysicalResourceId": physical_resource_id,
            "Reason": f"{e}",
        }


def is_delete_complete(fs_id: str):
    logger.info({"status": "calling is_delete_complete"})
    try:
        # check if file system is deleted
        esf_config: EfsConfig = describe_file_system(fs_id)
        if not esf_config or esf_config.get("LifeCycleState") == "deleted":
            return {"IsComplete": True}
        # if not, check if mount target are deleted
        mount_targets = efs_client.describe_mount_targets(FileSystemId=fs_id).get(
            "MountTargets", []
        )
        logger.info(
            {"status": "described mount targets", "mount_targets": mount_targets}
        )

        # if mount targets are deleted, trigger fs deletion
        if not mount_targets:
            delete_response = efs_client.delete_file_system(FileSystemId=fs_id)
            logger.info({"status": "deleted file system", "response": delete_response})

            return {"IsComplete": False}

        # if not, trigger mount target deletion
        for mount_target in mount_targets:
            delete_response = efs_client.delete_mount_target(
                MountTargetId=mount_target.get("MountTargetId")
            )
            logger.info({"status": "deleted mount target", "response": delete_response})
        return {"IsComplete": False}

    except:
        logger.exception("failed to describe file system")
        return {"IsComplete": False}


def on_event_handler(event, context):
    logger.info(event)
    fs_id = event.get("ResourceProperties", {}).get("fs_id")
    physical_resource_id = event.get("PhysicalResourceId")

    request_type = event["RequestType"]
    if request_type == "Create":
        return on_create()
    if request_type == "Update":
        return on_update()
    if request_type == "Delete":
        return on_delete(fs_id, physical_resource_id)
    raise Exception(f"Invalid request type: {request_type}")


def is_complete_handler(event, context):
    logger.info(event)
    fs_id = event.get("ResourceProperties", {}).get("fs_id")
    request_type = event["RequestType"]

    if request_type == "Create":
        return is_create_complete()
    if request_type == "Update":
        return is_update_complete()
    if request_type == "Delete":
        return is_delete_complete(fs_id)
    raise Exception(f"Invalid request type: {request_type}")
