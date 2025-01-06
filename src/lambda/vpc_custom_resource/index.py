from typing import List, TypedDict
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)
ec2_client = boto3.client("ec2")


class SecurityGroupDescription(TypedDict):
    Description: str
    GroupName: str
    GroupId: str
    IpPermissions: List[dict]
    IpPermissionsEgress: List[dict]
    VpcId: str
    Tags: List[dict]


class DescribeResponse(TypedDict):
    SecurityGroups: List[SecurityGroupDescription]
    NextMarker: str


def on_create():
    """Function to execute when creating a new custom resource

    Args:

    Returns:
        result (json): status
    """

    logger.info({"status": "create resource not needed for vpc custom resource"})

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

    logger.info({"status": "update resource not needed for vpc custom resource"})

    return {"Status": "SUCCESS"}


def is_update_complete():
    logger.info({"status": "calling is_update_complete"})
    return {"IsComplete": True}


def on_delete(vpc_id: str, physical_resource_id: str):
    """Function to execute when deleting the custom resource"""
    logger.info({"status": "deleting vpc custom resource"})

    nfs_sgs = []
    try:

        describe_sgs_response: DescribeResponse = ec2_client.describe_security_groups(
            Filters=[{"Name": "vpc-id", "Values": [vpc_id]}]
        )

        if (
            len(describe_sgs_response.get("SecurityGroups", [])) <= 1
            and describe_sgs_response.get("SecurityGroups", [])[0]["GroupName"]
            == "default"
        ):
            return {"Status": "SUCCESS"}

        for sg in describe_sgs_response.get("SecurityGroups", []):
            if sg["IpPermissions"]:
                ec2_client.revoke_security_group_ingress(
                    GroupId=sg["GroupId"], IpPermissions=[*sg["IpPermissions"]]
                )
            if sg["IpPermissionsEgress"]:
                ec2_client.revoke_security_group_egress(
                    GroupId=sg["GroupId"], IpPermissions=[*sg["IpPermissionsEgress"]]
                )
            if sg["GroupName"] != "default":
                if "nfs" in sg["GroupName"] and "inbound" in sg["GroupName"]:
                    nfs_sgs.append(sg)
                    pass
                else:
                    ec2_client.delete_security_group(GroupId=sg.get("GroupId"))

            logger.info({"status": f"deleted sg: {sg}"})

        # delete nfs inbound sg at the end
        for nfs_sg in nfs_sgs:
            ec2_client.delete_security_group(GroupId=nfs_sg.get("GroupId"))
            logger.info({"status": f"deleted nsf inbound sg: {nfs_sg}"})

    except Exception as e:
        logger.exception({"status": "failed to delete sgs", "exception": e})
        return {
            "Status": "FAILED",
            "PhysicalResourceId": physical_resource_id,
            "Reason": f"{e}",
        }
    return {"Status": "SUCCESS"}


def is_delete_complete(vpc_id: str):
    logger.info({"status": "calling is_delete_complete"})
    resp = on_delete(vpc_id, "")
    if resp.get("Status") == "SUCCESS":
        return {"IsComplete": True}
    return {"IsComplete": False}


def on_event_handler(event, context):
    logger.info(event)
    vpc_id: str = event.get("ResourceProperties", {}).get("vpc_id")
    physical_resource_id = event.get("PhysicalResourceId")

    request_type = event["RequestType"]
    if request_type == "Create":
        return on_create()
    if request_type == "Update":
        return on_update()
    if request_type == "Delete":
        return on_delete(vpc_id, physical_resource_id)
    raise Exception(f"Invalid request type: {request_type}")


def is_complete_handler(event, context):
    logger.info(event)
    vpc_id: str = event.get("ResourceProperties", {}).get("vpc_id")
    request_type = event["RequestType"]

    if request_type == "Create":
        return is_create_complete()
    if request_type == "Update":
        return is_update_complete()
    if request_type == "Delete":
        return is_delete_complete(vpc_id)
    raise Exception(f"Invalid request type: {request_type}")
