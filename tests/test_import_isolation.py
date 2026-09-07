"""battle_core must stay pure: no rendering or ML dependencies, no reaching into other app packages."""

import importlib
import pkgutil
import sys

import battle_core

FORBIDDEN = {"pygame", "torch", "numpy", "game", "rl", "dialogue"}


def test_battle_core_imports_nothing_forbidden():
    # Import every submodule of battle_core, then inspect what landed in sys.modules.
    for mod in pkgutil.iter_modules(battle_core.__path__, prefix="battle_core."):
        importlib.import_module(mod.name)

    leaked = {name.split(".")[0] for name in sys.modules} & FORBIDDEN
    assert not leaked, f"battle_core pulled in forbidden modules: {leaked}"
