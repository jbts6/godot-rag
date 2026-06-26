"""Godot State Charts addon configuration."""

from rag.addon_configs import AddonConfig, register

register(AddonConfig(
    name="statecharts",
    smoke_queries=[
        ("state machine", "statecharts"),
    ],
))
