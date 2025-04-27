from dataclasses import dataclass
from enum import Enum
from typing import Optional, Annotated

from PIL import Image
from dataclass_wizard import JSONWizard, JSONPyWizard, json_key
from mixin.json import JSONSerializableMixin

class WeaponType(Enum):
    """Weapon types in NIKKE Arena"""
    RL = "Rocket Launcher"  # Rocket Launcher
    SR = "Sniper Rifle"  # Sniper Rifle
    SG = "Shotgun"  # Shotgun
    AR = "Assault Rifle"  # Assault Rifle
    SMG = "Submachine Gun"  # Submachine Gun
    MG = "Machine Gun"  # Machine Gun


class ChargeSpeed(Enum):
    """Charge speed tiers for team compositions"""
    EXTREME_SPEED = "Full charge with 2 shots"  # 2 shots from 1s charge RL
    HIGH_SPEED = "Full charge with 3 shots"  # 3 shots from 1s charge RL
    MEDIUM_SPEED = "Full charge with 4 shots"  # 4 shots from 1s charge RL
    SG4 = "Full charge with 4 SG shots"  # 4 shots from fast-charge SG
    SG5 = "Full charge with 5 SG shots"  # 5 shots from fast-charge SG
    SG6 = "Full charge with 6 SG shots"  # 6 shots from fast-charge SG
    SG7 = "Full charge with 7 SG shots"  # 7 shots from fast-charge SG
    SG8 = "Full charge with 8 SG shots"  # 8 shots from fast-charge SG


class SkillType(Enum):
    """Types of skills that can generate charge"""
    DAMAGE = "Damage"
    HEAL = "Heal"
    BUFF = "Buff"
    DEBUFF = "Debuff"
    SPECIAL = "Special"  # For skills with unique mechanics

@dataclass
class ChargeValues:
    """Charge values for a character at different charge speeds"""
    extreme_speed: float  # Full charge with 2 shots / 4 SG shots
    high_speed: float  # Full charge with 3 shots / 6 SG shots
    sg5: float  # Full charge with 5 SG shots
    sg7: float  # Full charge with 7 SG shots

    def get_value(self, speed: ChargeSpeed) -> float:
        """Get charge value for a specific charge speed"""
        if speed == ChargeSpeed.EXTREME_SPEED or speed == ChargeSpeed.SG4:
            return self.extreme_speed
        elif speed == ChargeSpeed.HIGH_SPEED or speed == ChargeSpeed.SG6:
            return self.high_speed
        elif speed == ChargeSpeed.SG5:
            return self.sg5
        elif speed == ChargeSpeed.SG7:
            return self.sg7
        elif speed == ChargeSpeed.MEDIUM_SPEED or speed == ChargeSpeed.SG8:
            # For medium speed, we could calculate a value or use a fixed one
            # For simplicity, we'll return high_speed / 1.5
            return self.high_speed / 1.5
        return 0.0

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


