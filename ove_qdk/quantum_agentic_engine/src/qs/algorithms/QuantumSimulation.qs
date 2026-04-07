// Quantum Simulation Module
// Hamiltonian simulation and quantum dynamics
// Part of the Quantum Agentic Loop Engine

namespace QuantumAgenticEngine.Algorithms.Simulation {
    open Microsoft.Quantum.Canon;
    open Microsoft.Quantum.Intrinsic;
    open Microsoft.Quantum.Math;
    open Microsoft.Quantum.Convert;
    open Microsoft.Quantum.Arrays;
    open Microsoft.Quantum.Measurement;
    open Microsoft.Quantum.Diagnostics;
    open QuantumAgenticEngine.Utils;

    // ============================================
    // Hamiltonian Simulation Types
    // ============================================

    /// # Summary
    /// Pauli term in Hamiltonian
    struct PauliTerm {
        Coefficient : Double,
        PauliString : Pauli[],
        QubitIndices : Int[]
    }

    /// # Summary
    /// Hamiltonian representation
    struct Hamiltonian {
        Terms : PauliTerm[],
        NumQubits : Int,
        TotalCoefficients : Double
    }

    /// # Summary
    /// Time evolution configuration
    struct TimeEvolutionConfig {
        TotalTime : Double,
        TimeSteps : Int,
        TrotterOrder : Int,
        ErrorTolerance : Double
    }

    /// # Summary
    /// Simulation result
    struct SimulationResult {
        FinalState : Double[],
        Energy : Double,
        Fidelity : Double,
        TimeElapsed : Double
    }

    // ============================================
    // Trotter-Suzuki Decomposition
    // ============================================

    /// # Summary
    /// First-order Trotter step
    operation FirstOrderTrotterStep(
        hamiltonian : Hamiltonian,
        dt : Double,
        qubits : Qubit[]
    ) : Unit is Adj + Ctl {
        for term in hamiltonian.Terms {
            // Extract qubits for this term
            mutable termQubits = new Qubit[0];
            for idx in term.QubitIndices {
                if idx < Length(qubits) {
                    set termQubits += [qubits[idx]];
                }
            }

            // Apply exp(-i * coefficient * dt * PauliString)
            let angle = -2.0 * term.Coefficient * dt;
            Exp(term.PauliString, angle, termQubits);
        }
    }

    /// # Summary
    /// Second-order Trotter step (Strang splitting)
    operation SecondOrderTrotterStep(
        hamiltonian : Hamiltonian,
        dt : Double,
        qubits : Qubit[]
    ) : Unit is Adj + Ctl {
        let halfDt = dt / 2.0;

        // First half step
        for term in hamiltonian.Terms {
            mutable termQubits = new Qubit[0];
            for idx in term.QubitIndices {
                if idx < Length(qubits) {
                    set termQubits += [qubits[idx]];
                }
            }

            let angle = -2.0 * term.Coefficient * halfDt;
            Exp(term.PauliString, angle, termQubits);
        }

        // Middle step (reverse order)
        for idx in Length(hamiltonian.Terms) - 1 .. -1 .. 0 {
            let term = hamiltonian.Terms[idx];
            mutable termQubits = new Qubit[0];
            for qIdx in term.QubitIndices {
                if qIdx < Length(qubits) {
                    set termQubits += [qubits[qIdx]];
                }
            }

            let angle = -2.0 * term.Coefficient * halfDt;
            Exp(term.PauliString, angle, termQubits);
        }
    }

    /// # Summary
    /// Higher-order Trotter-Suzuki formula
    operation HigherOrderTrotter(
        hamiltonian : Hamiltonian,
        time : Double,
        order : Int,
        qubits : Qubit[]
    ) : Unit is Adj + Ctl {
        if order == 1 {
            FirstOrderTrotterStep(hamiltonian, time, qubits);
        } elif order == 2 {
            SecondOrderTrotterStep(hamiltonian, time, qubits);
        } else {
            // Recursive construction for higher orders
            let p = 4.0; // Suzuki coefficient
            let factor = 1.0 / (p - PowD(p, 1.0 / IntAsDouble(order - 1)));

            for _ in 0 .. 1 {
                HigherOrderTrotter(hamiltonian, time * factor, order - 2, qubits);
            }
            HigherOrderTrotter(hamiltonian, time * (1.0 - 4.0 * factor), order - 2, qubits);
            for _ in 0 .. 1 {
                HigherOrderTrotter(hamiltonian, time * factor, order - 2, qubits);
            }
        }
    }

    // ============================================
    // Product Formulas
    // ============================================

