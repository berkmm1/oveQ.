// Quantum Search Algorithms Module
// Implementation of Grover's algorithm and variants
// Part of the Quantum Agentic Loop Engine

namespace QuantumAgenticEngine.Algorithms.Search {
    open Microsoft.Quantum.Canon;
    open Microsoft.Quantum.Intrinsic;
    open Microsoft.Quantum.Math;
    open Microsoft.Quantum.Convert;
    open Microsoft.Quantum.Arrays;
    open Microsoft.Quantum.Measurement;
    open Microsoft.Quantum.Diagnostics;
    open Microsoft.Quantum.Random;
    open QuantumAgenticEngine.Utils;
    open QuantumAgenticEngine.Core;

    // ============================================
    // Grover's Algorithm Implementations
    // ============================================

    /// # Summary
    /// Oracle for marking target states
    operation MarkingOracle(
        markedQubits : Qubit[],
        targetState : Bool[]
    ) : Unit is Adj + Ctl {
        // Flip phase of target state
        for i in 0 .. Length(markedQubits) - 1 {
            if not targetState[i] {
                X(markedQubits[i]);
            }
        }

        // Apply controlled-Z
        Controlled Z(markedQubits[0 .. Length(markedQubits) - 2], markedQubits[Length(markedQubits) - 1]);

        // Uncompute
        for i in 0 .. Length(markedQubits) - 1 {
            if not targetState[i] {
                X(markedQubits[i]);
            }
        }
    }

    /// # Summary
    /// Phase oracle for marking
    operation PhaseOracle(
        inputQubits : Qubit[],
        oracleQubit : Qubit,
        markedElements : Int[]
    ) : Unit is Adj + Ctl {
        // Encode marked elements
        for element in markedElements {
            // Convert element index to binary and apply phase
            mutable temp = element;
            for i in 0 .. Length(inputQubits) - 1 {
                if temp % 2 == 1 {
                    CNOT(inputQubits[i], oracleQubit);
                }
                set temp = temp / 2;
            }
        }
    }

    /// # Summary
    /// Grover diffusion operator
    operation GroverDiffusion(
        searchQubits : Qubit[]
    ) : Unit is Adj + Ctl {
        let numQubits = Length(searchQubits);

        // Apply Hadamard to all qubits
        ApplyToEach(H, searchQubits);

        // Apply conditional phase shift
        ApplyToEach(X, searchQubits);

        // Multi-controlled Z
        Controlled Z(searchQubits[0 .. numQubits - 2], searchQubits[numQubits - 1]);

        ApplyToEach(X, searchQubits);
        ApplyToEach(H, searchQubits);
    }

    /// # Summary
    /// Single Grover iteration
    operation GroverIteration(
        searchQubits : Qubit[],
        targetState : Bool[],
        auxiliaryQubits : Qubit[]
    ) : Unit {
        // Apply oracle
        MarkingOracle(searchQubits, targetState);

        // Apply diffusion
        GroverDiffusion(searchQubits);
    }

    /// # Summary
    /// Complete Grover's algorithm
    operation GroverSearch(
        numQubits : Int,
        targetState : Bool[],
        numIterations : Int
    ) : Result[] {
        use searchQubits = Qubit[numQubits];
        use auxiliaryQubits = Qubit[2];

        // Initialize superposition
        ApplyToEach(H, searchQubits);

        // Apply Grover iterations
        for iter in 0 .. numIterations - 1 {
            GroverIteration(searchQubits, targetState, auxiliaryQubits);
        }

        // Measure
        mutable results = new Result[numQubits];
        for i in 0 .. numQubits - 1 {
            set results w/= i <- M(searchQubits[i]);
        }

        return results;
    }

    /// # Summary
    /// Grover's algorithm with multiple targets
    operation GroverSearchMultipleTargets(
        numQubits : Int,
        targetStates : Bool[][],
        numIterations : Int
    ) : Result[] {
        use searchQubits = Qubit[numQubits];

        // Initialize superposition
        ApplyToEach(H, searchQubits);

        // Apply iterations for multiple targets
        for iter in 0 .. numIterations - 1 {
            // Oracle for all targets
            for target in targetStates {
                MarkingOracle(searchQubits, target);
            }

            // Diffusion
            GroverDiffusion(searchQubits);
        }

        // Measure
        mutable results = new Result[numQubits];
        for i in 0 .. numQubits - 1 {
            set results w/= i <- M(searchQubits[i]);
        }

        return results;
    }

