from aws_cdk import (
    aws_iam as iam,
)
from constructs import Construct
from stacks.sagemaker.constructs.custom_resources import CustomResource


class EfsCustomResource(CustomResource):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        fs_id: str,
    ) -> None:
        super().__init__(
            scope,
            construct_id,
            properties={
                "fs_id": fs_id,
            },
            lambda_file_name="efs_custom_resource",
            iam_policy=iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "elasticfilesystem:DescribeFileSystems",
                    "elasticfilesystem:DeleteFileSystem",
                    "elasticfilesystem:DescribeMountTargets",
                    "elasticfilesystem:DeleteMountTarget",
                ],
                resources=["*"],
            ),
        )
