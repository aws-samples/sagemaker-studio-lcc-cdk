from aws_cdk import aws_iam as iam
from constructs import Construct


class StudioUserRole(iam.Role):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        domain_name: str,
    ) -> None:
        super().__init__(
            scope,
            construct_id,
            role_name=f"{domain_name}DataScientistRole",
            assumed_by=iam.CompositePrincipal(
                iam.ServicePrincipal("sagemaker.amazonaws.com")
            ),
            inline_policies={
                "StudioUserInlinePolicy": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=["s3:List*", "s3:HeadBucket"],
                            resources=["*"],
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=["iam:PassRole"],
                            resources=["arn:aws:iam::*:role/*"],
                            conditions={
                                "StringEquals": {
                                    "iam:PassedToService": "sagemaker.amazonaws.com"
                                }
                            },
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "sagemaker:Delete*",
                                "sagemaker:Stop*",
                                "sagemaker:Update*",
                                "sagemaker:Start*",
                                "sagemaker:Create*",
                                "sagemaker:DisassociateTrialComponent",
                                "sagemaker:AssociateTrialComponent",
                                "sagemaker:BatchPutMetrics",
                            ],
                            resources=["*"],
                            conditions={
                                "StringEquals": {
                                    "aws:PrincipalTag/workspace_id": "${sagemaker:ResourceTag/workspace_id}"
                                }
                            },
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=["sagemaker:CreatePresignedDomainUrl"],
                            resources=["*"],
                            conditions={
                                "StringEquals": {
                                    "sagemaker:ResourceTag/workspace_id": "${aws:PrincipalTag/workspace_id}"
                                }
                            },
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "sagemaker:AddTags",
                                "sagemaker:InvokeEndpoint",
                                "sagemaker:CreateApp",
                                "sagemaker:Describe*",
                                "sagemaker:List*",
                            ],
                            resources=["*"],
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "kms:Get*",
                                "kms:Decrypt",
                                "kms:List*",
                                "kms:ReEncryptFrom",
                                "kms:GenerateDataKey",
                                "kms:Encrypt",
                                "kms:ReEncryptTo",
                                "kms:Describe*",
                            ],
                            resources=["*"],
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "ec2:Describe*",
                                "ec2:CreateNetworkInterface",
                                "ec2:CreateNetworkInterfacePermission",
                                "ec2:CreateVpcEndpoint",
                                "ec2:DeleteNetworkInterface",
                                "ec2:DeleteNetworkInterfacePermission",
                                "ec2:AttachClassicLinkVpc",
                                "ec2:AcceptVpcPeeringConnection",
                                "ec2:DescribeVpcAttribute",
                                "ec2:AssociateVpcCidrBlock",
                            ],
                            resources=["*"],
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "sns:CreateTopic",
                                "sns:DeleteTopic",
                                "sns:ListTopics",
                                "sns:Subscribe",
                                "sns:TagResource",
                            ],
                            resources=["*"],
                        ),
                    ]
                )
            },
        )