    /// # Summary
    /// Lie-Trotter product formula
    operation LieTrotterFormula(
        hamiltonian : Hamiltonian,
        time : Double,
        numSteps : Int,
        qubits : Qubit[]
    ) : Unit {
        let dt = time / IntAsDouble(numSteps);

        for step in 0 .. numSteps - 1 {
            FirstOrderTrotterStep(hamiltonian, dt, qubits);
        }
    }

    /// # Summary
    /// Symmetric Trotter (Strang) formula
    operation SymmetricTrotterFormula(
        hamiltonian : Hamiltonian,
        time : Double,
        numSteps : Int,
        qubits : Qubit[]
    ) : Unit {
        let dt = time / IntAsDouble(numSteps);

        for step in 0 .. numSteps - 1 {
            SecondOrderTrotterStep(hamiltonian, dt, qubits);
        }
    }

    /// # Summary
    /// Randomized Trotter formula
    operation RandomizedTrotterFormula(
        hamiltonian : Hamiltonian,
        time : Double,
        numSteps : Int,
        qubits : Qubit[]
    ) : Unit {
        let dt = time / IntAsDouble(numSteps);
        let numTerms = Length(hamiltonian.Terms);

        for step in 0 .. numSteps - 1 {
            // Random permutation of terms
            mutable permutedIndices = new Int[numTerms];
            for i in 0 .. numTerms - 1 {
                set permutedIndices w/= i <- i;
            }

            // Apply in random order
            for i in 0 .. numTerms - 1 {
                let termIdx = permutedIndices[i];
                let term = hamiltonian.Terms[termIdx];

                mutable termQubits = new Qubit[0];
                for idx in term.QubitIndices {
                    if idx < Length(qubits) {
                        set termQubits += [qubits[idx]];
                    }
                }

                let angle = -2.0 * term.Coefficient * dt;
                Exp(term.PauliString, angle, termQubits);
            }
        }
    }

    // ============================================
    // Qubitization and Quantum Walk
    // ============================================

    /// # Summary
    /// Qubitization of Hamiltonian
    operation Qubitization(
        hamiltonian : Hamiltonian,
        time : Double,
        controlQubits : Qubit[],
        systemQubits : Qubit[]
    ) : Unit {
        // Prepare control state
        ApplyToEach(H, controlQubits);

        // Apply block encoding
        let numTerms = Length(hamiltonian.Terms);

        for termIdx in 0 .. numTerms - 1 {
            let term = hamiltonian.Terms[termIdx];

            // Controlled application of term
            if termIdx < Length(controlQubits) {
                mutable termQubits = new Qubit[0];
                for idx in term.QubitIndices {
                    if idx < Length(systemQubits) {
                        set termQubits += [systemQubits[idx]];
                    }
                }

                let angle = -2.0 * term.Coefficient * time;
                Controlled Exp([controlQubits[termIdx]], (term.PauliString, angle, termQubits));
            }
        }

        // Unprepare control state
        ApplyToEach(H, controlQubits);
    }

    /// # Summary
    /// Quantum walk operator for Hamiltonian simulation
    operation QuantumWalkOperator(
        hamiltonian : Hamiltonian,
        walkQubits : Qubit[],
        coinQubits : Qubit[]
    ) : Unit is Adj + Ctl {
        let numTerms = Length(hamiltonian.Terms);

        // Coin operator (creates superposition over terms)
        ApplyToEach(H, coinQubits);

        // Shift operator (applies Hamiltonian terms)
        for termIdx in 0 .. numTerms - 1 {
            let term = hamiltonian.Terms[termIdx];

            if termIdx < Length(coinQubits) {
                mutable termQubits = new Qubit[0];
                for idx in term.QubitIndices {
                    if idx < Length(walkQubits) {
                        set termQubits += [walkQubits[idx]];
                    }
                }

                let angle = -2.0 * term.Coefficient;
                Controlled Exp([coinQubits[termIdx]], (term.PauliString, angle, termQubits));
            }
        }
    }

    // ============================================
    // Linear Systems and Matrix Exponentiation
    // ============================================

    /// # Summary
    /// Matrix exponentiation via Hamiltonian simulation
    operation MatrixExponentiation(
        matrixQubits : Qubit[],
        vectorQubits : Qubit[],
        time : Double,
        numSteps : Int
    ) : Unit {
        let dt = time / IntAsDouble(numSteps);

        for step in 0 .. numSteps - 1 {
            // Simulate e^(-iAt) by treating A as Hamiltonian
            for i in 0 .. Length(matrixQubits) - 1 {
                for j in 0 .. Length(vectorQubits) - 1 {
                    if i == j {
                        Rz(-2.0 * dt * IntAsDouble(i), vectorQubits[j]);
                    } else {
                        // Off-diagonal coupling
                        CNOT(matrixQubits[i], vectorQubits[j]);
                        Rz(-dt, vectorQubits[j]);
                        CNOT(matrixQubits[i], vectorQubits[j]);
                    }
                }
            }
        }
    }

