import time

import gymnasium as gym
import numpy as np

from stable_baselines3 import A2C
from stable_baselines3.common.vec_env import DummyVecEnv, SubprocVecEnv
from stable_baselines3.common.utils import set_random_seed
from stable_baselines3.common.evaluation import evaluate_policy
from stable_baselines3.common.env_util import make_vec_env

##todo Multiprocessing RL Training

# todo To multiprocess RL training, we will just have to wrap the Gym env into a `SubprocVecEnv` object, that will take care of synchronising the processes. The idea is that each process will run an indepedent instance of the Gym env.

# todo For that, we need an additional utility function, `make_env`, that will instantiate the environments and make sure they are different (using different random seed).

from typing import Callable


def make_env(env_id: str, rank: int, seed: int = 0) -> Callable:
    """
    Utility function for multiprocessed env.

    :param env_id: (str) the environment ID
    :param num_env: (int) the number of environment you wish to have in subprocesses
    :param seed: (int) the inital seed for RNG
    :param rank: (int) index of the subprocess
    :return: (Callable)
    """

    def _init() -> gym.Env:
        env = gym.make(env_id)
        env.reset(seed=seed + rank)
        return env

    set_random_seed(seed)
    return _init


# todo The number of parallel process used is defined by the num_cpu variable.

# todo Because we use vectorized environment (SubprocVecEnv), the actions sent to the wrapped env must be an array (one action per process). Also, observations, rewards and dones are arrays.

env_id = "CartPole-v1"
num_cpu = 4  # Number of processes to use
# Create the vectorized environment
env = SubprocVecEnv([make_env(env_id, i) for i in range(num_cpu)])

model = A2C("MlpPolicy", env, verbose=0)

# todo Stable-Baselines3 provides you with make_vec_env() helper which does exactly the previous steps for you:

# By default, we use a DummyVecEnv as it is usually faster (cf doc)
vec_env = make_vec_env(env_id, n_envs=num_cpu)

model = A2C("MlpPolicy", vec_env, verbose=0)


# Let's evaluate the un-trained agent, this should be a random agent.

# We create a separate environment for evaluation
eval_env = gym.make(env_id)

# Random Agent, before training
mean_reward, std_reward = evaluate_policy(model, eval_env, n_eval_episodes=10)
print(f"Mean reward: {mean_reward} +/- {std_reward:.2f}")


# bold text## Multiprocess VS Single Process Training

# Here, we will compare time taken using one vs 4 processes, it should take ~30s in total.

n_timesteps = 25000

# Multiprocessed RL Training
start_time = time.time()
model.learn(n_timesteps)
total_time_multi = time.time() - start_time

print(
    f"Took {total_time_multi:.2f}s for multiprocessed version - {n_timesteps / total_time_multi:.2f} FPS"
)

# Single Process RL Training
single_process_model = A2C("MlpPolicy", env_id, verbose=0)

start_time = time.time()
single_process_model.learn(n_timesteps)
total_time_single = time.time() - start_time

print(
    f"Took {total_time_single:.2f}s for single process version - {n_timesteps / total_time_single:.2f} FPS"
)

print(
    "Multiprocessed training is {:.2f}x faster!".format(
        total_time_single / total_time_multi
    )
)

# Evaluate the trained agent
mean_reward, std_reward = evaluate_policy(model, eval_env, n_eval_episodes=10)
print(f"Mean reward: {mean_reward} +/- {std_reward:.2f}")
