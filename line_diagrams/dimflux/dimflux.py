from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import pandas as pd
from dim_flux.core.realizer import Realizer
from dim_flux.fca.lattice import cover_relations
from dim_flux.fdp.forces import ForceDirectedPlacement
from dim_flux.utils.variables import Variables

class DimFlux:
    '''
    Wrapper around the dim-flux PyPI package exposing the concepts, coordinates,
    and cover relations of the force-optimized lattice diagram.
    '''
    def __init__(
        self, cxt: Union[str, pd.DataFrame],
        w_rep: float = 100.0, w_att: float = 1.0, w_grav: float = 30.0,
        timeout_ms: Optional[int] = 60000,
    ) -> None:
        vars = Variables(cxt, {
            'plot_si_graph': False,
            'si_graph_annotations': False,
            'plot_initial_layout': False,
            'initial_layout_annotations': False,
            'plot_optimized_layout': False,
            'optimized_layout_annotations': False,
            'plot_individual_forces': False,
            'plot_combined_forces': False,
            'plot_gradients': False,
            'plot_origin': False,
        }, w_rep=w_rep, w_att=w_att, w_grav=w_grav, timeout_ms=timeout_ms)

        realizer = Realizer(vars)
        vars.base_vectors = realizer.base_vectors
        vars.coordinates = realizer.coordinates
        vars.lectic_order = realizer.lectic_order

        forces = ForceDirectedPlacement(vars)
        vars.coordinates = forces.coordinates

        Path('input.cxt').unlink(missing_ok=True)

        self.concepts: List[int] = list(vars.concepts)
        self.coordinates: Dict[int, Tuple[float, float]] = {
            c: tuple(vars.coordinates[c]) for c in self.concepts
        }
        self.cover_relations: set[Tuple[int, int]] = cover_relations(vars.lattice)
