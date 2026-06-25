from __future__ import annotations

from githelp.project_profiles.base import ProjectProfile
from githelp.project_profiles.generic import GenericProjectProfile
from githelp.project_profiles.mmore import MMoreProjectProfile


def create_project_profile(config: dict) -> ProjectProfile:
    profile_name = config.get("project_profile", "generic")

    if profile_name == "generic":
        return GenericProjectProfile()

    if profile_name == "mmore":
        return MMoreProjectProfile()

    raise ValueError(f"Unsupported project profile: {profile_name}")
