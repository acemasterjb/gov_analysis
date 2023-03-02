#!/usr/bin/env python
# coding: utf-8

# # Plutocracy Report
# 
# This article aims to analyze the top 60 Decentralised Autonomous Organizations (DAOs), ranked by [treasury size](https://deepdao.io/) to determine the impact of large token holders on their governance.
# 
# For this, we create a report based on on-chain data about proposals and voters. This report will focus on three proposals and assess their _decisiveness of whales_ metric, representing how governance decisions are affected once whale votes are discounted. For an analysis of the decisiveness of whales for all 60 DAOs, check out our [extensive report here](https://acemasterjb.github.io/gov_analysis/extensive_analysis).

# In[1]:


# sets up the pynb environment
import os
import sys

from IPython.display import HTML
import pandas as pd

module_path = os.path.abspath(os.path.join(".."))
if module_path not in sys.path:
    sys.path.append(module_path)

from libs.data_processing.statistics import (
    get_number_of_whales_to_all_voters_ratio,
    get_score_comparisons,
)


# Our data sources include DeepDAO and Snapshot, both of which specialize in providing data on DAO governance. We also use Coingecko to find market data for DAO governance tokens.
# 
# Using this data, we compile two spreadsheets that act as the local database for this analysis. Each spreadsheet contains each voter's choice and voting power for up to the last one hundred proposals in each DAO. **One spreadsheet filters out "whales"** which, in the context of this analysis, are voters that have voting power **at or above the 95th percentile of voting power for that proposal**.

# In[2]:


plutocracy_report_data = pd.read_excel(
    "../plutocracy_report.xlsx", sheet_name=None, engine="openpyxl"
)
plutocracy_report_data_filtered = pd.read_excel(
    "../plutocracy_report_filtered.xlsx", sheet_name=None, engine="openpyxl"
)


# We then ask the following question: **How many whales have voted up to the last 100 proposals for each of the DAOs we analyzed?** Voting power for each of these DAOs varies by the type of [voting strategy](https://docs.snapshot.org/strategies/what-is-a-strategy) outlined in their respective Snapshot spaces.
# 
# However, to keep this analysis simple, we assume the common `erc-20-balance` strategy and define the cost of voting power (`vp`) as the US dollar value of a DAO's native token at the time of the proposal.

# In[3]:


pd.set_option("display.max_rows", int(1e3))
score_differences = get_score_comparisons(
    plutocracy_report_data, plutocracy_report_data_filtered
)


# In[15]:


score_differences_dfs = dict()

initial_series_data = {
    organization: 0
    for organization in plutocracy_report_data.keys()
}
changed_outcome_proportions = pd.Series(initial_series_data, name="changed outcomes %")

for score_difference in score_differences:
    for organization, data in score_difference.items():
        data: dict[str, list] = data
        items = data.items()
        score_differences_dfs[organization] = pd.DataFrame(
            [score_data for _, score_data in items],
            index=pd.Index(
                ([proposal_id for proposal_id, _ in items]), name="Proposal ID"
            ),
            columns=[
                "score_differences",
                "whale_vp_proportion",
                "total_vp",
                "outcome_changed",
                "outcome_old",
                "outcome_new"
            ],
        ).astype({"total_vp": "float64"}, copy=False
        ).sort_values(["whale_vp_proportion","total_vp"], ascending=False)

        try:
            changed_outcome_proportions[organization] = score_differences_dfs[organization]["outcome_changed"].value_counts(normalize=True)[True]
        except KeyError:
            changed_outcome_proportions[organization] = 0

        space_id = plutocracy_report_data[organization].iloc[0]["proposal_space_id"]

        score_differences_dfs[organization]["total_vp"] = score_differences_dfs[
            organization
        ]["total_vp"].apply("{:.9f}".format)

        score_differences_dfs[organization].index = score_differences_dfs[organization].index.to_series().apply(
            lambda s: f'<a href=http://snapshot.org/#/{space_id}/proposal/{s} rel="noopener noreferrer" target="_blank">{s[0:9]}</a>'
        )
        score_differences_dfs[organization].style.format({"whale_vp_proportion": "{:.2%}".format})

changed_outcome_proportions_raw = changed_outcome_proportions.copy()
changed_outcome_proportions = changed_outcome_proportions.apply(
    lambda proportion: "{:.2%}".format(proportion)
)


# In[5]:


