import aws_cdk as cdk
from aws_cdk import Aspects
from cdk_nag import AwsSolutionsChecks

from stacks.vpc import NetworkingStack
from stacks.sagemaker import SagemakerStudioStack

app = cdk.App()
env = cdk.Environment(
    region=app.node.try_get_context("region"),
)

networking_stack = NetworkingStack(
    env=env,
    scope=app,
    construct_id="NetworkingStack",
)

SagemakerStudioStack(
    env=env,
    scope=app,
    construct_id="SageMakerStudioStack",
    domain_name="sagemaker-domain",
    vpc_id=networking_stack.vpc_id,
    subnet_ids=networking_stack.subnet_ids,
    security_group_id=networking_stack.security_group_id,
    workspace_id="project1",
    user_ids=[
        "user1",
        "user2",
        "user3",
    ],
)

Aspects.of(app).add(AwsSolutionsChecks(verbose=True))

app.synth()