    // ============================================
    // Amplitude Amplification
    // ============================================

    /// # Summary
    /// General amplitude amplification
    operation AmplitudeAmplification(
        statePreparation : (Qubit[] => Unit is Adj + Ctl),
        oracle : (Qubit[] => Unit is Adj + Ctl),
        diffusion : (Qubit[] => Unit is Adj + Ctl),
        qubits : Qubit[],
        numIterations : Int
    ) : Unit {
        // Prepare initial state
        statePreparation(qubits);

        // Apply amplification iterations
        for iter in 0 .. numIterations - 1 {
            // Apply oracle
            oracle(qubits);

            // Apply diffusion
            diffusion(qubits);
        }
    }

    /// # Summary
    /// Fixed-point amplitude amplification
    operation FixedPointAmplitudeAmplification(
        stateQubits : Qubit[],
        targetQubits : Qubit[],
        successProbability : Double,
        numQueries : Int
    ) : Unit {
        let lambda = ArcSin(Sqrt(successProbability));

        for j in 1 .. numQueries {
            let phiJ = 2.0 * ArcTan(1.0 / (Tan(2.0 * IntAsDouble(j) * lambda) * Sqrt(IntAsDouble(numQueries - j + 1))));
            let thetaJ = 2.0 * ArcTan(1.0 / (Tan(2.0 * IntAsDouble(j) * lambda) * Sqrt(IntAsDouble(numQueries - j + 1))));

            // Apply phase rotations
            for q in stateQubits {
                Rz(phiJ, q);
            }

            // Oracle application
            for t in targetQubits {
                CNOT(t, stateQubits[0]);
            }

            // Diffusion
            for q in stateQubits {
                Ry(thetaJ, q);
            }
        }
    }

    /// # Summary
    /// Oblivious amplitude amplification
    operation ObliviousAmplitudeAmplification(
        systemQubits : Qubit[],
        ancillaQubits : Qubit[],
        unitary : (Qubit[] => Unit is Adj + Ctl),
        numIterations : Int
    ) : Unit {
        for iter in 0 .. numIterations - 1 {
            // Apply unitary
            unitary(systemQubits);

            // Reflection about ancilla
            ApplyToEach(H, ancillaQubits);
            ApplyToEach(X, ancillaQubits);

            // Multi-controlled operation
            if Length(ancillaQubits) > 1 {
                Controlled Z(ancillaQubits[0 .. Length(ancillaQubits) - 2], ancillaQubits[Length(ancillaQubits) - 1]);
            }

            ApplyToEach(X, ancillaQubits);
            ApplyToEach(H, ancillaQubits);
        }
    }

    // ============================================
    // Quantum Counting
    // ============================================

    /// # Summary
    /// Quantum counting with phase estimation
    operation QuantumCounting(
        searchQubits : Qubit[],
        countingQubits : Qubit[],
        targetState : Bool[]
    ) : Int {
        let numCounting = Length(countingQubits);
        let numSearch = Length(searchQubits);

        // Initialize counting register
        ApplyToEach(H, countingQubits);

        // Apply controlled Grover operations
        for i in 0 .. numCounting - 1 {
            let power = 1 <<< i;

            for _ in 0 .. power - 1 {
                // Controlled Grover iteration
                for j in 0 .. numSearch - 1 {
                    Controlled H([countingQubits[i]], searchQubits[j]);
                }

                Controlled MarkingOracle(countingQubits[i .. i], (searchQubits, targetState));
                Controlled GroverDiffusion(countingQubits[i .. i], searchQubits);
            }
        }

        // Inverse QFT on counting register
        Adjoint QFT(countingQubits);

        // Measure counting register
        mutable result = 0;
        for i in 0 .. numCounting - 1 {
            let bit = M(countingQubits[i]);
            if bit == One {
                set result += 1 <<< i;
            }
        }

        return result;
    }

