namespace QuantumAgentic.Learning {
    open Microsoft.Quantum.Canon;
    open Microsoft.Quantum.Intrinsic;
    open Microsoft.Quantum.Measurement;
    open Microsoft.Quantum.Arrays;
    open Microsoft.Quantum.Math;
    open Microsoft.Quantum.Convert;
    open Microsoft.Quantum.Random;
    open Microsoft.Quantum.Diagnostics;

    // ============================================
    // QUANTUM REINFORCEMENT LEARNING
    // ============================================

    /// # Summary
    /// Quantum Q-Learning state representation
    struct QuantumQLearningState {
        QValueQubits : Qubit[],
        PolicyQubits : Qubit[],
        StateQubits : Qubit[],
        AdvantageQubits : Qubit[]
    }

    /// # Summary
    /// Experience tuple for replay buffer
    struct Experience {
        State : Double[],
        Action : Int,
        Reward : Double,
        NextState : Double[],
        Done : Bool
    }

    /// # Summary
    /// QRL Agent configuration
    struct QRLConfig {
        StateDim : Int,
        ActionDim : Int,
        HiddenDim : Int,
        Gamma : Double,
        Epsilon : Double,
        EpsilonDecay : Double,
        EpsilonMin : Double,
        LearningRate : Double,
        BufferSize : Int,
        BatchSize : Int,
        TargetUpdateFreq : Int
    }

    /// # Summary
    /// Default QRL configuration
    function DefaultQRLConfig() : QRLConfig {
        return QRLConfig(
            StateDim: 16,
            ActionDim: 8,
            HiddenDim: 32,
            Gamma: 0.99,
            Epsilon: 1.0,
            EpsilonDecay: 0.995,
            EpsilonMin: 0.01,
            LearningRate: 0.001,
            BufferSize: 10000,
            BatchSize: 32,
            TargetUpdateFreq: 100
        );
    }

    /// # Summary
    /// Initialize quantum reinforcement learning agent
    operation InitializeQRLAgent(config : QRLConfig) : QuantumQLearningState {
        use qValueQubits = Qubit[config.ActionDim * 8];
        use policyQubits = Qubit[config.ActionDim * 4];
        use stateQubits = Qubit[config.StateDim];
        use advantageQubits = Qubit[config.ActionDim];

        // Initialize Q-values in superposition
        ApplyToEach(H, qValueQubits);

        // Initialize uniform policy
        ApplyToEach(H, policyQubits);

        // Initialize state representation
        ApplyToEach(H, stateQubits);

        // Initialize advantage estimates
        ApplyToEach(H, advantageQubits);

        // Create entanglement between components
        CreateQRLEntanglement(qValueQubits, policyQubits, stateQubits, advantageQubits);

        return QuantumQLearningState(
            QValueQubits: qValueQubits,
            PolicyQubits: policyQubits,
            StateQubits: stateQubits,
            AdvantageQubits: advantageQubits
        );
    }

    /// # Summary
    /// Create entanglement between QRL components
    operation CreateQRLEntanglement(
        qValues : Qubit[],
        policy : Qubit[],
        state : Qubit[],
        advantage : Qubit[]
    ) : Unit {
        // State-QValue entanglement
        for i in 0..MinI(Length(state), Length(qValues) / 8) - 1 {
            for j in 0..7 {
                CNOT(state[i], qValues[i * 8 + j]);
            }
        }

        // QValue-Policy entanglement
        for i in 0..MinI(Length(qValues) / 8, Length(policy) / 4) - 1 {
            for j in 0..3 {
                CNOT(qValues[i * 8], policy[i * 4 + j]);
            }
        }

        // QValue-Advantage entanglement
        for i in 0..MinI(Length(qValues) / 8, Length(advantage)) - 1 {
            CNOT(qValues[i * 8], advantage[i]);
        }
    }

    /// # Summary
    /// Encode state into quantum register
    operation EncodeState(stateQubits : Qubit[], state : Double[]) : Unit {
        let n = Length(stateQubits);
        let d = Length(state);

        for i in 0..MinI(n, d) - 1 {
            // Amplitude encoding
            let angle = ArcCos(state[i]);
            Ry(2.0 * angle, stateQubits[i]);

            // Phase encoding for additional information
            let phase = state[i] * PI();
            Rz(phase, stateQubits[i]);
        }
    }

