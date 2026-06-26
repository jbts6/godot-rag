"""Dialogue Manager addon configuration."""

from rag.addon_configs import AddonConfig, register

register(AddonConfig(
    name="dialogue_manager",
    smoke_queries=[
        ("DialogueManager", "dialogue_manager"),
    ],
))
