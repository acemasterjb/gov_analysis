from graphql import DocumentNode
from gql import gql


def proposals(
    space_id: str, limit: int, order_direction: str = "desc", skip: int = 0
) -> DocumentNode:
    query_params = """proposals(
        first: {limit}
        skip: {skip}
        orderBy: "created"
        orderDirection: {order_direction}
        where: {where_clause}
    )"""
    query_body = """{
        id
        created
        choices
        snapshot
        state
        author
        scores
        scores_total
        network
        space {
            id
            name
        }
    }"""

    where_clause = 'space: "{space_id}"'.format(space_id=space_id)
    where_clause = "".join(["{", where_clause, "}"])

    query_params = query_params.format(
        limit=limit,
        order_direction=order_direction,
        skip=skip,
        where_clause=where_clause,
    )
    query = "".join(["query{", query_params, query_body, "}"])

    return gql(query)


def votes(proposal_id: str) -> DocumentNode:
    query_params = """votes(
        orderBy: "created"
        orderDirection: desc
        where: {where_clause}
    )
    """
    query_body = """{
        id
        voter
        choice
        created
        vp
        proposal {
            id
            scores
            scores_total
            state
            space {
                id
                name
            }
            type
            created
            choices
            snapshot
            network
        }
    }
    """

    where_clause = 'proposal: "{proposal_id}"'.format(proposal_id=proposal_id)
    where_clause = "".join(["{", where_clause, "}"])

    query_params = query_params.format(where_clause=where_clause)
    query = "".join(["query{", query_params, query_body, "}"])

    return gql(query)
