from stealthbench.configs.camoufox import CamoufoxConfig
from stealthbench.core.config import Config


def test_label_is_camoufox():
    assert CamoufoxConfig().label == "camoufox"


def test_satisfies_config_protocol():
    assert isinstance(CamoufoxConfig(), Config)


def test_sdk_import_is_lazy_not_module_level():
    # build() imports Camoufox lazily (mirror configs/uc.py). The module must not
    # bind the SDK at import time, so importing the config never pulls the browser.
    import stealthbench.configs.camoufox as mod

    assert not hasattr(mod, "Camoufox")