    /// # Summary
    /// Quantum Q-Network forward pass
    operation QuantumQNetwork(
        stateQubits : Qubit[],
        qValueQubits : Qubit[],
        config : QRLConfig
    ) : Double[] {
        // Encode state
        // (Already encoded by caller)

        // Layer 1: State to hidden
        use hiddenQubits = Qubit[config.HiddenDim];
        ApplyToEach(H, hiddenQubits);

        for i in 0..Length(stateQubits) - 1 {
            for j in 0..MinI(config.HiddenDim / Length(stateQubits), config.HiddenDim - 1) {
                let hIdx = (i * config.HiddenDim / Length(stateQubits) + j) % config.HiddenDim;
                CNOT(stateQubits[i], hiddenQubits[hIdx]);
            }
        }

        // Layer 2: Hidden to Q-values
        let qValuesPerAction = Length(qValueQubits) / config.ActionDim;

        for action in 0..config.ActionDim - 1 {
            for h in 0..MinI(config.HiddenDim, qValuesPerAction) - 1 {
                let qIdx = action * qValuesPerAction + h;
                if qIdx < Length(qValueQubits) {
                    CNOT(hiddenQubits[h % config.HiddenDim], qValueQubits[qIdx]);
                    // Parameterized rotation
                    let theta = IntAsDouble(action * 10 + h) * 0.1;
                    Ry(theta, qValueQubits[qIdx]);
                }
            }
        }

        // Measure Q-values
        mutable qValues = [];
        for action in 0..config.ActionDim - 1 {
            mutable actionValue = 0.0;
            for q in 0..qValuesPerAction - 1 {
                let qIdx = action * qValuesPerAction + q;
                if qIdx < Length(qValueQubits) {
                    let result = M(qValueQubits[qIdx]);
                    let value = result == One ? 1.0 | -1.0;
                    set actionValue += value;
                }
            }
            set qValues += [actionValue / IntAsDouble(qValuesPerAction)];
        }

        return qValues;
    }

    /// # Summary
    /// Select action using epsilon-greedy with quantum enhancement
    operation SelectAction(
        qValues : Double[],
        epsilon : Double
    ) : Int {
        let rand = DrawRandomDouble(0.0, 1.0);

        if rand < epsilon {
            // Random exploration
            return DrawRandomInt(0, Length(qValues) - 1);
        } else {
            // Greedy selection with quantum tie-breaking
            mutable maxQ = qValues[0];
            mutable bestActions = [0];

            for i in 1..Length(qValues) - 1 {
                if qValues[i] > maxQ {
                    set maxQ = qValues[i];
                    set bestActions = [i];
                } elif AbsD(qValues[i] - maxQ) < 0.001 {
                    set bestActions += [i];
                }
            }

            // Quantum random tie-breaking
            if Length(bestActions) > 1 {
                use tieBreaker = Qubit();
                H(tieBreaker);
                let idx = DrawRandomInt(0, Length(bestActions) - 1);
                return bestActions[idx];
            } else {
                return bestActions[0];
            }
        }
    }

    /// # Summary
    /// Quantum policy gradient computation
    operation QuantumPolicyGradient(
        stateQubits : Qubit[],
        policyQubits : Qubit[],
        action : Int,
        advantage : Double,
        config : QRLConfig
    ) : Double[] {
        // Encode action in policy qubits
        let actionStart = action * 4;
        for i in 0..3 {
            if actionStart + i < Length(policyQubits) {
                Ry(PI() / 2.0, policyQubits[actionStart + i]);
            }
        }

        // Policy gradient: ∇log π(a|s) * A(s,a)
        mutable gradients = [];

        for i in 0..Length(policyQubits) - 1 {
            // Parameter shift for gradient estimation
            let shift = PI() / 2.0;

            // Positive shift
            Ry(shift, policyQubits[i]);
            let probPlus = MeasurePolicyProbability(policyQubits, action);

            // Negative shift
            Ry(-2.0 * shift, policyQubits[i]);
            let probMinus = MeasurePolicyProbability(policyQubits, action);

            // Restore
            Ry(shift, policyQubits[i]);

            // Gradient
            let grad = (probPlus - probMinus) / 2.0 * advantage;
            set gradients += [grad];
        }

        return gradients;
    }