    /// # Summary
    /// Time evolution of quantum state
    operation TimeEvolution(
        initialState : Qubit[],
        hamiltonian : Hamiltonian,
        config : TimeEvolutionConfig
    ) : Result[] {
        let dt = config.TotalTime / IntAsDouble(config.TimeSteps);

        // Initialize state
        ApplyToEach(H, initialState);

        // Time evolution
        for step in 0 .. config.TimeSteps - 1 {
            if config.TrotterOrder == 1 {
                FirstOrderTrotterStep(hamiltonian, dt, initialState);
            } elif config.TrotterOrder == 2 {
                SecondOrderTrotterStep(hamiltonian, dt, initialState);
            } else {
                HigherOrderTrotter(hamiltonian, dt, config.TrotterOrder, initialState);
            }
        }

        // Measure final state
        mutable results = new Result[Length(initialState)];
        for i in 0 .. Length(initialState) - 1 {
            set results w/= i <- M(initialState[i]);
        }

        return results;
    }

    // ============================================
    // Specific Physical Systems
    // ============================================

    /// # Summary
    /// Transverse-field Ising model
    operation TransverseFieldIsingModel(
        spinQubits : Qubit[],
        J : Double,
        h : Double,
        time : Double,
        numSteps : Int
    ) : Unit {
        let numSpins = Length(spinQubits);
        let dt = time / IntAsDouble(numSteps);

        for step in 0 .. numSteps - 1 {
            // ZZ interactions
            for i in 0 .. numSpins - 2 {
                CNOT(spinQubits[i], spinQubits[i + 1]);
                Rz(-2.0 * J * dt, spinQubits[i + 1]);
                CNOT(spinQubits[i], spinQubits[i + 1]);
            }

            // Transverse field (X rotations)
            for i in 0 .. numSpins - 1 {
                Rx(-2.0 * h * dt, spinQubits[i]);
            }
        }
    }

    /// # Summary
    /// Heisenberg model
    operation HeisenbergModel(
        spinQubits : Qubit[],
        Jx : Double,
        Jy : Double,
        Jz : Double,
        time : Double,
        numSteps : Int
    ) : Unit {
        let numSpins = Length(spinQubits);
        let dt = time / IntAsDouble(numSteps);

        for step in 0 .. numSteps - 1 {
            for i in 0 .. numSpins - 2 {
                // XX interaction
                H(spinQubits[i]);
                H(spinQubits[i + 1]);
                CNOT(spinQubits[i], spinQubits[i + 1]);
                Rz(-2.0 * Jx * dt, spinQubits[i + 1]);
                CNOT(spinQubits[i], spinQubits[i + 1]);
                H(spinQubits[i]);
                H(spinQubits[i + 1]);

                // YY interaction
                Rx(PI() / 2.0, spinQubits[i]);
                Rx(PI() / 2.0, spinQubits[i + 1]);
                CNOT(spinQubits[i], spinQubits[i + 1]);
                Rz(-2.0 * Jy * dt, spinQubits[i + 1]);
                CNOT(spinQubits[i], spinQubits[i + 1]);
                Rx(-PI() / 2.0, spinQubits[i]);
                Rx(-PI() / 2.0, spinQubits[i + 1]);

                // ZZ interaction
                CNOT(spinQubits[i], spinQubits[i + 1]);
                Rz(-2.0 * Jz * dt, spinQubits[i + 1]);
                CNOT(spinQubits[i], spinQubits[i + 1]);
            }
        }
    }

