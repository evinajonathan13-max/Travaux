"""KTN:Li woven-domain experiment — RATISS topological quantification."""

from .fabric import generate_fabric, fabric_summary, FabricResult, WARP, WEFT, PX_BACKGROUND
from .topology import compute_persistence, p_sig_contrast

__all__ = [
    "generate_fabric", "fabric_summary", "FabricResult", "WARP", "WEFT",
    "PX_BACKGROUND", "compute_persistence", "p_sig_contrast",
]
