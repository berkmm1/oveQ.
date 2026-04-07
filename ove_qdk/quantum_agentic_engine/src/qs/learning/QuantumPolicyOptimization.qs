namespace QuantumAgentic.PolicyOptimization {
    open Microsoft.Quantum.Canon;
    open Microsoft.Quantum.Intrinsic;
    open Microsoft.Quantum.Measurement;
    open Microsoft.Quantum.Arrays;
    open Microsoft.Quantum.Math;
    open Microsoft.Quantum.Convert;
    open Microsoft.Quantum.Random;
    open Microsoft.Quantum.Diagnostics;

    // ============================================
    // QUANTUM POLICY OPTIMIZATION ALGORITHMS
    // ============================================

    /// # Summary
    /// Policy gradient configuration
    struct PolicyGradientConfig {
        LearningRate : Double,
        Gamma : Double,
        Lambda : Double,
        ClipEpsilon : Double,
        ValueFunctionCoeff : Double,
        EntropyCoeff : Double,
        MaxGradientNorm : Double
    }

    /// # Summary
    /// Trajectory data for policy gradient
    struct Trajectory {
        States : Double[][],
        Actions : Int[],
        Rewards : Double[],
        Values : Double[],
        LogProbs : Double[]
    }

    /// # Summary
    /// Policy network output
    struct PolicyOutput {
        ActionProbs : Double[],
        Value : Double,
        LogProb : Double
    }

    /// # Summary
    /// Default policy gradient configuration
    function DefaultPolicyGradientConfig() : PolicyGradientConfig {
        return PolicyGradientConfig(
            LearningRate: 0.0003,
            Gamma: 0.99,
            Lambda: 0.95,
            ClipEpsilon: 0.2,
            ValueFunctionCoeff: 0.5,
            EntropyCoeff: 0.01,
            MaxGradientNorm: 0.5
        );
    }

    /// # Summary
    /// Quantum policy network forward pass
    operation QuantumPolicyNetwork(
        stateQubits : Qubit[],
        policyQubits : Qubit[],
        valueQubits : Qubit[],
        state : Double[]
    ) : PolicyOutput {
        // Encode state
        EncodeStateForPolicy(stateQubits, state);

        // Policy head
        ApplyPolicyLayers(stateQubits, policyQubits);

        // Value head
        ApplyValueLayers(stateQubits, valueQubits);

        // Measure policy output
        mutable actionProbs = [];
        let numActions = Length(policyQubits) / 4;

        for action in 0..numActions - 1 {
            mutable prob = 0.0;
            for i in 0..3 {
                let qIdx = action * 4 + i;
                if qIdx < Length(policyQubits) {
                    let result = M(policyQubits[qIdx]);
                    set prob += result == One ? 0.25 | 0.0;
                }
            }
            set actionProbs += [prob];
        }

        // Normalize probabilities
        let totalProb = Sum(actionProbs);
        if totalProb > 0.0 {
            mutable normalized = [];
            for p in actionProbs {
                set normalized += [p / totalProb];
            }
            set actionProbs = normalized;
        }

        // Measure value
        mutable value = 0.0;
        for q in valueQubits {
            let result = M(q);
            set value += result == One ? 1.0 | -1.0;
        }
        set value = value / IntAsDouble(Length(valueQubits));

        // Compute log probability (simplified)
        let logProb = Log(actionProbs[0] + 0.001);

        return PolicyOutput(
            ActionProbs: actionProbs,
            Value: value,
            LogProb: logProb
        );
    }

    /// # Summary
    /// Encode state for policy network
    operation EncodeStateForPolicy(stateQubits : Qubit[], state : Double[]) : Unit {
        let n = Length(stateQubits);
        let d = Length(state);

        for i in 0..MinI(n, d) - 1 {
            let angle = ArcCos(Clip(state[i], -1.0, 1.0));
            Ry(2.0 * angle, stateQubits[i]);
        }
    }

    /// # Summary
    /// Apply policy network layers
    operation ApplyPolicyLayers(stateQubits : Qubit[], policyQubits : Qubit[]) : Unit {
        // Entangle state with policy qubits
        for i in 0..MinI(Length(stateQubits), Length(policyQubits)) - 1 {
            CNOT(stateQubits[i], policyQubits[i]);
        }

        // Apply parameterized rotations
        for i in 0..Length(policyQubits) - 1 {
            let theta = IntAsDouble(i) * 0.1;
            Ry(theta, policyQubits[i]);
            Rz(theta * 0.5, policyQubits[i]);
        }

        // Entanglement within policy qubits
        for i in 0..Length(policyQubits) - 2 {
            CNOT(policyQubits[i], policyQubits[i + 1]);
        }
    }

    /// # Summary
    /// Apply value network layers
    operation ApplyValueLayers(stateQubits : Qubit[], valueQubits : Qubit[]) : Unit {
        // Entangle state with value qubits
        for i in 0..MinI(Length(stateQubits), Length(valueQubits)) - 1 {
            CNOT(stateQubits[i], valueQubits[i]);
        }

        // Apply rotations
        for i in 0..Length(valueQubits) - 1 {
            let theta = IntAsDouble(i) * 0.05;
            Rx(theta, valueQubits[i]);
        }

        // Global pooling
        for i in 0..Length(valueQubits) - 2 {
            CNOT(valueQubits[i], valueQubits[i + 1]);
        }
    }

    /// # Summary
    /// Compute Generalized Advantage Estimation (GAE)
    function ComputeGAE(
        rewards : Double[],
        values : Double[],
        gamma : Double,
        lambda : Double
    ) : Double[] {
        let n = Length(rewards);
        mutable advantages = [];
        mutable gae = 0.0;

        for t in n - 1..-1..0 {
            let nextValue = t < n - 1 ? values[t + 1] | 0.0;
            let delta = rewards[t] + gamma * nextValue - values[t];
            set gae = delta + gamma * lambda * gae;
            set advantages = [gae] + advantages;
        }

        return advantages;
    }

    /// # Summary
    /// Quantum Proximal Policy Optimization (PPO)
    operation QuantumPPO(
        stateQubits : Qubit[],
        policyQubits : Qubit[],
        valueQubits : Qubit[],
        trajectory : Trajectory,
        config : PolicyGradientConfig,
        epochs : Int
    ) : Unit {
        // Compute advantages
        let advantages = ComputeGAE(
            trajectory.Rewards,
            trajectory.Values,
            config.Gamma,
            config.Lambda
        );

        // Compute returns
        mutable returns = [];
        for i in 0..Length(advantages) - 1 {
            set returns += [advantages[i] + trajectory.Values[i]];
        }

        // PPO update epochs
        for epoch in 0..epochs - 1 {
            for t in 0..Length(trajectory.States) - 1 {
                // Get current policy output
                let output = QuantumPolicyNetwork(
                    stateQubits,
                    policyQubits,
                    valueQubits,
                    trajectory.States[t]
                );

                // Compute ratio
                let oldLogProb = trajectory.LogProbs[t];
                let newLogProb = output.LogProb;
                let ratio = Exp(newLogProb - oldLogProb);

                // Clipped surrogate objective
                let advantage = advantages[t];
                let clippedRatio = Clip(ratio, 1.0 - config.ClipEpsilon, 1.0 + config.ClipEpsilon);
                let surrogate1 = ratio * advantage;
                let surrogate2 = clippedRatio * advantage;
                let policyLoss = MinD(surrogate1, surrogate2);

                // Value loss
                let return_t = returns[t];
                let valueLoss = (output.Value - return_t) * (output.Value - return_t);

                // Entropy bonus
                mutable entropy = 0.0;
                for prob in output.ActionProbs {
                    if prob > 0.001 {
                        set entropy -= prob * Log(prob);
                    }
                }

                // Total loss
                let totalLoss = -policyLoss +
                               config.ValueFunctionCoeff * valueLoss -
                               config.EntropyCoeff * entropy;

                // Apply gradient update (simplified)
                ApplyPolicyGradient(policyQubits, totalLoss, config.LearningRate);
            }
        }
    }

    /// # Summary
    /// Apply policy gradient update
    operation ApplyPolicyGradient(
        policyQubits : Qubit[],
        loss : Double,
        learningRate : Double
    ) : Unit {
        let updateAngle = loss * learningRate * PI();

        for q in policyQubits {
            Ry(updateAngle, q);
        }
    }

    /// # Summary
    /// Quantum Trust Region Policy Optimization (TRPO)
    operation QuantumTRPO(
        stateQubits : Qubit[],
        policyQubits : Qubit[],
        trajectory : Trajectory,
        config : PolicyGradientConfig,
        maxKL : Double,
        damping : Double
    ) : Unit {
        // Compute policy gradient
        mutable policyGradient = [];

        for t in 0..Length(trajectory.States) - 1 {
            let output = QuantumPolicyNetwork(
                stateQubits,
                policyQubits,
                [],
                trajectory.States[t]
            );

            // Advantage-weighted gradient
            let advantage = trajectory.Rewards[t];
            let grad = output.LogProb * advantage;
            set policyGradient += [grad];
        }

        // Compute Fisher-vector product (simplified)
        // In practice, would use conjugate gradient

        // Natural gradient step
        for i in 0..Length(policyGradient) - 1 {
            let naturalGrad = policyGradient[i] / (damping + AbsD(policyGradient[i]));

            // Apply to qubits
            let qIdx = i % Length(policyQubits);
            let angle = naturalGrad * config.LearningRate * PI();
            Ry(angle, policyQubits[qIdx]);
        }
    }

    /// # Summary
    /// Quantum Actor-Critic with Experience Replay
    operation QuantumActorCriticER(
        stateQubits : Qubit[],
        policyQubits : Qubit[],
        valueQubits : Qubit[],
        batch : Trajectory[],
        config : PolicyGradientConfig
    ) : Unit {
        for trajectory in batch {
            // Update critic
            for t in 0..Length(trajectory.States) - 1 {
                let output = QuantumPolicyNetwork(
                    stateQubits,
                    policyQubits,
                    valueQubits,
                    trajectory.States[t]
                );

                // TD error
                let nextValue = t < Length(trajectory.States) - 1 ?
                    trajectory.Values[t + 1] | 0.0;
                let tdTarget = trajectory.Rewards[t] + config.Gamma * nextValue;
                let tdError = tdTarget - output.Value;

                // Update value function
                let valueUpdate = tdError * config.LearningRate * PI();
                for q in valueQubits {
                    Ry(valueUpdate, q);
                }

                // Update policy
                let policyUpdate = tdError * output.LogProb * config.LearningRate * PI();
                for q in policyQubits {
                    Rz(policyUpdate, q);
                }
            }
        }
    }

    /// # Summary
    /// Quantum Soft Actor-Critic (SAC)
    operation QuantumSAC(
        stateQubits : Qubit[],
        policyQubits : Qubit[],
        qValueQubits1 : Qubit[],
        qValueQubits2 : Qubit[],
        state : Double[],
        action : Int,
        reward : Double,
        nextState : Double[],
        done : Bool,
        config : PolicyGradientConfig,
        alpha : Double
    ) : Unit {
        // Encode current state
        EncodeStateForPolicy(stateQubits, state);

        // Get Q-values from both critics
        let qValues1 = MeasureQValues(stateQubits, qValueQubits1);
        let qValues2 = MeasureQValues(stateQubits, qValueQubits2);

        // Use minimum Q-value
        mutable minQValues = [];
        for i in 0..Length(qValues1) - 1 {
            set minQValues += [MinD(qValues1[i], qValues2[i])];
        }

        // Get policy output
        let policyOutput = QuantumPolicyNetwork(
            stateQubits,
            policyQubits,
            [],
            state
        );

        // Compute soft Q-value
        mutable softQ = 0.0;
        for i in 0..Length(policyOutput.ActionProbs) - 1 {
            set softQ += policyOutput.ActionProbs[i] * minQValues[i];
        }

        // Add entropy bonus
        let entropy = ComputeEntropy(policyOutput.ActionProbs);
        softQ = softQ + alpha * entropy;

        // Q-function loss
        let qTarget = reward + (done ? 0.0 | config.Gamma * softQ);
        let qLoss = (minQValues[action] - qTarget) * (minQValues[action] - qTarget);

        // Update Q-functions
        ApplyQLoss(qValueQubits1, qLoss, config.LearningRate);
        ApplyQLoss(qValueQubits2, qLoss, config.LearningRate);

        // Policy loss
        let policyLoss = -softQ;
        ApplyPolicyGradient(policyQubits, policyLoss, config.LearningRate);
    }

    /// # Summary
    /// Measure Q-values
    operation MeasureQValues(stateQubits : Qubit[], qValueQubits : Qubit[]) : Double[] {
        mutable qValues = [];
        let numActions = Length(qValueQubits) / 4;

        for action in 0..numActions - 1 {
            mutable qValue = 0.0;
            for i in 0..3 {
                let qIdx = action * 4 + i;
                if qIdx < Length(qValueQubits) {
                    let result = M(qValueQubits[qIdx]);
                    set qValue += result == One ? 0.25 | -0.25;
                }
            }
            set qValues += [qValue];
        }

        return qValues;
    }

    /// # Summary
    /// Apply Q-function loss
    operation ApplyQLoss(qValueQubits : Qubit[], loss : Double, learningRate : Double) : Unit {
        let updateAngle = loss * learningRate * PI();
        for q in qValueQubits {
            Ry(updateAngle, q);
        }
    }

    /// # Summary
    /// Compute entropy of probability distribution
    function ComputeEntropy(probs : Double[]) : Double {
        mutable entropy = 0.0;
        for p in probs {
            if p > 0.001 {
                set entropy -= p * Log(p);
            }
        }
        return entropy;
    }

    /// # Summary
    /// Quantum Deterministic Policy Gradient (DDPG)
    operation QuantumDDPG(
        stateQubits : Qubit[],
        actorQubits : Qubit[],
        criticQubits : Qubit[],
        state : Double[],
        action : Double[],
        reward : Double,
        nextState : Double[],
        config : PolicyGradientConfig
    ) : Unit {
        // Actor forward pass
        EncodeStateForPolicy(stateQubits, state);
        ApplyActorLayers(stateQubits, actorQubits);

        // Get deterministic action
        mutable deterministicAction = [];
        for q in actorQubits {
            let result = M(q);
            set deterministicAction += [result == One ? 1.0 | -1.0];
        }

        // Critic: Q(s, a)
        let currentQ = QuantumCritic(stateQubits, criticQubits, state, action);

        // Critic: Q(s', π(s'))
        use nextStateQubits = Qubit[Length(stateQubits)];
        EncodeStateForPolicy(nextStateQubits, nextState);
        ApplyActorLayers(nextStateQubits, actorQubits);

        mutable nextAction = [];
        for q in actorQubits {
            let result = M(q);
            set nextAction += [result == One ? 1.0 | -1.0];
        }

        let nextQ = QuantumCritic(nextStateQubits, criticQubits, nextState, nextAction);

        // Critic loss
        let criticTarget = reward + config.Gamma * nextQ;
        let criticLoss = (currentQ - criticTarget) * (currentQ - criticTarget);

        // Update critic
        ApplyCriticLoss(criticQubits, criticLoss, config.LearningRate);

        // Actor loss: -Q(s, π(s))
        let actorQ = QuantumCritic(stateQubits, criticQubits, state, deterministicAction);
        let actorLoss = -actorQ;

        // Update actor
        ApplyActorLoss(actorQubits, actorLoss, config.LearningRate);
    }

    /// # Summary
    /// Apply actor layers
    operation ApplyActorLayers(stateQubits : Qubit[], actorQubits : Qubit[]) : Unit {
        for i in 0..MinI(Length(stateQubits), Length(actorQubits)) - 1 {
            CNOT(stateQubits[i], actorQubits[i]);
            let theta = IntAsDouble(i) * 0.1;
            Ry(theta, actorQubits[i]);
        }
    }

    /// # Summary
    /// Quantum critic network
    operation QuantumCritic(
        stateQubits : Qubit[],
        criticQubits : Qubit[],
        state : Double[],
        action : Double[]
    ) : Double {
        EncodeStateForPolicy(stateQubits, state);

        // Encode action
        for i in 0..MinI(Length(action), Length(criticQubits) / 2) - 1 {
            let angle = action[i] * PI();
            Ry(angle, criticQubits[i]);
        }

        // Process state-action pair
        for i in 0..MinI(Length(stateQubits), Length(criticQubits) / 2) - 1 {
            let cIdx = i + Length(criticQubits) / 2;
            if cIdx < Length(criticQubits) {
                CNOT(stateQubits[i], criticQubits[cIdx]);
            }
        }

        // Measure Q-value
        mutable qValue = 0.0;
        for q in criticQubits {
            let result = M(q);
            set qValue += result == One ? 1.0 | -1.0;
        }

        return qValue / IntAsDouble(Length(criticQubits));
    }

    /// # Summary
    /// Apply critic loss
    operation ApplyCriticLoss(criticQubits : Qubit[], loss : Double, learningRate : Double) : Unit {
        let updateAngle = loss * learningRate * PI();
        for q in criticQubits {
            Ry(updateAngle, q);
        }
    }

    /// # Summary
    /// Apply actor loss
    operation ApplyActorLoss(actorQubits : Qubit[], loss : Double, learningRate : Double) : Unit {
        let updateAngle = loss * learningRate * PI();
        for q in actorQubits {
            Rz(updateAngle, q);
        }
    }

    /// # Summary
    /// Clip value to range
    function Clip(value : Double, minVal : Double, maxVal : Double) : Double {
        if value < minVal {
            return minVal;
        } elif value > maxVal {
            return maxVal;
        } else {
            return value;
        }
    }

    /// # Summary
    /// Sum array of doubles
    function Sum(values : Double[]) : Double {
        mutable total = 0.0;
        for v in values {
            set total += v;
        }
        return total;
    }

    /// # Summary
    /// Minimum of two doubles
    function MinD(a : Double, b : Double) : Double {
        return a < b ? a | b;
    }

    /// # Summary
    /// Maximum of two doubles
    function MaxD(a : Double, b : Double) : Double {
        return a > b ? a | b;
    }
}
