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


class CustomResource(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        properties: Dict,
        lambda_file_name: str,
        iam_policy: iam.PolicyStatement,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        on_event_lambda_fn = lambda_.Function(
            self,
            "EventLambda",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="index.on_event_handler",
            code=lambda_.Code.from_asset(
                os.path.join(os.getcwd(), "src", "lambda", lambda_file_name)
            ),
            initial_policy=[iam_policy],
            timeout=cdk.Duration.minutes(3),
        )
        is_complete_lambda_fn = lambda_.Function(
            self,
            "CompleteLambda",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="index.is_complete_handler",
            code=lambda_.Code.from_asset(
                os.path.join(os.getcwd(), "src", "lambda", lambda_file_name)
            ),
            initial_policy=[iam_policy],
            timeout=cdk.Duration.minutes(10),
        )

        provider = Provider(
            self,
            "Provider",
            on_event_handler=on_event_lambda_fn,
            is_complete_handler=is_complete_lambda_fn,
            total_timeout=cdk.Duration.minutes(10),
            log_retention=logs.RetentionDays.ONE_DAY,
        )

        cdk.CustomResource(
            self,
            "CustomResource",
            service_token=provider.service_token,
            properties={
                **properties,
                "on_event_lambda_version": on_event_lambda_fn.current_version.version,
                "is_complete_lambda_version": is_complete_lambda_fn.current_version.version,
            },
        )
