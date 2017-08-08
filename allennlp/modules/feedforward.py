from typing import Sequence, Union

import torch

from allennlp.common import Params
from allennlp.common.checks import ConfigurationError
from allennlp.nn import Activation


class FeedForward(torch.nn.Module):
    """
    This ``Module`` is a feed-forward neural network, just a sequence of ``Linear`` layers with
    activation functions in between.

    Parameters
    ----------
    input_dim : ``int``
        The dimensionality of the input.  We assume the input has shape ``(batch_size, input_dim)``.
    num_layers : ``int``
        The number of ``Linear`` layers to apply to the input.
    hidden_dims : ``Union[int, Sequence[int]]``
        The output dimension of each of the ``Linear`` layers.  If this is a single ``int``, we use
        it for all ``Linear`` layers.  If it is a ``Sequence[int]``, ``len(hidden_dims)`` must be
        ``num_layers``.
    activations : ``Union[Callable, Sequence[Callable]]``
        The activation function to use after each ``Linear`` layer.  If this is a single function,
        we use it after all ``Linear`` layers.  If it is a ``Sequence[Callable]``,
        ``len(activations)`` must be ``num_layers``.
    """
    def __init__(self,
                 input_dim: int,
                 num_layers: int,
                 hidden_dims: Union[int, Sequence[int]],
                 activations: Union[Activation, Sequence[Activation]]) -> None:
        super(FeedForward, self).__init__()
        if not isinstance(hidden_dims, list):
            hidden_dims = [hidden_dims] * num_layers  # type: ignore
        if not isinstance(activations, list):
            activations = [activations] * num_layers  # type: ignore
        if len(hidden_dims) != num_layers:
            raise ConfigurationError("len(hidden_dims) (%d) != num_layers (%d)" %
                                     (len(hidden_dims), num_layers))
        if len(activations) != num_layers:
            raise ConfigurationError("len(activations) (%d) != num_layers (%d)" %
                                     (len(activations), num_layers))
        self._activations = activations
        input_dims = [input_dim] + hidden_dims[:-1]
        linear_layers = []
        for layer_input_dim, layer_output_dim in zip(input_dims, hidden_dims):
            linear_layers.append(torch.nn.Linear(layer_input_dim, layer_output_dim))
        self._linear_layers = torch.nn.ModuleList(linear_layers)
        self._output_dim = hidden_dims[-1]

    def get_output_dim(self):
        return self._output_dim

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        # pylint: disable=arguments-differ
        output = inputs
        for layer, activation in zip(self._linear_layers, self._activations):
            output = activation(layer(output))
        return output

    @classmethod
    def from_params(cls, params: Params):
        input_dim = params.pop('input_dim')
        num_layers = params.pop('num_layers')
        hidden_dims = params.pop('hidden_dims')
        activations = params.pop('activations')
        if isinstance(activations, list):
            activations = [Activation.by_name(name)() for name in activations]
        else:
            activations = Activation.by_name(activations)()
        params.assert_empty(cls.__name__)
        return cls(input_dim=input_dim,
                   num_layers=num_layers,
                   hidden_dims=hidden_dims,
                   activations=activations)