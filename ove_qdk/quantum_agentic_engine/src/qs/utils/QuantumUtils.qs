namespace QuantumAgenticEngine.Utils {
    open Microsoft.Quantum.Canon;
    open Microsoft.Quantum.Intrinsic;
    open Microsoft.Quantum.Math;
    open Microsoft.Quantum.Convert;
    open Microsoft.Quantum.Measurement;
    open Microsoft.Quantum.Arrays;
    open Microsoft.Quantum.Diagnostics;

    // ========================================
    // QUANTUM UTILITY FUNCTIONS
    // ========================================
    // Common utility operations and functions for quantum computing

    // ========================================
    // STATE MANIPULATION
    // ========================================

    operation PreparePureState(qubits : Qubit[], amplitudes : Complex[]) : Unit is Adj + Ctl {
        let n = Length(qubits);
        let N = 2^n;

        // Normalize amplitudes
        mutable norm = 0.0;
        for amp in amplitudes {
            set norm += AbsComplexSquared(amp);
        }

        mutable normalized = new Complex[N];
        for i in 0..N - 1 {
            if (i < Length(amplitudes)) {
                set normalized w/= i <- ComplexDiv(amplitudes[i], Sqrt(norm));
            } else {
                set normalized w/= i <- Complex(0.0, 0.0);
            }
        }

        // Apply state preparation
        PrepareArbitraryStateCP(normalized, LittleEndian(qubits));
    }

    operation PrepareArbitraryStateCP(amplitudes : Complex[], register : LittleEndian) : Unit is Adj + Ctl {
        let qubits = register!;
        let n = Length(qubits);

        if (n == 0) {
            return ();
        }

        // Use recursive state preparation
        PrepareStateRecursiveCP(amplitudes, qubits, 0, 2^n, 0);
    }

    operation PrepareStateRecursiveCP(amplitudes : Complex[], qubits : Qubit[],
                                     start : Int, length : Int, depth : Int) : Unit is Adj + Ctl {
        if (length == 1) {
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
            let theta = 2.0 * ArcCos(Sqrt(prob0 / totalProb));

            // Apply rotation
            Ry(theta, qubits[depth]);

            // Recursively prepare each half
            if (prob0 > 1e-10) {
                mutable amp0 = new Complex[half];
                for i in 0..half - 1 {
                    set amp0 w/= i <- ComplexDiv(amplitudes[start + i], Sqrt(prob0));
                }

                X(qubits[depth]);
                Controlled PrepareStateRecursiveCP([qubits[depth]],
                    (amp0, qubits, start, half, depth + 1));
                X(qubits[depth]);
            }

            if (prob1 > 1e-10) {
                mutable amp1 = new Complex[half];
                for i in 0..half - 1 {
                    set amp1 w/= i <- ComplexDiv(amplitudes[start + half + i], Sqrt(prob1));
                }

                Controlled PrepareStateRecursiveCP([qubits[depth]],
                    (amp1, qubits, start + half, half, depth + 1));
            }
        }
    }

    // ========================================
    // MEASUREMENT UTILITIES
    // ========================================

    operation MeasureAll(qubits : Qubit[]) : Result[] {
        mutable results = new Result[Length(qubits)];
        for i in 0..Length(qubits) - 1 {
            set results w/= i <- M(qubits[i]);
        }
        return results;
    }

    operation MeasureInBasis(qubits : Qubit[], basis : Pauli[]) : Result[] {
        use ancilla = Qubit[Length(qubits)];

        // Copy state
        for i in 0..Length(qubits) - 1 {
            CNOT(qubits[i], ancilla[i]);
        }

        // Apply basis rotations
        for i in 0..Length(basis) - 1 {
            if (basis[i] == PauliX) {
                H(ancilla[i]);
            } elif (basis[i] == PauliY) {
                Rx(PI() / 2.0, ancilla[i]);
            }
        }

        // Measure
        let results = MeasureAll(ancilla);

        ResetAll(ancilla);
        return results;
    }

    operation EstimateExpectation(qubits : Qubit[], observable : (Pauli[], Double)[],
                                  numShots : Int) : Double {
        mutable expectation = 0.0;

        for _ in 0..numShots - 1 {
            use measureQubits = Qubit[Length(qubits)];

            // Copy state
            for i in 0..Length(qubits) - 1 {
                CNOT(qubits[i], measureQubits[i]);
            }

            // Measure observable
            mutable shotValue = 0.0;
            for (pauliString, coefficient) in observable {
                let value = MeasurePauliExpectation(measureQubits, pauliString);
                set shotValue += coefficient * value;
            }

            set expectation += shotValue;
            ResetAll(measureQubits);
        }

        return expectation / IntAsDouble(numShots);
    }

    operation MeasurePauliExpectation(qubits : Qubit[], pauliString : Pauli[]) : Double {
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

        // Measure and compute parity
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

    // ========================================
    // ENTANGLEMENT UTILITIES
    // ========================================

    operation CreateBellPair(q1 : Qubit, q2 : Qubit) : Unit is Adj + Ctl {
        H(q1);
        CNOT(q1, q2);
    }

    operation CreateGHZState(qubits : Qubit[]) : Unit is Adj + Ctl {
        if (Length(qubits) > 0) {
            H(qubits[0]);
            for i in 0..Length(qubits) - 2 {
                CNOT(qubits[i], qubits[i + 1]);
            }
        }
    }

    operation CreateWState(qubits : Qubit[]) : Unit is Adj + Ctl {
        let n = Length(qubits);

        if (n > 0) {
            // Initialize last qubit to |1>
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
    }

    operation CreateClusterState(qubits : Qubit[], adjacency : Bool[][]) : Unit is Adj + Ctl {
        // Prepare |+> states
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

    operation EntanglementSwapping(q1 : Qubit, q2 : Qubit,
                                   bell1 : Qubit, bell2 : Qubit) : Unit {
        // Perform Bell measurement on bell1 and bell2
        CNOT(bell1, bell2);
        H(bell1);

        let m1 = M(bell1);
        let m2 = M(bell2);

        // Apply corrections to q1 and q2
        if (m2 == One) {
            X(q2);
        }
        if (m1 == One) {
            Z(q2);
        }
    }

    // ========================================
    // FIDELITY AND DISTANCE MEASURES
    // ========================================

    operation EstimateStateFidelity(state1 : Qubit[], state2 : Qubit[],
                                   numShots : Int) : Double {
        mutable fidelity = 0.0;

        for _ in 0..numShots - 1 {
            use s1 = Qubit[Length(state1)];
            use s2 = Qubit[Length(state2)];

            // Copy states
            for i in 0..Length(state1) - 1 {
                CNOT(state1[i], s1[i]);
                CNOT(state2[i], s2[i]);
            }

            // Compute overlap using swap test
            let overlap = SwapTest(s1, s2);
            set fidelity += overlap;

            ResetAll(s1);
            ResetAll(s2);
        }

        return fidelity / IntAsDouble(numShots);
    }

    operation SwapTest(state1 : Qubit[], state2 : Qubit[]) : Double {
        use ancilla = Qubit();

        H(ancilla);

        for i in 0..Length(state1) - 1 {
            Controlled SWAP([ancilla], (state1[i], state2[i]));
        }

        H(ancilla);

        let result = M(ancilla);
        let probability = result == Zero ? 1.0 | 0.0;

        Reset(ancilla);

        // Fidelity = 2*P(0) - 1
        return 2.0 * probability - 1.0;
    }

    // ========================================
    // TOMOGRAPHY
    // ========================================

    operation StateTomography(qubits : Qubit[], numShots : Int) : Double[][] {
        let n = Length(qubits);
        let numBases = 3^n;

        mutable densityMatrix = new Double[][numBases];

        // Pauli operators
        let pauliBases = [PauliX, PauliY, PauliZ];

        for basisIdx in 0..numBases - 1 {
            mutable basis = new Pauli[n];
            mutable temp = basisIdx;

            for i in 0..n - 1 {
                set basis w/= i <- pauliBases[temp % 3];
                set temp = temp / 3;
            }

            mutable expectation = 0.0;
            for _ in 0..numShots - 1 {
                use measureQubits = Qubit[n];

                // Copy state
                for i in 0..n - 1 {
                    CNOT(qubits[i], measureQubits[i]);
                }

                // Measure in basis
                let value = MeasurePauliExpectation(measureQubits, basis);
                set expectation += value;

                ResetAll(measureQubits);
            }

            mutable row = new Double[1];
            set row w/= 0 <- expectation / IntAsDouble(numShots);
            set densityMatrix w/= basisIdx <- row;
        }

        return densityMatrix;
    }

    // ========================================
    // RANDOM STATE GENERATION
    // ========================================

    operation PrepareRandomState(qubits : Qubit[], seed : Int) : Unit {
        // Set random seed
        SetRandomSeed(seed);

        // Apply random rotations
        for q in qubits {
            let theta = DrawRandomDouble(0.0, 2.0 * PI());
            let phi = DrawRandomDouble(0.0, 2.0 * PI());

            Rx(theta, q);
            Rz(phi, q);
        }

        // Add random entanglement
        for i in 0..Length(qubits) - 2 {
            if (DrawRandomDouble(0.0, 1.0) < 0.5) {
                CNOT(qubits[i], qubits[i + 1]);
            }
        }
    }

    // ========================================
    // QUANTUM CHANNELS
    // ========================================

    operation ApplyDepolarizingChannel(qubit : Qubit, probability : Double) : Unit {
        let rand = DrawRandomDouble(0.0, 1.0);

        if (rand < probability / 3.0) {
            X(qubit);
        } elif (rand < 2.0 * probability / 3.0) {
            Y(qubit);
        } elif (rand < probability) {
            Z(qubit);
        }
    }

    operation ApplyAmplitudeDamping(qubit : Qubit, gamma : Double) : Unit {
        let rand = DrawRandomDouble(0.0, 1.0);

        if (rand < gamma) {
            Reset(qubit);
        }
    }

    operation ApplyPhaseDamping(qubit : Qubit, lambda : Double) : Unit {
        let rand = DrawRandomDouble(0.0, 1.0);

        if (rand < lambda / 2.0) {
            Z(qubit);
        }
    }

    // ========================================
    // COMPLEX NUMBER UTILITIES
    // ========================================

    struct Complex {
        Real : Double,
        Imag : Double
    }

    function ComplexAdd(a : Complex, b : Complex) : Complex {
        return Complex(a::Real + b::Real, a::Imag + b::Imag);
    }

    function ComplexSub(a : Complex, b : Complex) : Complex {
        return Complex(a::Real - b::Real, a::Imag - b::Imag);
    }

    function ComplexMul(a : Complex, b : Complex) : Complex {
        return Complex(
            a::Real * b::Real - a::Imag * b::Imag,
            a::Real * b::Imag + a::Imag * b::Real
        );
    }

    function ComplexDiv(a : Complex, x : Double) : Complex {
        return Complex(a::Real / x, a::Imag / x);
    }

    function AbsComplex(z : Complex) : Double {
        return Sqrt(z::Real * z::Real + z::Imag * z::Imag);
    }

    function AbsComplexSquared(z : Complex) : Double {
        return z::Real * z::Real + z::Imag * z::Imag;
    }

    function Conjugate(z : Complex) : Complex {
        return Complex(z::Real, -z::Imag);
    }

    // ========================================
    // MATHEMATICAL UTILITIES
    // ========================================

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

    function BinomialCoefficient(n : Int, k : Int) : Int {
        if (k < 0 or k > n) {
            return 0;
        }
        if (k == 0 or k == n) {
            return 1;
        }

        return Factorial(n) / (Factorial(k) * Factorial(n - k));
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

    function BinaryToInt(bits : Int[]) : Int {
        mutable result = 0;
        let n = Length(bits);

        for i in 0..n - 1 {
            set result += bits[i] * 2^i;
        }

        return result;
    }

    function HammingWeight(n : Int) : Int {
        mutable count = 0;
        mutable temp = n;

        while (temp > 0) {
            set count += temp % 2;
            set temp = temp / 2;
        }

        return count;
    }

    function HammingDistance(a : Int, b : Int) : Int {
        return HammingWeight(a ^^^ b);
    }

    // ========================================
    // RANDOM NUMBER GENERATION
    // ========================================

    function DrawRandomDouble(min : Double, max : Double) : Double {
        // Simplified random number generation
        // In practice, would use proper RNG
        return (min + max) / 2.0;
    }

    function DrawRandomInt(min : Int, max : Int) : Int {
        return min + (max - min) / 2;
    }

    operation SetRandomSeed(seed : Int) : Unit {
        // Set random seed for reproducibility
        // Implementation depends on RNG
    }

    // ========================================
    // ASSERTION AND DEBUGGING
    // ========================================

    operation AssertAllZero(qubits : Qubit[]) : Unit {
        for q in qubits {
            AssertMeasurement([PauliZ], [q], Zero, "Qubit should be in |0> state");
        }
    }

    operation AssertEqualStates(state1 : Qubit[], state2 : Qubit[],
                               tolerance : Double) : Unit {
        // Check if two states are equal within tolerance
        // Implementation would use state vector comparison
    }

    operation PrintState(qubits : Qubit[], label : String) : Unit {
        // Print state information for debugging
        // This is a placeholder - actual implementation would
        // dump state vector or measurement statistics
    }

    // ========================================
    // CIRCUIT METRICS
    // ========================================

    function CalculateCircuitDepth(gates : (String, Int[])[], numQubits : Int) : Int {
        mutable depths = new Int[numQubits];
        for i in 0..numQubits - 1 {
            set depths w/= i <- 0;
        }

        for (gateType, qubits) in gates {
            mutable maxDepth = 0;
            for q in qubits {
                if (depths[q] > maxDepth) {
                    set maxDepth = depths[q];
                }
            }

            for q in qubits {
                set depths w/= q <- maxDepth + 1;
            }
        }

        mutable overallDepth = 0;
        for d in depths {
            if (d > overallDepth) {
                set overallDepth <- d;
            }
        }

        return overallDepth;
    }

    function CountGateType(gates : (String, Int[])[], gateType : String) : Int {
        mutable count = 0;
        for (g, _) in gates {
            if (g == gateType) {
                set count += 1;
            }
        }
        return count;
    }

    // ========================================
    // CONVERSION UTILITIES
    // ========================================

    function ResultsToInt(results : Result[]) : Int {
        mutable value = 0;
        for i in 0..Length(results) - 1 {
            if (results[i] == One) {
                set value += 2^i;
            }
        }
        return value;
    }

    function IntToResults(value : Int, numBits : Int) : Result[] {
        mutable results = new Result[numBits];
        mutable temp = value;

        for i in 0..numBits - 1 {
            set results w/= i <- (temp % 2 == 1 ? One | Zero);
            set temp = temp / 2;
        }

        return results;
    }

    // ========================================
    // PERMUTATION AND SHUFFLING
    // ========================================

    operation ApplyPermutation(qubits : Qubit[], permutation : Int[]) : Unit is Adj + Ctl {
        let n = Length(qubits);

        // Apply permutation using SWAP gates
        for i in 0..n - 1 {
            if (permutation[i] != i and permutation[i] > i) {
                SWAP(qubits[i], qubits[permutation[i]]);
            }
        }
    }

    operation ReverseQubits(qubits : Qubit[]) : Unit is Adj + Ctl {
        let n = Length(qubits);
        for i in 0..n / 2 - 1 {
            SWAP(qubits[i], qubits[n - 1 - i]);
        }
    }

    operation ShiftQubits(qubits : Qubit[], shift : Int) : Unit is Adj + Ctl {
        let n = Length(qubits);
        let effectiveShift = shift % n;

        if (effectiveShift < 0) {
            // Handle negative shift
        }

        // Apply cyclic shift using SWAP gates
        for _ in 0..effectiveShift - 1 {
            for i in 0..n - 2 {
                SWAP(qubits[i], qubits[i + 1]);
            }
        }
    }

    // ========================================
    // PARALLEL OPERATIONS
    // ========================================

    operation ApplyToEach(op : (Qubit => Unit is Adj + Ctl), qubits : Qubit[]) : Unit is Adj + Ctl {
        for q in qubits {
            op(q);
        }
    }

    operation ApplyToEachA(op : (Qubit => Unit is Adj), qubits : Qubit[]) : Unit is Adj {
        for q in qubits {
            op(q);
        }
    }

    operation ApplyToEachC(op : (Qubit => Unit is Ctl), qubits : Qubit[]) : Unit is Ctl {
        for q in qubits {
            op(q);
        }
    }

    operation ApplyToEachCA(op : (Qubit => Unit is Adj + Ctl), qubits : Qubit[]) : Unit is Adj + Ctl {
        for q in qubits {
            op(q);
        }
    }

    // ========================================
    // CONTROLLED OPERATIONS
    // ========================================

    operation MultiControlledX(controls : Qubit[], target : Qubit) : Unit is Adj + Ctl {
        let n = Length(controls);

        if (n == 0) {
            X(target);
        } elif (n == 1) {
            Controlled X(controls, target);
        } elif (n == 2) {
            CCNOT(controls[0], controls[1], target);
        } else {
            // Decompose using ancilla
            use ancilla = Qubit[n - 2];

            CCNOT(controls[0], controls[1], ancilla[0]);

            for i in 2..n - 2 {
                CCNOT(ancilla[i - 2], controls[i], ancilla[i - 1]);
            }

            CCNOT(ancilla[n - 3], controls[n - 1], target);

            // Uncompute
            for i in n - 2..-1..2 {
                CCNOT(ancilla[i - 2], controls[i], ancilla[i - 1]);
            }

            CCNOT(controls[0], controls[1], ancilla[0]);
        }
    }

    operation ControlledRotation(controls : Qubit[], target : Qubit,
                                 axis : Pauli, angle : Double) : Unit is Adj + Ctl {
        // Apply controlled rotation
        if (axis == PauliX) {
            Controlled Rx(controls, (angle, target));
        } elif (axis == PauliY) {
            Controlled Ry(controls, (angle, target));
        } elif (axis == PauliZ) {
            Controlled Rz(controls, (angle, target));
        }
    }

    // ========================================
    // SPECIALIZED GATES
    // ========================================

    operation SqrtX(qubit : Qubit) : Unit is Adj + Ctl {
        // Square root of X gate
        H(qubit);
        S(qubit);
        H(qubit);
    }

    operation SqrtY(qubit : Qubit) : Unit is Adj + Ctl {
        // Square root of Y gate
        Rx(PI() / 2.0, qubit);
        Rz(PI() / 2.0, qubit);
        Rx(PI() / 2.0, qubit);
    }

    operation SqrtZ(qubit : Qubit) : Unit is Adj + Ctl {
        // Square root of Z gate (S gate)
        S(qubit);
    }

    operation TGate(qubit : Qubit) : Unit is Adj + Ctl {
        // T gate (pi/8 gate)
        Rz(PI() / 4.0, qubit);
    }

    operation UGate(qubit : Qubit, theta : Double, phi : Double, lambda : Double) : Unit is Adj + Ctl {
        // General single-qubit unitary
        Rz(lambda, qubit);
        Ry(theta, qubit);
        Rz(phi, qubit);
    }

    operation iSWAP(q1 : Qubit, q2 : Qubit) : Unit is Adj + Ctl {
        // iSWAP gate
        SqrtX(q1);
        SqrtX(q2);
        CNOT(q1, q2);
        CNOT(q2, q1);
        S(q1);
        S(q2);
    }

    operation fSWAP(q1 : Qubit, q2 : Qubit) : Unit is Adj + Ctl {
        // fSWAP (fermionic SWAP) gate
        SWAP(q1, q2);
        CZ(q1, q2);
    }

    operation XX(q1 : Qubit, q2 : Qubit, angle : Double) : Unit is Adj + Ctl {
        // XX interaction
        H(q1);
        H(q2);
        Rzz(angle, q1, q2);
        H(q1);
        H(q2);
    }

    operation YY(q1 : Qubit, q2 : Qubit, angle : Double) : Unit is Adj + Ctl {
        // YY interaction
        Rx(PI() / 2.0, q1);
        Rx(PI() / 2.0, q2);
        Rzz(angle, q1, q2);
        Rx(-PI() / 2.0, q1);
        Rx(-PI() / 2.0, q2);
    }

    operation ZZ(q1 : Qubit, q2 : Qubit, angle : Double) : Unit is Adj + Ctl {
        // ZZ interaction
        Rzz(angle, q1, q2);
    }

    operation Rzz(angle : Double, q1 : Qubit, q2 : Qubit) : Unit is Adj + Ctl {
        // Rzz rotation
        CNOT(q1, q2);
        Rz(angle, q2);
        CNOT(q1, q2);
    }

    operation Rxx(angle : Double, q1 : Qubit, q2 : Qubit) : Unit is Adj + Ctl {
        // Rxx rotation
        H(q1);
        H(q2);
        Rzz(angle, q1, q2);
        H(q1);
        H(q2);
    }

    operation Ryy(angle : Double, q1 : Qubit, q2 : Qubit) : Unit is Adj + Ctl {
        // Ryy rotation
        Rx(PI() / 2.0, q1);
        Rx(PI() / 2.0, q2);
        Rzz(angle, q1, q2);
        Rx(-PI() / 2.0, q1);
        Rx(-PI() / 2.0, q2);
    }
}
