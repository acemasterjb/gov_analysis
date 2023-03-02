#!/usr/bin/env python
# coding: utf-8

# # Plutocracy Report
# 
# This is an extensive analysis of the top 60 Decentralised Autonomous Organizations (DAOs), ranked by [treasury size](https://deepdao.io/) to determine the impact of large token holders on their governance.
# 
# For this, we create a report based on on-chain data about proposals and voters. This report lists sixty DAOs and assesses their _decisiveness_ of whales_ metric, representing how governance decisions are affected once whale votes are discounted.

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


# In[4]:


score_differences_dfs: dict[str, pd.DataFrame] = dict()

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
# 
# ### Filtered Proposals Analysis

# In[7]:


HTML(score_differences_dfs["Uniswap"].drop("score_differences", axis=1).to_html(render_links=True, escape=False))


# ### Proportion of Outcomes Changed

# In[8]:


print(f"{changed_outcome_proportions['Uniswap']} of Uniswap's proposal outcomes change after fitering out whale voting power.")


# ### Proposal Analysis

# The outcome of the proposal to add a Liquidity Mining Manager (LMM) for the [Optimism-Uniswap Liquidity Mining Program](https://snapshot.org/#/uniswap/proposal/0xfd3d3807bd2a6eda1327c311b83de235061d39ff1bdfb616c9f9b0d367c3ac2c) changes after removing whales.
# 
# If not for whale intervention, "Overnight Finance" would have been chosen as the LMM. Instead, "DeFiEdge" was selected. From the data, we see that without whale intervention, DeFiEdge would've had ~2,708,025 fewer votes out of the total ~2,728,492 voting power on this proposal. That is ~99.3% of voting power allocated for this proposal directed to choosing "DeFiEdge".

# In[9]:


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


# One highly contentious proposal whose outcome did not change after filtering out whales was [this temperature check to choose which Eth <> BNB bridge to use for Uniswap v3 governance](https://snapshot.org/#/uniswap/proposal/0x6b8df360fdf73085b21fdf5eef9f85916fbde95621a3d454cb20fbe545ffc852). We see that even for the least popular choices, whales still contributed to the majority of the votes. LayerZero", the runner-up, received ~37.7% of the total whale voting power. By comparison, "Wormhole" received ~51.1%.

# In[10]:


propsal_choices = plutocracy_report_data['Uniswap'][plutocracy_report_data['Uniswap']['proposal_id'] == '0x6b8df360fdf73085b21fdf5eef9f85916fbde95621a3d454cb20fbe545ffc852'].iloc[0]['proposal_choices']
mask = score_differences_dfs["Uniswap"].index.to_series().apply(
    lambda s: "0x6b8df36" in s,
)
proposal_score_differences = score_differences_dfs["Uniswap"].loc[mask]["score_differences"][0]
proposal_scores = plutocracy_report_data['Uniswap'][plutocracy_report_data['Uniswap']['proposal_id'] == '0x6b8df360fdf73085b21fdf5eef9f85916fbde95621a3d454cb20fbe545ffc852'].iloc[0]['proposal_scores']

pd.DataFrame(
    {choice: [score, score_diff] for choice, score, score_diff in zip(eval(propsal_choices), eval(proposal_scores), proposal_score_differences)},
    index=["Scores", "Score Differences"],
)


# ## ENS
# 
# ### Filtered Proposal Outcome Analysis

# In[11]:


HTML(score_differences_dfs["ENS"].astype({"total_vp": "float64"}, copy=False).sort_values(["whale_vp_proportion", "total_vp"], ascending=False).drop("score_differences", axis=1).to_html(render_links=True, escape=False))


# ### Proportion of Outcomes Changed

# In[12]:


print(f"{changed_outcome_proportions['ENS']} of ENS' proposal outcomes change after fitering out whale voting power.")


# ## Lido
# ### Filtered Proposal Analysis

# In[13]:


HTML(score_differences_dfs["Lido"].astype({"total_vp": "float64"}, copy=False).sort_values(["whale_vp_proportion", "total_vp"], ascending=False).drop("score_differences", axis=1).to_html(render_links=True, escape=False))


# ### Proportion of Outcomes Changed

# In[14]:


print(f"{changed_outcome_proportions['Lido']} of Lido's proposal outcomes change after fitering out whale voting power.")


# [This proposal](https://snapshot.org/#/lido-snapshot.eth/proposal/0xcbf534335fe07c046caa933e1623ac38bfb3d1890ab825264a0b47415cf7799b) to [expand the oracle set and quorum](https://mainnet.lido.fi/#/lido-dao/0x442af784a788a5bd6f42a01ebe9f287a871243fb/) of Lido DAO oracle node operators was passed on 16/12/22, onboarded 4 new oracle node operators, and set the quorum to 5/9 identical oracle reports to be accepted by the protocol.
# 
# Had whales not intervened, Option 1 to onboard 6 additional oracles and set the quorum to 6/11, would've passed.

