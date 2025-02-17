import logging
import typing

from flag_engine.identities.builders import (
    build_identity_dict,
    build_identity_model,
)

from environments.identities.models import Identity
from environments.models import Environment, Webhook
from features.models import Feature, FeatureState
from task_processor.decorators import register_task_handler
from users.models import FFAdminUser
from webhooks.webhooks import WebhookEventType, call_environment_webhooks

logger = logging.getLogger(__name__)


@register_task_handler()
def call_environment_webhook_for_feature_state_change(
    feature_id: int,
    environment_api_key: str,
    identity_id: typing.Union[id, str],
    identity_identifier: str,
    changed_by_user_id: int,
    timestamp: str,
    new_enabled_state: bool = None,
    new_value: typing.Union[bool, int, str] = None,
    previous_enabled_state: bool = None,
    previous_value: typing.Union[bool, int, str] = None,
):
    environment = Environment.objects.get(api_key=environment_api_key)
    if not environment.webhooks.filter(enabled=True).exists():
        logger.debug(
            "No webhooks exist for environment %d. Not calling webhooks.",
            environment.id,
        )
        return

    feature = Feature.objects.get(id=feature_id)
    changed_by = FFAdminUser.objects.get(id=changed_by_user_id)

    data = {
        "changed_by": changed_by.email,
        "timestamp": timestamp,
        "new_state": None,
    }

    if previous_enabled_state is not None and previous_value is not None:
        data["previous_state"] = Webhook.generate_webhook_feature_state_data(
            feature,
            environment,
            identity_id,
            identity_identifier,
            previous_enabled_state,
            previous_value,
        )

    if new_value is not None and new_value is not None:
        data["new_state"] = Webhook.generate_webhook_feature_state_data(
            feature,
            environment,
            identity_id,
            identity_identifier,
            new_enabled_state,
            new_value,
        )

    event_type = (
        WebhookEventType.FLAG_DELETED
        if new_enabled_state is None
        else WebhookEventType.FLAG_UPDATED
    )

    call_environment_webhooks(environment, data, event_type=event_type)


@register_task_handler()
def sync_identity_document_features(identity_uuid: str):
    identity = build_identity_model(
        Identity.dynamo_wrapper.get_item_from_uuid(identity_uuid)
    )

    valid_feature_names = set(
        FeatureState.objects.filter(
            environment__api_key=identity.environment_api_key
        ).values_list("feature__name", flat=True)
    )

    identity.prune_features(valid_feature_names)
    Identity.dynamo_wrapper.put_item(build_identity_dict(identity))