    /// # Summary
    /// Measure policy probability for an action
    operation MeasurePolicyProbability(policyQubits : Qubit[], action : Int) : Double {
        let actionStart = action * 4;
        mutable prob = 0.0;

        for i in 0..3 {
            if actionStart + i < Length(policyQubits) {
                let result = M(policyQubits[actionStart + i]);
                if result == One {
                    set prob += 0.25;
                }
            }
        }

        return prob;
    }

    /// # Summary
    /// Quantum Actor-Critic update
    operation QuantumActorCriticUpdate(
        agent : QuantumQLearningState,
        experience : Experience,
        config : QRLConfig
    ) : Unit {
        // Encode current state
        EncodeState(agent.StateQubits, experience.State);

        // Compute current Q-values (Critic)
        let currentQValues = QuantumQNetwork(agent.StateQubits, agent.QValueQubits, config);
        let currentQ = currentQValues[experience.Action];

        // Encode next state
        use nextStateQubits = Qubit[Length(agent.StateQubits)];
        EncodeState(nextStateQubits, experience.NextState);

        // Compute next Q-values
        use nextQValueQubits = Qubit[Length(agent.QValueQubits)];
        let nextQValues = QuantumQNetwork(nextStateQubits, nextQValueQubits, config);

        // Compute target Q-value
        mutable maxNextQ = nextQValues[0];
        for q in nextQValues {
            if q > maxNextQ {
                set maxNextQ = q;
            }
        }
        let targetQ = experience.Reward + (experience.Done ? 0.0 | config.Gamma * maxNextQ);

        // TD Error
        let tdError = targetQ - currentQ;

        // Update Q-values (Critic)
        UpdateQValues(agent.QValueQubits, experience.Action, tdError, config);

        // Update Policy (Actor)
        UpdatePolicy(agent.PolicyQubits, agent.StateQubits, experience.Action, tdError, config);

        // Update Advantage estimates
        UpdateAdvantage(agent.AdvantageQubits, tdError, config);
    }

    /// # Summary
    /// Update Q-values based on TD error
    operation UpdateQValues(
        qValueQubits : Qubit[],
        action : Int,
        tdError : Double,
        config : QRLConfig
    ) : Unit {
        let qValuesPerAction = Length(qValueQubits) / config.ActionDim;
        let actionStart = action * qValuesPerAction;

        // Apply update proportional to TD error
        let updateAngle = tdError * config.LearningRate * PI();

        for i in 0..qValuesPerAction - 1 {
            let qIdx = actionStart + i;
            if qIdx < Length(qValueQubits) {
                Ry(updateAngle, qValueQubits[qIdx]);
            }
        }
    }

    /// # Summary
    /// Update policy based on advantage
    operation UpdatePolicy(
        policyQubits : Qubit[],
        stateQubits : Qubit[],
        action : Int,
        advantage : Double,
        config : QRLConfig
    ) : Unit {
        let policyPerAction = Length(policyQubits) / config.ActionDim;
        let actionStart = action * policyPerAction;

        // Policy gradient update
        let updateAngle = advantage * config.LearningRate * PI() / 2.0;

        for i in 0..policyPerAction - 1 {
            let pIdx = actionStart + i;
            if pIdx < Length(policyQubits) {
                // Increase probability of good actions
                if advantage > 0.0 {
                    Ry(updateAngle, policyQubits[pIdx]);
                } else {
                    Ry(-updateAngle, policyQubits[pIdx]);
                }
            }
        }
    }

    /// # Summary
    /// Update advantage estimates
    operation UpdateAdvantage(
        advantageQubits : Qubit[],
        tdError : Double,
        config : QRLConfig
    ) : Unit {
        // Encode TD error into advantage qubits
        for i in 0..Length(advantageQubits) - 1 {
            let angle = tdError * PI() / 2.0;
            Ry(angle, advantageQubits[i]);
        }
    }