# In[15]:


propsal_choices = plutocracy_report_data['Lido'][plutocracy_report_data['Lido']['proposal_id'] == '0xcbf534335fe07c046caa933e1623ac38bfb3d1890ab825264a0b47415cf7799b'].iloc[0]['proposal_choices']
mask = score_differences_dfs["Lido"].index.to_series().apply(
    lambda s: "0xcbf5343" in s,
)
proposal_score_differences = score_differences_dfs["Lido"].loc[mask]["score_differences"][0]
proposal_scores = plutocracy_report_data['Lido'][plutocracy_report_data['Lido']['proposal_id'] == '0xcbf534335fe07c046caa933e1623ac38bfb3d1890ab825264a0b47415cf7799b'].iloc[0]['proposal_scores']

pd.DataFrame(
    {choice: [score, score_diff] for choice, score, score_diff in zip(eval(propsal_choices), eval(proposal_scores), proposal_score_differences)},
    index=["Scores", "Score Differences"],
)


# Here we see whale participation was consistent for all choices for this proposal. In fact, ~99.982% of voting power allocated to this proposal came from whales that voted for each of the outcomes. The second outcome alone had ~99.980% of the voting power allocated to this proposal and so removing it would make a huge impression on the outcome.
# 
# Voting power allocated to this proposal would be low without whale intervention: (only ~9277.7397 LDO would be allocated to this proposal). However, the community would still vote for adding more oracles that [broadcasts the chain state from the beacon chain to the execution layer](https://docs.lido.fi/guides/oracle-operator-manual) of ETH 2.0.

# ## Frax
# ### Filtered Proposal Outcome Analysis

# In[16]:


HTML(score_differences_dfs["Frax"].astype({"total_vp": "float64"}, copy=False).sort_values("whale_vp_proportion", ascending=False).drop("score_differences", axis=1).to_html(render_links=True, escape=False))


# ### Proportion of Outcomes Changed

# In[17]:


print(f"{changed_outcome_proportions['Frax']} of Frax's proposal outcomes change after fitering out whale voting power.")


# ## Decentraland
# Let's now look at Decentraland, where the largest holders regularly participate in governance and dominate voting.
# 
# ### Filtered Proposals Analysis

# In[18]:


HTML(score_differences_dfs["Decentraland"].astype({"total_vp": "float64"}, copy=False).sort_values(["whale_vp_proportion", "total_vp"], ascending=False).drop("score_differences", axis=1).to_html(render_links=True, escape=False))


# ### Proportion of Outcomes Changed

# In[19]:


print(f"{changed_outcome_proportions['Decentraland']} of Decentraland's proposal outcomes change after fitering out whale voting power.")


# For example, [this proposal](https://snapshot.org/#/snapshot.dcl.eth/proposal/0x7f6fed8c7645d1b793526564104e4f79864a9e30ae284029f752b6297478b4f5) to set a duration period for the tenure of Decentraland DAO committee members saw 99.9% of voting power attributed to whales, with 94.85% of proposal voting power allocated to voting for the proposal not to pass.

# In[20]:


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
# 
# ### Filtered Proposals Analysis

# In[21]:


HTML(score_differences_dfs["Curve Finance"].astype({"total_vp": "float64"}, copy=False).drop("score_differences", axis=1).sort_values(["whale_vp_proportion", "total_vp"], ascending=False).to_html(render_links=True, escape=False))


# ### Proportion of Outcomes Changed

# In[22]:


print(f"{changed_outcome_proportions['Curve Finance']} of Curve Finance's proposal outcomes change after fitering out whale voting power.")


# One proposal which would've passed if not for whale intervention was this proposal to [add the XSTUSD-3CRV pair](https://snapshot.org/#/curve.eth/proposal/0x0eb23ea0b877666ad3ddcd0d7da0114acdfe5ae6390b5628b7509f4338022db5) to Curve's [gauge](https://resources.curve.fi/reward-gauges/understanding-gauges) [controller](https://curve.readthedocs.io/dao-gauges.html#the-gauge-controller) to accrue CRV for liquidity providers of XSTUSD-3CRV.
# 
# XSTUSD is a stablecoin deployed on Polkadot and Kusama that's backed by a synthetic token called XOR ([Sora](https://sora.org/)'s native token). The [governance discussion](https://gov.curve.fi/t/proposal-to-add-xstusd-3crv-to-the-gauge-controller/2998/15) about the vote was particularly interesting.
# 
# ![](./res/curve_governance_shenanigans.png)
# 
# What stands out is XSTUSD's comparison with LUNA/UST. This proposal was created before the LUNA/UST [depegging disaster](https://rekt.news/luna-rekt/), but even before that, [quite a](https://twitter.com/runekek/status/1478166276979793922) [few people](https://twitter.com/FreddieRaynolds/status/1463960623402913797) had their concerns about it. So I checked out the first 16 accounts which showed really strong support for this proposal, and almost [every single](https://gov.curve.fi/u/meowtopia) [one was](https://gov.curve.fi/u/LiquidityKing) [created within](https://gov.curve.fi/u/Ryandotrrr) 2 days of the proposal's forum post. Clear signs of governance forum shenanigans, executed to raise hype for a proposal.

