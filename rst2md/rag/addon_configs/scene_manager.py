"""Scene Manager addon configuration."""

from rag.addon_configs import AddonConfig, register

register(AddonConfig(
    name="scene_manager",
    smoke_queries=[
        ("change_scene", "scene_manager"),
        ("SceneManager", "scene_manager"),
        ("fade pattern", "scene_manager"),
    ],
    custom_doc_dirs=["docs_wiki"],
))
