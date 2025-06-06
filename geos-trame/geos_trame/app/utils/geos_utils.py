def group_name_ref_array_to_list( group_name_ref_array: str ) -> list[ str ] | None:
    """Convert GEOS type groupNameRef_array to a list of string.

    Example: "{ test1, test2 }" becomes ["test1", "test2"]
    """
    if ( not group_name_ref_array or not group_name_ref_array.strip().startswith( '{' )
         or not group_name_ref_array.strip().endswith( '}' ) ):
        return None

    stripped = group_name_ref_array.strip().strip( '{}' )
    return [ item.strip() for item in stripped.split( ',' ) if item.strip() ]
