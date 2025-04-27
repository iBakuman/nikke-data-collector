from dataclasses import dataclass
from typing import Optional, Annotated

from PIL import Image
from dataclass_wizard import JSONWizard, JSONPyWizard, json_key

from collector.mixin import JSONSerializableMixin
from collector.models import WeaponType, ChargeValues


@dataclass
class Character(JSONWizard, JSONSerializableMixin):
    class _(JSONPyWizard.Meta):
        skip_defaults = True

    id: str = None
    name: str = None
    position: int = None
    weapon_type: Optional[WeaponType] = None
    charge_values: Optional[ChargeValues] = None
    image: Annotated[Optional[Image.Image], json_key("excluded", dump=False)] = None
