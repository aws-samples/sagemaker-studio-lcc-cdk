import aws_cdk as cdk
from aws_cdk import aws_sagemaker as sagemaker
from constructs import Construct
from cdk_nag import NagPackSuppression, NagSuppressions
from stacks.sagemaker.constructs import (
    Roles,
    CustomResources,
)
from typing import List


class SagemakerStudioStack(cdk.Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        domain_name: str,
        workspace_id: str,
        user_ids: List[str],
        vpc_id: str,
        subnet_ids: List[str],
        security_group_id: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        sagemaker_default_role = Roles.StudioDefaultRole(
            self, "sagemaker-default-role", domain_name=domain_name
        )

        domain = sagemaker.CfnDomain(
            self,
            "sagemaker-domain",
            domain_name=domain_name,
            auth_mode="IAM",
            app_network_access_type="VpcOnly",
            default_user_settings=sagemaker.CfnDomain.UserSettingsProperty(
                execution_role=sagemaker_default_role.role_arn,
                sharing_settings=sagemaker.CfnDomain.SharingSettingsProperty(),
            ),
            default_space_settings=sagemaker.CfnDomain.DefaultSpaceSettingsProperty(
                execution_role=sagemaker_default_role.role_arn
            ),
            subnet_ids=subnet_ids,
            vpc_id=vpc_id,
        )

        sagemaker_user_iam_role = Roles.StudioUserRole(
            scope=self,
            construct_id="sagemaker-role",
            domain_name=domain_name,
        )

        for user_id in user_ids:
            user_profile_name = f"{workspace_id}-{user_id.lower()}"

            profile = sagemaker.CfnUserProfile(
                self,
                user_profile_name,
                domain_id=domain.attr_domain_id,
                user_profile_name=user_profile_name,
                user_settings=sagemaker.CfnUserProfile.UserSettingsProperty(
                    security_groups=[security_group_id],
                    execution_role=sagemaker_user_iam_role.role_arn,
                ),
                tags=[
                    cdk.CfnTag(key="user_id", value=user_id),
                ],
            )

            CustomResources.StudioAppCustomResource(
                self,
                f"{user_profile_name}-studio-cr",
                user_profile_name=user_profile_name,
                domain_id=domain.attr_domain_id,
            ).node.add_dependency(profile)

        CustomResources.InstallPackagesCustomResource(
            self,
            "install-packages-construct",
            domain_id=domain.attr_domain_id,
        )

        CustomResources.ShutDownIdleKernelsCustomResource(
            self,
            "shut-down-idle-kernels-construct",
            domain_id=domain.attr_domain_id,
        )

        CustomResources.EfsCustomResource(
            self,
            "efs-custom-resource-construct",
            fs_id=domain.attr_home_efs_file_system_id,
        ).node.add_dependency(domain)

        cdk.Tags.of(self).add(key="workspace_id", value=workspace_id)

        NagSuppressions.add_stack_suppressions(
            stack=self,
            suppressions=[
                NagPackSuppression(
                    id="AwsSolutions-IAM4", reason="managed AWS policies allowed"
                ),
                NagPackSuppression(
                    id="AwsSolutions-IAM5", reason="wildcards permission allowed"
                ),
                NagPackSuppression(
                    id="AwsSolutions-L1", reason="cdk provisioned lambda"
                ),
                NagPackSuppression(
                    id="AwsSolutions-SF1", reason="cdk provisioned stepfunction"
                ),
                NagPackSuppression(
                    id="AwsSolutions-SF2", reason="cdk provisioned stepfunction"
                ),
            ],
        )
