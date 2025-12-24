import json
import os


class SuggestDecomposition:

    def __init__( self, cluster_name, n_unknowns, job_type='cpu' ):

        # return ["P4: 1x22", "P4: 2x11"]
        with open( f'{os.getenv("TRAME_DIR")}/assets/cluster.json', 'r' ) as file:
            all_cluster = json.load( file )
        self.selected_cluster = list( filter( lambda d: d.get( 'name' ) == cluster_name,
                                              all_cluster ) )
        self.n_unknowns = n_unknowns
        self.job_type = job_type

    # @property
    # def selected_cluster(self):
    #     return self.selected_cluster

    @staticmethod
    def compute( n_unknowns,
                 memory_per_unknown_bytes,
                 node_memory_gb,
                 cores_per_node,
                 min_unknowns_per_rank=10000,
                 strong_scaling=True ):
        """
        Suggests node/rank distribution for a cluster computation.
        
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

        return {
            'nodes': n_nodes,
            'ranks_per_node': ranks_per_node,
            'total_ranks': n_nodes * ranks_per_node,
            'unknowns_per_rank': n_unknowns // ( n_nodes * ranks_per_node )
        }

    def to_list( self ):

        if self.job_type == 'cpu':  #make it an enum
            sd = SuggestDecomposition.compute( self.n_unknowns, 64, self.selected_cluster[ 'mem_per_node' ],
                                               self.selected_cluster[ 'cpu' ][ 'per_node' ] )
        # elif job_type == 'gpu':
        # selected_cluster['n_nodes']*selected_cluster['gpu']['per_node']

        return [
            f"{self.selected_cluster['name']}: {sd['nodes']} x {sd['ranks_per_node']}",
            f"{self.selected_cluster['name']}: {sd['nodes'] * 2} x {sd['ranks_per_node'] // 2}"
        ]
