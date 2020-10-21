import pytest
from rlberry.rendering import BaseRenderInterface
from rlberry.rendering import RenderInterface2D
from rlberry.rendering.render2d import _activate_debug_mode

from rlberry.envs.interface import OnlineModel, GenerativeModel

from rlberry.envs.classic_control import MountainCar 

from rlberry.envs.finite import GridWorld
from rlberry.envs.finite import Chain

from rlberry.envs.toy_exploration import PBall2D
from rlberry.envs.toy_exploration import SimplePBallND


classes = [
            MountainCar,
            GridWorld,
            Chain,
            PBall2D,
            SimplePBallND
          ]

@pytest.mark.parametrize("ModelClass", classes)
def test_instantiation(ModelClass):
    env = ModelClass()

    if isinstance(env, BaseRenderInterface):
        env.disable_rendering()
        assert not env.is_render_enabled()
        env.enable_rendering()
        assert env.is_render_enabled()


@pytest.mark.parametrize("ModelClass", classes)
def test_render2d_interface(ModelClass):
    _activate_debug_mode() # don't create window

    env = ModelClass()

    if isinstance(env, RenderInterface2D):
        env.enable_rendering()

        if isinstance(env, OnlineModel):
            for ep in range(2):
                state = env.reset()
                for ii in range(50):
                    assert env.observation_space.contains(state)
                    action = env.action_space.sample()
                    next_s, reward, done, info = env.step(action)
                    state = next_s 
                env.render()
            env.clear_render_buffer()