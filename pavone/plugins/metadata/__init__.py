"""
元数据提取器插件
"""

from .avbase_metadata import AvBaseMetadata
from .aventertainments_metadata import AvEntertainmentsMetadata
from .base import MetadataPlugin
from .c0930_metadata import C0930Metadata
from .caribbeancom_metadata import CaribbeancomMetadata
from .dahlia_metadata import DahliaMetadata
from .duga_metadata import DugaMetadata
from .faleno_metadata import FalenoMetadata
from .fanza_metadata import FanzaMetadata
from .fc2hub_metadata import Fc2HubMetadata
from .fc2ppvdb_metadata import Fc2PpvdbMetadata
from .gcolle_metadata import GcolleMetadata
from .getchu_metadata import GetchuMetadata
from .h0930_metadata import H0930Metadata
from .h4610_metadata import H4610Metadata
from .heydouga_metadata import HeydougaMetadata
from .heyzo_metadata import HeyzoMetadata
from .jav321_metadata import Jav321Metadata
from .javbus_metadata import JavbusMetadata
from .javfree_metadata import JavfreeMetadata
from .madouqu_metadata import MadouquMetadata
from .mgstage_metadata import MgstageMetadata
from .muramura_metadata import MuramuraMetadata
from .mywife_metadata import MyWifeMetadata
from .onepondo_metadata import OnePondoMetadata
from .pacopacomama_metadata import PacopacomamaMetadata
from .pcolle_metadata import PcolleMetadata
from .ppvdatabank_metadata import PPVDataBankMetadata
from .supfc2_metadata import SupFC2Metadata
from .tenmusume_metadata import TenMusumeMetadata
from .tokyohot_metadata import TokyoHotMetadata

# MissAV插件在missav_plugin.py中定义
# AV01插件在av01_plugin.py中定义
# av-league: ActorProvider only, no MovieMetadata implementation
# gfriends: ActorProvider only, no MovieMetadata implementation

__all__ = [
    "MetadataPlugin",
    "CaribbeancomMetadata",
    "OnePondoMetadata",
    "PPVDataBankMetadata",
    "SupFC2Metadata",
    "AvBaseMetadata",
    "AvEntertainmentsMetadata",
    "C0930Metadata",
    "DahliaMetadata",
    "DugaMetadata",
    "FalenoMetadata",
    "TenMusumeMetadata",
    "FanzaMetadata",
    "Fc2HubMetadata",
    "Fc2PpvdbMetadata",
    "GcolleMetadata",
    "GetchuMetadata",
    "H0930Metadata",
    "H4610Metadata",
    "HeydougaMetadata",
    "HeyzoMetadata",
    "Jav321Metadata",
    "JavbusMetadata",
    "JavfreeMetadata",
    "MadouquMetadata",
    "MgstageMetadata",
    "MuramuraMetadata",
    "MyWifeMetadata",
    "PacopacomamaMetadata",
    "PcolleMetadata",
    "TokyoHotMetadata",
]