voting_ratios = get_number_of_whales_to_all_voters_ratio(
    plutocracy_report_data, plutocracy_report_data_filtered
)


# In[6]:


dao_overview = pd.DataFrame(
    [list(result.items())[0][1] for result in voting_ratios],
    columns=[
        "# of whales",
        "all voters",
    ],
)
dao_overview.set_index(
    pd.Index([list(result.items())[0][0] for result in voting_ratios], name="DAO"),
    inplace=True
)

dao_overview.insert(2, changed_outcome_proportions.name, changed_outcome_proportions)
dao_overview


# Here we see that there are quite a few proposals whose outcomes would've changed if whales were not involved, in this analysis, we take a look at some of these cases in Uniswap, Decentraland and Curve Finance in particular.

# ---

# Next, we take a look at how governance decisions are affected once whale votes are discounted. We do so by comparing the scores of each proposal and checking whether the outcome of the proposal is changed when whales are filtered out.
# 
# We check whether a proposal's outcome changes by checking if the largest vote choice score changes after filtering out whales. Specifically, in python we do the following:
# ```python
# has_changed_outcome = not unfiltered_winning_choice_index == filtered_winning_choice_index
# ```

# ## Uniswap

# ### Proportion of Outcomes Changed

# In[7]:


print(f"{changed_outcome_proportions['Uniswap']} of Uniswap's proposal outcomes change after fitering out whale voting power.")


# ### Proposal Analysis

# The outcome of the proposal to add a Liquidity Mining Manager (LMM) for the [Optimism-Uniswap Liquidity Mining Program](https://snapshot.org/#/uniswap/proposal/0xfd3d3807bd2a6eda1327c311b83de235061d39ff1bdfb616c9f9b0d367c3ac2c) changes after removing whales.
# 
# If not for whale intervention, "Overnight Finance" would have been chosen as the LMM. Instead, "DeFiEdge" was selected. From the data, we see that without whale intervention, DeFiEdge would've had ~2,708,025 fewer votes out of the total ~2,728,492 voting power on this proposal. That is ~99.3% of voting power allocated for this proposal directed to choosing "DeFiEdge".

# In[8]:


propsal_choices = plutocracy_report_data['Uniswap'][plutocracy_report_data['Uniswap']['proposal_id'] == '0xfd3d3807bd2a6eda1327c311b83de235061d39ff1bdfb616c9f9b0d367c3ac2c'].iloc[0]['proposal_choices']
mask = score_differences_dfs["Uniswap"].index.to_series().apply(
    lambda s: "0xfd3d380" in s,
)
proposal_score_differences = score_differences_dfs["Uniswap"].loc[mask]["score_differences"][0]
proposal_scores = plutocracy_report_data['Uniswap'][plutocracy_report_data['Uniswap']['proposal_id'] == '0xfd3d3807bd2a6eda1327c311b83de235061d39ff1bdfb616c9f9b0d367c3ac2c'].iloc[0]['proposal_scores']

pd.DataFrame(
    {choice: [score, score_diff] for choice, score, score_diff in zip(eval(propsal_choices), eval(proposal_scores), proposal_score_differences)},
    index=["Scores", "Score Differences"],
)


# ## Decentraland
# Let's now look at Decentraland, where the largest holders regularly participate in governance.

# ### Proportion of Outcomes Changed

# In[9]:


print(f"{changed_outcome_proportions['Decentraland']} of Decentraland's proposal outcomes change after fitering out whale voting power.")


# ### Proposal Analysis

# For example, [this proposal](https://snapshot.org/#/snapshot.dcl.eth/proposal/0x7f6fed8c7645d1b793526564104e4f79864a9e30ae284029f752b6297478b4f5) to set a duration period for the tenure of Decentraland DAO committee members saw 99.9% of voting power attributed to whales, with 94.85% of proposal voting power allocated to voting for the proposal not to pass.

# In[10]:


propsal_choices = plutocracy_report_data['Decentraland'][plutocracy_report_data['Decentraland']['proposal_id'] == '0x7f6fed8c7645d1b793526564104e4f79864a9e30ae284029f752b6297478b4f5'].iloc[0]['proposal_choices']
mask = score_differences_dfs["Decentraland"].index.to_series().apply(
    lambda s: "0x7f6fed8" in s,
)
proposal_score_differences = score_differences_dfs["Decentraland"].loc[mask]["score_differences"][0]
proposal_scores = plutocracy_report_data['Decentraland'][plutocracy_report_data['Decentraland']['proposal_id'] == '0x7f6fed8c7645d1b793526564104e4f79864a9e30ae284029f752b6297478b4f5'].iloc[0]['proposal_scores']

