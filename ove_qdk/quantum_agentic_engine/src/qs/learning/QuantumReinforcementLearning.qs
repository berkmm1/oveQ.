namespace QuantumAgentic.Learning {
    open Microsoft.Quantum.Canon;
    open Microsoft.Quantum.Intrinsic;
    open Microsoft.Quantum.Measurement;
    open Microsoft.Quantum.Arrays;
    open Microsoft.Quantum.Math;
    open Microsoft.Quantum.Convert;
    open Microsoft.Quantum.Random;
    open Microsoft.Quantum.Diagnostics;

    operation DrawRandomDouble(min : Double, max : Double) : Double {
        return min + (max - min) * Microsoft.Quantum.Random.DrawRandomDouble(0.0, 1.0);
    }

    operation DrawRandomInt(min : Int, max : Int) : Int {
        return Microsoft.Quantum.Random.DrawRandomInt(min, max);
    }

    struct QuantumQLearningState {
        QValueQubits : Qubit[],
        PolicyQubits : Qubit[],
        StateQubits : Qubit[],
        AdvantageQubits : Qubit[]
    }

    struct Experience {
        State : Double[],
        Action : Int,
        Reward : Double,
        NextState : Double[],
        Done : Bool
    }

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

    function DefaultQRLConfig() : QRLConfig {
        return QRLConfig(
            16,
            8,
            32,
            0.99,
            1.0,
            0.995,
            0.01,
            0.001,
            10000,
            32,
            100
        );
    }

    operation InitializeQRLAgent(config : QRLConfig) : QuantumQLearningState {
        use qValueQubits = Qubit[config.ActionDim * 8];
        use policyQubits = Qubit[config.ActionDim * 4];
        use stateQubits = Qubit[config.StateDim];
        use advantageQubits = Qubit[config.ActionDim];
        ApplyToEach(H, qValueQubits);
        ApplyToEach(H, policyQubits);
        ApplyToEach(H, stateQubits);
        ApplyToEach(H, advantageQubits);
        CreateQRLEntanglement(qValueQubits, policyQubits, stateQubits, advantageQubits);
        return QuantumQLearningState(
            qValueQubits,
            policyQubits,
            stateQubits,
            advantageQubits
        );
    }

    operation CreateQRLEntanglement(
        qValues : Qubit[],
        policy : Qubit[],
        state : Qubit[],
        advantage : Qubit[]
    ) : Unit {
        for i in 0..MinI(Length(state), Length(qValues) / 8) - 1 {
            for j in 0..7 {
                CNOT(state[i], qValues[i * 8 + j]);
            }
        }
        for i in 0..MinI(Length(qValues) / 8, Length(policy) / 4) - 1 {
            for j in 0..3 {
                CNOT(qValues[i * 8], policy[i * 4 + j]);
            }
        }
        for i in 0..MinI(Length(qValues) / 8, Length(advantage)) - 1 {
            CNOT(qValues[i * 8], advantage[i]);
        }
    }

    operation EncodeState(stateQubits : Qubit[], state : Double[]) : Unit {
        let n = Length(stateQubits);
        let d = Length(state);
        for i in 0..MinI(n, d) - 1 {
            let angle = ArcCos(np_clip(state[i], -1.0, 1.0));
            Ry(2.0 * angle, stateQubits[i]);
            let phase = state[i] * PI();
            Rz(phase, stateQubits[i]);
        }
    }

    function np_clip(val : Double, min : Double, max : Double) : Double {
        if (val < min) { return min; }
        if (val > max) { return max; }
        return val;
    }

    operation QuantumQNetwork(
        stateQubits : Qubit[],
        qValueQubits : Qubit[],
        config : QRLConfig
    ) : Double[] {
        use hiddenQubits = Qubit[config.HiddenDim];
        ApplyToEach(H, hiddenQubits);
        for i in 0..Length(stateQubits) - 1 {
            for j in 0..MinI(config.HiddenDim / MaxI(1, Length(stateQubits)), config.HiddenDim - 1) {
                let hIdx = (i * config.HiddenDim / MaxI(1, Length(stateQubits)) + j) % config.HiddenDim;
                CNOT(stateQubits[i], hiddenQubits[hIdx]);
            }
        }
        let qValuesPerAction = Length(qValueQubits) / MaxI(1, config.ActionDim);
        for action in 0..config.ActionDim - 1 {
            for h in 0..MinI(config.HiddenDim, qValuesPerAction) - 1 {
                let qIdx = action * qValuesPerAction + h;
                if qIdx < Length(qValueQubits) {
                    CNOT(hiddenQubits[h % config.HiddenDim], qValueQubits[qIdx]);
                    let theta = IntAsDouble(action * 10 + h) * 0.1;
                    Ry(theta, qValueQubits[qIdx]);
                }
            }
        }
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
            set qValues += [actionValue / IntAsDouble(MaxI(1, qValuesPerAction))];
        }
        return qValues;
    }

    operation SelectAction(
        qValues : Double[],
        epsilon : Double
    ) : Int {
        let rand = DrawRandomDouble(0.0, 1.0);
        if rand < epsilon {
            return DrawRandomInt(0, Length(qValues) - 1);
        } else {
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
            if Length(bestActions) > 1 {
                return bestActions[DrawRandomInt(0, Length(bestActions) - 1)];
            } else {
                return bestActions[0];
            }
        }
    }

    operation QuantumActorCriticUpdate(
        agent : QuantumQLearningState,
        experience : Experience,
        config : QRLConfig
    ) : Unit {
        EncodeState(agent.StateQubits, experience.State);
        let currentQValues = QuantumQNetwork(agent.StateQubits, agent.QValueQubits, config);
        let currentQ = currentQValues[experience.Action];
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
        let targetQ = experience.Reward + (experience.Done ? 0.0 | config.Gamma * maxNextQ);
        let tdError = targetQ - currentQ;
        UpdateQValues(agent.QValueQubits, experience.Action, tdError, config);
        UpdatePolicy(agent.PolicyQubits, agent.StateQubits, experience.Action, tdError, config);
        UpdateAdvantage(agent.AdvantageQubits, tdError, config);
    }

    operation UpdateQValues(
        qValueQubits : Qubit[],
        action : Int,
        tdError : Double,
        config : QRLConfig
    ) : Unit {
        let qValuesPerAction = Length(qValueQubits) / MaxI(1, config.ActionDim);
        let actionStart = action * qValuesPerAction;
        let updateAngle = tdError * config.LearningRate * PI();
        for i in 0..qValuesPerAction - 1 {
            let qIdx = actionStart + i;
            if qIdx < Length(qValueQubits) {
                Ry(updateAngle, qValueQubits[qIdx]);
            }
        }
    }

    operation UpdatePolicy(
        policyQubits : Qubit[],
        stateQubits : Qubit[],
        action : Int,
        advantage : Double,
        config : QRLConfig
    ) : Unit {
        let policyPerAction = Length(policyQubits) / MaxI(1, config.ActionDim);
        let actionStart = action * policyPerAction;
        let updateAngle = advantage * config.LearningRate * PI() / 2.0;
        for i in 0..policyPerAction - 1 {
            let pIdx = actionStart + i;
            if pIdx < Length(policyQubits) {
                if advantage > 0.0 {
                    Ry(updateAngle, policyQubits[pIdx]);
                } else {
                    Ry(-updateAngle, policyQubits[pIdx]);
                }
            }
        }
    }

    operation UpdateAdvantage(
        advantageQubits : Qubit[],
        tdError : Double,
        config : QRLConfig
    ) : Unit {
        for i in 0..Length(advantageQubits) - 1 {
            let angle = tdError * PI() / 2.0;
            Ry(angle, advantageQubits[i]);
        }
    }

    operation QuantumRLTrainingLoop(
        agent : QuantumQLearningState,
        env : (Int -> (Double[], Double, Bool)),
        config : QRLConfig,
        episodes : Int,
        maxSteps : Int
    ) : Double[] {
        mutable episodeRewards = [];
        mutable epsilon = config.Epsilon;
        for episode in 0..episodes - 1 {
            mutable state = [0.0, size = config.StateDim];
            mutable episodeReward = 0.0;
            mutable done = false;
            mutable step = 0;
            mutable experiences = [];
            while not done and step < maxSteps {
                EncodeState(agent.StateQubits, state);
                let qValues = QuantumQNetwork(agent.StateQubits, agent.QValueQubits, config);
                let action = SelectAction(qValues, epsilon);
                let (nextState, reward, newDone) = env(action);
                let exp = Experience(
                    state,
                    action,
                    reward,
                    nextState,
                    newDone
                );
                set experiences += [exp];
                set episodeReward += reward;
                set state = nextState;
                set done = newDone;
                set step += 1;
            }
            for exp in experiences {
                QuantumActorCriticUpdate(agent, exp, config);
            }
            set epsilon = MaxD(epsilon * config.EpsilonDecay, config.EpsilonMin);
            set episodeRewards += [episodeReward];
        }
        return episodeRewards;
    }
}