    /// # Summary
    /// Approximate quantum counting
    operation ApproximateQuantumCounting(
        searchQubits : Qubit[],
        precisionQubits : Qubit[],
        confidence : Double
    ) : Double {
        let numPrecision = Length(precisionQubits);

        // Initialize
        ApplyToEach(H, precisionQubits);

        // Iterative phase estimation
        for i in 0 .. numPrecision - 1 {
            let angle = PI() / IntAsDouble(1 <<< (numPrecision - i));
            Rz(angle, precisionQubits[i]);

            // Controlled search operation
            for q in searchQubits {
                Controlled H([precisionQubits[i]], q);
            }
        }

        // Measure
        mutable count = 0.0;
        for i in 0 .. numPrecision - 1 {
            let bit = M(precisionQubits[i]);
            if bit == One {
                set count += 1.0 / IntAsDouble(1 <<< (numPrecision - i));
            }
        }

        // Scale to number of solutions
        let searchSpace = IntAsDouble(1 <<< Length(searchQubits));
        return count * searchSpace * Sin(PI() * confidence) * Sin(PI() * confidence);
    }

    // ============================================
    // Quantum Minimum Finding
    // ============================================

    /// # Summary
    /// Durr-Hoyer minimum finding algorithm
    operation DurrHoyerMinimumFinding(
        valueQubits : Qubit[],
        indexQubits : Qubit[],
        comparisonOracle : (Qubit[], Qubit[], Qubit => Unit),
        numElements : Int
    ) : Int {
        let numIndex = Length(indexQubits);
        let numValue = Length(valueQubits);

        // Initialize random index
        ApplyToEach(H, indexQubits);

        // Iterative improvement
        mutable iterations = Round(Ln(IntAsDouble(numElements)) / Ln(2.0));

        for iter in 0 .. iterations - 1 {
            use comparisonQubit = Qubit();

            // Prepare comparison qubit
            H(comparisonQubit);

            // Apply comparison oracle
            comparisonOracle(valueQubits, indexQubits, comparisonQubit);

            // Grover search for better element
            let numGroverIterations = Round(PI() / (4.0 * ArcSin(1.0 / Sqrt(IntAsDouble(numElements - iter)))));

            for _ in 0 .. numGroverIterations - 1 {
                // Oracle marks elements better than current
                Z(comparisonQubit);

                // Diffusion on index register
                GroverDiffusion(indexQubits);
            }

            Reset(comparisonQubit);
        }

        // Measure final index
        mutable result = 0;
        for i in 0 .. numIndex - 1 {
            let bit = M(indexQubits[i]);
            if bit == One {
                set result += 1 <<< i;
            }
        }

        return result;
    }

    /// # Summary
    /// Quantum minimum finding with threshold
    operation ThresholdQuantumMinimum(
        valueQubits : Qubit[],
        thresholdQubit : Qubit,
        threshold : Double
    ) : Bool {
        // Encode threshold
        let thresholdAngle = threshold * PI();
        Ry(thresholdAngle, thresholdQubit);

        // Compare values
        for q in valueQubits {
            CNOT(q, thresholdQubit);
        }

        // Measure if any value is below threshold
        let result = M(thresholdQubit);

        return result == One;
    }

    // ============================================
    // Quantum Element Distinctness
    // ============================================

    /// # Summary
    /// Element distinctness algorithm
    operation ElementDistinctness(
        elementQubits : Qubit[],
        collisionOracle : (Qubit[], Qubit => Unit),
        numElements : Int
    ) : Bool {
        let n = numElements;
        let r = Round(Pow(IntAsDouble(n), 2.0 / 3.0));

        use flagQubit = Qubit();

        // Initialize flag
        H(flagQubit);

        // Setup subroutine
        for i in 0 .. r - 1 {
            // Random sampling
            for q in elementQubits {
                H(q);
            }
        }

        // Check subroutine
        for i in 0 .. n - 1 {
            collisionOracle(elementQubits, flagQubit);
        }

        // Swapping subroutine
        for i in 0 .. r - 1 {
            for q in elementQubits {
                H(q);
            }
        }

        // Measure flag
        let distinct = M(flagQubit) == Zero;

        Reset(flagQubit);

        return distinct;
    }

