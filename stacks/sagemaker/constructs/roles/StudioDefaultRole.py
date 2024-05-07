from aws_cdk import aws_iam as iam
from constructs import Construct


class StudioDefaultRole(iam.Role):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        domain_name: str,
    ) -> None:

        super().__init__(
            scope,
            construct_id,
            role_name=f"{domain_name}DefaultRole",
            assumed_by=iam.CompositePrincipal(
                iam.ServicePrincipal("sagemaker.amazonaws.com")
            ),
            inline_policies={
                "StudioDefaultInlinePolicy": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=[
                                "kms:Get*",
                                "kms:Decrypt",
                                "kms:List*",
                                "kms:ReEncryptFrom",
                                "kms:Encrypt",
                                "kms:ReEncryptTo",
                                "kms:Describe",
                                "kms:GenerateDataKey",
                            ],
                            resources=["*"],
                            effect=iam.Effect.ALLOW,
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "cloudwatch:Put*",
                                "cloudwatch:Get*",
                                "cloudwatch:List*",
                                "cloudwatch:DescribeAlarms",
                                "logs:Put*",
                                "logs:Get*",
                                "logs:List*",
                                "logs:CreateLogGroup",
                                "logs:CreateLogStream",
                                "logs:ListLogDeliveries",
                                "logs:Describe*",
                                "logs:CreateLogDelivery",
                                "logs:PutResourcePolicy",
                                "logs:UpdateLogDelivery",
                            ],
                            resources=["*"],
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "sagemaker:Describe*",
                                "sagemaker:GetSearchSuggestions",
                                "sagemaker:List*",
                                "sagemaker:*App",
                                "sagemaker:Search",
                                "sagemaker:RenderUiTemplate",
                                "sagemaker:BatchGetMetrics",
                                "ec2:DescribeDhcpOptions",
                                "ec2:DescribeNetworkInterfaces",
                                "ec2:DescribeRouteTables",
                                "ec2:DescribeSecurityGroups",
                                "ec2:DescribeSubnets",
                                "ec2:DescribeVpcEndpoints",
                                "ec2:DescribeVpcs",
                                "iam:ListRoles",
                            ],
                            resources=["*"],
                        ),
                    ]
                )
            },
        )