    /// # Summary
    /// Hubbard model simulation
    operation HubbardModel(
        siteQubits : Qubit[],
        spinQubits : Qubit[],
        t : Double,
        U : Double,
        time : Double,
        numSteps : Int
    ) : Unit {
        let numSites = Length(siteQubits);
        let dt = time / IntAsDouble(numSteps);

        for step in 0 .. numSteps - 1 {
            // Hopping term
            for i in 0 .. numSites - 2 {
                // Spin-up hopping
                CNOT(siteQubits[i], siteQubits[i + 1]);
                Rz(-2.0 * t * dt, siteQubits[i + 1]);
                CNOT(siteQubits[i], siteQubits[i + 1]);

                // Spin-down hopping
                if i < Length(spinQubits) - 1 {
                    CNOT(spinQubits[i], spinQubits[i + 1]);
                    Rz(-2.0 * t * dt, spinQubits[i + 1]);
                    CNOT(spinQubits[i], spinQubits[i + 1]);
                }
            }

            // On-site interaction
            for i in 0 .. Min(numSites, Length(spinQubits)) - 1 {
                CNOT(siteQubits[i], spinQubits[i]);
                Rz(-2.0 * U * dt, spinQubits[i]);
                CNOT(siteQubits[i], spinQubits[i]);
            }
        }
    }

    /// # Summary
    /// Molecular Hamiltonian simulation
    operation MolecularHamiltonian(
        orbitalQubits : Qubit[],
        oneBodyTerms : Double[],
        twoBodyTerms : Double[],
        time : Double,
        numSteps : Int
    ) : Unit {
        let numOrbitals = Length(orbitalQubits);
        let dt = time / IntAsDouble(numSteps);

        for step in 0 .. numSteps - 1 {
            // One-body terms
            for i in 0 .. numOrbitals - 1 {
                if i < Length(oneBodyTerms) {
                    Rz(-2.0 * oneBodyTerms[i] * dt, orbitalQubits[i]);
                }
            }

            // Two-body terms
            for i in 0 .. numOrbitals - 1 {
                for j in i + 1 .. numOrbitals - 1 {
                    let termIdx = i * numOrbitals + j;
                    if termIdx < Length(twoBodyTerms) {
                        CNOT(orbitalQubits[i], orbitalQubits[j]);
                        Rz(-2.0 * twoBodyTerms[termIdx] * dt, orbitalQubits[j]);
                        CNOT(orbitalQubits[i], orbitalQubits[j]);
                    }
                }
            }
        }
    }

    // ============================================
    // Dynamics and Observables
    // ============================================

    /// # Summary
    /// Measure energy expectation value
    operation MeasureEnergy(
        stateQubits : Qubit[],
        hamiltonian : Hamiltonian,
        numShots : Int
    ) : Double {
        mutable totalEnergy = 0.0;

        for shot in 0 .. numShots - 1 {
            mutable shotEnergy = 0.0;

            for term in hamiltonian.Terms {
                // Measure Pauli string expectation
                mutable termQubits = new Qubit[0];
                for idx in term.QubitIndices {
                    if idx < Length(stateQubits) {
                        set termQubits += [stateQubits[idx]];
                    }
                }

                // Change basis and measure
                for i in 0 .. Length(term.PauliString) - 1 {
                    if i < Length(termQubits) {
                        if term.PauliString[i] == PauliX {
                            H(termQubits[i]);
                        } elif term.PauliString[i] == PauliY {
                            Rx(PI() / 2.0, termQubits[i]);
                        }
                    }
                }

                // Measure
                mutable parity = 1.0;
                for q in termQubits {
                    let result = M(q);
                    if result == One {
                        set parity *= -1.0;
                    }
                }

                set shotEnergy += term.Coefficient * parity;
            }

            set totalEnergy += shotEnergy;
        }

        return totalEnergy / IntAsDouble(numShots);
    }

    /// # Summary
    /// Measure time-dependent observable
    operation MeasureTimeDependentObservable(
        stateQubits : Qubit[],
        observable : Pauli[],
        times : Double[],
        hamiltonian : Hamiltonian
    ) : Double[] {
        mutable expectations = new Double[Length(times)];

        for tIdx in 0 .. Length(times) - 1 {
            let time = times[tIdx];

            // Evolve state to time t
            use evolvedQubits = Qubit[Length(stateQubits)];

            // Copy initial state
            for i in 0 .. Length(stateQubits) - 1 {
                CNOT(stateQubits[i], evolvedQubits[i]);
            }

            // Time evolution
            let config = TimeEvolutionConfig(
                TotalTime = time,
                TimeSteps = 10,
                TrotterOrder = 2,
                ErrorTolerance = 0.001
            );
            let _ = TimeEvolution(evolvedQubits, hamiltonian, config);

            // Measure observable
            mutable expectation = 0.0;
            for i in 0 .. Length(observable) - 1 {
                if i < Length(evolvedQubits) {
                    if observable[i] == PauliX {
                        H(evolvedQubits[i]);
                    } elif observable[i] == PauliY {
                        Rx(PI() / 2.0, evolvedQubits[i]);
                    }

                    let result = M(evolvedQubits[i]);
                    if result == One {
                        set expectation -= 1.0;
                    } else {
                        set expectation += 1.0;
                    }
                }
            }

            set expectations w/= tIdx <- expectation / IntAsDouble(Length(observable));
        }

        return expectations;
    }

