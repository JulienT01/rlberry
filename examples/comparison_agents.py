"""
=========================
Compare Bandit Algorithms
=========================

This example illustrate the use of compare_agents, a function that uses multiple-testing to assess whether trained agents are
statistically different or not.

Remark that in the case where two agents are not deemed statistically different it can mean either that they are as efficient,
or it can mean that there have not been enough fits to assess the variability of the agents.

"""

import numpy as np

from rlberry.manager.comparison import compare_agents
from rlberry.manager import AgentManager
from rlberry_research.envs.bandits import BernoulliBandit
from rlberry_research.agents.bandits import (
    IndexAgent,
    makeBoundedMOSSIndex,
    makeBoundedNPTSIndex,
    makeBoundedUCBIndex,
    makeETCIndex,
)

# Parameters of the problem
means = np.array([0.6, 0.6, 0.6, 0.9])  # means of the arms
A = len(means)
T = 2000  # Horizon
N = 50  # number of fits

# Construction of the experiment

env_ctor = BernoulliBandit
env_kwargs = {"p": means}


class UCBAgent(IndexAgent):
    name = "UCB"

    def __init__(self, env, **kwargs):
        index, _ = makeBoundedUCBIndex()
        IndexAgent.__init__(self, env, index, writer_extra="reward", **kwargs)


class ETCAgent(IndexAgent):
    name = "ETC"

    def __init__(self, env, m=20, **kwargs):
        index, _ = makeETCIndex(A, m)
        IndexAgent.__init__(
            self, env, index, writer_extra="action_and_reward", **kwargs
        )


class MOSSAgent(IndexAgent):
    name = "MOSS"

    def __init__(self, env, **kwargs):
        index, _ = makeBoundedMOSSIndex(T, A)
        IndexAgent.__init__(
            self, env, index, writer_extra="action_and_reward", **kwargs
        )


class NPTSAgent(IndexAgent):
    name = "NPTS"

    def __init__(self, env, **kwargs):
        index, tracker_params = makeBoundedNPTSIndex()
        IndexAgent.__init__(
            self,
            env,
            index,
            writer_extra="reward",
            tracker_params=tracker_params,
            **kwargs,
        )


Agents_class = [MOSSAgent, NPTSAgent, UCBAgent, ETCAgent]

managers = [
    AgentManager(
        Agent,
        train_env=(env_ctor, env_kwargs),
        fit_budget=T,
        parallelization="process",
        mp_context="fork",
        n_fit=N,
    )
    for Agent in Agents_class
]


for manager in managers:
    manager.fit()


def eval_function(manager, eval_budget=None, agent_id=0):
    df = manager.get_writer_data()[agent_id]
    return T * np.max(means) - np.sum(df.loc[df["tag"] == "reward", "value"])


print(
    compare_agents(managers, method="tukey_hsd", eval_function=eval_function, B=10_000)
)