pd.DataFrame(
    {choice: [score, score_diff] for choice, score, score_diff in zip(eval(propsal_choices), eval(proposal_scores), proposal_score_differences)},
    index=["Scores", "Score Differences"],
)


# This is clearly a case of large holders voting to support their own interests. Once whales are filtered out of the votes (which would've given existing and future committee members set terms, making the roles more democratic) the proposal would've passed, albeit, with very low voting power by comparison.

# ## Curve Finance

# ### Proportion of Outcomes Changed

# In[11]:


print(f"{changed_outcome_proportions['Curve Finance']} of Curve Finance's proposal outcomes change after fitering out whale voting power.")


# ### Proposal Analysis

# One proposal which would've passed if not for whale intervention was this proposal to [add the XSTUSD-3CRV pair](https://snapshot.org/#/curve.eth/proposal/0x0eb23ea0b877666ad3ddcd0d7da0114acdfe5ae6390b5628b7509f4338022db5) to Curve's [gauge](https://resources.curve.fi/reward-gauges/understanding-gauges) [controller](https://curve.readthedocs.io/dao-gauges.html#the-gauge-controller) to accrue CRV for liquidity providers of XSTUSD-3CRV.
# 
# XSTUSD is a stablecoin deployed on Polkadot and Kusama that's backed by a synthetic token called XOR ([Sora](https://sora.org/)'s native token). The [governance discussion](https://gov.curve.fi/t/proposal-to-add-xstusd-3crv-to-the-gauge-controller/2998/15) about the vote was particularly interesting.
# 
# ![](./res/curve_governance_shenanigans.png)
# 
# What stands out is XSTUSD's comparison with LUNA/UST. This proposal was created before the LUNA/UST [depegging disaster](https://rekt.news/luna-rekt/), but even before that, [quite a](https://twitter.com/runekek/status/1478166276979793922) [few people](https://twitter.com/FreddieRaynolds/status/1463960623402913797) had their concerns about it. So I checked out the first 16 accounts which showed really strong support for this proposal, and almost [every single](https://gov.curve.fi/u/meowtopia) [one was](https://gov.curve.fi/u/LiquidityKing) [created within](https://gov.curve.fi/u/Ryandotrrr) 2 days of the proposal's forum post. Clear signs of governance forum shenanigans, executed to raise hype for a proposal.

# In[12]:


propsal_choices = plutocracy_report_data['Curve Finance'][plutocracy_report_data['Curve Finance']['proposal_id'] == '0x0eb23ea0b877666ad3ddcd0d7da0114acdfe5ae6390b5628b7509f4338022db5'].iloc[0]['proposal_choices']
mask = score_differences_dfs["Curve Finance"].index.to_series().apply(
    lambda s: "0x0eb23ea" in s,
)
proposal_score_differences = score_differences_dfs["Curve Finance"].loc[mask]["score_differences"][0]
proposal_scores = plutocracy_report_data['Curve Finance'][plutocracy_report_data['Curve Finance']['proposal_id'] == '0x0eb23ea0b877666ad3ddcd0d7da0114acdfe5ae6390b5628b7509f4338022db5'].iloc[0]['proposal_scores']

pd.DataFrame(
    {choice: [score, score_diff] for choice, score, score_diff in zip(eval(propsal_choices), eval(proposal_scores), proposal_score_differences)},
    index=["Scores", "Score Differences"],
)


# Just over 4% of voting power for this proposal was allocated by whales to vote "Yes" (which is just over half the total voting power allocated to the "Yes" choice for this proposal), whereas ~89% of whale voting power was allocated to voting "NO" (~97% of total voting power for this choice).

# It's important to highlight that whales are also sensible and not always "evil", which I would classify as entities that promote proposals that are detrimental to the DAO for their own interests. It's a good thing that CRV whales didn't have an incentive to pass this proposal as well.

# Just over 10% of whale voting power for this proposal was allocated to voting "Aye" on this proposal (~27% of voting power allocated to the "Aye" choice came from whales). Whereas ~45% of voting power from whales was allocated to the "Nay" choice (~73% of whale voting power allocated to "Nay").
