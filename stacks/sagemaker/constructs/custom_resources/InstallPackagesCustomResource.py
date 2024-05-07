from aws_cdk import (
    aws_iam as iam,
)
from constructs import Construct
from stacks.sagemaker.constructs.custom_resources import CustomResource


class InstallPackagesCustomResource(CustomResource):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        domain_id: str,
    ) -> None:
        super().__init__(
            scope,
            construct_id,
            properties={
                "domain_id": domain_id,
                "package_lifecycle_config": f"{domain_id}-package-lifecycle-config",
            },
            lambda_file_name="lcc_install_packages_lambda",
            iam_policy=iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "sagemaker:CreateStudioLifecycleConfig",
                    "sagemaker:DeleteStudioLifecycleConfig",
                    "sagemaker:Describe*",
                    "sagemaker:List*",
                    "sagemaker:UpdateDomain",
                ],
                resources=["*"],
            ),
        )
