from aws_cdk import (
    aws_iam as iam,
)
from constructs import Construct
from stacks.sagemaker.constructs.custom_resources import CustomResource


class StudioAppCustomResource(CustomResource):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        user_profile_name: str,
        domain_id: str,
    ) -> None:
        super().__init__(
            scope,
            construct_id,
            properties={"user_profile_name": user_profile_name, "domain_id": domain_id},
            lambda_file_name="studio_app_custom_resource",
            iam_policy=iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "sagemaker:ListApps",
                    "sagemaker:DeleteApp",
                    "sagemaker:DeleteUserProfile",
                ],
                resources=["*"],
            ),
        )