    /// # Summary
    /// Quantum Proximal Policy Optimization (PPO)
    operation QuantumPPOUpdate(
        agent : QuantumQLearningState,
        experiences : Experience[],
        config : QRLConfig,
        clipEpsilon : Double
    ) : Unit {
        // Compute advantages for all experiences
        mutable advantages = [];
        for exp in experiences {
            EncodeState(agent.StateQubits, exp.State);
            let qValues = QuantumQNetwork(agent.StateQubits, agent.QValueQubits, config);
            let qValue = qValues[exp.Action];

            use nextStateQubits = Qubit[Length(agent.StateQubits)];
            EncodeState(nextStateQubits, exp.NextState);
            use nextQValueQubits = Qubit[Length(agent.QValueQubits)];
            let nextQValues = QuantumQNetwork(nextStateQubits, nextQValueQubits, config);

            mutable maxNextQ = nextQValues[0];
            for q in nextQValues {
                if q > maxNextQ {
                    set maxNextQ = q;
                }
            }

            let advantage = exp.Reward + config.Gamma * maxNextQ - qValue;
            set advantages += [advantage];
        }

        // PPO update for each experience
        for i in 0..Length(experiences) - 1 {
            let exp = experiences[i];
            let advantage = advantages[i];

            // Compute old policy probability
            let oldProb = MeasurePolicyProbability(agent.PolicyQubits, exp.Action);

            // Compute new policy probability
            let newProb = MeasurePolicyProbability(agent.PolicyQubits, exp.Action);

            // Probability ratio
            let ratio = newProb / (oldProb + 0.0001);

            // Clipped objective
            let clippedRatio = ratio > 1.0 + clipEpsilon ? 1.0 + clipEpsilon |
                              (ratio < 1.0 - clipEpsilon ? 1.0 - clipEpsilon | ratio);

            let surrogate = MinD(ratio * advantage, clippedRatio * advantage);

            // Update policy
            UpdatePolicy(agent.PolicyQubits, agent.StateQubits, exp.Action, surrogate, config);
        }
    }

    /// # Summary
    /// Quantum Soft Actor-Critic (SAC)
    operation QuantumSACUpdate(
        agent : QuantumQLearningState,
        experience : Experience,
        config : QRLConfig,
        alpha : Double
    ) : Unit {
        // Encode state
        EncodeState(agent.StateQubits, experience.State);

        // Get Q-values from both critics
        let qValues1 = QuantumQNetwork(agent.StateQubits, agent.QValueQubits, config);

        use qValueQubits2 = Qubit[Length(agent.QValueQubits)];
        let qValues2 = QuantumQNetwork(agent.StateQubits, qValueQubits2, config);

        // Use minimum Q-value for stability
        mutable minQValues = [];
        for i in 0..Length(qValues1) - 1 {
            set minQValues += [MinD(qValues1[i], qValues2[i])];
        }

        // Compute policy entropy
        mutable policyEntropy = 0.0;
        for i in 0..Length(agent.PolicyQubits) - 1 {
            let result = M(agent.PolicyQubits[i]);
            let p = result == One ? 0.5 | 0.5; // Simplified
            set policyEntropy -= p * Log(p);
        }

        // Soft Q-value target
        mutable softQValues = [];
        for q in minQValues {
            set softQValues += [q - alpha * policyEntropy];
        }

        // Update Q-networks
        let targetQ = experience.Reward + config.Gamma * softQValues[experience.Action];
        UpdateQValues(agent.QValueQubits, experience.Action, targetQ - qValues1[experience.Action], config);
    }

