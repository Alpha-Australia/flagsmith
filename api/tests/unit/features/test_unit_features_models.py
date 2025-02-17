from datetime import timedelta

import pytest
from django.utils import timezone

from features.models import Feature, FeatureState

now = timezone.now()
yesterday = now - timedelta(days=1)
tomorrow = now + timedelta(days=1)


def test_feature_state_get_environment_flags_queryset_returns_only_latest_versions(
    feature, environment
):
    # Given
    feature_state_v1 = FeatureState.objects.get(
        feature=feature, environment=environment, feature_segment=None, identity=None
    )

    feature_state_v2 = feature_state_v1.clone(
        env=environment, live_from=timezone.now(), version=2
    )
    feature_state_v1.clone(env=environment, as_draft=True)  # draft feature state

    # When
    feature_states = FeatureState.get_environment_flags_queryset(
        environment_id=environment.id
    )

    # Then
    assert feature_states.count() == 1
    assert feature_states.first() == feature_state_v2


def test_project_hide_disabled_flags_have_no_effect_on_feature_state_get_environment_flags_queryset(
    environment, project
):
    # Given
    project.hide_disabled_flags = True
    project.save()
    # two flags - one disable on enabled
    Feature.objects.create(default_enabled=False, name="disable_flag", project=project)
    Feature.objects.create(default_enabled=True, name="enabled_flag", project=project)

    # When
    feature_states = FeatureState.get_environment_flags_queryset(
        environment_id=environment.id
    )
    # Then
    assert feature_states.count() == 2


def test_feature_states_get_environment_flags_queryset_filter_using_feature_name(
    environment, project
):
    # Given
    flag_1_name = "flag_1"
    Feature.objects.create(default_enabled=True, name=flag_1_name, project=project)
    Feature.objects.create(default_enabled=True, name="flag_2", project=project)

    # When
    feature_states = FeatureState.get_environment_flags_queryset(
        environment_id=environment.id, feature_name=flag_1_name
    )

    # Then
    assert feature_states.count() == 1
    assert feature_states.first().feature.name == "flag_1"


@pytest.mark.parametrize(
    "feature_state_version_generator",
    (
        (None, None, False),
        (2, None, True),
        (None, 2, False),
        (2, 3, False),
        (3, 2, True),
    ),
    indirect=True,
)
def test_feature_state_gt_operator_for_versions(feature_state_version_generator):
    first, second, expected_result = feature_state_version_generator
    assert (first > second) == expected_result


@pytest.mark.parametrize(
    "version, live_from, expected_is_live",
    (
        (1, yesterday, True),
        (None, None, False),
        (None, yesterday, False),
        (None, tomorrow, False),
        (1, tomorrow, False),
    ),
)
def test_feature_state_is_live(version, live_from, expected_is_live):
    assert (
        FeatureState(version=version, live_from=live_from).is_live == expected_is_live
    )


def test_creating_a_feature_with_defaults_does_not_set_defaults_if_disabled(
    project, environment
):
    # Given
    project.prevent_flag_defaults = True
    project.save()

    default_state = True
    default_value = "default"

    feature = Feature(
        project=project,
        name="test_flag_defaults",
        initial_value=default_value,
        default_enabled=default_state,
    )

    # When
    feature.save()

    # Then
    feature_state = FeatureState.objects.get(feature=feature, environment=environment)
    assert feature_state.enabled is False
    assert feature_state.get_feature_state_value() is None
