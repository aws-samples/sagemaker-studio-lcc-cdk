from aws_cdk import (
    aws_iam as iam,
    aws_lambda as lambda_,
    aws_logs as logs,
)
import aws_cdk as cdk
from aws_cdk.custom_resources import Provider
from constructs import Construct
import os
from typing import Dict
from stacks.sagemaker.constructs.custom_resources import CustomResource


class VpcCustomResource(CustomResource):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        vpc_id: str,
        **kwargs,
    ) -> None:
        super().__init__(
            scope,
            construct_id,
            properties={
                "vpc_id": vpc_id,
            },
            lambda_file_name="vpc_custom_resource",
            iam_policy=iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "ec2:RevokeSecurityGroupIngress",
                    "ec2:RevokeSecurityGroupEgress",
                    "ec2:DeleteSecurityGroup",
                    "ec2:DeleteVpc",
                    "ec2:DescribeSecurityGroups",
                    "ec2:DescribeVpcs",
                    "elasticfilesystem:DescribeFileSystems",
                ],
                resources=["*"],
            ),
        )
