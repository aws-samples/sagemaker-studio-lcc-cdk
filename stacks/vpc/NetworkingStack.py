import aws_cdk as cdk
from aws_cdk import (
    aws_ec2 as ec2,
)
from constructs import Construct
from stacks.sagemaker.constructs import (
    CustomResources,
)
from cdk_nag import (
    NagSuppressions,
    NagPackSuppression,
)


class NetworkingStack(cdk.Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        vpc = ec2.Vpc(
            self,
            "PrimaryVPC",
            ip_addresses=ec2.IpAddresses.cidr("10.0.0.0/16"),
            max_azs=3,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    name="Public", subnet_type=ec2.SubnetType.PUBLIC, cidr_mask=26
                ),
            ],
            enable_dns_hostnames=True,
            enable_dns_support=True,
            nat_gateways=1,
            flow_logs={
                "FlowLogsCW": ec2.FlowLogOptions(
                    destination=ec2.FlowLogDestination.to_cloud_watch_logs()
                )
            },
        )

        # setup security group to be used for sagemaker studio domain
        security_group = ec2.SecurityGroup(
            self,
            "SecurityGroup",
            vpc=vpc,
            description="Security Group for SageMaker Studio Notebook, Training Job and Hosting Endpoint",
        )

        security_group.add_ingress_rule(
            ec2.Peer.ipv4(vpc.vpc_cidr_block),
            ec2.Port.tcp(443),
            "Allow TCP ingress from VPC",
        )

        security_group.add_ingress_rule(
            ec2.Peer.ipv4(vpc.vpc_cidr_block),
            ec2.Port.tcp(2049),
            "Allow TCP traffic to EFS",
        )

        self.security_group_id = security_group.security_group_id
        self.vpc_id = vpc.vpc_id
        self.subnet_ids = [subnet.subnet_id for subnet in vpc.private_subnets]

        CustomResources.VpcCustomResource(
            self,
            "vpc-custom-resource-construct",
            vpc_id=vpc.vpc_id,
        )

        # add cdk nag stack suppression here
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
