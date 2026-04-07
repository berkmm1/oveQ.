namespace QuantumAgentic.ActorCritic {
    open Microsoft.Quantum.Canon;
    open Microsoft.Quantum.Intrinsic;
    open Microsoft.Quantum.Measurement;
    open Microsoft.Quantum.Arrays;
    open Microsoft.Quantum.Math;
    open Microsoft.Quantum.Convert;
    open Microsoft.Quantum.Random;
    open Microsoft.Quantum.Diagnostics;

    // ============================================
    // QUANTUM ACTOR-CRITIC ALGORITHMS
    // ============================================

    /// # Summary
    /// Actor-Critic agent state
    struct ActorCriticState {
        ActorQubits : Qubit[],
        CriticQubits : Qubit[],
        SharedQubits : Qubit[]
    }

    /// # Summary
    /// Actor-Critic configuration
    struct ActorCriticConfig {
        StateDim : Int,
        ActionDim : Int,
        HiddenDim : Int,
        ActorLearningRate : Double,
        CriticLearningRate : Double,
        Gamma : Double,
        Lambda : Double,
        EntropyCoeff : Double,
        ValueCoeff : Double
    }

    /// # Summary
    /// Actor output (action distribution)
    struct ActorOutput {
        ActionProbs : Double[],
        LogProb : Double,
        Entropy : Double
    }

    /// # Summary
    /// Critic output (value estimate)
    struct CriticOutput {
        Value : Double,
        Advantage : Double
    }

    /// # Summary
    /// Default Actor-Critic configuration
    function DefaultActorCriticConfig() : ActorCriticConfig {
        return ActorCriticConfig(
            StateDim: 16,
            ActionDim: 4,
            HiddenDim: 32,
            ActorLearningRate: 0.0003,
            CriticLearningRate: 0.001,
            Gamma: 0.99,
            Lambda: 0.95,
            EntropyCoeff: 0.01,
            ValueCoeff: 0.5
        );
    }

    /// # Summary
    /// Initialize Actor-Critic agent
    operation InitializeActorCritic(config : ActorCriticConfig) : ActorCriticState {
        use actorQubits = Qubit[config.ActionDim * 8];
        use criticQubits = Qubit[8];
        use sharedQubits = Qubit[config.HiddenDim];

        // Initialize with superposition
        ApplyToEach(H, actorQubits);
        ApplyToEach(H, criticQubits);
        ApplyToEach(H, sharedQubits);

        // Create shared representations
        CreateSharedRepresentation(sharedQubits, config);

        return ActorCriticState(
            ActorQubits: actorQubits,
            CriticQubits: criticQubits,
            SharedQubits: sharedQubits
        );
    }

    /// # Summary
    /// Create shared feature representation
    operation CreateSharedRepresentation(sharedQubits : Qubit[], config : ActorCriticConfig) : Unit {
        // Layered feature extraction
        let numLayers = 3;

        for layer in 0..numLayers - 1 {
            // Entanglement layer
            for i in 0..Length(sharedQubits) - 2 {
                CNOT(sharedQubits[i], sharedQubits[i + 1]);
            }

            // Rotation layer
            for i in 0..Length(sharedQubits) - 1 {
                let angle = IntAsDouble(layer * 100 + i) * 0.05;
                Ry(angle, sharedQubits[i]);
                Rz(angle * 0.5, sharedQubits[i]);
            }
        }
    }

    /// # Summary
    /// Encode state for Actor-Critic
    operation EncodeActorCriticState(
        sharedQubits : Qubit[],
        state : Double[]
    ) : Unit {
        let n = Length(sharedQubits);
        let d = Length(state);

        for i in 0..MinI(n, d) - 1 {
            let angle = ArcCos(Clip(state[i], -1.0, 1.0));
            Ry(2.0 * angle, sharedQubits[i]);
        }
    }

    /// # Summary
    /// Actor network forward pass
    operation ActorForward(
        sharedQubits : Qubit[],
        actorQubits : Qubit[],
        config : ActorCriticConfig
    ) : ActorOutput {
        // Process shared features through actor layers
        ApplyActorLayers(sharedQubits, actorQubits, config);

        // Measure action probabilities
        mutable actionProbs = [];
        let qubitsPerAction = Length(actorQubits) / config.ActionDim;

        for action in 0..config.ActionDim - 1 {
            mutable prob = 0.0;
            for i in 0..qubitsPerAction - 1 {
                let qIdx = action * qubitsPerAction + i;
                if qIdx < Length(actorQubits) {
                    let result = M(actorQubits[qIdx]);
                    set prob += result == One ? 1.0 / IntAsDouble(qubitsPerAction) | 0.0;
                }
            }
            set actionProbs += [prob];
        }

        // Softmax normalization
        let maxProb = Max(actionProbs);
        mutable expProbs = [];
        mutable sumExp = 0.0;

        for p in actionProbs {
            let expP = Exp(p - maxProb);
            set expProbs += [expP];
            set sumExp += expP;
        }

        mutable normalizedProbs = [];
        for p in expProbs {
            set normalizedProbs += [p / sumExp];
        }

        // Compute log probability and entropy
        let logProb = Log(normalizedProbs[0] + 0.001);
        let entropy = ComputeEntropyActor(normalizedProbs);

        return ActorOutput(
            ActionProbs: normalizedProbs,
            LogProb: logProb,
            Entropy: entropy
        );
    }

    /// # Summary
    /// Apply actor network layers
    operation ApplyActorLayers(
        sharedQubits : Qubit[],
        actorQubits : Qubit[],
        config : ActorCriticConfig
    ) : Unit {
        // Connect shared to actor
        for i in 0..MinI(Length(sharedQubits), Length(actorQubits)) - 1 {
            CNOT(sharedQubits[i], actorQubits[i]);
        }

        // Actor-specific processing
        for i in 0..Length(actorQubits) - 1 {
            let theta = IntAsDouble(i) * 0.1;
            Ry(theta, actorQubits[i]);
        }

        // Action-wise entanglement
        let qubitsPerAction = Length(actorQubits) / config.ActionDim;
        for action in 0..config.ActionDim - 1 {
            let startIdx = action * qubitsPerAction;
            for i in 0..qubitsPerAction - 2 {
                let idx1 = startIdx + i;
                let idx2 = startIdx + i + 1;
                if idx2 < Length(actorQubits) {
                    CNOT(actorQubits[idx1], actorQubits[idx2]);
                }
            }
        }
    }

    /// # Summary
    /// Critic network forward pass
    operation CriticForward(
        sharedQubits : Qubit[],
        criticQubits : Qubit[],
        config : ActorCriticConfig
    ) : CriticOutput {
        // Process shared features through critic layers
        ApplyCriticLayers(sharedQubits, criticQubits, config);

        // Measure value estimate
        mutable value = 0.0;
        for q in criticQubits {
            let result = M(q);
            set value += result == One ? 1.0 | -1.0;
        }
        set value = value / IntAsDouble(Length(criticQubits));

        // Advantage will be computed separately
        return CriticOutput(
            Value: value,
            Advantage: 0.0
        );
    }

    /// # Summary
    /// Apply critic network layers
    operation ApplyCriticLayers(
        sharedQubits : Qubit[],
        criticQubits : Qubit[],
        config : ActorCriticConfig
    ) : Unit {
        // Connect shared to critic
        for i in 0..MinI(Length(sharedQubits), Length(criticQubits)) - 1 {
            CNOT(sharedQubits[i], criticQubits[i]);
        }

        // Critic-specific processing
        for i in 0..Length(criticQubits) - 1 {
            let theta = IntAsDouble(i) * 0.05;
            Rx(theta, criticQubits[i]);
        }

        // Global pooling
        for i in 0..Length(criticQubits) - 2 {
            CNOT(criticQubits[i], criticQubits[i + 1]);
        }
    }

    /// # Summary
    /// Sample action from actor output
    operation SampleAction(actorOutput : ActorOutput) : Int {
        let probs = actorOutput.ActionProbs;
        let rand = DrawRandomDouble(0.0, 1.0);

        mutable cumSum = 0.0;
        for i in 0..Length(probs) - 1 {
            set cumSum += probs[i];
            if rand <= cumSum {
                return i;
            }
        }

        return Length(probs) - 1;
    }

    /// # Summary
    /// Compute entropy of probability distribution
    function ComputeEntropyActor(probs : Double[]) : Double {
        mutable entropy = 0.0;
        for p in probs {
            if p > 0.001 {
                set entropy -= p * Log(p);
            }
        }
        return entropy;
    }

    /// # Summary
    /// Advantage Actor-Critic (A2C) update
    operation A2CUpdate(
        state : ActorCriticState,
        trajectory : (Double[], Int, Double)[],  // (state, action, reward) tuples
        config : ActorCriticConfig
    ) : Unit {
        // Compute returns and advantages
        mutable returns = [];
        mutable advantages = [];

        let n = Length(trajectory);
        mutable nextValue = 0.0;

        for t in n - 1..-1..0 {
            let (s, a, r) = trajectory[t];

            // Encode state
            EncodeActorCriticState(state.SharedQubits, s);

            // Get current value
            let criticOutput = CriticForward(state.SharedQubits, state.CriticQubits, config);
            let currentValue = criticOutput.Value;

            // Compute return
            let return_t = r + config.Gamma * nextValue;
            set returns = [return_t] + returns;

            // Compute advantage
            let advantage = return_t - currentValue;
            set advantages = [advantage] + advantages;

            set nextValue = currentValue;
        }

        // Update critic
        for i in 0..n - 1 {
            let (s, a, r) = trajectory[i];
            let return_t = returns[i];

            EncodeActorCriticState(state.SharedQubits, s);
            let criticOutput = CriticForward(state.SharedQubits, state.CriticQubits, config);

            let valueLoss = (criticOutput.Value - return_t) * (criticOutput.Value - return_t);
            let criticUpdate = -valueLoss * config.CriticLearningRate * PI();

            for q in state.CriticQubits {
                Ry(criticUpdate, q);
            }
        }

        // Update actor
        for i in 0..n - 1 {
            let (s, a, r) = trajectory[i];
            let advantage = advantages[i];

            EncodeActorCriticState(state.SharedQubits, s);
            let actorOutput = ActorForward(state.SharedQubits, state.ActorQubits, config);

            // Policy gradient
            let policyLoss = -actorOutput.LogProb * advantage;
            let entropyBonus = -config.EntropyCoeff * actorOutput.Entropy;
            let totalLoss = policyLoss + entropyBonus;

            let actorUpdate = -totalLoss * config.ActorLearningRate * PI();

            for q in state.ActorQubits {
                Rz(actorUpdate, q);
            }
        }
    }

    /// # Summary
    /// Generalized Advantage Estimation (GAE)
    function ComputeGAEActorCritic(
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
    /// Asynchronous Advantage Actor-Critic (A3C) worker update
    operation A3CWorkerUpdate(
        globalState : ActorCriticState,
        localState : ActorCriticState,
        trajectory : (Double[], Int, Double)[],
        config : ActorCriticConfig
    ) : Unit {
        // Perform local update
        A2CUpdate(localState, trajectory, config);

        // Sync with global (simplified - would use gradient accumulation)
        for i in 0..MinI(Length(globalState.ActorQubits), Length(localState.ActorQubits)) - 1 {
            CNOT(localState.ActorQubits[i], globalState.ActorQubits[i]);
        }

        for i in 0..MinI(Length(globalState.CriticQubits), Length(localState.CriticQubits)) - 1 {
            CNOT(localState.CriticQubits[i], globalState.CriticQubits[i]);
        }
    }

    /// # Summary
    /// Soft Actor-Critic (SAC) temperature adjustment
    operation SACTemperatureUpdate(
        alpha : Double,
        targetEntropy : Double,
        logAlpha : Double,
        alphaOptimizerLR : Double,
        actorOutput : ActorOutput
    ) : Double {
        // Compute alpha loss
        let alphaLoss = -logAlpha * (actorOutput.Entropy - targetEntropy);

        // Update log alpha
        let newLogAlpha = logAlpha - alphaOptimizerLR * alphaLoss;

        return Exp(newLogAlpha);
    }

    /// # Summary
    /// Deterministic Policy Gradient (DPG) update
    operation DPGUpdate(
        state : ActorCriticState,
        states : Double[][],
        actions : Double[],
        rewards : Double[],
        nextStates : Double[][],
        config : ActorCriticConfig
    ) : Unit {
        for i in 0..Length(states) - 1 {
            // Critic update
            EncodeActorCriticState(state.SharedQubits, states[i]);
            let currentQ = CriticForward(state.SharedQubits, state.CriticQubits, config).Value;

            EncodeActorCriticState(state.SharedQubits, nextStates[i]);
            let nextQ = CriticForward(state.SharedQubits, state.CriticQubits, config).Value;

            let targetQ = rewards[i] + config.Gamma * nextQ;
            let criticLoss = (currentQ - targetQ) * (currentQ - targetQ);

            let criticUpdate = -criticLoss * config.CriticLearningRate * PI();
            for q in state.CriticQubits {
                Ry(criticUpdate, q);
            }

            // Actor update (gradient of Q w.r.t. action)
            let actorLoss = -currentQ;
            let actorUpdate = -actorLoss * config.ActorLearningRate * PI();
            for q in state.ActorQubits {
                Rz(actorUpdate, q);
            }
        }
    }

    /// # Summary
    /// Twin Delayed Deep Deterministic Policy Gradient (TD3)
    operation TD3Update(
        state : ActorCriticState,
        states : Double[][],
        actions : Double[],
        rewards : Double[],
        nextStates : Double[][],
        dones : Bool[],
        config : ActorCriticConfig
    ) : Unit {
        use criticQubits2 = Qubit[Length(state.CriticQubits)];

        for i in 0..Length(states) - 1 {
            // Get Q-values from both critics
            EncodeActorCriticState(state.SharedQubits, states[i]);
            let q1 = CriticForward(state.SharedQubits, state.CriticQubits, config).Value;

            // Second critic (would be separate network in practice)
            let q2 = CriticForward(state.SharedQubits, criticQubits2, config).Value;

            // Use minimum Q-value
            let currentQ = MinD(q1, q2);

            // Target Q
            EncodeActorCriticState(state.SharedQubits, nextStates[i]);
            let nextQ1 = CriticForward(state.SharedQubits, state.CriticQubits, config).Value;
            let nextQ2 = CriticForward(state.SharedQubits, criticQubits2, config).Value;
            let nextQ = MinD(nextQ1, nextQ2);

            let targetQ = rewards[i] + (dones[i] ? 0.0 | config.Gamma * nextQ);

            // Update both critics
            let criticLoss1 = (q1 - targetQ) * (q1 - targetQ);
            let criticLoss2 = (q2 - targetQ) * (q2 - targetQ);

            let update1 = -criticLoss1 * config.CriticLearningRate * PI();
            let update2 = -criticLoss2 * config.CriticLearningRate * PI();

            for q in state.CriticQubits {
                Ry(update1, q);
            }
            for q in criticQubits2 {
                Ry(update2, q);
            }
        }

        ResetAll(criticQubits2);
    }

    /// # Summary
    /// Helper: Clip value
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
    /// Helper: Maximum of array
    function Max(values : Double[]) : Double {
        mutable maxVal = values[0];
        for v in values {
            if v > maxVal {
                set maxVal = v;
            }
        }
        return maxVal;
    }

    /// # Summary
    /// Helper: Minimum of two doubles
    function MinD(a : Double, b : Double) : Double {
        return a < b ? a | b;
    }

    /// # Summary
    /// Reset Actor-Critic state
    operation ResetActorCritic(state : ActorCriticState) : Unit {
        ResetAll(state.ActorQubits);
        ResetAll(state.CriticQubits);
        ResetAll(state.SharedQubits);
    }
}
