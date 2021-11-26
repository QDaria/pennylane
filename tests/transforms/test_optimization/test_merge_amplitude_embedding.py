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

import pytest
from pennylane import numpy as np

import pennylane as qml
from pennylane.transforms.optimization import merge_amplitude_embedding
from pennylane._device import DeviceError


class TestMergeAmplitudeEmbedding:
    """Test that amplitude embedding gates are combined into a single."""

    def test_multi_amplitude_embedding(self):
        """Test that the transformation is working correctly by joining two AmplitudeEmbedding."""

        def qfunc():
            qml.AmplitudeEmbedding([0.0, 1.0], wires=0)
            qml.AmplitudeEmbedding([0.0, 1.0], wires=1)
            qml.Hadamard(wires=0)
            qml.Hadamard(wires=0)
            qml.state()

        transformed_qfunc = merge_amplitude_embedding(qfunc)
        ops = qml.transforms.make_tape(transformed_qfunc)().operations

        assert len(ops) == 3

        # Check that the solution is as expected.
        dev = qml.device("default.qubit", wires=2)
        assert np.allclose(qml.QNode(transformed_qfunc, dev)()[-1], 1)

    def test_repeated_qubit(self):
        """Check that AmplitudeEmbedding cannot be applied if the qubit has already been used."""

        def qfunc():
            qml.CNOT(wires=[0.0, 1.0])
            qml.AmplitudeEmbedding([0.0, 1.0], wires=1)

        transformed_qfunc = merge_amplitude_embedding(qfunc)

        dev = qml.device("default.qubit", wires=2)
        qnode = qml.QNode(transformed_qfunc, dev)

        with pytest.raises(DeviceError, match="applied in the same qubit"):
            qnode()

    def test_decorator(self):
        """Check that the decorator works."""

        @merge_amplitude_embedding
        def qfunc():
            qml.AmplitudeEmbedding([0, 1, 0, 0], wires=[0, 1])
            qml.AmplitudeEmbedding([0, 1], wires=2)

            return qml.state()

        dev = qml.device("default.qubit", wires=3)
        qnode = qml.QNode(qfunc, dev)
        assert qnode()[3] == 1.0


class TestMergeAmplitudeEmbeddingInterfaces:
    """Test that merging amplitude embedding operations works in all interfaces."""

    def test_merge_amplitude_embedding_autograd(self):
        """Test QNode in autograd interface."""

        def qfunc(amplitude):
            qml.AmplitudeEmbedding(amplitude, wires=0)
            qml.AmplitudeEmbedding(amplitude, wires=1)
            return qml.state()

        dev = qml.device("default.qubit", wires=2)
        optimized_qfunc = qml.transforms.merge_amplitude_embedding(qfunc)
        optimized_qnode = qml.QNode(optimized_qfunc, dev)

        amplitude = np.array([0.0, 1.0], requires_grad=True)
        # Check the state |11> is being generated.
        assert optimized_qnode(amplitude)[-1] == 1

    def test_merge_amplitude_embedding_torch(self):
        """Test QNode in torch interface."""
        torch = pytest.importorskip("torch", minversion="1.8")

        def qfunc(amplitude):
            qml.AmplitudeEmbedding(amplitude, wires=0)
            qml.AmplitudeEmbedding(amplitude, wires=1)
            return qml.state()

        dev = qml.device("default.qubit", wires=2)
        optimized_qfunc = qml.transforms.merge_amplitude_embedding(qfunc)
        optimized_qnode = qml.QNode(optimized_qfunc, dev, interface="torch")

        amplitude = torch.tensor([0.0, 1.0], requires_grad=True)
        # Check the state |11> is being generated.
        assert optimized_qnode(amplitude)[-1] == 1

    def test_merge_amplitude_embedding_tf(self):
        """Test QNode in tensorflow interface."""
        tf = pytest.importorskip("tensorflow")

        def qfunc(amplitude):
            qml.AmplitudeEmbedding(amplitude, wires=0)
            qml.AmplitudeEmbedding(amplitude, wires=1)
            return qml.state()

        dev = qml.device("default.qubit", wires=2)
        optimized_qfunc = qml.transforms.merge_amplitude_embedding(qfunc)
        optimized_qnode = qml.QNode(optimized_qfunc, dev, interface="tf")

        amplitude = tf.Variable([0.0, 1.0])
        # Check the state |11> is being generated.
        assert optimized_qnode(amplitude)[-1] == 1

    def test_merge_amplitude_embedding_jax(self):
        """Test QNode in JAX interface."""
        jax = pytest.importorskip("jax")
        from jax import numpy as jnp

        from jax.config import config

        remember = config.read("jax_enable_x64")
        config.update("jax_enable_x64", True)

        def qfunc(amplitude):
            qml.AmplitudeEmbedding(amplitude, wires=0)
            qml.AmplitudeEmbedding(amplitude, wires=1)
            return qml.state()

        dev = qml.device("default.qubit", wires=2)
        optimized_qfunc = qml.transforms.merge_amplitude_embedding(qfunc)
        optimized_qnode = qml.QNode(optimized_qfunc, dev, interface="jax")

        amplitude = jnp.array([0.0, 1.0], dtype=jnp.float64)
        # Check the state |11> is being generated.
        assert optimized_qnode(amplitude)[-1] == 1