    /// # Summary
    /// Quantum Double Q-Learning
    operation QuantumDoubleQLearning(
        agent : QuantumQLearningState,
        experience : Experience,
        config : QRLConfig
    ) : Unit {
        // Use two Q-networks to reduce overestimation
        use qValueQubits2 = Qubit[Length(agent.QValueQubits)];

        // Encode current state
        EncodeState(agent.StateQubits, experience.State);

        // Q1 selects action
        let qValues1 = QuantumQNetwork(agent.StateQubits, agent.QValueQubits, config);
        mutable maxQ1 = qValues1[0];
        mutable bestAction = 0;
        for i in 1..Length(qValues1) - 1 {
            if qValues1[i] > maxQ1 {
                set maxQ1 = qValues1[i];
                set bestAction = i;
            }
        }

        // Q2 evaluates action
        use nextStateQubits = Qubit[Length(agent.StateQubits)];
        EncodeState(nextStateQubits, experience.NextState);
        let qValues2 = QuantumQNetwork(nextStateQubits, qValueQubits2, config);
        let qValue2 = qValues2[bestAction];

        // Target with Q2 evaluation
        let target = experience.Reward + (experience.Done ? 0.0 | config.Gamma * qValue2);

        // Update Q1
        UpdateQValues(agent.QValueQubits, experience.Action, target - qValues1[experience.Action], config);
    }

    /// # Summary
    /// Quantum Dueling DQN
    operation QuantumDuelingDQN(
        agent : QuantumQLearningState,
        experience : Experience,
        config : QRLConfig
    ) : Unit {
        // Separate value and advantage streams
        use valueQubits = Qubit[8];
        use advantageQubits = Qubit[config.ActionDim * 4];

        // Encode state
        EncodeState(agent.StateQubits, experience.State);

        // Compute state value V(s)
        ApplyToEach(H, valueQubits);
        for i in 0..Length(agent.StateQubits) - 1 {
            for j in 0..Length(valueQubits) - 1 {
                CNOT(agent.StateQubits[i], valueQubits[j]);
            }
        }

        mutable valueSum = 0.0;
        for v in valueQubits {
            let result = M(v);
            set valueSum += result == One ? 1.0 | -1.0;
        }
        let stateValue = valueSum / IntAsDouble(Length(valueQubits));

        // Compute advantages A(s,a)
        ApplyToEach(H, advantageQubits);
        for i in 0..Length(agent.StateQubits) - 1 {
            for j in 0..Length(advantageQubits) - 1 {
                CNOT(agent.StateQubits[i], advantageQubits[j]);
            }
        }

        // Q(s,a) = V(s) + A(s,a) - mean(A(s,a'))
        mutable advantages = [];
        let advPerAction = Length(advantageQubits) / config.ActionDim;
        for action in 0..config.ActionDim - 1 {
            mutable advSum = 0.0;
            for i in 0..advPerAction - 1 {
                let idx = action * advPerAction + i;
                if idx < Length(advantageQubits) {
                    let result = M(advantageQubits[idx]);
                    set advSum += result == One ? 1.0 | -1.0;
                }
            }
            set advantages += [advSum / IntAsDouble(advPerAction)];
        }

        // Compute mean advantage
        mutable meanAdv = 0.0;
        for a in advantages {
            set meanAdv += a;
        }
        set meanAdv /= IntAsDouble(Length(advantages));

        // Q-values
        mutable qValues = [];
        for adv in advantages {
            set qValues += [stateValue + adv - meanAdv];
        }

        // Update with TD error
        use nextStateQubits = Qubit[Length(agent.StateQubits)];
        EncodeState(nextStateQubits, experience.NextState);
        use nextQValueQubits = Qubit[Length(agent.QValueQubits)];
        let nextQValues = QuantumQNetwork(nextStateQubits, nextQValueQubits, config);

        mutable maxNextQ = nextQValues[0];
        for q in nextQValues {
            if q > maxNextQ {
                set maxNextQ = q;
            }
        }

        let target = experience.Reward + (experience.Done ? 0.0 | config.Gamma * maxNextQ);
        let tdError = target - qValues[experience.Action];

        UpdateQValues(agent.QValueQubits, experience.Action, tdError, config);
    }