    /// # Summary
    /// Compute correlation function
    operation CorrelationFunction(
        stateQubits : Qubit[],
        operatorA : Pauli[],
        operatorB : Pauli[],
        times : Double[],
        hamiltonian : Hamiltonian
    ) : Double[] {
        mutable correlations = new Double[Length(times)];

        for tIdx in 0 .. Length(times) - 1 {
            let time = times[tIdx];

            // Measure <A(t)B(0)>
            use workQubits = Qubit[Length(stateQubits)];

            // Prepare state with B applied
            for i in 0 .. Length(operatorB) - 1 {
                if i < Length(stateQubits) {
                    if operatorB[i] == PauliX {
                        H(stateQubits[i]);
                    } elif operatorB[i] == PauliY {
                        Rx(PI() / 2.0, stateQubits[i]);
                    }
                }
            }

            // Evolve
            let config = TimeEvolutionConfig(
                TotalTime = time,
                TimeSteps = 10,
                TrotterOrder = 2,
                ErrorTolerance = 0.001
            );
            let _ = TimeEvolution(stateQubits, hamiltonian, config);

            // Measure A
            mutable correlation = 0.0;
            for i in 0 .. Length(operatorA) - 1 {
                if i < Length(stateQubits) {
                    if operatorA[i] == PauliX {
                        H(stateQubits[i]);
                    } elif operatorA[i] == PauliY {
                        Rx(PI() / 2.0, stateQubits[i]);
                    }

                    let result = M(stateQubits[i]);
                    if result == One {
                        set correlation -= 1.0;
                    } else {
                        set correlation += 1.0;
                    }
                }
            }

            set correlations w/= tIdx <- correlation;
        }

        return correlations;
    }

    // ============================================
    // Adiabatic State Preparation
    // ============================================

    /// # Summary
    /// Adiabatic state preparation
    operation AdiabaticStatePreparation(
        initialHamiltonian : Hamiltonian,
        finalHamiltonian : Hamiltonian,
        qubits : Qubit[],
        totalTime : Double,
        numSteps : Int
    ) : Unit {
        let dt = totalTime / IntAsDouble(numSteps);

        // Prepare ground state of initial Hamiltonian
        ApplyToEach(H, qubits);

        // Adiabatic evolution
        for step in 0 .. numSteps - 1 {
            let s = IntAsDouble(step) / IntAsDouble(numSteps);

            // Interpolated Hamiltonian: H(s) = (1-s)H_initial + sH_final
            // Apply initial Hamiltonian part
            for term in initialHamiltonian.Terms {
                mutable termQubits = new Qubit[0];
                for idx in term.QubitIndices {
                    if idx < Length(qubits) {
                        set termQubits += [qubits[idx]];
                    }
                }

                let angle = -2.0 * term.Coefficient * (1.0 - s) * dt;
                Exp(term.PauliString, angle, termQubits);
            }

            // Apply final Hamiltonian part
            for term in finalHamiltonian.Terms {
                mutable termQubits = new Qubit[0];
                for idx in term.QubitIndices {
                    if idx < Length(qubits) {
                        set termQubits += [qubits[idx]];
                    }
                }

                let angle = -2.0 * term.Coefficient * s * dt;
                Exp(term.PauliString, angle, termQubits);
            }
        }
    }

    /// # Summary
    /// Quantum annealing simulation
    operation QuantumAnnealing(
        problemHamiltonian : Hamiltonian,
        qubits : Qubit[],
        annealingSchedule : Double[],
        totalTime : Double
    ) : Unit {
        let numSteps = Length(annealingSchedule);
        let dt = totalTime / IntAsDouble(numSteps);

        // Initial transverse field
        ApplyToEach(H, qubits);

        // Annealing schedule
        for step in 0 .. numSteps - 1 {
            let s = annealingSchedule[step];

            // Decrease transverse field
            for q in qubits {
                Rx(-2.0 * (1.0 - s) * dt, q);
            }

            // Increase problem Hamiltonian
            for term in problemHamiltonian.Terms {
                mutable termQubits = new Qubit[0];
                for idx in term.QubitIndices {
                    if idx < Length(qubits) {
                        set termQubits += [qubits[idx]];
                    }
                }

                let angle = -2.0 * term.Coefficient * s * dt;
                Exp(term.PauliString, angle, termQubits);
            }
        }
    }
}
