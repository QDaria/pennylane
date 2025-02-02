# Copyright 2018-2021 Xanadu Quantum Technologies Inc.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
r"""
Contains the SqueezingEmbedding template.
"""
# pylint: disable-msg=too-many-branches,too-many-arguments,protected-access
import pennylane as qml
from pennylane.operation import Operation, AnyWires


class SqueezingEmbedding(Operation):
    r"""Encodes :math:`N` features into the squeezing amplitudes :math:`r \geq 0` or phases :math:`\phi \in [0, 2\pi)`
    of :math:`M` modes, where :math:`N\leq M`.

    The mathematical definition of the squeezing gate is given by the operator

    .. math::

        S(z) = \exp\left(\frac{r}{2}\left(e^{-i\phi}\a^2 -e^{i\phi}{\ad}^{2} \right) \right),

    where :math:`\a` and :math:`\ad` are the bosonic creation and annihilation operators.

    ``features`` has to be an iterable of at most ``len(wires)`` floats. If there are fewer entries in
    ``features`` than wires, the circuit does not apply the remaining squeezing gates.

    Args:
        features (tensor_like): tensor of features
        wires (Iterable): wires that the template acts on
        method (str): ``'phase'`` encodes the input into the phase of single-mode squeezing, while
            ``'amplitude'`` uses the amplitude
        c (float): value of the phase of all squeezing gates if ``execution='amplitude'``, or the
            amplitude of all squeezing gates if ``execution='phase'``

    Raises:
        ValueError: if inputs do not have the correct format

    Example:

        Depending on the ``method`` argument, the feature vector will be encoded in the phase or the amplitude.
        The argument ``c`` will define the value of the other quantity.
        The default values are :math:`0.1` for ``c`` and ``'amplitude'`` for ``method``.

        .. code-block:: python

            dev = qml.device('default.gaussian', wires=3)

            @qml.qnode(dev)
            def circuit(feature_vector):
                qml.SqueezingEmbedding(features=feature_vector, wires=range(3))
                qml.QuadraticPhase(0.1, wires=1)
                return qml.expval(qml.NumberOperator(wires=1))

            X = [1, 2, 3]

        >>> print(circuit(X))
            13.018280763205285

        And, the resulting circuit is:

        >>> print(qml.draw(circuit)(X))
            0: ──S(1, 0.1)──────────┤
            1: ──S(2, 0.1)──P(0.1)──┤ ⟨n⟩
            2: ──S(3, 0.1)──────────┤

        Using different parameters:

        .. code-block:: python

            dev = qml.device('default.gaussian', wires=3)

            @qml.qnode(dev)
            def circuit(feature_vector):
                qml.SqueezingEmbedding(features=feature_vector, wires=range(3), method='phase', c=0.5)
                qml.QuadraticPhase(0.1, wires=1)
                return qml.expval(qml.NumberOperator(wires=1))

            X = [1, 2, 3]

        >>> print(circuit(X))
            0.22319028857312428

        And, the resulting circuit is:

        >>> print(qml.draw(circuit)(X))
            0: ──S(0.5, 1)──────────┤
            1: ──S(0.5, 2)──P(0.1)──┤ ⟨n⟩
            2: ──S(0.5, 3)──────────┤
    """

    num_wires = AnyWires
    grad_method = None

    def __init__(self, features, wires, method="amplitude", c=0.1, do_queue=True, id=None):

        shape = qml.math.shape(features)
        constants = [c] * shape[0]
        constants = qml.math.convert_like(constants, features)

        if len(shape) != 1:
            raise ValueError(f"Features must be a one-dimensional tensor; got shape {shape}.")

        n_features = shape[0]
        if n_features != len(wires):
            raise ValueError(f"Features must be of length {len(wires)}; got length {n_features}.")

        if method == "amplitude":
            pars = qml.math.stack([features, constants], axis=1)

        elif method == "phase":
            pars = qml.math.stack([constants, features], axis=1)

        else:
            raise ValueError(f"did not recognize method {method}")

        super().__init__(pars, wires=wires, do_queue=do_queue, id=id)

    @property
    def num_params(self):
        return 1

    def expand(self):

        pars = self.parameters[0]

        with qml.tape.QuantumTape() as tape:

            for i in range(len(self.wires)):
                qml.Squeezing(pars[i, 0], pars[i, 1], wires=self.wires[i : i + 1])

        return tape
