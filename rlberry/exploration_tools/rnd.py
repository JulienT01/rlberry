import torch
import gym.spaces as spaces
from torch.nn import functional as F
from rlberry.exploration_tools.uncertainty_estimator \
    import UncertaintyEstimator
from rlberry.agents.utils.torch_models import ConvolutionalNetwork
from rlberry.agents.utils.torch_models import MultiLayerPerceptron


# choose device
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")


def get_network(shape):
    if len(shape) == 3:
        H, W, C = shape
        return ConvolutionalNetwork(in_channels=C,
                                    in_width=W,
                                    in_height=H,
                                    activation="ELU").to(device=device)
    elif len(shape) == 2:
        H, W = shape
        return ConvolutionalNetwork(in_channels=1,
                                    in_width=W,
                                    in_height=H,
                                    activation="ELU").to(device=device)

    elif len(shape) == 1:
        return MultiLayerPerceptron(in_size=shape[0],
                                    activation="RELU").to(device=device)

    else:
        raise ValueError("Incompatible observation shape: {}"
                         .format(shape))


class RandomNetworkDistillation(UncertaintyEstimator):
    """
    References
    ----------
    Burda Yuri, Harrison Edwards, Amos Storkey, and Oleg Klimov. 2018.
    "Exploration by random network distillation."
    In International Conference on Learning Representations.
    """

    def __init__(self,
                 observation_space,
                 action_space,
                 learning_rate=0.001,
                 update_period=10,
                 **kwargs):
        assert isinstance(observation_space, spaces.Box)
        UncertaintyEstimator.__init__(self, observation_space, action_space)
        self.learning_rate = learning_rate
        self.loss_fn = F.mse_loss
        self.update_period = update_period
        self.reset()

    def reset(self, **kwargs):
        self.random_target_network = get_network(self.observation_space.shape)
        self.predictor_network = get_network(self.observation_space.shape)
        self.rnd_optimizer = torch.optim.Adam(
                                self.predictor_network.parameters(),
                                lr=self.learning_rate,
                                betas=(0.9, 0.999))

        self.count = 0
        self.loss = torch.tensor(0.0)

    def _get_embeddings(self, state):
        state_tensor = torch.from_numpy(state).unsqueeze(0).to(device)
        random_embedding = self.random_target_network(state_tensor)
        predicted_embedding = self.predictor_network.forward(state_tensor)
        return random_embedding, predicted_embedding

    def update(self, state, action, next_state, reward, **kwargs):
        random_embedding, predicted_embedding \
            = self._get_embeddings(state)

        self.loss += self.loss_fn(random_embedding.detach(),
                                  predicted_embedding)

        self.count += 1
        if self.count % self.update_period == 0:
            self.loss /= self.update_period
            self.rnd_optimizer.zero_grad()
            self.loss.backward()
            self.rnd_optimizer.step()
            self.loss = torch.tensor(0.0)

    def measure(self, state, action, **kwargs):
        random_embedding, predicted_embedding \
            = self._get_embeddings(state)

        diff = predicted_embedding.detach() - random_embedding.detach()
        return torch.norm(diff, p=2)