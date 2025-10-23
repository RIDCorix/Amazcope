from any_registries import Registry

dependency_registry = Registry(key=lambda dep: dep.name).auto_load("*/config/*.py")
