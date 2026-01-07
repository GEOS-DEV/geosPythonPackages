from geos.trame.app.io.ssh_tools import SimulationConstant


class SuggestDecomposition:

    def __init__( self, selected_cluster: SimulationConstant, n_unknowns: int, job_type: str = 'cpu' ) -> None:
        """Initialize the decomposition hinter for HPC."""
        self.selected_cluster: SimulationConstant = selected_cluster
        self.n_unknowns: int = n_unknowns
        self.job_type: str = job_type  #TODO should be an enum
        self.sd: list[ dict ] = []

    @staticmethod
    def compute( n_unknowns: int,
                 memory_per_unknown_bytes: int,
                 node_memory_gb: int,
                 cores_per_node: int,
                 min_unknowns_per_rank: int = 10000,
                 strong_scaling: bool = True ) -> list[ dict ]:
        """Suggests node/rank distribution for a cluster computation.

        Parameters:
        - n_unknowns: total number of unknowns
        - memory_per_unknown_bytes: estimated memory per unknown
        - node_memory_gb: available memory per node
        - cores_per_node: cores available per node
        - min_unknowns_per_rank: minimum for efficiency
        - strong_scaling: True if problem size is fixed

        Note:
            - 10,000-100,000 unknowns per rank is often a sweet spot for many PDE solvers
            - Use power-of-2 decompositions when possible (helps with communication patterns)
            - For 3D problems, try to maintain cubic subdomains (minimizes surface-to-volume ratio, reducing communication)
            - Don't oversubscribe: avoid using more ranks than provide parallel efficiency

        """
        # Memory constraint
        node_memory_bytes = node_memory_gb * 1e9
        max_unknowns_per_node = int( 0.8 * node_memory_bytes / memory_per_unknown_bytes )

        # Compute minimum nodes needed
        min_nodes = max( 1, ( n_unknowns + max_unknowns_per_node - 1 ) // max_unknowns_per_node )

        # Determine ranks per node
        unknowns_per_node = n_unknowns // min_nodes
        unknowns_per_rank = max( min_unknowns_per_rank, unknowns_per_node // cores_per_node )

        # Calculate total ranks needed
        n_ranks = max( 1, n_unknowns // unknowns_per_rank )

        # Distribute across nodes
        ranks_per_node = min( cores_per_node, ( n_ranks + min_nodes - 1 ) // min_nodes )
        n_nodes = ( n_ranks + ranks_per_node - 1 ) // ranks_per_node

        return [
            {
                'id':1,
                'nodes': n_nodes,
                'ranks_per_node': ranks_per_node,
                'total_ranks': n_nodes * ranks_per_node,
                'unknowns_per_rank': n_unknowns // ( n_nodes * ranks_per_node )
            },
            {
                'id':2,
                'nodes': n_nodes * 2,
                'ranks_per_node': ranks_per_node // 2,
                'total_ranks': n_nodes * ranks_per_node,
                'unknowns_per_rank': n_unknowns // ( n_nodes * ranks_per_node )
            },
        ]

    def get_sd( self ) -> list[ dict ]:
        """Get the suggested decomposition popoulated."""
        if self.job_type == 'cpu' and self.selected_cluster:  #make it an enum
            self.sd = SuggestDecomposition.compute( self.n_unknowns, 64, self.selected_cluster.mem_per_node,
                                                    self.selected_cluster.cores_per_node )
            self.sd = [{**item,'label': f"{self.selected_cluster.name} : {item['nodes']} x {item['ranks_per_node']}"} for item in self.sd ]
        else:
            self.sd = [
                {
                    'id': -1,
                    'label':'No: 0x0',
                    'nodes': 0,
                    'ranks_per_node': 0,
                    'total_ranks': 0,
                    'unknowns_per_rank': 0
                },
            ]
        # elif job_type == 'gpu':
        # selected_cluster['n_nodes']*selected_cluster['gpu']['per_node']

        return self.sd

    # def to_list( self ) -> list[ str ]:
    #     """Pretty printer to list of string for display in UI."""
    #     sd = self.get_sd()
    #     return [ f"{self.selected_cluster.name} : {sd_item['nodes']} x {sd_item['ranks_per_node']}" for sd_item in sd ]
