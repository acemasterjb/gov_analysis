from graphql import DocumentNode
from gql import dsl, gql


def votes(
    chain_id: str,
    proposal_ids: list[str],
    governance_ids: list[str],
    upper_limit: int,
    skip: int,
) -> DocumentNode:
    query_proposals_params = """proposals(
        proposalIds: {proposal_ids},
        chainId: "{chain_id}",
        governanceIds: {governance_ids}
    )
    """

    query_body_top = """{
        id
        title
        """

    query_votes_params = """votes(
            pagination: {pagination_clause}
        )
    """

    query_body_bottom = """{
            id
            voter{
                address
                ens
            }
            support
            weight
            reason
            transaction{
                block{
                    timestamp
                }
            }
        }
    }"""

    query_proposals_params = query_proposals_params.format(
        proposal_ids=proposal_ids, chain_id=chain_id, governance_ids=governance_ids
    ).replace("'", '"')
    query_votes_params = query_votes_params.format(
        pagination_clause={"limit": upper_limit, "offset": skip}
    ).replace("'", "")

    query = "".join(
        [
            "query{",
            query_proposals_params,
            query_body_top,
            query_votes_params,
            query_body_bottom,
            "}",
        ]
    )

    return gql(query)


def proposals(
    schema: dsl.DSLSchema,
    organization_ids: list[str],
    upper_limit: int,
    skip: int,
) -> DocumentNode:
    query = dsl.DSLQuery(
        schema.Query.governances(organizationIds=organization_ids).select(
            schema.Governance.id,
            schema.Governance.name,
            schema.Governance.chainId,
            schema.Governance.organization.select(
                schema.Organization.name,
                schema.Organization.id,
            ),
            schema.Governance.proposals(
                pagination={"limit": upper_limit, "offset": skip}
            ).select(
                schema.Proposal.id,
                schema.Proposal.title,
                schema.Proposal.start.select(
                    schema.Block.timestamp,
                ),
                schema.Proposal.end.select(
                    schema.Block.timestamp,
                ),
                schema.Proposal.eta,
                schema.Proposal.proposer.select(
                    schema.Account.id,
                    schema.Account.address,
                    schema.Account.ens,
                ),
                schema.Proposal.voteStats.select(
                    schema.VoteStat.support,
                    schema.VoteStat.weight,
                    schema.VoteStat.votes,
                    schema.VoteStat.percent,
                ),
            ),
        )
    )

    return dsl.dsl_gql(query)


def organizations(
    schema: dsl.DSLSchema,
    organization_names: list[str],
    upper_limit: int = 3000,
    skip: int = 0,
):
    query = dsl.DSLQuery(
        schema.Query.organizations(
            names=organization_names, pagination={"limit": upper_limit, "offset": skip}
        ).select(
            schema.Organization.id,
            schema.Organization.name,
            schema.Organization.governances.select(
                schema.Governance.contracts.select(
                    schema.Contracts.tokens.select(
                        schema.TokenContract.address,
                        schema.TokenContract.type,
                    )
                )
            ),
        )
    )

    return dsl.dsl_gql(query)