    /// # Summary
    /// Quantum Multi-Step Learning
    operation QuantumMultiStepLearning(
        agent : QuantumQLearningState,
        experiences : Experience[],
        config : QRLConfig,
        nSteps : Int
    ) : Unit {
        let n = MinI(nSteps, Length(experiences));

        // Compute n-step return
        mutable nStepReturn = 0.0;
        mutable gammaPower = 1.0;

        for i in 0..n - 1 {
            set nStepReturn += gammaPower * experiences[i].Reward;
            set gammaPower *= config.Gamma;
        }

        // Add bootstrapped value if not done
        if not experiences[n - 1].Done {
            use nextStateQubits = Qubit[Length(agent.StateQubits)];
            EncodeState(nextStateQubits, experiences[n - 1].NextState);
            use nextQValueQubits = Qubit[Length(agent.QValueQubits)];
            let nextQValues = QuantumQNetwork(nextStateQubits, nextQValueQubits, config);

            mutable maxNextQ = nextQValues[0];
            for q in nextQValues {
                if q > maxNextQ {
                    set maxNextQ = q;
                }
            }
            set nStepReturn += gammaPower * maxNextQ;
        }

        // Update with n-step target
        EncodeState(agent.StateQubits, experiences[0].State);
        let currentQValues = QuantumQNetwork(agent.StateQubits, agent.QValueQubits, config);
        let tdError = nStepReturn - currentQValues[experiences[0].Action];

        UpdateQValues(agent.QValueQubits, experiences[0].Action, tdError, config);
    }

    /// # Summary
    /// Quantum Prioritized Experience Replay
    operation QuantumPrioritizedReplay(
        agent : QuantumQLearningState,
        experiences : Experience[],
        priorities : Double[],
        config : QRLConfig
    ) : Unit {
        // Sample experiences based on priorities
        mutable sampledIndices = [];
        let batchSize = MinI(config.BatchSize, Length(experiences));

        // Compute sum of priorities
        mutable prioritySum = 0.0;
        for p in priorities {
            set prioritySum += p;
        }

        // Sample
        for _ in 0..batchSize - 1 {
            let rand = DrawRandomDouble(0.0, prioritySum);
            mutable cumSum = 0.0;
            mutable selectedIdx = 0;

            for i in 0..Length(priorities) - 1 {
                set cumSum += priorities[i];
                if cumSum >= rand {
                    set selectedIdx = i;
                }
            }
            set sampledIndices += [selectedIdx];
        }

        // Update sampled experiences
        for idx in sampledIndices {
            QuantumActorCriticUpdate(agent, experiences[idx], config);
        }
    }

    /// # Summary
    /// Quantum Curiosity-Driven Exploration
    operation QuantumCuriosityUpdate(
        agent : QuantumQLearningState,
        experience : Experience,
        config : QRLConfig,
        curiosityWeight : Double
    ) : Unit {
        // Forward model: predict next state
        use predictedNextState = Qubit[Length(agent.StateQubits)];
        ApplyToEach(H, predictedNextState);

        for i in 0..Length(agent.StateQubits) - 1 {
            CNOT(agent.StateQubits[i], predictedNextState[i]);
            // Learned transition
            let theta = IntAsDouble(i) * 0.1;
            Ry(theta, predictedNextState[i]);
        }

        // Compute prediction error (curiosity reward)
        mutable predictionError = 0.0;
        use actualNextState = Qubit[Length(agent.StateQubits)];
        EncodeState(actualNextState, experience.NextState);

        for i in 0..Length(predictedNextState) - 1 {
            // Compare predicted vs actual
            CNOT(predictedNextState[i], actualNextState[i]);
            let result = M(actualNextState[i]);
            set predictionError += result == One ? 1.0 | 0.0;
        }

        // Add curiosity to reward
        let intrinsicReward = curiosityWeight * predictionError;
        let totalReward = experience.Reward + intrinsicReward;

        // Update with augmented reward
        let augmentedExp = Experience(
            State: experience.State,
            Action: experience.Action,
            Reward: totalReward,
            NextState: experience.NextState,
            Done: experience.Done
        );

        QuantumActorCriticUpdate(agent, augmentedExp, config);
    }

