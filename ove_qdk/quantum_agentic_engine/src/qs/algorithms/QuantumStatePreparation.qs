namespace QuantumAgenticEngine.Algorithms.StatePreparation {
    open Microsoft.Quantum.Canon;
    open Microsoft.Quantum.Intrinsic;
    open Microsoft.Quantum.Math;
    open Microsoft.Quantum.Convert;
    open Microsoft.Quantum.Measurement;
    open Microsoft.Quantum.Arrays;
    open Microsoft.Quantum.Diagnostics;
    open Microsoft.Quantum.Preparation;
    open QuantumAgenticEngine.Core;
    open QuantumAgenticEngine.Utils;

    // ========================================
    // QUANTUM STATE PREPARATION
    // ========================================
    // Efficient state preparation algorithms
    // for arbitrary quantum states

    // ========================================
    // AMPLITUDE ENCODING
    // ========================================

    operation PrepareAmplitudeEncoding(
        amplitudes : Double[],
        qubits : Qubit[]
    ) : Unit is Adj + Ctl {
        // Prepare state: sum_i amplitudes[i] |i>
        let n = Length(qubits);
        let numStates = 2^n;

        // Normalize amplitudes
        mutable normalized = new Complex[numStates];
        mutable norm = 0.0;

        for i in 0..numStates - 1 {
            if (i < Length(amplitudes)) {
                set norm += amplitudes[i] * amplitudes[i];
            }
        }

        let sqrtNorm = Sqrt(norm);

        for i in 0..numStates - 1 {
            if (i < Length(amplitudes)) {
                let realPart = amplitudes[i] / sqrtNorm;
                set normalized w/= i <- Complex(realPart, 0.0);
            } else {
                set normalized w/= i <- Complex(0.0, 0.0);
            }
        }

        // Use state preparation routine
        PrepareArbitraryState(normalized, LittleEndian(qubits));
    }

    operation PrepareArbitraryState(
        amplitudes : Complex[],
        indexRegister : LittleEndian
    ) : Unit is Adj + Ctl {
        // Shende-Bullock-Markov algorithm for state preparation
        let n = Length(indexRegister!);
        let numStates = 2^n;

        // Prepare recursively
        PrepareStateRecursive(amplitudes, indexRegister!, 0, numStates, 0);
    }

    operation PrepareStateRecursive(
        amplitudes : Complex[],
        qubits : Qubit[],
        start : Int,
        length : Int,
        depth : Int
    ) : Unit is Adj + Ctl {
        if (length == 1) {
            // Base case: single state
            return ();
        }

        let half = length / 2;

        // Compute probabilities for each half
        mutable prob0 = 0.0;
        mutable prob1 = 0.0;

        for i in start..start + half - 1 {
            set prob0 += AbsComplexSquared(amplitudes[i]);
        }

        for i in start + half..start + length - 1 {
            set prob1 += AbsComplexSquared(amplitudes[i]);
        }

        let totalProb = prob0 + prob1;

        if (totalProb > 1e-10) {
            // Rotation angle
            let theta = 2.0 * ArcCos(Sqrt(prob0 / totalProb));

            // Apply rotation to current qubit
            Ry(theta, qubits[depth]);

            // Recursively prepare each half
            if (prob0 > 1e-10) {
                // Normalize amplitudes for |0> branch
                mutable amp0 = new Complex[half];
                for i in 0..half - 1 {
                    set amp0 w/= i <- ComplexDiv(amplitudes[start + i], Sqrt(prob0));
                }

                // Controlled preparation for |0> branch
                X(qubits[depth]);
                Controlled PrepareStateRecursive([qubits[depth]], (
                    amp0, qubits, start, half, depth + 1
                ));
                X(qubits[depth]);
            }

            if (prob1 > 1e-10) {
                // Normalize amplitudes for |1> branch
                mutable amp1 = new Complex[half];
                for i in 0..half - 1 {
                    set amp1 w/= i <- ComplexDiv(amplitudes[start + half + i], Sqrt(prob1));
                }

                // Controlled preparation for |1> branch
                Controlled PrepareStateRecursive([qubits[depth]], (
                    amp1, qubits, start + half, half, depth + 1
                ));
            }
        }
    }

    // ========================================
    // ANGLE ENCODING
    // ========================================

    operation PrepareAngleEncoding(
        angles : Double[],
        qubits : Qubit[]
    ) : Unit is Adj + Ctl {
        // Encode classical data as rotation angles
        // |x> -> R(x_1) tensor R(x_2) tensor ... tensor R(x_n)

        let n = Length(qubits);

        for i in 0..Min([n, Length(angles)]) - 1 {
            Ry(angles[i], qubits[i]);
        }
    }

    operation PrepareDenseAngleEncoding(
        data : Double[],
        qubits : Qubit[]
    ) : Unit is Adj + Ctl {
        // Dense angle encoding: two features per qubit
        let n = Length(qubits);
        let numFeatures = Length(data);

        for i in 0..n - 1 {
            let feature1Idx = 2 * i;
            let feature2Idx = 2 * i + 1;

            if (feature1Idx < numFeatures) {
                let theta1 = data[feature1Idx];
                let theta2 = feature2Idx < numFeatures ? data[feature2Idx] | 0.0;

                // U(theta1, theta2) = Rz(theta2) Ry(theta1)
                Ry(theta1, qubits[i]);
                Rz(theta2, qubits[i]);
            }
        }
    }

    // ========================================
    // BASIS ENCODING
    // ========================================

    operation PrepareBasisEncoding(
        binaryData : Int[],
        qubits : Qubit[]
    ) : Unit is Adj + Ctl {
        // Encode binary data directly in computational basis
        let n = Length(qubits);

        for i in 0..Min([n, Length(binaryData)]) - 1 {
            if (binaryData[i] == 1) {
                X(qubits[i]);
            }
        }
    }

    operation PrepareIntegerEncoding(
        value : Int,
        qubits : Qubit[]
    ) : Unit is Adj + Ctl {
        // Encode integer in binary representation
        let n = Length(qubits);

        for i in 0..n - 1 {
            let bit = (value >>> i) &&& 1;
            if (bit == 1) {
                X(qubits[i]);
            }
        }
    }

    // ========================================
    // GAUSSIAN STATE PREPARATION
    // ========================================

    operation PrepareGaussianState(
        mean : Double,
        stdDev : Double,
        qubits : Qubit[]
    ) : Unit is Adj + Ctl {
        // Prepare discretized Gaussian state
        let n = Length(qubits);
        let numPoints = 2^n;

        // Compute Gaussian amplitudes
        mutable amplitudes = new Double[numPoints];

        for i in 0..numPoints - 1 {
            let x = IntAsDouble(i) - mean;
            let amp = ExpD(-x * x / (2.0 * stdDev * stdDev));
            set amplitudes w/= i <- amp;
        }

        PrepareAmplitudeEncoding(amplitudes, qubits);
    }

    operation PrepareMultivariateGaussian(
        means : Double[],
        covariance : Double[][],
        qubits : Qubit[][]
    ) : Unit is Adj + Ctl {
        // Prepare product of 1D Gaussians (simplified)
        let numDimensions = Length(means);

        for d in 0..numDimensions - 1 {
            let stdDev = Sqrt(covariance[d][d]);
            PrepareGaussianState(means[d], stdDev, qubits[d]);
        }
    }

    // ========================================
    // UNIFORM SUPERPOSITION
    // ========================================

    operation PrepareUniformSuperposition(
        qubits : Qubit[]
    ) : Unit is Adj + Ctl {
        // Prepare (1/sqrt(2^n)) sum_i |i>
        for q in qubits {
            H(q);
        }
    }

    operation PrepareWeightedSuperposition(
        weights : Double[],
        qubits : Qubit[]
    ) : Unit is Adj + Ctl {
        // Prepare superposition with specified weights
        let n = Length(qubits);
        let numStates = 2^n;

        mutable amplitudes = new Double[numStates];

        for i in 0..numStates - 1 {
            if (i < Length(weights)) {
                set amplitudes w/= i <- Sqrt(weights[i]);
            } else {
                set amplitudes w/= i <- 0.0;
            }
        }

        PrepareAmplitudeEncoding(amplitudes, qubits);
    }

    // ========================================
    // ENTANGLED STATE PREPARATION
    // ========================================

    operation PrepareBellState(
        qubits : Qubit[]
    ) : Unit is Adj + Ctl {
        // Prepare Bell state: (|00> + |11>) / sqrt(2)
        H(qubits[0]);
        CNOT(qubits[0], qubits[1]);
    }

    operation PrepareGHZState(
        qubits : Qubit[]
    ) : Unit is Adj + Ctl {
        // Prepare GHZ state: (|0...0> + |1...1>) / sqrt(2)
        H(qubits[0]);
        for i in 0..Length(qubits) - 2 {
            CNOT(qubits[i], qubits[i + 1]);
        }
    }

    operation PrepareWState(
        qubits : Qubit[]
    ) : Unit is Adj + Ctl {
        // Prepare W state: (|100...0> + |010...0> + ... + |00...01>) / sqrt(n)
        let n = Length(qubits);

        // Start with |0...01>
        X(qubits[n - 1]);

        // Iteratively build W state
        for i in n - 2..-1..0 {
            let theta = 2.0 * ArcCos(Sqrt(1.0 / IntAsDouble(n - i)));

            use ancilla = Qubit();
            Ry(theta, ancilla);

            Controlled SWAP([ancilla], (qubits[i], qubits[i + 1]));

            Reset(ancilla);
        }
    }

    operation PrepareClusterState(
        qubits : Qubit[],
        adjacency : Bool[][]
    ) : Unit is Adj + Ctl {
        // Prepare graph/cluster state
        // Start with |+> states
        for q in qubits {
            H(q);
        }

        // Apply controlled-Z for each edge
        let n = Length(qubits);
        for i in 0..n - 1 {
            for j in i + 1..n - 1 {
                if (adjacency[i][j]) {
                    CZ(qubits[i], qubits[j]);
                }
            }
        }
    }

    // ========================================
    // COHERENT STATE PREPARATION
    // ========================================

    operation PrepareCoherentState(
        alpha : Complex,
        qubits : Qubit[]
    ) : Unit is Adj + Ctl {
        // Approximate coherent state |alpha>
        // Truncated to Hilbert space dimension
        let n = Length(qubits);
        let dim = 2^n;

        mutable amplitudes = new Double[dim];
        let absAlpha = AbsComplex(alpha);
        let expFactor = ExpD(-absAlpha * absAlpha / 2.0);

        for k in 0..dim - 1 {
            let kFact = Factorial(k);
            let amp = expFactor * Pow(absAlpha, IntAsDouble(k)) / Sqrt(IntAsDouble(kFact));
            set amplitudes w/= k <- amp;
        }

        PrepareAmplitudeEncoding(amplitudes, qubits);
    }

    operation PrepareSqueezedState(
        r : Double,
        phi : Double,
        qubits : Qubit[]
    ) : Unit is Adj + Ctl {
        // Approximate squeezed vacuum state
        let n = Length(qubits);
        let dim = 2^n;

        mutable amplitudes = new Double[dim];

        for k in 0..dim - 1 {
            if (k % 2 == 0) {
                let m = k / 2;
                let tanhR = Tanh(r);
                let sechR = 1.0 / Cosh(r);

                let amp = Sqrt(sechR) * Sqrt(DoubleFactorial(2 * m - 1)) /
                         (Pow(2.0, IntAsDouble(m)) * Sqrt(Factorial(m))) *
                         Pow(tanhR, IntAsDouble(m));

                set amplitudes w/= k <- amp;
            } else {
                set amplitudes w/= k <- 0.0;
            }
        }

        PrepareAmplitudeEncoding(amplitudes, qubits);
    }

    // ========================================
    // THERMAL STATE PREPARATION
    // ========================================

    operation PrepareThermalState(
        temperature : Double,
        hamiltonian : (Pauli[], Double)[],
        qubits : Qubit[]
    ) : Unit is Adj + Ctl {
        // Prepare Gibbs state: rho = exp(-H/T) / Z
        // Using purification approach

        let n = Length(qubits);
        use ancilla = Qubit[n];

        // Prepare maximally mixed state on system
        // by entangling with ancilla
        for i in 0..n - 1 {
            H(qubits[i]);
            CNOT(qubits[i], ancilla[i]);
        }

        // Apply imaginary time evolution (simplified)
        let beta = 1.0 / temperature;
        ImaginaryTimeEvolution(hamiltonian, beta, qubits);

        ResetAll(ancilla);
    }

    operation ImaginaryTimeEvolution(
        hamiltonian : (Pauli[], Double)[],
        time : Double,
        qubits : Qubit[]
    ) : Unit is Adj + Ctl {
        // Trotterized imaginary time evolution
        let numSteps = 100;
        let dt = time / IntAsDouble(numSteps);

        for _ in 0..numSteps - 1 {
            for (pauliString, coefficient) in hamiltonian {
                let angle = -2.0 * coefficient * dt;
                ExpPauli(angle, pauliString, qubits);
            }
        }
    }

    // ========================================
    // MATRIX PRODUCT STATE PREPARATION
    // ========================================

    operation PrepareMPS(
        tensors : Double[][][],
        qubits : Qubit[]
    ) : Unit is Adj + Ctl {
        // Prepare Matrix Product State
        let n = Length(qubits);
        let bondDim = Length(tensors[0]);

        use ancilla = Qubit[Ceiling(Lg(IntAsDouble(bondDim)))];

        // Prepare initial bond state
        H(ancilla[0]);

        for i in 0..n - 1 {
            // Apply local tensor
            ApplyMPSTensor(tensors[i], ancilla, qubits[i]);

            // Update bond (simplified)
            if (i < n - 1) {
                // Apply isometry to update ancilla
            }
        }

        ResetAll(ancilla);
    }

    operation ApplyMPSTensor(
        tensor : Double[][],
        bondQubits : Qubit[],
        physicalQubit : Qubit
    ) : Unit is Adj + Ctl {
        // Apply MPS tensor operation
        let bondDim = Length(tensor);
        let physDim = 2;

        for b in 0..bondDim - 1 {
            for p in 0..physDim - 1 {
                let amplitude = tensor[b][p];
                if (AbsD(amplitude) > 1e-10) {
                    // Controlled rotation based on bond state
                    // Simplified implementation
                }
            }
        }
    }

    // ========================================
    // QUANTUM RANDOM ACCESS MEMORY
    // ========================================

    operation QRAM(
        address : Qubit[],
        data : Double[],
        output : Qubit[]
    ) : Unit is Adj + Ctl {
        // Quantum RAM: |i>|0> -> |i>|data[i]>
        let numEntries = Length(data);
        let addrBits = Length(address);

        for i in 0..numEntries - 1 {
            // Prepare address state |i>
            use addrControl = Qubit();

            // Set control based on address
            let binaryAddr = IntToBinary(i, addrBits);
            for j in 0..addrBits - 1 {
                if (binaryAddr[j] == 1) {
                    Controlled X([address[j]], addrControl);
                } else {
                    use notAddr = Qubit();
                    X(notAddr);
                    CNOT(address[j], notAddr);
                    Controlled X([notAddr], addrControl);
                    Reset(notAddr);
                }
            }

            // Encode data[i] when address matches
            let dataValue = data[i];
            let dataBits = DoubleToBinary(dataValue, Length(output));

            for j in 0..Length(output) - 1 {
                if (dataBits[j] == 1) {
                    Controlled X([addrControl], output[j]);
                }
            }

            Reset(addrControl);
        }
    }

    // ========================================
    // SPARSE STATE PREPARATION
    // ========================================

    operation PrepareSparseState(
        nonzeroIndices : Int[],
        nonzeroValues : Double[],
        qubits : Qubit[]
    ) : Unit is Adj + Ctl {
        // Prepare state with sparse representation
        let n = Length(qubits);
        let numNonzero = Length(nonzeroIndices);

        // Use index register
        use indexQubits = Qubit[Ceiling(Lg(IntAsDouble(numNonzero)))];

        // Prepare uniform superposition over nonzero indices
        PrepareUniformSuperposition(indexQubits);

        // Map index to actual state
        for i in 0..numNonzero - 1 {
            let actualIndex = nonzeroIndices[i];
            let value = nonzeroValues[i];

            // Controlled preparation
            use isIndex = Qubit();

            let binaryI = IntToBinary(i, Length(indexQubits));
            for j in 0..Length(indexQubits) - 1 {
                if (binaryI[j] == 1) {
                    Controlled X([indexQubits[j]], isIndex);
                }
            }

            // Prepare |actualIndex> with amplitude |value>
            Controlled PrepareIndexState([isIndex], (actualIndex, value, qubits));

            Reset(isIndex);
        }

        ResetAll(indexQubits);
    }

    operation PrepareIndexState(
        index : Int,
        amplitude : Double,
        qubits : Qubit[]
    ) : Unit is Adj + Ctl {
        // Prepare specific basis state with given amplitude
        let binary = IntToBinary(index, Length(qubits));

        for i in 0..Length(qubits) - 1 {
            if (binary[i] == 1) {
                X(qubits[i]);
            }
        }

        // Apply amplitude (if needed)
        Ry(2.0 * ArcCos(amplitude), qubits[0]);
    }

    // ========================================
    // UTILITY FUNCTIONS
    // ========================================

    function AbsComplex(z : Complex) : Double {
        return Sqrt(z::Real * z::Real + z::Imag * z::Imag);
    }

    function AbsComplexSquared(z : Complex) : Double {
        return z::Real * z::Real + z::Imag * z::Imag;
    }

    function ComplexDiv(z : Complex, x : Double) : Complex {
        return Complex(z::Real / x, z::Imag / x);
    }

    function Factorial(n : Int) : Int {
        mutable result = 1;
        for i in 2..n {
            set result *= i;
        }
        return result;
    }

    function DoubleFactorial(n : Int) : Int {
        mutable result = 1;
        mutable i = n;
        while (i > 0) {
            set result *= i;
            set i -= 2;
        }
        return result;
    }

    function ExpD(x : Double) : Double {
        // Taylor series approximation
        mutable result = 1.0;
        mutable term = 1.0;

        for n in 1..20 {
            set term *= x / IntAsDouble(n);
            set result += term;
        }

        return result;
    }

    function Pow(base : Double, exp : Int) : Double {
        mutable result = 1.0;
        for _ in 0..exp - 1 {
            set result *= base;
        }
        return result;
    }

    function Tanh(x : Double) : Double {
        let eX = ExpD(x);
        let eNegX = ExpD(-x);
        return (eX - eNegX) / (eX + eNegX);
    }

    function Cosh(x : Double) : Double {
        return (ExpD(x) + ExpD(-x)) / 2.0;
    }

    function IntToBinary(value : Int, numBits : Int) : Int[] {
        mutable result = new Int[numBits];
        mutable temp = value;

        for i in 0..numBits - 1 {
            set result w/= i <- temp % 2;
            set temp = temp / 2;
        }

        return result;
    }

    function DoubleToBinary(value : Double, numBits : Int) : Int[] {
        // Simplified: just encode sign and magnitude
        mutable result = new Int[numBits];

        let scaled = Truncate(AbsD(value) * IntAsDouble(2^(numBits - 2)));
        let binary = IntToBinary(scaled, numBits - 1);

        for i in 0..numBits - 2 {
            set result w/= i <- binary[i];
        }

        // Sign bit
        set result w/= (numBits - 1) <- (value < 0.0 ? 1 | 0);

        return result;
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

    function Ceiling(x : Double) : Int {
        let floor = Floor(x);
        return x > IntAsDouble(floor) ? floor + 1 | floor;
    }

    function AbsD(x : Double) : Double {
        return x >= 0.0 ? x | -x;
    }

    function Min(a : Int, b : Int) : Int {
        return a < b ? a | b;
    }

    // ========================================
    // COMPLEX NUMBER STRUCT
    // ========================================

    struct Complex {
        Real : Double,
        Imag : Double
    }

    // ========================================
    // ADVANCED STATE PREPARATION
    // ========================================

    operation PrepareSymmetricState(
        qubits : Qubit[]
    ) : Unit is Adj + Ctl {
        // Prepare state symmetric under qubit permutations
        // (|0...0> + |1...1> + sum over permutations of |10...0>) / sqrt(n+1)

        let n = Length(qubits);

        // Superposition of |0...0>, |1...1>, and W-state components
        use control = Qubit[2];
        H(control[0]);
        H(control[1]);

        // |00> -> |0...0>
        // |01> -> |1...1>
        // |10> or |11> -> W-state

        // |0...0> component
        use is00 = Qubit();
        X(is00);
        CNOT(control[0], is00);
        CNOT(control[1], is00);
        // Already |0...0>, nothing to do

        // |1...1> component
        use is01 = Qubit();
        X(is01);
        CNOT(control[0], is01);
        X(is01);
        CNOT(control[1], is01);
        for q in qubits {
            Controlled X([is01], q);
        }

        // W-state component
        use is1x = Qubit();
        CNOT(control[0], is1x);
        Controlled PrepareWState([is1x], qubits);

        ResetAll(control);
        Reset(is00);
        Reset(is01);
        Reset(is1x);
    }

    operation PrepareDickeState(
        qubits : Qubit[],
        hammingWeight : Int
    ) : Unit is Adj + Ctl {
        // Prepare Dicke state: uniform superposition of all states
        // with exactly hammingWeight ones

        let n = Length(qubits);

        // Use split-and-merge approach
        if (hammingWeight == 0) {
            // All zeros, nothing to do
            return ();
        } elif (hammingWeight == n) {
            // All ones
            for q in qubits {
                X(q);
            }
        } else {
            // Split and prepare recursively
            let k1 = hammingWeight / 2;
            let k2 = hammingWeight - k1;
            let n1 = n / 2;
            let n2 = n - n1;

            use split = Qubit();
            let theta = 2.0 * ArcCos(Sqrt(IntAsDouble(k1) / IntAsDouble(hammingWeight)));
            Ry(theta, split);

            // Prepare sub-states
            Controlled PrepareDickeState([split], (qubits[0..n1 - 1], k1));
            X(split);
            Controlled PrepareDickeState([split], (qubits[n1..n - 1], k2));
            X(split);

            Reset(split);
        }
    }

    operation PrepareHypergraphState(
        qubits : Qubit[],
        hyperedges : Int[][]
    ) : Unit is Adj + Ctl {
        // Prepare hypergraph state
        // Start with |+>^tensor n
        for q in qubits {
            H(q);
        }

        // Apply controlled-Z for each hyperedge
        for edge in hyperedges {
            // Multi-controlled Z
            ApplyMultiControlledZ(qubits, edge);
        }
    }

    operation ApplyMultiControlledZ(
        qubits : Qubit[],
        controlIndices : Int[]
    ) : Unit is Adj + Ctl {
        // Apply Z controlled on all qubits in controlIndices
        if (Length(controlIndices) == 1) {
            Z(qubits[controlIndices[0]]);
        } elif (Length(controlIndices) == 2) {
            CZ(qubits[controlIndices[0]], qubits[controlIndices[1]]);
        } else {
            // Decompose multi-controlled Z
            use ancilla = Qubit[Length(controlIndices) - 2];

            // Build control tree
            CCNOT(qubits[controlIndices[0]], qubits[controlIndices[1]], ancilla[0]);

            for i in 2..Length(controlIndices) - 2 {
                CCNOT(ancilla[i - 2], qubits[controlIndices[i]], ancilla[i - 1]);
            }

            // Final controlled Z
            Controlled Z([ancilla[Length(controlIndices) - 3]], qubits[controlIndices[Length(controlIndices) - 1]]);

            // Uncompute
            for i in Length(controlIndices) - 2..-1..2 {
                CCNOT(ancilla[i - 2], qubits[controlIndices[i]], ancilla[i - 1]);
            }

            CCNOT(qubits[controlIndices[0]], qubits[controlIndices[1]], ancilla[0]);

            ResetAll(ancilla);
        }
    }
}
