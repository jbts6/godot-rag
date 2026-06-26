"""LimboAI addon configuration."""

from rag.addon_configs import AddonConfig, register

register(AddonConfig(
    name="limboai",
    smoke_queries=[
        ("BehaviorTree", "limboai"),
    ],
))