    /// # Summary
    /// Collision detection
    operation CollisionDetection(
        element1Qubits : Qubit[],
        element2Qubits : Qubit[],
        collisionQubit : Qubit
    ) : Unit {
        // Compare elements
        for i in 0 .. Min(Length(element1Qubits), Length(element2Qubits)) - 1 {
            CNOT(element1Qubits[i], element2Qubits[i]);
            CNOT(element2Qubits[i], collisionQubit);
            CNOT(element1Qubits[i], element2Qubits[i]); // Uncompute
        }

        // If all bits match, collisionQubit will be |0>
        X(collisionQubit);
    }

    // ============================================
    // Quantum Walk Search
    // ============================================

    /// # Summary
    /// Quantum walk on graph
    operation QuantumWalkSearch(
        vertexQubits : Qubit[],
        coinQubits : Qubit[],
        shiftOracle : (Qubit[], Qubit[] => Unit),
        markedVertices : Bool[],
        numSteps : Int
    ) : Result[] {
        // Initialize
        ApplyToEach(H, vertexQubits);
        ApplyToEach(H, coinQubits);

        // Quantum walk steps
        for step in 0 .. numSteps - 1 {
            // Coin operator
            ApplyToEach(H, coinQubits);

            // Shift operator
            shiftOracle(vertexQubits, coinQubits);

            // Oracle for marked vertices
            MarkingOracle(vertexQubits, markedVertices);
        }

        // Measure
        mutable results = new Result[Length(vertexQubits)];
        for i in 0 .. Length(vertexQubits) - 1 {
            set results w/= i <- M(vertexQubits[i]);
        }

        return results;
    }

    /// # Summary
    /// Szegedy quantum walk
    operation SzegedyQuantumWalk(
        stateQubits1 : Qubit[],
        stateQubits2 : Qubit[],
        walkOperator : (Qubit[], Qubit[] => Unit is Adj + Ctl),
        numSteps : Int
    ) : Unit {
        // Initialize both registers
        ApplyToEach(H, stateQubits1);
        ApplyToEach(H, stateQubits2);

        // Apply walk operator
        for step in 0 .. numSteps - 1 {
            walkOperator(stateQubits1, stateQubits2);

            // Swap registers
            for i in 0 .. Min(Length(stateQubits1), Length(stateQubits2)) - 1 {
                SWAP(stateQubits1[i], stateQubits2[i]);
            }
        }
    }

    // ============================================
    // Spatial Search
    // ============================================

    /// # Summary
    /// Spatial search on grid
    operation SpatialSearchGrid(
        positionQubits : Qubit[],
        markedPosition : (Int, Int),
        gridSize : Int,
        numSteps : Int
    ) : (Int, Int) {
        let dim = Length(positionQubits) / 2;

        // Initialize uniform superposition
        ApplyToEach(H, positionQubits);

        // Spatial search iterations
        for step in 0 .. numSteps - 1 {
            // Oracle
            let (markedX, markedY) = markedPosition;
            use oracleQubit = Qubit();

            // Mark position
            for i in 0 .. dim - 1 {
                if (markedX >>> i) % 2 == 1 {
                    CNOT(positionQubits[i], oracleQubit);
                }
                if (markedY >>> i) % 2 == 1 {
                    CNOT(positionQubits[dim + i], oracleQubit);
                }
            }

            Reset(oracleQubit);

            // Diffusion (quantum walk on grid)
            for i in 0 .. Length(positionQubits) - 1 {
                H(positionQubits[i]);
            }
        }

        // Measure position
        mutable x = 0;
        mutable y = 0;

        for i in 0 .. dim - 1 {
            if M(positionQubits[i]) == One {
                set x += 1 <<< i;
            }
            if M(positionQubits[dim + i]) == One {
                set y += 1 <<< i;
            }
        }

        return (x, y);
    }

    // ============================================
    // Quantum Binary Search
    // ============================================

