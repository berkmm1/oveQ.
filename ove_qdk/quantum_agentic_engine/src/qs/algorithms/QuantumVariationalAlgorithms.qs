namespace QuantumAgenticEngine.Algorithms.Variational {
    open Microsoft.Quantum.Canon;
    open Microsoft.Quantum.Intrinsic;
    open Microsoft.Quantum.Math;
    open Microsoft.Quantum.Convert;
    open Microsoft.Quantum.Measurement;
    open Microsoft.Quantum.Arrays;
    open Microsoft.Quantum.Random;
    open Microsoft.Quantum.Diagnostics;
    open Microsoft.Quantum.Characterization;
    open Microsoft.Quantum.Oracles;
    open Microsoft.Quantum.Simulation;
    open Microsoft.Quantum.Arithmetic;
    open QuantumAgenticEngine.Core;
    open QuantumAgenticEngine.Utils;

    // ========================================
    // VARIATIONAL QUANTUM ALGORITHMS
    // ========================================
    // Comprehensive implementation of variational quantum algorithms
    // including VQE, QAOA, VQLS, and advanced ansatz constructions

    // ========================================
    // DATA STRUCTURES
    // ========================================

    struct VariationalConfig {
        MaxIterations : Int,
        ConvergenceThreshold : Double,
        LearningRate : Double,
        NumShots : Int,
        OptimizerType : String,
        GradientMethod : String
    }

    struct VQEConfig {
        BaseConfig : VariationalConfig,
        MoleculeData : MolecularData,
        BasisSet : String,
        ActiveSpace : (Int, Int),
        MapperType : String
    }

    struct MolecularData {
        NumElectrons : Int,
        NumOrbitals : Int,
        NuclearRepulsion : Double,
        OneBodyIntegrals : Double[][],
        TwoBodyIntegrals : Double[][]
    }

    struct QAOAConfig {
        BaseConfig : VariationalConfig,
        ProblemHamiltonian : (Pauli[], Double)[],
        MixerType : String,
        NumLayers : Int,
        WarmStart : Bool
    }

    struct VQLSConfig {
        BaseConfig : VariationalConfig,
        MatrixA : Double[][],
        VectorB : Double[],
        AnsatzDepth : Int
    }

    struct OptimizationResult {
        OptimalParameters : Double[],
        OptimalValue : Double,
        Converged : Bool,
        Iterations : Int,
        History : Double[]
    }

    struct AnsatzConfig {
        NumQubits : Int,
        NumLayers : Int,
        Entanglement : String,
        RotationBlocks : String[],
        Repetition : String
    }

    // ========================================
    // HARDWARE-EFFICIENT ANSATZ
    // ========================================

    operation HardwareEfficientAnsatz(
        qubits : Qubit[],
        parameters : Double[],
        config : AnsatzConfig
    ) : Unit is Adj + Ctl {
        let numQubits = config.NumQubits;
        let numLayers = config.NumLayers;
        let paramsPerLayer = numQubits * 3;

        for layer in 0..numLayers - 1 {
            let layerStart = layer * paramsPerLayer;

            // Rotation layer
            for q in 0..numQubits - 1 {
                let paramIdx = layerStart + q * 3;
                Rx(parameters[paramIdx], qubits[q]);
                Ry(parameters[paramIdx + 1], qubits[q]);
                Rz(parameters[paramIdx + 2], qubits[q]);
            }

            // Entanglement layer
            ApplyEntanglementLayer(qubits, config.Entanglement, layer);
        }
    }

    operation ApplyEntanglementLayer(
        qubits : Qubit[],
        pattern : String,
        layer : Int
    ) : Unit is Adj + Ctl {
        let numQubits = Length(qubits);

        if (pattern == "linear") {
            for i in 0..numQubits - 2 {
                CNOT(qubits[i], qubits[i + 1]);
            }
        } elif (pattern == "circular") {
            for i in 0..numQubits - 2 {
                CNOT(qubits[i], qubits[i + 1]);
            }
            CNOT(qubits[numQubits - 1], qubits[0]);
        } elif (pattern == "full") {
            for i in 0..numQubits - 1 {
                for j in i + 1..numQubits - 1 {
                    CNOT(qubits[i], qubits[j]);
                }
            }
        } elif (pattern == "sca") {
            // Shifted circular alternating
            let offset = layer % 2;
            for i in offset..2..numQubits - 2 {
                CNOT(qubits[i], qubits[i + 1]);
            }
        } elif (pattern == "pairwise") {
            // Pairwise entanglement
            let start = layer % 2;
            for i in start..2..numQubits - 2 {
                if (i + 1 < numQubits) {
                    CNOT(qubits[i], qubits[i + 1]);
                }
            }
        }
    }

    // ========================================
    // UCCSD ANSATZ FOR QUANTUM CHEMISTRY
    // ========================================

    operation UCCSDAnsatz(
        qubits : Qubit[],
        parameters : Double[],
        molecule : MolecularData
    ) : Unit is Adj + Ctl {
        let numElectrons = molecule.NumElectrons;
        let numOrbitals = molecule.NumOrbitals;
        let numQubits = numOrbitals * 2; // Spin orbitals

        // Hartree-Fock reference state
        PrepareHartreeFockState(qubits, numElectrons);

        // Single excitations
        mutable paramIdx = 0;
        for p in 0..numOrbitals - 1 {
            for q in p + 1..numOrbitals - 1 {
                // Spin-up excitation
                if (IsOccupied(p, numElectrons) and not IsOccupied(q, numElectrons)) {
                    ApplySingleExcitation(qubits, p, q, parameters[paramIdx]);
                    set paramIdx += 1;
                }
                // Spin-down excitation
                if (IsOccupied(p + numOrbitals, numElectrons) and not IsOccupied(q + numOrbitals, numElectrons)) {
                    ApplySingleExcitation(qubits, p + numOrbitals, q + numOrbitals, parameters[paramIdx]);
                    set paramIdx += 1;
                }
            }
        }

        // Double excitations
        for p in 0..numOrbitals - 1 {
            for q in p + 1..numOrbitals - 1 {
                for r in 0..numOrbitals - 1 {
                    for s in r + 1..numOrbitals - 1 {
                        if (IsValidDoubleExcitation(p, q, r, s, numElectrons)) {
                            ApplyDoubleExcitation(qubits, p, q, r, s, parameters[paramIdx]);
                            set paramIdx += 1;
                        }
                    }
                }
            }
        }
    }

    operation PrepareHartreeFockState(
        qubits : Qubit[],
        numElectrons : Int
    ) : Unit is Adj + Ctl {
        // Prepare |1...10...0> with numElectrons ones
        for i in 0..numElectrons - 1 {
            X(qubits[i]);
        }
    }

    function IsOccupied(orbital : Int, numElectrons : Int) : Bool {
        return orbital < numElectrons;
    }

    function IsValidDoubleExcitation(
        p : Int, q : Int, r : Int, s : Int, numElectrons : Int
    ) : Bool {
        return (IsOccupied(p, numElectrons) and IsOccupied(q, numElectrons) and
                not IsOccupied(r, numElectrons) and not IsOccupied(s, numElectrons));
    }

    operation ApplySingleExcitation(
        qubits : Qubit[],
        i : Int,
        j : Int,
        theta : Double
    ) : Unit is Adj + Ctl {
        // Single excitation: exp(-i*theta*(a_i^dagger a_j - h.c.))
        use ancilla = Qubit();

        // Prepare ancilla in |+> state
        H(ancilla);

        // Controlled excitation
        Controlled X([ancilla, qubits[i]], qubits[j]);
        Controlled X([ancilla, qubits[j]], qubits[i]);

        // Phase rotation
        Rz(2.0 * theta, ancilla);

        // Uncompute
        Controlled X([ancilla, qubits[j]], qubits[i]);
        Controlled X([ancilla, qubits[i]], qubits[j]);

        H(ancilla);
    }

    operation ApplyDoubleExcitation(
        qubits : Qubit[],
        p : Int, q : Int, r : Int, s : Int,
        theta : Double
    ) : Unit is Adj + Ctl {
        // Double excitation: exp(-i*theta*(a_p^dagger a_q^dagger a_r a_s - h.c.))
        use ancilla = Qubit();

        H(ancilla);

        // Four-qubit controlled operation
        Controlled X([ancilla, qubits[p], qubits[q]], qubits[r]);
        Controlled X([ancilla, qubits[p], qubits[q]], qubits[s]);

        Rz(2.0 * theta, ancilla);

        Controlled X([ancilla, qubits[p], qubits[q]], qubits[s]);
        Controlled X([ancilla, qubits[p], qubits[q]], qubits[r]);

        H(ancilla);
    }

    // ========================================
    // ADAPT-VQE ALGORITHM
    // ========================================

    operation AdaptVQE(
        molecule : MolecularData,
        config : VQEConfig
    ) : OptimizationResult {
        let numQubits = molecule.NumOrbitals * 2;
        let threshold = config.BaseConfig.ConvergenceThreshold;
        let maxIterations = config.BaseConfig.MaxIterations;

        mutable operatorPool = BuildOperatorPool(molecule);
        mutable selectedOperators = new (Int, Double)[0];
        mutable currentEnergy = 0.0;
        mutable converged = false;
        mutable iteration = 0;
        mutable energyHistory = new Double[0];

        // Initial state preparation
        use qubits = Qubit[numQubits];
        PrepareHartreeFockState(qubits, molecule.NumElectrons);

        repeat {
            // Find operator with largest gradient
            let (bestOpIdx, maxGradient) = FindLargestGradient(
                qubits, operatorPool, molecule, config
            );

            if (AbsD(maxGradient) < threshold) {
                set converged = true;
            } else {
                // Add operator to ansatz
                set selectedOperators += [(bestOpIdx, 0.0)];

                // Optimize all parameters
                let optimized = OptimizeAdaptParameters(
                    qubits, selectedOperators, operatorPool, molecule, config
                );
                set selectedOperators = optimized;

                // Measure energy
                set currentEnergy = MeasureEnergy(qubits, molecule, config);
                set energyHistory += [currentEnergy];

                set iteration += 1;
            }
        } until (converged or iteration >= maxIterations);

        // Extract final parameters
        mutable finalParams = new Double[Length(selectedOperators)];
        for i in 0..Length(selectedOperators) - 1 {
            set finalParams w/= i <- selectedOperators[i]::1;
        }

        return OptimizationResult(
            OptimalParameters: finalParams,
            OptimalValue: currentEnergy,
            Converged: converged,
            Iterations: iteration,
            History: energyHistory
        );
    }

    function BuildOperatorPool(molecule : MolecularData) : (Pauli[], Double)[][] {
        // Build pool of excitation operators
        let numOrbitals = molecule.NumOrbitals;
        mutable pool = new (Pauli[], Double)[][0];

        // Add single excitations
        for p in 0..numOrbitals - 1 {
            for q in p + 1..numOrbitals - 1 {
                let op = BuildExcitationOperator(p, q, numOrbitals);
                set pool += [op];
            }
        }

        // Add double excitations
        for p in 0..numOrbitals - 1 {
            for q in p + 1..numOrbitals - 1 {
                for r in 0..numOrbitals - 1 {
                    for s in r + 1..numOrbitals - 1 {
                        let op = BuildDoubleExcitationOperator(p, q, r, s, numOrbitals);
                        set pool += [op];
                    }
                }
            }
        }

        return pool;
    }

    function BuildExcitationOperator(
        i : Int, j : Int, numOrbitals : Int
    ) : (Pauli[], Double)[] {
        // Build Jordan-Wigner representation of a_i^dagger a_j
        mutable terms = new (Pauli[], Double)[0];

        // X_i X_j + Y_i Y_j with appropriate Z strings
        mutable xString = new Pauli[numOrbitals * 2];
        mutable yString = new Pauli[numOrbitals * 2];

        for k in 0..numOrbitals * 2 - 1 {
            set xString w/= k <- PauliI;
            set yString w/= k <- PauliI;
        }

        set xString w/= i <- PauliX;
        set xString w/= j <- PauliX;
        set yString w/= i <- PauliY;
        set yString w/= j <- PauliY;

        // Add Z strings
        for k in i + 1..j - 1 {
            set xString w/= k <- PauliZ;
            set yString w/= k <- PauliZ;
        }

        set terms += [(xString, 0.5)];
        set terms += [(yString, 0.5)];

        return terms;
    }

    function BuildDoubleExcitationOperator(
        p : Int, q : Int, r : Int, s : Int,
        numOrbitals : Int
    ) : (Pauli[], Double)[] {
        // Build Jordan-Wigner representation of double excitation
        mutable terms = new (Pauli[], Double)[0];

        // Various combinations of X and Y
        let combinations = [
            (PauliX, PauliX, PauliX, PauliX),
            (PauliX, PauliX, PauliY, PauliY),
            (PauliX, PauliY, PauliX, PauliY),
            (PauliX, PauliY, PauliY, PauliX),
            (PauliY, PauliX, PauliX, PauliY),
            (PauliY, PauliX, PauliY, PauliX),
            (PauliY, PauliY, PauliX, PauliX),
            (PauliY, PauliY, PauliY, PauliY)
        ];

        for (px, py, rx, ry) in combinations {
            mutable pauliString = new Pauli[numOrbitals * 2];
            for k in 0..numOrbitals * 2 - 1 {
                set pauliString w/= k <- PauliI;
            }
            set pauliString w/= p <- px;
            set pauliString w/= q <- py;
            set pauliString w/= r <- rx;
            set pauliString w/= s <- ry;

            // Add Z strings between operators
            for k in Min([p, q, r, s]) + 1..Max([p, q, r, s]) - 1 {
                if (k != p and k != q and k != r and k != s) {
                    set pauliString w/= k <- PauliZ;
                }
            }

            set terms += [(pauliString, 0.125)];
        }

        return terms;
    }

    operation FindLargestGradient(
        qubits : Qubit[],
        operatorPool : (Pauli[], Double)[][],
        molecule : MolecularData,
        config : VQEConfig
    ) : (Int, Double) {
        mutable maxGradient = 0.0;
        mutable bestIdx = 0;

        for opIdx in 0..Length(operatorPool) - 1 {
            let gradient = ComputeOperatorGradient(
                qubits, operatorPool[opIdx], molecule, config
            );

            if (AbsD(gradient) > AbsD(maxGradient)) {
                set maxGradient = gradient;
                set bestIdx = opIdx;
            }
        }

        return (bestIdx, maxGradient);
    }

    operation ComputeOperatorGradient(
        qubits : Qubit[],
        operator : (Pauli[], Double)[],
        molecule : MolecularData,
        config : VQEConfig
    ) : Double {
        // Compute gradient using parameter shift rule
        let shift = PI() / 2.0;

        // Forward shift
        use forwardQubits = Qubit[Length(qubits)];
        ApplyAdaptAnsatz(forwardQubits, [(0, shift)], [operator]);
        let forwardEnergy = MeasureEnergy(forwardQubits, molecule, config);

        // Backward shift
        use backwardQubits = Qubit[Length(qubits)];
        ApplyAdaptAnsatz(backwardQubits, [(0, -shift)], [operator]);
        let backwardEnergy = MeasureEnergy(backwardQubits, molecule, config);

        return 0.5 * (forwardEnergy - backwardEnergy);
    }

    operation ApplyAdaptAnsatz(
        qubits : Qubit[],
        parameters : (Int, Double)[],
        operatorPool : (Pauli[], Double)[][]
    ) : Unit is Adj + Ctl {
        for (opIdx, theta) in parameters {
            let operator = operatorPool[opIdx];
            ApplyEvolutionOperator(qubits, operator, theta);
        }
    }

    operation ApplyEvolutionOperator(
        qubits : Qubit[],
        operator : (Pauli[], Double)[],
        theta : Double
    ) : Unit is Adj + Ctl {
        for (pauliString, coefficient) in operator {
            let time = theta * coefficient;
            ExpPauli(time, pauliString, qubits);
        }
    }

    function OptimizeAdaptParameters(
        qubits : Qubit[],
        selectedOperators : (Int, Double)[],
        operatorPool : (Pauli[], Double)[][],
        molecule : MolecularData,
        config : VQEConfig
    ) : (Int, Double)[] {
        // Simple gradient descent optimization
        let learningRate = config.BaseConfig.LearningRate;
        let maxOptIter = 100;

        mutable optimized = selectedOperators;

        for optIter in 0..maxOptIter - 1 {
            mutable newOperators = new (Int, Double)[Length(optimized)];

            for i in 0..Length(optimized) - 1 {
                let (opIdx, currentTheta) = optimized[i];
                let gradient = ComputeSingleGradient(
                    qubits, i, optimized, operatorPool, molecule, config
                );
                let newTheta = currentTheta - learningRate * gradient;
                set newOperators w/= i <- (opIdx, newTheta);
            }

            set optimized = newOperators;
        }

        return optimized;
    }

    operation ComputeSingleGradient(
        qubits : Qubit[],
        paramIdx : Int,
        selectedOperators : (Int, Double)[],
        operatorPool : (Pauli[], Double)[][],
        molecule : MolecularData,
        config : VQEConfig
    ) : Double {
        let shift = PI() / 2.0;
        let (opIdx, currentTheta) = selectedOperators[paramIdx];

        // Forward parameter shift
        mutable forwardParams = selectedOperators;
        set forwardParams w/= paramIdx <- (opIdx, currentTheta + shift);

        use forwardQubits = Qubit[Length(qubits)];
        ApplyAdaptAnsatz(forwardQubits, forwardParams, operatorPool);
        let forwardEnergy = MeasureEnergy(forwardQubits, molecule, config);

        // Backward parameter shift
        mutable backwardParams = selectedOperators;
        set backwardParams w/= paramIdx <- (opIdx, currentTheta - shift);

        use backwardQubits = Qubit[Length(qubits)];
        ApplyAdaptAnsatz(backwardQubits, backwardParams, operatorPool);
        let backwardEnergy = MeasureEnergy(backwardQubits, molecule, config);

        return 0.5 * (forwardEnergy - backwardEnergy);
    }

    // ========================================
    // QAOA IMPLEMENTATION
    // ========================================

    operation QAOA(
        config : QAOAConfig
    ) : OptimizationResult {
        let numQubits = GetNumQubits(config.ProblemHamiltonian);
        let numLayers = config.NumLayers;
        let numParams = numLayers * 2; // gamma and beta for each layer

        mutable parameters = InitializeQAOAParameters(config);
        mutable bestEnergy = 0.0;
        mutable converged = false;
        mutable iteration = 0;
        mutable energyHistory = new Double[0];

        repeat {
            // Evaluate cost function
            let energy = EvaluateQAOAEnergy(numQubits, parameters, config);
            set energyHistory += [energy];

            if (energy < bestEnergy or iteration == 0) {
                set bestEnergy = energy;
            }

            // Update parameters using optimizer
            let gradients = ComputeQAOAGradients(numQubits, parameters, config);
            set parameters = UpdateParameters(parameters, gradients, config);

            // Check convergence
            if (iteration > 10) {
                let recentChange = AbsD(energyHistory[iteration] - energyHistory[iteration - 10]);
                if (recentChange < config.BaseConfig.ConvergenceThreshold) {
                    set converged = true;
                }
            }

            set iteration += 1;
        } until (converged or iteration >= config.BaseConfig.MaxIterations);

        return OptimizationResult(
            OptimalParameters: parameters,
            OptimalValue: bestEnergy,
            Converged: converged,
            Iterations: iteration,
            History: energyHistory
        );
    }

    function GetNumQubits(hamiltonian : (Pauli[], Double)[]) : Int {
        if (Length(hamiltonian) > 0) {
            return Length(hamiltonian[0]::0);
        }
        return 0;
    }

    function InitializeQAOAParameters(config : QAOAConfig) : Double[] {
        mutable params = new Double[config.NumLayers * 2];

        if (config.WarmStart) {
            // Warm start with classical solution
            for i in 0..config.NumLayers - 1 {
                set params w/= i <- 0.1 * IntAsDouble(i + 1);
                set params w/= (i + config.NumLayers) <- 0.1 * IntAsDouble(i + 1);
            }
        } else {
            // Random initialization
            for i in 0..Length(params) - 1 {
                set params w/= i <- DrawRandomDouble(0.0, 0.1);
            }
        }

        return params;
    }

    operation EvaluateQAOAEnergy(
        numQubits : Int,
        parameters : Double[],
        config : QAOAConfig
    ) : Double {
        let numShots = config.BaseConfig.NumShots;
        mutable totalEnergy = 0.0;

        for shot in 0..numShots - 1 {
            use qubits = Qubit[numQubits];

            // Prepare QAOA state
            PrepareQAOAState(qubits, parameters, config);

            // Measure energy
            let sampleEnergy = MeasureHamiltonian(qubits, config.ProblemHamiltonian);
            set totalEnergy += sampleEnergy;
        }

        return totalEnergy / IntAsDouble(numShots);
    }

    operation PrepareQAOAState(
        qubits : Qubit[],
        parameters : Double[],
        config : QAOAConfig
    ) : Unit is Adj + Ctl {
        let numLayers = config.NumLayers;
        let numQubits = Length(qubits);

        // Initial superposition
        for q in qubits {
            H(q);
        }

        // Apply QAOA layers
        for layer in 0..numLayers - 1 {
            let gamma = parameters[layer];
            let beta = parameters[layer + numLayers];

            // Apply problem Hamiltonian
            ApplyProblemHamiltonian(qubits, gamma, config.ProblemHamiltonian);

            // Apply mixer
            ApplyMixerHamiltonian(qubits, beta, config.MixerType);
        }
    }

    operation ApplyProblemHamiltonian(
        qubits : Qubit[],
        gamma : Double,
        hamiltonian : (Pauli[], Double)[]
    ) : Unit is Adj + Ctl {
        for (pauliString, coefficient) in hamiltonian {
            let angle = 2.0 * gamma * coefficient;
            ExpPauli(angle, pauliString, qubits);
        }
    }

    operation ApplyMixerHamiltonian(
        qubits : Qubit[],
        beta : Double,
        mixerType : String
    ) : Unit is Adj + Ctl {
        if (mixerType == "X") {
            // Standard X mixer
            for q in qubits {
                Rx(2.0 * beta, q);
            }
        } elif (mixerType == "XY") {
            // XY mixer (preserves Hamming weight)
            let numQubits = Length(qubits);
            for i in 0..numQubits - 1 {
                for j in i + 1..numQubits - 1 {
                    // XX + YY coupling
                    use ancilla = Qubit();
                    H(ancilla);

                    Controlled X([ancilla], qubits[i]);
                    Controlled X([ancilla], qubits[j]);
                    Rz(2.0 * beta, ancilla);
                    Controlled X([ancilla], qubits[j]);
                    Controlled X([ancilla], qubits[i]);

                    H(ancilla);
                }
            }
        } elif (mixerType == "controlled") {
            // Controlled mixer with constraints
            for q in qubits {
                Rx(2.0 * beta, q);
            }
            // Add constraint-preserving operations
        }
    }

    operation MeasureHamiltonian(
        qubits : Qubit[],
        hamiltonian : (Pauli[], Double)[]
    ) : Double {
        mutable energy = 0.0;

        for (pauliString, coefficient) in hamiltonian {
            let expectation = MeasurePauliExpectation(qubits, pauliString);
            set energy += coefficient * expectation;
        }

        return energy;
    }

    operation MeasurePauliExpectation(
        qubits : Qubit[],
        pauliString : Pauli[]
    ) : Double {
        // Measure expectation value of Pauli string
        use measureQubits = Qubit[Length(qubits)];

        // Copy state
        for i in 0..Length(qubits) - 1 {
            CNOT(qubits[i], measureQubits[i]);
        }

        // Apply basis rotations
        for i in 0..Length(pauliString) - 1 {
            if (pauliString[i] == PauliX) {
                H(measureQubits[i]);
            } elif (pauliString[i] == PauliY) {
                Rx(PI() / 2.0, measureQubits[i]);
            }
        }

        // Measure
        mutable parity = 0;
        for i in 0..Length(pauliString) - 1 {
            if (pauliString[i] != PauliI) {
                let result = M(measureQubits[i]);
                if (result == One) {
                    set parity = 1 - parity;
                }
            }
        }

        ResetAll(measureQubits);

        return parity == 0 ? 1.0 | -1.0;
    }

    operation ComputeQAOAGradients(
        numQubits : Int,
        parameters : Double[],
        config : QAOAConfig
    ) : Double[] {
        let shift = PI() / 2.0;
        mutable gradients = new Double[Length(parameters)];

        for i in 0..Length(parameters) - 1 {
            // Forward shift
            mutable forwardParams = parameters;
            set forwardParams w/= i <- parameters[i] + shift;
            let forwardEnergy = EvaluateQAOAEnergy(numQubits, forwardParams, config);

            // Backward shift
            mutable backwardParams = parameters;
            set backwardParams w/= i <- parameters[i] - shift;
            let backwardEnergy = EvaluateQAOAEnergy(numQubits, backwardParams, config);

            set gradients w/= i <- 0.5 * (forwardEnergy - backwardEnergy);
        }

        return gradients;
    }

    function UpdateParameters(
        parameters : Double[],
        gradients : Double[],
        config : QAOAConfig
    ) : Double[] {
        let learningRate = config.BaseConfig.LearningRate;
        mutable newParams = parameters;

        for i in 0..Length(parameters) - 1 {
            set newParams w/= i <- parameters[i] - learningRate * gradients[i];
        }

        return newParams;
    }

    // ========================================
    // VQLS - VARIATIONAL QUANTUM LINEAR SOLVER
    // ========================================

    operation VQLS(
        config : VQLSConfig
    ) : OptimizationResult {
        let numQubits = Ceiling(Lg(IntAsDouble(Length(config.VectorB))));
        let ansatzDepth = config.AnsatzDepth;
        let numParams = numQubits * ansatzDepth * 3;

        mutable parameters = InitializeVQLSParameters(numParams);
        mutable bestCost = 0.0;
        mutable converged = false;
        mutable iteration = 0;
        mutable costHistory = new Double[0];

        repeat {
            // Evaluate cost function
            let cost = EvaluateVQLSCost(numQubits, parameters, config);
            set costHistory += [cost];

            if (cost < bestCost or iteration == 0) {
                set bestCost = cost;
            }

            // Compute gradients
            let gradients = ComputeVQLSGradients(numQubits, parameters, config);

            // Update parameters
            set parameters = UpdateVQLSParameters(parameters, gradients, config);

            // Check convergence
            if (iteration > 10) {
                let recentChange = AbsD(costHistory[iteration] - costHistory[iteration - 10]);
                if (recentChange < config.BaseConfig.ConvergenceThreshold) {
                    set converged = true;
                }
            }

            set iteration += 1;
        } until (converged or iteration >= config.BaseConfig.MaxIterations);

        return OptimizationResult(
            OptimalParameters: parameters,
            OptimalValue: bestCost,
            Converged: converged,
            Iterations: iteration,
            History: costHistory
        );
    }

    function InitializeVQLSParameters(numParams : Int) : Double[] {
        mutable params = new Double[numParams];
        for i in 0..numParams - 1 {
            set params w/= i <- DrawRandomDouble(-0.1, 0.1);
        }
        return params;
    }

    operation EvaluateVQLSCost(
        numQubits : Int,
        parameters : Double[],
        config : VQLSConfig
    ) : Double {
        let numShots = config.BaseConfig.NumShots;
        let matrixA = config.MatrixA;
        let vectorB = config.VectorB;

        // Decompose A into Pauli terms
        let pauliDecomposition = DecomposeMatrix(matrixA);

        mutable totalCost = 0.0;

        // Compute |psi> = A|x> - |b>
        for shot in 0..numShots - 1 {
            use qubits = Qubit[numQubits];
            use ancilla = Qubit();

            // Prepare |x> using ansatz
            PrepareVQLSAnsatz(qubits, parameters, config);

            // Apply A to |x>
            H(ancilla);
            for (pauliString, coefficient, idx) in pauliDecomposition {
                Controlled ApplyPauliString([ancilla], (pauliString, qubits));
                Rz(2.0 * coefficient, ancilla);
                Controlled Adjoint ApplyPauliString([ancilla], (pauliString, qubits));
            }
            H(ancilla);

            // Measure overlap with |b>
            let ancillaResult = M(ancilla);
            if (ancillaResult == One) {
                set totalCost += 1.0;
            }

            ResetAll(qubits);
            Reset(ancilla);
        }

        return totalCost / IntAsDouble(numShots);
    }

    operation PrepareVQLSAnsatz(
        qubits : Qubit[],
        parameters : Double[],
        config : VQLSConfig
    ) : Unit is Adj + Ctl {
        let numQubits = Length(qubits);
        let depth = config.AnsatzDepth;
        let paramsPerLayer = numQubits * 3;

        for layer in 0..depth - 1 {
            let layerStart = layer * paramsPerLayer;

            // Rotation layer
            for q in 0..numQubits - 1 {
                let paramIdx = layerStart + q * 3;
                Rx(parameters[paramIdx], qubits[q]);
                Ry(parameters[paramIdx + 1], qubits[q]);
                Rz(parameters[paramIdx + 2], qubits[q]);
            }

            // Entanglement layer
            for q in 0..numQubits - 2 {
                CNOT(qubits[q], qubits[q + 1]);
            }
        }
    }

    function DecomposeMatrix(matrix : Double[][]) : (Pauli[], Double, Int)[] {
        // Simplified Pauli decomposition
        let n = Length(matrix);
        let numQubits = Ceiling(Lg(IntAsDouble(n)));

        mutable decomposition = new (Pauli[], Double, Int)[0];

        // Generate all Pauli strings
        let pauliStrings = GenerateAllPauliStrings(numQubits);

        for (pauliString, idx) in pauliStrings {
            let coefficient = ComputePauliCoefficient(matrix, pauliString);
            if (AbsD(coefficient) > 1e-10) {
                set decomposition += [(pauliString, coefficient, idx)];
            }
        }

        return decomposition;
    }

    function GenerateAllPauliStrings(numQubits : Int) : (Pauli[], Int)[] {
        let numStrings = 4^numQubits;
        mutable result = new (Pauli[], Int)[0];

        for i in 0..numStrings - 1 {
            mutable pauliString = new Pauli[numQubits];
            mutable temp = i;
            for q in 0..numQubits - 1 {
                let pauliIdx = temp % 4;
                set temp = temp / 4;

                if (pauliIdx == 0) {
                    set pauliString w/= q <- PauliI;
                } elif (pauliIdx == 1) {
                    set pauliString w/= q <- PauliX;
                } elif (pauliIdx == 2) {
                    set pauliString w/= q <- PauliY;
                } else {
                    set pauliString w/= q <- PauliZ;
                }
            }
            set result += [(pauliString, i)];
        }

        return result;
    }

    function ComputePauliCoefficient(
        matrix : Double[][],
        pauliString : Pauli[]
    ) : Double {
        // Compute Tr(matrix * PauliString) / 2^n
        let n = Length(matrix);
        mutable trace = 0.0;

        for i in 0..n - 1 {
            for j in 0..n - 1 {
                let pauliElement = GetPauliMatrixElement(pauliString, i, j);
                set trace += matrix[i][j] * pauliElement;
            }
        }

        return trace / IntAsDouble(n);
    }

    function GetPauliMatrixElement(
        pauliString : Pauli[],
        i : Int, j : Int
    ) : Double {
        // Get matrix element of Pauli string
        mutable result = 1.0;

        for q in 0..Length(pauliString) - 1 {
            let bitI = (i >>> q) &&& 1;
            let bitJ = (j >>> q) &&& 1;

            let pauli = pauliString[q];
            mutable element = 0.0;

            if (pauli == PauliI) {
                set element = bitI == bitJ ? 1.0 | 0.0;
            } elif (pauli == PauliX) {
                set element = bitI != bitJ ? 1.0 | 0.0;
            } elif (pauli == PauliY) {
                if (bitI == 0 and bitJ == 1) {
                    set element = -1.0;
                } elif (bitI == 1 and bitJ == 0) {
                    set element = 1.0;
                }
            } elif (pauli == PauliZ) {
                set element = bitI == bitJ ? (bitI == 0 ? 1.0 | -1.0) | 0.0;
            }

            set result *= element;
        }

        return result;
    }

    operation ApplyPauliString(
        pauliString : Pauli[],
        qubits : Qubit[]
    ) : Unit is Adj + Ctl {
        for q in 0..Length(pauliString) - 1 {
            if (pauliString[q] == PauliX) {
                X(qubits[q]);
            } elif (pauliString[q] == PauliY) {
                Y(qubits[q]);
            } elif (pauliString[q] == PauliZ) {
                Z(qubits[q]);
            }
        }
    }

    operation ComputeVQLSGradients(
        numQubits : Int,
        parameters : Double[],
        config : VQLSConfig
    ) : Double[] {
        let shift = PI() / 2.0;
        mutable gradients = new Double[Length(parameters)];

        for i in 0..Length(parameters) - 1 {
            mutable forwardParams = parameters;
            set forwardParams w/= i <- parameters[i] + shift;
            let forwardCost = EvaluateVQLSCost(numQubits, forwardParams, config);

            mutable backwardParams = parameters;
            set backwardParams w/= i <- parameters[i] - shift;
            let backwardCost = EvaluateVQLSCost(numQubits, backwardParams, config);

            set gradients w/= i <- 0.5 * (forwardCost - backwardCost);
        }

        return gradients;
    }

    function UpdateVQLSParameters(
        parameters : Double[],
        gradients : Double[],
        config : VQLSConfig
    ) : Double[] {
        let learningRate = config.BaseConfig.LearningRate;
        mutable newParams = parameters;

        for i in 0..Length(parameters) - 1 {
            set newParams w/= i <- parameters[i] - learningRate * gradients[i];
        }

        return newParams;
    }

    // ========================================
    // VQE - VARIATIONAL QUANTUM EIGENSOLVER
    // ========================================

    operation VQE(
        molecule : MolecularData,
        config : VQEConfig
    ) : OptimizationResult {
        let numQubits = molecule.NumOrbitals * 2;
        let numParams = EstimateNumVQEParameters(molecule);

        mutable parameters = InitializeVQEParameters(numParams);
        mutable bestEnergy = 0.0;
        mutable converged = false;
        mutable iteration = 0;
        mutable energyHistory = new Double[0];

        repeat {
            // Evaluate energy
            let energy = EvaluateVQEEnergy(numQubits, parameters, molecule, config);
            set energyHistory += [energy];

            if (energy < bestEnergy or iteration == 0) {
                set bestEnergy = energy;
            }

            // Compute gradients
            let gradients = ComputeVQEGradients(numQubits, parameters, molecule, config);

            // Update parameters
            set parameters = UpdateVQEParameters(parameters, gradients, config);

            // Check convergence
            if (iteration > 10) {
                let recentChange = AbsD(energyHistory[iteration] - energyHistory[iteration - 10]);
                if (recentChange < config.BaseConfig.ConvergenceThreshold) {
                    set converged = true;
                }
            }

            set iteration += 1;
        } until (converged or iteration >= config.BaseConfig.MaxIterations);

        return OptimizationResult(
            OptimalParameters: parameters,
            OptimalValue: bestEnergy,
            Converged: converged,
            Iterations: iteration,
            History: energyHistory
        );
    }

    function EstimateNumVQEParameters(molecule : MolecularData) : Int {
        // Estimate based on excitation rank
        let numOrbitals = molecule.NumOrbitals;
        let numElectrons = molecule.NumElectrons;

        // Single excitations
        let singleExcitations = numElectrons * (numOrbitals - numElectrons / 2);

        // Double excitations (approximate)
        let doubleExcitations = singleExcitations * singleExcitations / 4;

        return singleExcitations + doubleExcitations;
    }

    function InitializeVQEParameters(numParams : Int) : Double[] {
        mutable params = new Double[numParams];
        for i in 0..numParams - 1 {
            set params w/= i <- DrawRandomDouble(-0.01, 0.01);
        }
        return params;
    }

    operation EvaluateVQEEnergy(
        numQubits : Int,
        parameters : Double[],
        molecule : MolecularData,
        config : VQEConfig
    ) : Double {
        let numShots = config.BaseConfig.NumShots;

        // Get molecular Hamiltonian in Pauli form
        let hamiltonian = GetMolecularHamiltonian(molecule);

        mutable totalEnergy = 0.0;

        for shot in 0..numShots - 1 {
            use qubits = Qubit[numQubits];

            // Prepare ansatz state
            UCCSDAnsatz(qubits, parameters, molecule);

            // Measure energy
            let sampleEnergy = MeasureHamiltonian(qubits, hamiltonian);
            set totalEnergy += sampleEnergy;

            ResetAll(qubits);
        }

        return totalEnergy / IntAsDouble(numShots);
    }

    function GetMolecularHamiltonian(molecule : MolecularData) : (Pauli[], Double)[] {
        // Convert molecular integrals to Pauli Hamiltonian
        mutable hamiltonian = new (Pauli[], Double)[0];

        let numOrbitals = molecule.NumOrbitals;
        let numQubits = numOrbitals * 2;

        // One-body terms
        for p in 0..numOrbitals - 1 {
            for q in 0..numOrbitals - 1 {
                let integral = molecule.OneBodyIntegrals[p][q];
                if (AbsD(integral) > 1e-10) {
                    // Spin-up contribution
                    let pauliUp = OneBodyToPauli(p, q, numQubits, 0);
                    set hamiltonian += [(pauliUp, integral)];

                    // Spin-down contribution
                    let pauliDown = OneBodyToPauli(p, q, numQubits, numOrbitals);
                    set hamiltonian += [(pauliDown, integral)];
                }
            }
        }

        // Two-body terms
        for p in 0..numOrbitals - 1 {
            for q in 0..numOrbitals - 1 {
                for r in 0..numOrbitals - 1 {
                    for s in 0..numOrbitals - 1 {
                        let integral = molecule.TwoBodyIntegrals[p * numOrbitals + q][r * numOrbitals + s];
                        if (AbsD(integral) > 1e-10) {
                            // Add two-body Pauli terms
                            let pauliTerms = TwoBodyToPauli(p, q, r, s, numQubits);
                            for (pauliString, coeff) in pauliTerms {
                                set hamiltonian += [(pauliString, integral * coeff)];
                            }
                        }
                    }
                }
            }
        }

        // Add nuclear repulsion
        mutable identityString = new Pauli[numQubits];
        for i in 0..numQubits - 1 {
            set identityString w/= i <- PauliI;
        }
        set hamiltonian += [(identityString, molecule.NuclearRepulsion)];

        return hamiltonian;
    }

    function OneBodyToPauli(
        p : Int, q : Int,
        numQubits : Int,
        spinOffset : Int
    ) : Pauli[] {
        mutable pauliString = new Pauli[numQubits];
        for i in 0..numQubits - 1 {
            set pauliString w/= i <- PauliI;
        }

        let i = p + spinOffset;
        let j = q + spinOffset;

        // a_i^dagger a_j + h.c. mapped to Pauli operators
        // Simplified Jordan-Wigner
        for k in Min([i, j]) + 1..Max([i, j]) - 1 {
            set pauliString w/= k <- PauliZ;
        }

        if (i == j) {
            set pauliString w/= i <- PauliZ;
        } else {
            set pauliString w/= i <- PauliX;
            set pauliString w/= j <- PauliX;
        }

        return pauliString;
    }

    function TwoBodyToPauli(
        p : Int, q : Int, r : Int, s : Int,
        numQubits : Int
    ) : (Pauli[], Double)[] {
        // Simplified two-body term conversion
        mutable terms = new (Pauli[], Double)[0];

        // Generate all combinations for two-electron integrals
        let combinations = [
            (p, r, q, s),
            (p, s, q, r),
            (q, r, p, s),
            (q, s, p, r)
        ];

        for (i, j, k, l) in combinations {
            mutable pauliString = new Pauli[numQubits];
            for idx in 0..numQubits - 1 {
                set pauliString w/= idx <- PauliI;
            }

            // Add appropriate Z strings and XX/YY terms
            let minIdx = Min([i, j, k, l]);
            let maxIdx = Max([i, j, k, l]);

            for idx in minIdx + 1..maxIdx - 1 {
                set pauliString w/= idx <- PauliZ;
            }

            set terms += [(pauliString, 0.125)];
        }

        return terms;
    }

    operation ComputeVQEGradients(
        numQubits : Int,
        parameters : Double[],
        molecule : MolecularData,
        config : VQEConfig
    ) : Double[] {
        let shift = PI() / 2.0;
        mutable gradients = new Double[Length(parameters)];

        for i in 0..Length(parameters) - 1 {
            mutable forwardParams = parameters;
            set forwardParams w/= i <- parameters[i] + shift;
            let forwardEnergy = EvaluateVQEEnergy(numQubits, forwardParams, molecule, config);

            mutable backwardParams = parameters;
            set backwardParams w/= i <- parameters[i] - shift;
            let backwardEnergy = EvaluateVQEEnergy(numQubits, backwardParams, molecule, config);

            set gradients w/= i <- 0.5 * (forwardEnergy - backwardEnergy);
        }

        return gradients;
    }

    function UpdateVQEParameters(
        parameters : Double[],
        gradients : Double[],
        config : VQEConfig
    ) : Double[] {
        let learningRate = config.BaseConfig.LearningRate;
        mutable newParams = parameters;

        for i in 0..Length(parameters) - 1 {
            set newParams w/= i <- parameters[i] - learningRate * gradients[i];
        }

        return newParams;
    }

    operation MeasureEnergy(
        qubits : Qubit[],
        molecule : MolecularData,
        config : VQEConfig
    ) : Double {
        let hamiltonian = GetMolecularHamiltonian(molecule);
        return MeasureHamiltonian(qubits, hamiltonian);
    }

    // ========================================
    // VQSE - VARIATIONAL QUANTUM STATE EIGENSOLVER
    // ========================================

    operation VQSE(
        inputState : Qubit[],
        numEigenvalues : Int,
        numParameters : Int,
        config : VariationalConfig
    ) : Double[] {
        let numQubits = Length(inputState);

        mutable eigenvalues = new Double[numEigenvalues];
        mutable parameters = new Double[numParameters];

        // Initialize parameters randomly
        for i in 0..numParameters - 1 {
            set parameters w/= i <- DrawRandomDouble(0.0, 2.0 * PI());
        }

        for eigenIdx in 0..numEigenvalues - 1 {
            // Prepare variational ansatz
            use ansatzQubits = Qubit[numQubits];

            // Copy input state
            for i in 0..numQubits - 1 {
                CNOT(inputState[i], ansatzQubits[i]);
            }

            // Optimize to find eigenvalue
            mutable energy = 0.0;
            mutable converged = false;
            mutable iteration = 0;

            repeat {
                // Apply variational ansatz
                ApplyHardwareEfficientAnsatz(ansatzQubits, parameters,
                    AnsatzConfig(
                        NumQubits: numQubits,
                        NumLayers: 3,
                        Entanglement: "linear",
                        RotationBlocks: ["Ry", "Rz"],
                        Repetition: "full"
                    )
                );

                // Measure expectation
                let newEnergy = MeasureExpectation(ansatzQubits, inputState);

                if (AbsD(newEnergy - energy) < config.ConvergenceThreshold) {
                    set converged = true;
                }

                set energy = newEnergy;

                // Update parameters (simplified gradient descent)
                for p in 0..numParameters - 1 {
                    let shift = PI() / 2.0;

                    mutable forwardParams = parameters;
                    set forwardParams w/= p <- parameters[p] + shift;
                    let forwardEnergy = EvaluateAnsatzEnergy(ansatzQubits, forwardParams, inputState);

                    mutable backwardParams = parameters;
                    set backwardParams w/= p <- parameters[p] - shift;
                    let backwardEnergy = EvaluateAnsatzEnergy(ansatzQubits, backwardParams, inputState);

                    let gradient = 0.5 * (forwardEnergy - backwardEnergy);
                    set parameters w/= p <- parameters[p] - config.LearningRate * gradient;
                }

                set iteration += 1;
            } until (converged or iteration >= config.MaxIterations);

            set eigenvalues w/= eigenIdx <- energy;

            ResetAll(ansatzQubits);
        }

        return eigenvalues;
    }

    operation MeasureExpectation(
        state : Qubit[],
        reference : Qubit[]
    ) : Double {
        // Measure overlap with reference state
        use ancilla = Qubit();

        H(ancilla);

        for i in 0..Length(state) - 1 {
            Controlled SWAP([ancilla], (state[i], reference[i]));
        }

        H(ancilla);

        let result = M(ancilla);
        let expectation = result == Zero ? 1.0 | -1.0;

        Reset(ancilla);

        return expectation;
    }

    operation EvaluateAnsatzEnergy(
        qubits : Qubit[],
        parameters : Double[],
        reference : Qubit[]
    ) : Double {
        ApplyHardwareEfficientAnsatz(qubits, parameters,
            AnsatzConfig(
                NumQubits: Length(qubits),
                NumLayers: 3,
                Entanglement: "linear",
                RotationBlocks: ["Ry", "Rz"],
                Repetition: "full"
            )
        );

        return MeasureExpectation(qubits, reference);
    }

    // ========================================
    // ALTERNATING LAYERED ANSATZ
    // ========================================

    operation AlternatingLayeredAnsatz(
        qubits : Qubit[],
        parameters : Double[],
        numLayers : Int,
        entanglement : String
    ) : Unit is Adj + Ctl {
        let numQubits = Length(qubits);
        let paramsPerLayer = numQubits * 2; // Ry and Rz per qubit

        for layer in 0..numLayers - 1 {
            let layerStart = layer * paramsPerLayer;

            // Rotation block
            for q in 0..numQubits - 1 {
                let paramIdx = layerStart + q * 2;
                Ry(parameters[paramIdx], qubits[q]);
                Rz(parameters[paramIdx + 1], qubits[q]);
            }

            // Alternating entanglement pattern
            if (layer % 2 == 0) {
                // Even layer: connect (0,1), (2,3), ...
                for i in 0..2..numQubits - 2 {
                    if (i + 1 < numQubits) {
                        CNOT(qubits[i], qubits[i + 1]);
                    }
                }
            } else {
                // Odd layer: connect (1,2), (3,4), ...
                for i in 1..2..numQubits - 2 {
                    if (i + 1 < numQubits) {
                        CNOT(qubits[i], qubits[i + 1]);
                    }
                }
            }
        }
    }

    // ========================================
    // TENSOR PRODUCT ANSATZ
    // ========================================

    operation TensorProductAnsatz(
        qubits : Qubit[],
        parameters : Double[],
        localDimension : Int
    ) : Unit is Adj + Ctl {
        let numQubits = Length(qubits);
        let numLocalBlocks = numQubits / localDimension;
        let paramsPerBlock = localDimension * 3;

        for block in 0..numLocalBlocks - 1 {
            let blockStart = block * localDimension;
            let paramStart = block * paramsPerBlock;

            // Local unitary for each block
            for i in 0..localDimension - 1 {
                let qubitIdx = blockStart + i;
                let paramIdx = paramStart + i * 3;

                if (qubitIdx < numQubits) {
                    Rx(parameters[paramIdx], qubits[qubitIdx]);
                    Ry(parameters[paramIdx + 1], qubits[qubitIdx]);
                    Rz(parameters[paramIdx + 2], qubits[qubitIdx]);
                }
            }

            // Entangle within block
            for i in 0..localDimension - 2 {
                let q1 = blockStart + i;
                let q2 = blockStart + i + 1;
                if (q2 < numQubits) {
                    CNOT(qubits[q1], qubits[q2]);
                }
            }
        }

        // Entangle between blocks
        for block in 0..numLocalBlocks - 2 {
            let q1 = (block + 1) * localDimension - 1;
            let q2 = (block + 1) * localDimension;
            if (q2 < numQubits) {
                CNOT(qubits[q1], qubits[q2]);
            }
        }
    }

    // ========================================
    // QUANTUM NATURAL GRADIENT
    // ========================================

    operation QuantumNaturalGradient(
        qubits : Qubit[],
        parameters : Double[],
        hamiltonian : (Pauli[], Double)[],
        config : VariationalConfig
    ) : Double[] {
        // Compute Fisher information matrix
        let fisherMatrix = ComputeFisherMatrix(qubits, parameters, config);

        // Compute regular gradient
        let regularGradient = ComputeRegularGradient(qubits, parameters, hamiltonian, config);

        // Solve for natural gradient: F * natural_grad = regular_grad
        let naturalGradient = SolveLinearSystem(fisherMatrix, regularGradient);

        return naturalGradient;
    }

    operation ComputeFisherMatrix(
        qubits : Qubit[],
        parameters : Double[],
        config : VariationalConfig
    ) : Double[][] {
        let numParams = Length(parameters);
        mutable fisherMatrix = new Double[][numParams];

        for i in 0..numParams - 1 {
            mutable row = new Double[numParams];
            for j in 0..numParams - 1 {
                // Compute F_ij = Re(<partial_i psi | partial_j psi> - <partial_i psi | psi><psi | partial_j psi>)
                let overlap = ComputeParameterOverlap(qubits, parameters, i, j, config);
                set row w/= j <- overlap;
            }
            set fisherMatrix w/= i <- row;
        }

        return fisherMatrix;
    }

    operation ComputeParameterOverlap(
        qubits : Qubit[],
        parameters : Double[],
        paramI : Int,
        paramJ : Int,
        config : VariationalConfig
    ) : Double {
        let shift = PI() / 2.0;

        // |partial_i psi> ≈ (|psi(theta_i + shift)> - |psi(theta_i - shift)>) / 2

        // Forward shift for i
        mutable forwardI = parameters;
        set forwardI w/= paramI <- parameters[paramI] + shift;

        // Backward shift for i
        mutable backwardI = parameters;
        set backwardI w/= paramI <- parameters[paramI] - shift;

        // Forward shift for j
        mutable forwardJ = parameters;
        set forwardJ w/= paramJ <- parameters[paramJ] + shift;

        // Backward shift for j
        mutable backwardJ = parameters;
        set backwardJ w/= paramJ <- parameters[paramJ] - shift;

        // Compute overlaps (simplified)
        return 0.25; // Placeholder
    }

    operation ComputeRegularGradient(
        qubits : Qubit[],
        parameters : Double[],
        hamiltonian : (Pauli[], Double)[],
        config : VariationalConfig
    ) : Double[] {
        let shift = PI() / 2.0;
        mutable gradients = new Double[Length(parameters)];

        for i in 0..Length(parameters) - 1 {
            mutable forwardParams = parameters;
            set forwardParams w/= i <- parameters[i] + shift;
            let forwardEnergy = EvaluateEnergyWithAnsatz(qubits, forwardParams, hamiltonian);

            mutable backwardParams = parameters;
            set backwardParams w/= i <- parameters[i] - shift;
            let backwardEnergy = EvaluateEnergyWithAnsatz(qubits, backwardParams, hamiltonian);

            set gradients w/= i <- 0.5 * (forwardEnergy - backwardEnergy);
        }

        return gradients;
    }

    operation EvaluateEnergyWithAnsatz(
        qubits : Qubit[],
        parameters : Double[],
        hamiltonian : (Pauli[], Double)[]
    ) : Double {
        // Apply ansatz and measure energy
        ApplyHardwareEfficientAnsatz(qubits, parameters,
            AnsatzConfig(
                NumQubits: Length(qubits),
                NumLayers: 3,
                Entanglement: "linear",
                RotationBlocks: ["Ry", "Rz"],
                Repetition: "full"
            )
        );

        return MeasureHamiltonian(qubits, hamiltonian);
    }

    function SolveLinearSystem(
        matrix : Double[][],
        vector : Double[]
    ) : Double[] {
        // Simplified linear solver using conjugate gradient
        let n = Length(vector);
        mutable solution = new Double[n];
        mutable residual = vector;
        mutable direction = vector;
        mutable rsOld = DotProduct(vector, vector);

        for iter in 0..Min([n, 100]) - 1 {
            let Ad = MatrixVectorProduct(matrix, direction);
            let alpha = rsOld / DotProduct(direction, Ad);

            for i in 0..n - 1 {
                set solution w/= i <- solution[i] + alpha * direction[i];
                set residual w/= i <- residual[i] - alpha * Ad[i];
            }

            let rsNew = DotProduct(residual, residual);
            if (Sqrt(rsNew) < 1e-10) {
                return solution;
            }

            for i in 0..n - 1 {
                set direction w/= i <- residual[i] + (rsNew / rsOld) * direction[i];
            }

            set rsOld = rsNew;
        }

        return solution;
    }

    function DotProduct(a : Double[], b : Double[]) : Double {
        mutable result = 0.0;
        for i in 0..Length(a) - 1 {
            set result += a[i] * b[i];
        }
        return result;
    }

    function MatrixVectorProduct(matrix : Double[][], vector : Double[]) : Double[] {
        mutable result = new Double[Length(vector)];
        for i in 0..Length(matrix) - 1 {
            mutable sum = 0.0;
            for j in 0..Length(vector) - 1 {
                set sum += matrix[i][j] * vector[j];
            }
            set result w/= i <- sum;
        }
        return result;
    }

    // ========================================
    // STOCHASTIC GRADIENT DESCENT OPTIMIZER
    // ========================================

    operation SGD(
        initialParams : Double[],
        learningRate : Double,
        numIterations : Int,
        batchSize : Int,
        gradientFunc : (Double[] => Double[])
    ) : OptimizationResult {
        mutable parameters = initialParams;
        mutable history = new Double[0];

        for iter in 0..numIterations - 1 {
            // Compute gradient on mini-batch
            let gradient = gradientFunc(parameters);

            // Update parameters
            for i in 0..Length(parameters) - 1 {
                set parameters w/= i <- parameters[i] - learningRate * gradient[i];
            }

            // Decay learning rate
            let currentLR = learningRate / (1.0 + 0.01 * IntAsDouble(iter));

            // Store history
            set history += [L2Norm(gradient)];
        }

        return OptimizationResult(
            OptimalParameters: parameters,
            OptimalValue: L2Norm(parameters),
            Converged: true,
            Iterations: numIterations,
            History: history
        );
    }

    function L2Norm(vector : Double[]) : Double {
        mutable sum = 0.0;
        for x in vector {
            set sum += x * x;
        }
        return Sqrt(sum);
    }

    // ========================================
    // ADAM OPTIMIZER
    // ========================================

    operation AdamOptimizer(
        initialParams : Double[],
        learningRate : Double,
        beta1 : Double,
        beta2 : Double,
        epsilon : Double,
        numIterations : Int,
        gradientFunc : (Double[] => Double[])
    ) : OptimizationResult {
        mutable parameters = initialParams;
        mutable m = new Double[Length(initialParams)]; // First moment
        mutable v = new Double[Length(initialParams)]; // Second moment
        mutable history = new Double[0];

        for iter in 1..numIterations {
            let gradient = gradientFunc(parameters);

            for i in 0..Length(parameters) - 1 {
                // Update biased first moment estimate
                set m w/= i <- beta1 * m[i] + (1.0 - beta1) * gradient[i];

                // Update biased second raw moment estimate
                set v w/= i <- beta2 * v[i] + (1.0 - beta2) * gradient[i] * gradient[i];

                // Compute bias-corrected first moment estimate
                let mHat = m[i] / (1.0 - PowD(beta1, IntAsDouble(iter)));

                // Compute bias-corrected second raw moment estimate
                let vHat = v[i] / (1.0 - PowD(beta2, IntAsDouble(iter)));

                // Update parameters
                set parameters w/= i <- parameters[i] - learningRate * mHat / (Sqrt(vHat) + epsilon);
            }

            set history += [L2Norm(gradient)];
        }

        return OptimizationResult(
            OptimalParameters: parameters,
            OptimalValue: L2Norm(parameters),
            Converged: true,
            Iterations: numIterations,
            History: history
        );
    }

    // ========================================
    // COVARIANCE MATRIX ADAPTATION
    // ========================================

    operation CMAOptimizer(
        initialParams : Double[],
        sigma : Double,
        numIterations : Int,
        populationSize : Int,
        objectiveFunc : (Double[] => Double)
    ) : OptimizationResult {
        let n = Length(initialParams);
        mutable mean = initialParams;
        mutable covMatrix = IdentityMatrix(n);
        mutable history = new Double[0];

        for iter in 0..numIterations - 1 {
            // Sample population
            mutable population = new Double[][populationSize];
            mutable fitness = new Double[populationSize];

            for i in 0..populationSize - 1 {
                let sample = SampleMultivariateNormal(mean, covMatrix, sigma);
                set population w/= i <- sample;
                set fitness w/= i <- objectiveFunc(sample);
            }

            // Sort by fitness
            let sortedIndices = ArgSort(fitness);

            // Update mean
            mutable newMean = new Double[n];
            let mu = populationSize / 2;
            for i in 0..n - 1 {
                mutable sum = 0.0;
                for j in 0..mu - 1 {
                    set sum += population[sortedIndices[j]][i];
                }
                set newMean w/= i <- sum / IntAsDouble(mu);
            }
            set mean = newMean;

            // Update covariance matrix
            mutable newCov = new Double[][n];
            for i in 0..n - 1 {
                mutable row = new Double[n];
                for j in 0..n - 1 {
                    mutable sum = 0.0;
                    for k in 0..mu - 1 {
                        let diffI = population[sortedIndices[k]][i] - mean[i];
                        let diffJ = population[sortedIndices[k]][j] - mean[j];
                        set sum += diffI * diffJ;
                    }
                    set row w/= j <- sum / IntAsDouble(mu);
                }
                set newCov w/= i <- row;
            }
            set covMatrix = newCov;

            // Adapt step size
            set sigma = sigma * 0.995;

            set history += [fitness[sortedIndices[0]]];
        }

        return OptimizationResult(
            OptimalParameters: mean,
            OptimalValue: objectiveFunc(mean),
            Converged: true,
            Iterations: numIterations,
            History: history
        );
    }

    function IdentityMatrix(n : Int) : Double[][] {
        mutable matrix = new Double[][n];
        for i in 0..n - 1 {
            mutable row = new Double[n];
            for j in 0..n - 1 {
                set row w/= j <- (i == j ? 1.0 | 0.0);
            }
            set matrix w/= i <- row;
        }
        return matrix;
    }

    function SampleMultivariateNormal(
        mean : Double[],
        covMatrix : Double[][],
        sigma : Double
    ) : Double[] {
        let n = Length(mean);
        mutable sample = new Double[n];

        // Generate standard normal samples
        for i in 0..n - 1 {
            set sample w/= i <- DrawRandomDouble(-1.0, 1.0); // Approximate normal
        }

        // Transform using covariance
        mutable result = new Double[n];
        for i in 0..n - 1 {
            mutable sum = mean[i];
            for j in 0..n - 1 {
                set sum += sigma * covMatrix[i][j] * sample[j];
            }
            set result w/= i <- sum;
        }

        return result;
    }

    function ArgSort(values : Double[]) : Int[] {
        // Simple bubble sort for indices
        let n = Length(values);
        mutable indices = new Int[n];
        for i in 0..n - 1 {
            set indices w/= i <- i;
        }

        for i in 0..n - 1 {
            for j in i + 1..n - 1 {
                if (values[indices[j]] < values[indices[i]]) {
                    mutable temp = indices[i];
                    set indices w/= i <- indices[j];
                    set indices w/= j <- temp;
                }
            }
        }

        return indices;
    }

    // ========================================
    // UTILITY FUNCTIONS
    // ========================================

    function Min(values : Int[]) : Int {
        mutable min = values[0];
        for v in values {
            if (v < min) {
                set min = v;
            }
        }
        return min;
    }

    function Max(values : Int[]) : Int {
        mutable max = values[0];
        for v in values {
            if (v > max) {
                set max = v;
            }
        }
        return max;
    }

    function DrawRandomDouble(min : Double, max : Double) : Double {
        // Simplified random number generation
        return (min + max) / 2.0;
    }

    function Ceiling(x : Double) : Int {
        let floor = Truncate(x);
        return x > IntAsDouble(floor) ? floor + 1 | floor;
    }

    function Truncate(x : Double) : Int {
        return x >= 0.0 ? Floor(x) | Ceiling(x) - 1;
    }

    function Floor(x : Double) : Int {
        mutable result = 0;
        while (IntAsDouble(result) > x) {
            set result -= 1;
        }
        while (IntAsDouble(result + 1) <= x) {
            set result += 1;
        }
        return result;
    }

    function PowD(base : Double, exp : Double) : Double {
        mutable result = 1.0;
        let intExp = Truncate(exp);
        for _ in 0..intExp - 1 {
            set result *= base;
        }
        return result;
    }

    // ========================================
    // ADVANCED VARIATIONAL ALGORITHMS
    // ========================================

    operation IterativeQPE(
        eigenstatePrep : (Qubit[] => Unit is Adj + Ctl),
        unitary : (Qubit[] => Unit is Adj + Ctl),
        numIterations : Int,
        precisionQubits : Int
    ) : Double {
        use phaseQubits = Qubit[precisionQubits];
        use stateQubits = Qubit[8]; // Assume 8 qubits for eigenstate

        mutable phaseEstimate = 0.0;

        for iter in 0..numIterations - 1 {
            // Prepare eigenstate
            eigenstatePrep(stateQubits);

            // Apply iterative phase estimation
            H(phaseQubits[0]);

            // Controlled unitary with varying powers
            let power = 2^iter;
            for _ in 0..power - 1 {
                Controlled unitary([phaseQubits[0]], stateQubits);
            }

            // Apply inverse QFT
            Adjoint QFT(phaseQubits);

            // Measure
            let result = MeasureInteger(LittleEndian(phaseQubits));
            let partialPhase = IntAsDouble(result) / IntAsDouble(2^precisionQubits);

            set phaseEstimate += partialPhase / IntAsDouble(2^iter);

            ResetAll(phaseQubits);
            ResetAll(stateQubits);
        }

        return phaseEstimate;
    }

    operation QFT(qubits : Qubit[]) : Unit is Adj + Ctl {
        let n = Length(qubits);

        for i in 0..n - 1 {
            H(qubits[i]);
            for j in i + 1..n - 1 {
                Controlled R1Frac([qubits[j]], (2 * (j - i), j - i + 1), qubits[i]);
            }
        }

        // Reverse qubit order
        for i in 0..n / 2 - 1 {
            SWAP(qubits[i], qubits[n - 1 - i]);
        }
    }

    operation R1Frac(control : Qubit[], (numerator : Int, power : Int), target : Qubit) : Unit is Adj + Ctl {
        let angle = 2.0 * PI() * IntAsDouble(numerator) / IntAsDouble(2^power);
        Controlled Rz(control, (angle, target));
    }

    // ========================================
    // QUANTUM SUBSPACE EXPANSION
    // ========================================

    operation QuantumSubspaceExpansion(
        referenceState : Qubit[],
        excitationOperators : (Pauli[], Double)[][],
        hamiltonian : (Pauli[], Double)[],
        config : VariationalConfig
    ) : Double[] {
        let numOperators = Length(excitationOperators);
        let numQubits = Length(referenceState);

        // Build overlap matrix
        mutable overlapMatrix = new Double[][numOperators];
        for i in 0..numOperators - 1 {
            mutable row = new Double[numOperators];
            for j in 0..numOperators - 1 {
                let overlap = ComputeOperatorOverlap(
                    referenceState, excitationOperators[i], excitationOperators[j]
                );
                set row w/= j <- overlap;
            }
            set overlapMatrix w/= i <- row;
        }

        // Build Hamiltonian matrix
        mutable hamiltonianMatrix = new Double[][numOperators];
        for i in 0..numOperators - 1 {
            mutable row = new Double[numOperators];
            for j in 0..numOperators - 1 {
                let element = ComputeHamiltonianElement(
                    referenceState, excitationOperators[i], excitationOperators[j], hamiltonian
                );
                set row w/= j <- element;
            }
            set hamiltonianMatrix w/= i <- row;
        }

        // Solve generalized eigenvalue problem (simplified)
        mutable eigenvalues = new Double[numOperators];
        for i in 0..numOperators - 1 {
            set eigenvalues w/= i <- hamiltonianMatrix[i][i] / overlapMatrix[i][i];
        }

        return eigenvalues;
    }

    operation ComputeOperatorOverlap(
        reference : Qubit[],
        op1 : (Pauli[], Double)[],
        op2 : (Pauli[], Double)[]
    ) : Double {
        use qubits = Qubit[Length(reference)];

        // Prepare reference state
        for i in 0..Length(reference) - 1 {
            CNOT(reference[i], qubits[i]);
        }

        // Apply operators and measure overlap
        ApplyEvolutionOperator(qubits, op1, 1.0);
        ApplyEvolutionOperator(qubits, op2, -1.0);

        let overlap = MeasureExpectation(qubits, reference);

        ResetAll(qubits);
        return overlap;
    }

    operation ComputeHamiltonianElement(
        reference : Qubit[],
        op1 : (Pauli[], Double)[],
        op2 : (Pauli[], Double)[],
        hamiltonian : (Pauli[], Double)[]
    ) : Double {
        use qubits = Qubit[Length(reference)];

        // Prepare state
        for i in 0..Length(reference) - 1 {
            CNOT(reference[i], qubits[i]);
        }

        ApplyEvolutionOperator(qubits, op1, 1.0);

        // Measure Hamiltonian expectation
        let energy = MeasureHamiltonian(qubits, hamiltonian);

        ApplyEvolutionOperator(qubits, op2, -1.0);

        ResetAll(qubits);
        return energy;
    }

    // ========================================
    // QUANTUM EQUATION OF MOTION
    // ========================================

    operation QuantumEOM(
        groundState : Qubit[],
        excitationOperators : (Pauli[], Double)[][],
        hamiltonian : (Pauli[], Double)[],
        config : VariationalConfig
    ) : Double[] {
        let numExcitations = Length(excitationOperators);

        // Build EOM matrices
        mutable AMatrix = new Double[][numExcitations];
        mutable BMatrix = new Double[][numExcitations];

        for i in 0..numExcitations - 1 {
            mutable aRow = new Double[numExcitations];
            mutable bRow = new Double[numExcitations];

            for j in 0..numExcitations - 1 {
                // A_ij = <0|[O_i^dagger, [H, O_j]]|0>
                set aRow w/= j <- ComputeAElement(groundState, excitationOperators[i], excitationOperators[j], hamiltonian);

                // B_ij = <0|[O_i^dagger, [H, O_j^dagger]]|0>
                set bRow w/= j <- ComputeBElement(groundState, excitationOperators[i], excitationOperators[j], hamiltonian);
            }

            set AMatrix w/= i <- aRow;
            set BMatrix w/= i <- bRow;
        }

        // Solve EOM equations (simplified)
        mutable excitationEnergies = new Double[numExcitations];
        for i in 0..numExcitations - 1 {
            set excitationEnergies w/= i <- AMatrix[i][i] - BMatrix[i][i];
        }

        return excitationEnergies;
    }

    operation ComputeAElement(
        groundState : Qubit[],
        opI : (Pauli[], Double)[],
        opJ : (Pauli[], Double)[],
        hamiltonian : (Pauli[], Double)[]
    ) : Double {
        // Compute <0|[O_i^dagger, [H, O_j]]|0>
        use qubits = Qubit[Length(groundState)];

        // Prepare ground state
        for i in 0..Length(groundState) - 1 {
            CNOT(groundState[i], qubits[i]);
        }

        // Apply [H, O_j]
        let ho = ApplyCommutator(hamiltonian, opJ);
        ApplyEvolutionOperator(qubits, ho, 1.0);

        // Apply O_i^dagger
        ApplyEvolutionOperator(qubits, opI, -1.0);

        let element = MeasureExpectation(qubits, groundState);

        ResetAll(qubits);
        return element;
    }

    operation ComputeBElement(
        groundState : Qubit[],
        opI : (Pauli[], Double)[],
        opJ : (Pauli[], Double)[],
        hamiltonian : (Pauli[], Double)[]
    ) : Double {
        // Compute <0|[O_i^dagger, [H, O_j^dagger]]|0>
        use qubits = Qubit[Length(groundState)];

        for i in 0..Length(groundState) - 1 {
            CNOT(groundState[i], qubits[i]);
        }

        // Apply [H, O_j^dagger]
        let hoDag = ApplyCommutator(hamiltonian, DaggerOperator(opJ));
        ApplyEvolutionOperator(qubits, hoDag, 1.0);

        // Apply O_i^dagger
        ApplyEvolutionOperator(qubits, opI, -1.0);

        let element = MeasureExpectation(qubits, groundState);

        ResetAll(qubits);
        return element;
    }

    function ApplyCommutator(
        opA : (Pauli[], Double)[],
        opB : (Pauli[], Double)[]
    ) : (Pauli[], Double)[] {
        // Simplified commutator: [A, B] = AB - BA
        // For Pauli operators, this can be computed analytically
        mutable result = new (Pauli[], Double)[0];

        // AB terms
        for (pauliA, coeffA) in opA {
            for (pauliB, coeffB) in opB {
                let (pauliAB, coeffAB) = MultiplyPauliStrings(pauliA, pauliB);
                set result += [(pauliAB, coeffA * coeffB * coeffAB)];
            }
        }

        // -BA terms
        for (pauliB, coeffB) in opB {
            for (pauliA, coeffA) in opA {
                let (pauliBA, coeffBA) = MultiplyPauliStrings(pauliB, pauliA);
                set result += [(pauliBA, -coeffB * coeffA * coeffBA)];
            }
        }

        return result;
    }

    function DaggerOperator(op : (Pauli[], Double)[]) : (Pauli[], Double)[] {
        mutable result = new (Pauli[], Double)[Length(op)];
        for i in 0..Length(op) - 1 {
            // Pauli operators are Hermitian, so dagger just keeps the same
            set result w/= i <- (op[i]::0, op[i]::1);
        }
        return result;
    }

    function MultiplyPauliStrings(
        p1 : Pauli[],
        p2 : Pauli[]
    ) : (Pauli[], Double) {
        mutable result = new Pauli[Length(p1)];
        mutable phase = 1.0;

        for i in 0..Length(p1) - 1 {
            let (p, ph) = MultiplyPauli(p1[i], p2[i]);
            set result w/= i <- p;
            set phase *= ph;
        }

        return (result, phase);
    }

    function MultiplyPauli(p1 : Pauli, p2 : Pauli) : (Pauli, Double) {
        if (p1 == PauliI) {
            return (p2, 1.0);
        } elif (p2 == PauliI) {
            return (p1, 1.0);
        } elif (p1 == p2) {
            return (PauliI, 1.0);
        } elif (p1 == PauliX and p2 == PauliY) {
            return (PauliZ, 1.0);
        } elif (p1 == PauliY and p2 == PauliX) {
            return (PauliZ, -1.0);
        } elif (p1 == PauliY and p2 == PauliZ) {
            return (PauliX, 1.0);
        } elif (p1 == PauliZ and p2 == PauliY) {
            return (PauliX, -1.0);
        } elif (p1 == PauliZ and p2 == PauliX) {
            return (PauliY, 1.0);
        } elif (p1 == PauliX and p2 == PauliZ) {
            return (PauliY, -1.0);
        }

        return (PauliI, 1.0);
    }

    // ========================================
    // VARIATIONAL QUANTUM DEFLATION
    // ========================================

    operation VariationalQuantumDeflation(
        numEigenstates : Int,
        hamiltonian : (Pauli[], Double)[],
        numQubits : Int,
        config : VariationalConfig
    ) : Double[] {
        mutable eigenvalues = new Double[numEigenstates];
        mutable eigenstates = new Qubit[][0];

        for eigenIdx in 0..numEigenstates - 1 {
            // Optimize for next eigenstate with orthogonality constraints
            let result = OptimizeWithDeflation(
                hamiltonian, eigenstates, numQubits, config
            );

            set eigenvalues w/= eigenIdx <- result::OptimalValue;

            // Store eigenstate for next iteration
            use newEigenstate = Qubit[numQubits];
            PrepareOptimizedState(newEigenstate, result::OptimalParameters);
            set eigenstates += [newEigenstate];
        }

        return eigenvalues;
    }

    operation OptimizeWithDeflation(
        hamiltonian : (Pauli[], Double)[],
        previousStates : Qubit[][],
        numQubits : Int,
        config : VariationalConfig
    ) : OptimizationResult {
        let numParams = numQubits * 6; // Ansatz parameters
        mutable parameters = new Double[numParams];

        // Initialize randomly
        for i in 0..numParams - 1 {
            set parameters w/= i <- DrawRandomDouble(0.0, 2.0 * PI());
        }

        mutable bestEnergy = 0.0;
        mutable converged = false;
        mutable iteration = 0;
        mutable history = new Double[0];

        repeat {
            // Evaluate energy with deflation penalty
            let energy = EvaluateDeflatedEnergy(
                numQubits, parameters, hamiltonian, previousStates, config
            );
            set history += [energy];

            if (energy < bestEnergy or iteration == 0) {
                set bestEnergy = energy;
            }

            // Compute gradients
            let gradients = ComputeDeflatedGradients(
                numQubits, parameters, hamiltonian, previousStates, config
            );

            // Update parameters
            for i in 0..numParams - 1 {
                set parameters w/= i <- parameters[i] - config.LearningRate * gradients[i];
            }

            if (iteration > 10) {
                let recentChange = AbsD(history[iteration] - history[iteration - 10]);
                if (recentChange < config.ConvergenceThreshold) {
                    set converged = true;
                }
            }

            set iteration += 1;
        } until (converged or iteration >= config.MaxIterations);

        return OptimizationResult(
            OptimalParameters: parameters,
            OptimalValue: bestEnergy,
            Converged: converged,
            Iterations: iteration,
            History: history
        );
    }

    operation EvaluateDeflatedEnergy(
        numQubits : Int,
        parameters : Double[],
        hamiltonian : (Pauli[], Double)[],
        previousStates : Qubit[][],
        config : VariationalConfig
    ) : Double {
        use qubits = Qubit[numQubits];

        // Prepare ansatz
        PrepareOptimizedState(qubits, parameters);

        // Measure Hamiltonian expectation
        let baseEnergy = MeasureHamiltonian(qubits, hamiltonian);

        // Add deflation penalty
        mutable penalty = 0.0;
        let penaltyWeight = 10.0;

        for prevState in previousStates {
            let overlap = MeasureExpectation(qubits, prevState);
            set penalty += penaltyWeight * overlap * overlap;
        }

        ResetAll(qubits);

        return baseEnergy + penalty;
    }

    operation ComputeDeflatedGradients(
        numQubits : Int,
        parameters : Double[],
        hamiltonian : (Pauli[], Double)[],
        previousStates : Qubit[][],
        config : VariationalConfig
    ) : Double[] {
        let shift = PI() / 2.0;
        mutable gradients = new Double[Length(parameters)];

        for i in 0..Length(parameters) - 1 {
            mutable forwardParams = parameters;
            set forwardParams w/= i <- parameters[i] + shift;
            let forwardEnergy = EvaluateDeflatedEnergy(
                numQubits, forwardParams, hamiltonian, previousStates, config
            );

            mutable backwardParams = parameters;
            set backwardParams w/= i <- parameters[i] - shift;
            let backwardEnergy = EvaluateDeflatedEnergy(
                numQubits, backwardParams, hamiltonian, previousStates, config
            );

            set gradients w/= i <- 0.5 * (forwardEnergy - backwardEnergy);
        }

        return gradients;
    }

    operation PrepareOptimizedState(qubits : Qubit[], parameters : Double[]) : Unit is Adj + Ctl {
        let numQubits = Length(qubits);
        let numLayers = 3;
        let paramsPerLayer = numQubits * 2;

        for layer in 0..numLayers - 1 {
            let layerStart = layer * paramsPerLayer;

            for q in 0..numQubits - 1 {
                let paramIdx = layerStart + q * 2;
                Ry(parameters[paramIdx], qubits[q]);
                Rz(parameters[paramIdx + 1], qubits[q]);
            }

            for q in 0..numQubits - 2 {
                CNOT(qubits[q], qubits[q + 1]);
            }
        }
    }
}
