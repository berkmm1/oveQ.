import pytest
import numpy as np
import qsharp
from core.agent_host import QuantumAgentHost, AgentConfig
from core.quantum_backend import QSharpBackend, BackendConfig, BackendType

def test_quantum_agent_integration():
    """Test that QuantumAgentHost can initialize and run a step with Q# backend"""
    # Initialize Q# with base profile
    qsharp.init(target_profile=qsharp.TargetProfile.Base)

    config = AgentConfig(
        num_perception_qubits=4,
        num_decision_qubits=4,
        num_action_qubits=4
    )

    agent = QuantumAgentHost(config)

    # Verify backend is QSharp
    assert isinstance(agent.backend, QSharpBackend)

    # Test perception
    state = np.random.randn(4)
    perceived = agent.perceive(state)
    assert len(perceived) == 4

    # Test processing (which now uses backend)
    processed = agent.process(perceived)
    assert len(processed) == 4

    # Test decision
    action, q_values = agent.decide(processed)
    assert isinstance(action, int)
    assert len(q_values) == config.num_action_qubits

    print(f"Action selected: {action}")
    print(f"Q-values: {q_values}")

if __name__ == "__main__":
    test_quantum_agent_integration()