# In[23]:


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

# ## Radicle
# ### Filtered Proposals Analysis

# In[24]:


HTML(score_differences_dfs["Radicle"].astype({"total_vp": "float64"}, copy=False).drop("score_differences", axis=1).sort_values(["whale_vp_proportion", "total_vp"], ascending=False).to_html(render_links=True, escape=False))


# ### Proportion of Outcomes Changed

# In[25]:


print(f"{changed_outcome_proportions['Radicle']} of Radicle's proposal outcomes change after fitering out whale voting power.")


# One such proposal was the one to [distribute RAD remaining](https://snapshot.org/#/gov.radicle.eth/proposal/QmepPgXwo5q9GipZFKa32rnxaYoo3LrfRqduinftbU3L3S) following a Liquidity Bootsrapping (LBP) round conducted in February '21. This leftover RAD was proposed to be redistributed to participants of the LBP, i.e. people who bought RAD in this period from the Balancer LBP for RAD tokens.

# In[26]:


propsal_choices = plutocracy_report_data['Radicle'][plutocracy_report_data['Radicle']['proposal_id'] == 'QmepPgXwo5q9GipZFKa32rnxaYoo3LrfRqduinftbU3L3S'].iloc[0]['proposal_choices']
mask = score_differences_dfs["Radicle"].index.to_series().apply(
    lambda s: "QmepPgXwo" in s,
)
proposal_score_differences = score_differences_dfs["Radicle"].loc[mask]["score_differences"][0]
proposal_scores = plutocracy_report_data['Radicle'][plutocracy_report_data['Radicle']['proposal_id'] == 'QmepPgXwo5q9GipZFKa32rnxaYoo3LrfRqduinftbU3L3S'].iloc[0]['proposal_scores']

pd.DataFrame(
    {choice: [score, score_diff] for choice, score, score_diff in zip(eval(propsal_choices), eval(proposal_scores), proposal_score_differences)},
    index=["Scores", "Score Differences"],
)


# Just over 10% of whale voting power for this proposal was allocated to voting "Aye" on this proposal (~27% of voting power allocated to the "Aye" choice came from whales). Whereas ~45% of voting power from whales was allocated to the "Nay" choice (~73% of whale voting power allocated to "Nay").

# ## Gitcoin
# ### Filtered Proposals Analysis

# In[27]:


HTML(score_differences_dfs["Gitcoin"].astype({"total_vp": "float64"}, copy=False).drop("score_differences", axis=1).sort_values(["whale_vp_proportion", "total_vp"], ascending=False).to_html(render_links=True, escape=False))


# ### Proportion of Outcomes Changed

# In[28]:


print(f"{changed_outcome_proportions['Gitcoin']} of Gitcoin's proposal outcomes change after fitering out whale voting power.")


# ## Euler
# ### Filtered Proposals Analysis

# In[29]:


HTML(score_differences_dfs["Euler"].astype({"total_vp": "float64"}, copy=False).drop("score_differences", axis=1).sort_values(["whale_vp_proportion", "total_vp"], ascending=False).to_html(render_links=True, escape=False))


# ### Proportion of Outcomes Changed

# In[30]:


print(f"{changed_outcome_proportions['Euler']} of Euler's proposal outcomes change after fitering out whale voting power.")


# ## Gearbox
# ### Filtered Proposals Analysis

# In[31]:


HTML(score_differences_dfs["Gearbox"].astype({"total_vp": "float64"}, copy=False).drop("score_differences", axis=1).sort_values(["whale_vp_proportion", "total_vp"], ascending=False).to_html(render_links=True, escape=False))


# ### Proportion of Outcomes Changed

# In[32]:


print(f"{changed_outcome_proportions['Gearbox']} of Gearbox's proposal outcomes change after fitering out whale voting power.")


# ## SuperRare
# ### Filtered Proposals Analysis

# In[33]:


HTML(score_differences_dfs["SuperRare DAO"].astype({"total_vp": "float64"}, copy=False).drop("score_differences", axis=1).sort_values(["whale_vp_proportion", "total_vp"], ascending=False).to_html(render_links=True, escape=False))


# ### Proportion of Outcomes Changed

# In[34]:


print(f"{changed_outcome_proportions['SuperRare DAO']} of SuperRare DAO's proposal outcomes change after fitering out whale voting power.")


# ## Hop
# ### Filtered Proposals Analysis

# In[35]:


HTML(score_differences_dfs["Hop"].astype({"total_vp": "float64"}, copy=False).drop("score_differences", axis=1).sort_values(["whale_vp_proportion", "total_vp"], ascending=False).to_html(render_links=True, escape=False))


# ### Proportion of Outcomes Changed

# In[36]:


print(f"{changed_outcome_proportions['Hop']} of Hop's proposal outcomes change after fitering out whale voting power.")


# ## JPEG’d
# ### Filtered Proposals Analysis

# In[37]:


HTML(score_differences_dfs["JPEG’d"].astype({"total_vp": "float64"}, copy=False).drop("score_differences", axis=1).sort_values(["whale_vp_proportion", "total_vp"], ascending=False).to_html(render_links=True, escape=False))


# ### Proportion of Outcomes Changed

# In[38]:


print(f"{changed_outcome_proportions['JPEG’d']} of JPEG’d's proposal outcomes change after fitering out whale voting power.")


# ## Merit Circle
# ### Filtered Proposals Analysis

# In[39]:


HTML(score_differences_dfs["Merit Circle"].astype({"total_vp": "float64"}, copy=False).drop("score_differences", axis=1).sort_values(["whale_vp_proportion", "total_vp"], ascending=False).to_html(render_links=True, escape=False))


# ### Proportion of Outcomes Changed

# In[40]:


print(f"{changed_outcome_proportions['Merit Circle']} of Merit Circle's proposal outcomes change after fitering out whale voting power.")


# ## Aavegotchi
# ### Filtered Proposals Analysis

# In[41]:


HTML(score_differences_dfs["Aavegotchi"].astype({"total_vp": "float64"}, copy=False).drop("score_differences", axis=1).sort_values(["whale_vp_proportion", "total_vp"], ascending=False).to_html(render_links=True, escape=False))


# ### Proportion of Outcomes Changed

# In[42]:


print(f"{changed_outcome_proportions['Aavegotchi']} of Aavegotchi's proposal outcomes change after fitering out whale voting power.")


# ## Rook
# ### Filtered Proposals Analysis

# In[43]:


HTML(score_differences_dfs["Rook"].astype({"total_vp": "float64"}, copy=False).drop("score_differences", axis=1).sort_values(["whale_vp_proportion", "total_vp"], ascending=False).to_html(render_links=True, escape=False))


# ### Proportion of Outcomes Changed

# In[44]:


print(f"{changed_outcome_proportions['Rook']} of Rook's proposal outcomes change after fitering out whale voting power.")


# ## ApeCoin DAO
# ### Filtered Proposals Analysis

# In[45]:


HTML(score_differences_dfs["ApeCoin DAO"].astype({"total_vp": "float64"}, copy=False).drop("score_differences", axis=1).sort_values(["whale_vp_proportion", "total_vp"], ascending=False).to_html(render_links=True, escape=False))


# ### Proportion of Outcomes Changed

# In[46]:


print(f"{changed_outcome_proportions['ApeCoin DAO']} of ApeCoin DAO's proposal outcomes change after fitering out whale voting power.")


# ## Klima DAO
# ### Filtered Proposals Analysis

# In[47]:


HTML(score_differences_dfs["Klima DAO"].astype({"total_vp": "float64"}, copy=False).drop("score_differences", axis=1).sort_values(["whale_vp_proportion", "total_vp"], ascending=False).to_html(render_links=True, escape=False))


# ### Proportion of Outcomes Changed

# In[48]:


print(f"{changed_outcome_proportions['Klima DAO']} of Klima DAO's proposal outcomes change after fitering out whale voting power.")


# ## Hector Network
# ### Filtered Proposals Analysis

# In[49]:


HTML(score_differences_dfs["Hector Network"].astype({"total_vp": "float64"}, copy=False).drop("score_differences", axis=1).sort_values(["whale_vp_proportion", "total_vp"], ascending=False).to_html(render_links=True, escape=False))


# ### Proportion of Outcomes Changed

# In[50]:


print(f"{changed_outcome_proportions['Hector Network']} of Hector Network's proposal outcomes change after fitering out whale voting power.")


# ## Vesta
# ### Filtered Proposals Analysis

# In[51]:


HTML(score_differences_dfs["Vesta"].astype({"total_vp": "float64"}, copy=False).drop("score_differences", axis=1).sort_values(["whale_vp_proportion", "total_vp"], ascending=False).to_html(render_links=True, escape=False))


# ### Filtered Proposals Analysis

# In[52]:


print(f"{changed_outcome_proportions['Vesta']} of Vesta's proposal outcomes change after fitering out whale voting power.")