    /// # Summary
    /// Quantum binary search
    operation QuantumBinarySearch(
        sortedArrayQubits : Qubit[],
        targetQubits : Qubit[],
        resultQubit : Qubit,
        arraySize : Int
    ) : Int {
        mutable left = 0;
        mutable right = arraySize - 1;
        mutable result = -1;

        while left <= right {
            let mid = (left + right) / 2;

            // Compare middle element with target
            use comparisonQubit = Qubit();

            // Quantum comparison
            for i in 0 .. Min(Length(sortedArrayQubits), Length(targetQubits)) - 1 {
                CNOT(sortedArrayQubits[i], targetQubits[i]);
                CNOT(targetQubits[i], comparisonQubit);
            }

            let comparison = M(comparisonQubit);

            if comparison == Zero {
                set result = mid;
                set left = right + 1; // Exit loop
            } else {
                // Decide which half to search
                H(resultQubit);
                let goLeft = M(resultQubit) == Zero;

                if goLeft {
                    set right = mid - 1;
                } else {
                    set left = mid + 1;
                }
            }

            Reset(comparisonQubit);
        }

        return result;
    }

    // ============================================
    // Utility Functions
    // ============================================

    /// # Summary
    /// Calculate optimal Grover iterations
    function OptimalGroverIterations(searchSpaceSize : Int, numSolutions : Int) : Int {
        let N = IntAsDouble(searchSpaceSize);
        let M = IntAsDouble(numSolutions);

        if M >= N {
            return 1;
        }

        let iterations = Round(PI() / (4.0 * ArcSin(Sqrt(M / N))));
        return iterations;
    }

    /// # Summary
    /// Verify search result
    operation VerifySearchResult(
        result : Result[],
        targetState : Bool[]
    ) : Bool {
        if Length(result) != Length(targetState) {
            return false;
        }

        for i in 0 .. Length(result) - 1 {
            let expected = targetState[i] ? One | Zero;
            if result[i] != expected {
                return false;
            }
        }

        return true;
    }

    /// # Summary
    /// Success probability estimation
    operation EstimateSuccessProbability(
        searchQubits : Qubit[],
        targetState : Bool[],
        numShots : Int
    ) : Double {
        mutable successes = 0;

        for shot in 0 .. numShots - 1 {
            // Run Grover search
            let results = GroverSearch(Length(searchQubits), targetState, 1);

            // Check if correct
            if VerifySearchResult(results, targetState) {
                set successes += 1;
            }
        }

        return IntAsDouble(successes) / IntAsDouble(numShots);
    }

    /// # Summary
    /// Quantum search with error correction
    operation ErrorCorrectedGroverSearch(
        searchQubits : Qubit[],
        ancillaQubits : Qubit[],
        syndromeQubits : Qubit[],
        targetState : Bool[],
        numIterations : Int
    ) : Result[] {
        // Encode search qubits with error correction
        for i in 0 .. Length(searchQubits) - 1 {
            // Simple 3-qubit repetition code
            if i * 3 < Length(ancillaQubits) {
                CNOT(searchQubits[i], ancillaQubits[i * 3]);
                CNOT(searchQubits[i], ancillaQubits[i * 3 + 1]);
            }
        }

        // Apply Grover iterations with periodic error correction
        for iter in 0 .. numIterations - 1 {
            // Error correction every few iterations
            if iter % 3 == 0 && Length(syndromeQubits) >= 2 {
                // Syndrome measurement
                for i in 0 .. Length(searchQubits) - 1 {
                    if i * 3 + 2 < Length(ancillaQubits) {
                        CNOT(searchQubits[i], syndromeQubits[0]);
                        CNOT(ancillaQubits[i * 3], syndromeQubits[0]);
                        CNOT(ancillaQubits[i * 3], syndromeQubits[1]);
                        CNOT(ancillaQubits[i * 3 + 1], syndromeQubits[1]);

                        // Correct errors based on syndrome
                        let syndrome0 = M(syndromeQubits[0]);
                        let syndrome1 = M(syndromeQubits[1]);

                        if syndrome0 == One {
                            X(searchQubits[i]);
                        }
                        if syndrome1 == One {
                            X(ancillaQubits[i * 3 + 1]);
                        }
                    }
                }
            }

            // Grover iteration
            use auxQubits = Qubit[2];
            GroverIteration(searchQubits, targetState, auxQubits);
        }

        // Measure
        mutable results = new Result[Length(searchQubits)];
        for i in 0 .. Length(searchQubits) - 1 {
            set results w/= i <- M(searchQubits[i]);
        }

        return results;
    }
}