    /// # Summary
    /// Quantum Hierarchical RL - Option framework
    operation QuantumHierarchicalRL(
        agent : QuantumQLearningState,
        experience : Experience,
        config : QRLConfig,
        option : Int
    ) : Unit {
        // Option-specific Q-values
        let optionStart = option * config.ActionDim;

        // Update option policy
        for i in 0..config.ActionDim - 1 {
            let qIdx = optionStart + i;
            if qIdx < Length(agent.QValueQubits) / 8 {
                let updateAngle = experience.Reward * config.LearningRate * PI() / 4.0;
                Ry(updateAngle, agent.QValueQubits[qIdx * 8]);
            }
        }

        // Update option termination
        if experience.Done {
            // Encourage option termination on done
            for i in 0..Length(agent.PolicyQubits) - 1 {
                Rz(PI() / 4.0, agent.PolicyQubits[i]);
            }
        }
    }

    /// # Summary
    /// Quantum Model-Based RL - Planning
    operation QuantumModelBasedPlanning(
        agent : QuantumQLearningState,
        currentState : Double[],
        config : QRLConfig,
        planningSteps : Int
    ) : Int {
        // Encode current state
        EncodeState(agent.StateQubits, currentState);

        mutable bestAction = 0;
        mutable bestValue = -1000000.0;

        // Simulate future trajectories
        for action in 0..config.ActionDim - 1 {
            mutable simulatedValue = 0.0;
            mutable gammaPower = 1.0;

            use simState = Qubit[Length(agent.StateQubits)];
            EncodeState(simState, currentState);

            for step in 0..planningSteps - 1 {
                // Simulate transition
                for i in 0..Length(simState) - 1 {
                    let theta = IntAsDouble(action * 10 + step * 5 + i) * 0.05;
                    Ry(theta, simState[i]);
                }

                // Get Q-value
                use simQValues = Qubit[Length(agent.QValueQubits)];
                let qValues = QuantumQNetwork(simState, simQValues, config);

                mutable maxQ = qValues[0];
                for q in qValues {
                    if q > maxQ {
                        set maxQ = q;
                    }
                }

                set simulatedValue += gammaPower * maxQ;
                set gammaPower *= config.Gamma;
            }

            if simulatedValue > bestValue {
                set bestValue = simulatedValue;
                set bestAction = action;
            }
        }

        return bestAction;
    }

    /// # Summary
    /// Quantum Transfer Learning for RL
    operation QuantumTransferLearning(
        sourceAgent : QuantumQLearningState,
        targetAgent : QuantumQLearningState,
        transferRatio : Double
    ) : Unit {
        // Transfer Q-value knowledge
        for i in 0..MinI(Length(sourceAgent.QValueQubits), Length(targetAgent.QValueQubits)) - 1 {
            // Entangle source and target
            CNOT(sourceAgent.QValueQubits[i], targetAgent.QValueQubits[i]);

            // Weighted transfer
            let angle = transferRatio * PI() / 2.0;
            Ry(angle, targetAgent.QValueQubits[i]);

            // Disentangle
            CNOT(sourceAgent.QValueQubits[i], targetAgent.QValueQubits[i]);
        }

        // Transfer policy knowledge
        for i in 0..MinI(Length(sourceAgent.PolicyQubits), Length(targetAgent.PolicyQubits)) - 1 {
            CNOT(sourceAgent.PolicyQubits[i], targetAgent.PolicyQubits[i]);
            let angle = transferRatio * PI() / 2.0;
            Ry(angle, targetAgent.PolicyQubits[i]);
            CNOT(sourceAgent.PolicyQubits[i], targetAgent.PolicyQubits[i]);
        }
    }

    /// # Summary
    /// Quantum Meta-Learning for fast adaptation
    operation QuantumMetaLearning(
        agents : QuantumQLearningState[],
        tasks : Experience[][],
        config : QRLConfig,
        metaLearningRate : Double
    ) : Unit {
        // Compute meta-gradient across tasks
        mutable metaGradient = [];

        for taskIdx in 0..Length(tasks) - 1 {
            let agent = agents[taskIdx % Length(agents)];
            let task = tasks[taskIdx];

            // Fast adaptation on task
            for exp in task {
                QuantumActorCriticUpdate(agent, exp, config);
            }

            // Compute task-specific gradient
            // (Simplified - would accumulate gradients)
        }

        // Meta-update: update initial parameters
        for agent in agents {
            for i in 0..Length(agent.QValueQubits) - 1 {
                let metaUpdate = metaLearningRate * PI() / 10.0;
                Ry(metaUpdate, agent.QValueQubits[i]);
            }
        }
    }

