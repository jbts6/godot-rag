"""Godot Doctor addon configuration."""

from rag.addon_configs import AddonConfig, register

register(AddonConfig(
    name="doctor",
    smoke_queries=[
        ("verify_node_path", "doctor"),
    ],
))
