import pytest

from rlberry.envs.classic_control import MountainCar
from rlberry.envs.classic_control import Acrobot
from rlberry.envs.finite import Chain
from rlberry.envs.finite import GridWorld
from rlberry.envs.benchmarks.ball_exploration import PBall2D, SimplePBallND
from rlberry.rendering import RenderInterface
from rlberry.rendering import RenderInterface2D


classes = [
    Acrobot,
    MountainCar,
    GridWorld,
    Chain,
    PBall2D,
    SimplePBallND
]


@pytest.mark.parametrize("ModelClass", classes)
def test_instantiation(ModelClass):
    env = ModelClass()

    if isinstance(env, RenderInterface):
        env.disable_rendering()
        assert not env.is_render_enabled()
        env.enable_rendering()
        assert env.is_render_enabled()


@pytest.mark.parametrize("ModelClass", classes)
def test_render2d_interface(ModelClass):
    env = ModelClass()
    env._disable_screen = True       # don't create window

    if isinstance(env, RenderInterface2D):
        env.enable_rendering()

        if env.is_online():
            for ep in range(2):
                state = env.reset()
                for ii in range(50):
                    assert env.observation_space.contains(state)
                    action = env.action_space.sample()
                    next_s, reward, done, info = env.step(action)
                    state = next_s
                env.render()
            env.clear_render_buffer()