    /// # Summary
    /// Quantum ensemble of RL agents
    operation QuantumEnsembleRL(
        agents : QuantumQLearningState[],
        state : Double[],
        config : QRLConfig
    ) : Int {
        mutable allQValues = [];

        // Get Q-values from all agents
        for agent in agents {
            EncodeState(agent.StateQubits, state);
            let qValues = QuantumQNetwork(agent.StateQubits, agent.QValueQubits, config);
            set allQValues += [qValues];
        }

        // Ensemble: average Q-values
        mutable ensembleQValues = [];
        for action in 0..config.ActionDim - 1 {
            mutable sumQ = 0.0;
            for agentQValues in allQValues {
                set sumQ += agentQValues[action];
            }
            set ensembleQValues += [sumQ / IntAsDouble(Length(agents))];
        }

        // Select best action
        mutable bestAction = 0;
        mutable bestQ = ensembleQValues[0];
        for i in 1..Length(ensembleQValues) - 1 {
            if ensembleQValues[i] > bestQ {
                set bestQ = ensembleQValues[i];
                set bestAction = i;
            }
        }

        return bestAction;
    }

    /// # Summary
    /// Quantum adversarial training for robust RL
    operation QuantumAdversarialTraining(
        agent : QuantumQLearningState,
        adversary : QuantumQLearningState,
        experience : Experience,
        config : QRLConfig
    ) : Unit {
        // Agent tries to maximize reward
        QuantumActorCriticUpdate(agent, experience, config);

        // Adversary tries to perturb observations
        use perturbedState = Qubit[Length(agent.StateQubits)];
        EncodeState(perturbedState, experience.State);

        // Apply adversarial perturbation
        for i in 0..Length(perturbedState) - 1 {
            let perturbationAngle = PI() / 8.0;
            Ry(perturbationAngle, perturbedState[i]);
        }

        // Train agent to be robust to perturbations
        let perturbedExp = Experience(
            State: experience.State,
            Action: experience.Action,
            Reward: experience.Reward * 0.5, // Penalize for being fooled
            NextState: experience.NextState,
            Done: experience.Done
        );

        QuantumActorCriticUpdate(agent, perturbedExp, config);
    }

    /// # Summary
    /// Main training loop for quantum RL
    operation QuantumRLTrainingLoop(
        agent : QuantumQLearningState,
        env : (Double[] -> (Double[], Double, Bool)),
        config : QRLConfig,
        episodes : Int,
        maxSteps : Int
    ) : Double[] {
        mutable episodeRewards = [];
        mutable epsilon = config.Epsilon;

        for episode in 0..episodes - 1 {
            mutable state = [0.0]; // Initial state
            mutable episodeReward = 0.0;
            mutable done = false;
            mutable step = 0;

            mutable experiences = [];

            while not done and step < maxSteps {
                // Select action
                EncodeState(agent.StateQubits, state);
                let qValues = QuantumQNetwork(agent.StateQubits, agent.QValueQubits, config);
                let action = SelectAction(qValues, epsilon);

                // Execute action
                let (nextState, reward, newDone) = env(action);

                // Store experience
                let exp = Experience(
                    State: state,
                    Action: action,
                    Reward: reward,
                    NextState: nextState,
                    Done: newDone
                );
                set experiences += [exp];

                set episodeReward += reward;
                set state = nextState;
                set done = newDone;
                set step += 1;
            }

            // Update agent
            for exp in experiences {
                QuantumActorCriticUpdate(agent, exp, config);
            }

            // Decay epsilon
            set epsilon = MaxD(epsilon * config.EpsilonDecay, config.EpsilonMin);

            set episodeRewards += [episodeReward];

            if episode % 10 == 0 {
                Message($"Episode {episode}, Reward: {episodeReward}, Epsilon: {epsilon}");
            }
        }

        return episodeRewards;
    }
}
