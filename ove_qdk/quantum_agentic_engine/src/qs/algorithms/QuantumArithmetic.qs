namespace QuantumAgenticEngine.Algorithms.Arithmetic {
    open Microsoft.Quantum.Canon;
    open Microsoft.Quantum.Intrinsic;
    open Microsoft.Quantum.Math;
    open Microsoft.Quantum.Convert;
    open Microsoft.Quantum.Measurement;
    open Microsoft.Quantum.Arrays;
    open Microsoft.Quantum.Arithmetic;
    open Microsoft.Quantum.Diagnostics;
    open QuantumAgenticEngine.Core;
    open QuantumAgenticEngine.Utils;

    // ========================================
    // QUANTUM ARITHMETIC OPERATIONS
    // ========================================
    // Comprehensive quantum arithmetic library
    // including adders, multipliers, and advanced operations

    // ========================================
    // QUANTUM ADDERS
    // ========================================

    operation QuantumAdder(
        a : Qubit[],
        b : Qubit[],
        sum : Qubit[]
    ) : Unit is Adj + Ctl {
        let n = Length(a);

        // Ripple-carry adder implementation
        use carry = Qubit[n];

        // Initialize first carry
        X(carry[0]);

        for i in 0..n - 1 {
            // Full adder: sum[i] = a[i] XOR b[i] XOR carry[i]
            // carry[i+1] = MAJ(a[i], b[i], carry[i])

            // Compute sum
            CNOT(a[i], sum[i]);
            CNOT(b[i], sum[i]);
            CNOT(carry[i], sum[i]);

            // Compute next carry
            if (i < n - 1) {
                MajorityGate(a[i], b[i], carry[i], carry[i + 1]);
            }
        }

        // Uncompute carries
        for i in n - 2..-1..0 {
                UncomputeMajorityGate(a[i], b[i], carry[i], carry[i + 1]);
        }

        Reset(carry[0]);
    }

    operation MajorityGate(
        a : Qubit,
        b : Qubit,
        c : Qubit,
        out : Qubit
    ) : Unit is Adj + Ctl {
        // Majority = (a AND b) OR (b AND c) OR (c AND a)
        CNOT(a, out);
        CNOT(b, out);
        CNOT(c, out);

        CCNOT(a, b, out);
        CCNOT(b, c, out);
        CCNOT(c, a, out);
    }

    operation UncomputeMajorityGate(
        a : Qubit,
        b : Qubit,
        c : Qubit,
        out : Qubit
    ) : Unit is Adj + Ctl {
        Adjoint MajorityGate(a, b, c, out);
    }

    operation QuantumAdderDraper(
        a : Qubit[],
        b : Qubit[],
        sum : Qubit[]
    ) : Unit is Adj + Ctl {
        // Draper adder using Quantum Fourier Transform
        let n = Length(a);

        // QFT on sum register
        QFT(sum);

        // Add a to sum in Fourier space
        for i in 0..n - 1 {
            for j in 0..n - i - 1 {
                Controlled R1([a[j]], (2.0 * PI() / IntAsDouble(2^(i + 1)), sum[i]));
            }
        }

        // Add b to sum in Fourier space
        for i in 0..n - 1 {
            for j in 0..n - i - 1 {
                Controlled R1([b[j]], (2.0 * PI() / IntAsDouble(2^(i + 1)), sum[i]));
            }
        }

        // Inverse QFT
        Adjoint QFT(sum);
    }

    operation QuantumAdderCDKM(
        a : Qubit[],
        b : Qubit[],
        sum : Qubit[]
    ) : Unit is Adj + Ctl {
        // Cuccaro-Draper-Kutin-Moulton adder (optimized)
        let n = Length(a);

        use ancilla = Qubit[n - 1];

        // Forward pass
        for i in 0..n - 2 {
            MAJ(a[i], b[i], ancilla[i], ancilla[i + 1]);
        }

        MAJ(a[n - 1], b[n - 1], ancilla[n - 2], sum[n - 1]);

        CNOT(ancilla[n - 2], sum[n - 2]);

        // Backward pass
        for i in n - 2..-1..1 {
            UMA(a[i], b[i], ancilla[i - 1], ancilla[i]);
            CNOT(ancilla[i - 1], sum[i - 1]);
        }

        UMA(a[0], b[0], ancilla[0], sum[0]);
    }

    operation MAJ(
        a : Qubit,
        b : Qubit,
        cIn : Qubit,
        cOut : Qubit
    ) : Unit is Adj + Ctl {
        // Majority gate for CDKM adder
        CNOT(cIn, b);
        CNOT(cIn, a);
        CCNOT(a, b, cOut);
    }

    operation UMA(
        a : Qubit,
        b : Qubit,
        cIn : Qubit,
        cOut : Qubit
    ) : Unit is Adj + Ctl {
        // Unmajority and add gate
        CCNOT(a, b, cOut);
        CNOT(cIn, a);
        CNOT(a, b);
    }

    // ========================================
    // QUANTUM MULTIPLIERS
    // ========================================

    operation QuantumMultiplier(
        a : Qubit[],
        b : Qubit[],
        product : Qubit[]
    ) : Unit is Adj + Ctl {
        let n = Length(a);
        let m = Length(b);

        // Schoolbook multiplication
        for i in 0..n - 1 {
            for j in 0..m - 1 {
                use partial = Qubit();
                CCNOT(a[i], b[j], partial);

                // Add partial product to result
                let targetIdx = i + j;
                if (targetIdx < Length(product)) {
                    CNOT(partial, product[targetIdx]);
                }

                Reset(partial);
            }
        }
    }

    operation QuantumMultiplierKaratsuba(
        a : Qubit[],
        b : Qubit[],
        product : Qubit[]
    ) : Unit is Adj + Ctl {
        let n = Length(a);

        if (n <= 4) {
            // Base case: use schoolbook multiplication
            QuantumMultiplier(a, b, product);
        } else {
            // Split numbers
            let mid = n / 2;

            use lowA = Qubit[mid];
            use highA = Qubit[n - mid];
            use lowB = Qubit[mid];
            use highB = Qubit[n - mid];

            // Copy values
            for i in 0..mid - 1 {
                CNOT(a[i], lowA[i]);
                CNOT(b[i], lowB[i]);
            }
            for i in mid..n - 1 {
                CNOT(a[i], highA[i - mid]);
                CNOT(b[i], highB[i - mid]);
            }

            // z0 = lowA * lowB
            use z0 = Qubit[2 * mid];
            QuantumMultiplierKaratsuba(lowA, lowB, z0);

            // z2 = highA * highB
            use z2 = Qubit[2 * (n - mid)];
            QuantumMultiplierKaratsuba(highA, highB, z2);

            // z1 = (lowA + highA) * (lowB + highB) - z0 - z2
            use sumA = Qubit[Max([mid, n - mid]) + 1];
            use sumB = Qubit[Max([mid, n - mid]) + 1];

            QuantumAdder(lowA, highA, sumA);
            QuantumAdder(lowB, highB, sumB);

            use z1 = Qubit[2 * (Max([mid, n - mid]) + 1)];
            QuantumMultiplierKaratsuba(sumA, sumB, z1);

            // Combine results (simplified)
            for i in 0..Length(z0) - 1 {
                CNOT(z0[i], product[i]);
            }

            ResetAll(lowA);
            ResetAll(highA);
            ResetAll(lowB);
            ResetAll(highB);
            ResetAll(z0);
            ResetAll(z2);
            ResetAll(sumA);
            ResetAll(sumB);
            ResetAll(z1);
        }
    }

    // ========================================
    // QUANTUM DIVISION
    // ========================================

    operation QuantumDivision(
        dividend : Qubit[],
        divisor : Qubit[],
        quotient : Qubit[],
        remainder : Qubit[]
    ) : Unit is Adj + Ctl {
        let n = Length(dividend);
        let m = Length(divisor);

        // Copy dividend to remainder
        for i in 0..n - 1 {
            CNOT(dividend[i], remainder[i]);
        }

        // Long division algorithm
        for i in n - m..-1..0 {
            // Compare remainder[i:i+m] with divisor
            use comparison = Qubit();
            QuantumCompare(remainder[i..i + m - 1], divisor, comparison);

            // If remainder >= divisor, subtract and set quotient bit
            Controlled QuantumSubtractor([comparison], (
                divisor,
                remainder[i..i + m - 1],
                remainder[i..i + m - 1]
            ));
            CNOT(comparison, quotient[i]);

            Reset(comparison);
        }
    }

    operation QuantumCompare(
        a : Qubit[],
        b : Qubit[],
        result : Qubit
    ) : Unit is Adj + Ctl {
        // Compare two quantum numbers
        // result = 1 if a >= b, else 0

        let n = Length(a);
        use diff = Qubit[n];

        // Compute a - b
        QuantumSubtractor(b, a, diff);

        // Check if result is negative (borrow occurred)
        // Simplified: check MSB
        CNOT(diff[n - 1], result);
        X(result); // Invert because we want a >= b

        ResetAll(diff);
    }

    operation QuantumSubtractor(
        a : Qubit[],
        b : Qubit[],
        diff : Qubit[]
    ) : Unit is Adj + Ctl {
        // Compute b - a using two's complement
        let n = Length(a);

        // Invert a
        for i in 0..n - 1 {
            X(a[i]);
        }

        // Add 1 (two's complement)
        use one = Qubit[n];
        X(one[0]);

        // b + (~a) + 1
        QuantumAdder(b, a, diff);
        QuantumAdder(diff, one, diff);

        // Restore a
        for i in 0..n - 1 {
            X(a[i]);
        }

        ResetAll(one);
    }

    // ========================================
    // MODULAR ARITHMETIC
    // ========================================

    operation ModularAdder(
        a : Qubit[],
        b : Qubit[],
        modulus : Int,
        result : Qubit[]
    ) : Unit is Adj + Ctl {
        let n = Length(a);

        // Compute a + b
        use sum = Qubit[n + 1];
        QuantumAdder(a, b, sum[0..n - 1]);

        // Check if sum >= modulus
        use comparison = Qubit();
        let modulusQubits = IntToQubitArray(modulus, n + 1);
        QuantumCompare(sum, modulusQubits, comparison);

        // If sum >= modulus, subtract modulus
        Controlled ModularSubtract([comparison], (sum, modulus, sum));

        // Copy result
        for i in 0..n - 1 {
            CNOT(sum[i], result[i]);
        }

        ResetAll(sum);
        Reset(comparison);
        ResetAll(modulusQubits);
    }

    operation ModularSubtract(
        a : Qubit[],
        b : Int,
        result : Qubit[]
    ) : Unit is Adj + Ctl {
        let n = Length(a);
        let bQubits = IntToQubitArray(b, n);

        QuantumSubtractor(bQubits, a, result);

        ResetAll(bQubits);
    }

    operation ModularMultiplier(
        a : Qubit[],
        b : Qubit[],
        modulus : Int,
        result : Qubit[]
    ) : Unit is Adj + Ctl {
        let n = Length(a);

        // Compute a * b
        use product = Qubit[2 * n];
        QuantumMultiplier(a, b, product);

        // Compute product mod modulus
        ModularReduction(product, modulus, result);

        ResetAll(product);
    }

    operation ModularReduction(
        value : Qubit[],
        modulus : Int,
        result : Qubit[]
    ) : Unit is Adj + Ctl {
        let n = Length(result);
        let modulusBits = IntToQubitArray(modulus, n);

        // Repeated subtraction (simplified Barrett reduction)
        use temp = Qubit[n];

        for i in 0..n - 1 {
            CNOT(value[i], temp[i]);
        }

        // Subtract modulus while temp >= modulus
        for _ in 0..2^n - 1 {
            use comparison = Qubit();
            QuantumCompare(temp, modulusBits, comparison);

            Controlled ModularSubtract([comparison], (temp, modulus, temp));

            Reset(comparison);
        }

        // Copy result
        for i in 0..n - 1 {
            CNOT(temp[i], result[i]);
        }

        ResetAll(temp);
        ResetAll(modulusBits);
    }

    operation ModularExponentiation(
        base : Qubit[],
        exponent : Qubit[],
        modulus : Int,
        result : Qubit[]
    ) : Unit is Adj + Ctl {
        let n = Length(exponent);

        // Initialize result to 1
        X(result[0]);

        // Square-and-multiply algorithm
        for i in n - 1..-1..0 {
            // Square result
            use squared = Qubit[2 * Length(result)];
            ModularMultiplier(result, result, modulus, squared[0..Length(result) - 1]);

            for j in 0..Length(result) - 1 {
                CNOT(squared[j], result[j]);
            }

            // Multiply by base if exponent bit is 1
            use product = Qubit[2 * Length(result)];
            Controlled ModularMultiplier([exponent[i]], (
                result, base, modulus, product[0..Length(result) - 1]
            ));

            for j in 0..Length(result) - 1 {
                Controlled CNOT([exponent[i]], (product[j], result[j]));
            }

            ResetAll(squared);
            ResetAll(product);
        }
    }

    // ========================================
    // UTILITY FUNCTIONS
    // ========================================

    function IntToQubitArray(value : Int, numBits : Int) : Qubit[] {
        // This is a placeholder - in actual Q#, you'd prepare this state
        // For now, return an empty array as a marker
        return new Qubit[0];
    }

    operation PrepareIntState(value : Int, qubits : Qubit[]) : Unit is Adj + Ctl {
        let binary = IntToBinary(value, Length(qubits));

        for i in 0..Length(qubits) - 1 {
            if (binary[i] == 1) {
                X(qubits[i]);
            }
        }
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

    // ========================================
    // QUANTUM COMPARATORS
    // ========================================

    operation QuantumComparator(
        a : Qubit[],
        b : Qubit[],
        gt : Qubit,  // a > b
        eq : Qubit,  // a == b
        lt : Qubit   // a < b
    ) : Unit is Adj + Ctl {
        let n = Length(a);

        use diff = Qubit[n];

        // Compute a - b
        QuantumSubtractor(b, a, diff);

        // Check sign (MSB)
        CNOT(diff[n - 1], lt);

        // Check if all bits are zero (equality)
        use allZero = Qubit();
        X(allZero);
        for i in 0..n - 1 {
            Controlled X([diff[i]], allZero);
        }
        CNOT(allZero, eq);

        // gt = NOT (lt OR eq)
        use notLt = Qubit();
        X(notLt);
        CNOT(lt, notLt);

        use notEq = Qubit();
        X(notEq);
        CNOT(eq, notEq);

        CCNOT(notLt, notEq, gt);

        ResetAll(diff);
        Reset(allZero);
        Reset(notLt);
        Reset(notEq);
    }

    // ========================================
    // QUANTUM COUNTERS
    // ========================================

    operation QuantumCounter(
        controls : Qubit[],
        counter : Qubit[]
    ) : Unit is Adj + Ctl {
        // Increment counter for each control qubit in |1> state
        for control in controls {
            Controlled Increment([control], counter);
        }
    }

    operation Increment(counter : Qubit[]) : Unit is Adj + Ctl {
        // Increment a quantum counter
        let n = Length(counter);

        use carry = Qubit[n];
        X(carry[0]);

        for i in 0..n - 1 {
            // Half adder
            CNOT(carry[i], counter[i]);

            if (i < n - 1) {
                CCNOT(carry[i], counter[i], carry[i + 1]);
            }
        }

        Reset(carry[0]);
    }

    operation Decrement(counter : Qubit[]) : Unit is Adj + Ctl {
        // Decrement a quantum counter
        Adjoint Increment(counter);
    }

    // ========================================
    // QUANTUM ACCUMULATORS
    // ========================================

    operation QuantumAccumulator(
        inputs : Qubit[][],
        accumulator : Qubit[]
    ) : Unit is Adj + Ctl {
        // Sum all input arrays into accumulator
        for input in inputs {
            use sum = Qubit[Length(accumulator)];
            QuantumAdder(accumulator, input, sum);

            for i in 0..Length(accumulator) - 1 {
                CNOT(sum[i], accumulator[i]);
            }

            ResetAll(sum);
        }
    }

    // ========================================
    // FIXED-POINT ARITHMETIC
    // ========================================

    operation FixedPointAdder(
        a : Qubit[],
        b : Qubit[],
        sum : Qubit[],
        fractionalBits : Int
    ) : Unit is Adj + Ctl {
        // Fixed-point addition (integer + fractional parts)
        QuantumAdder(a, b, sum);

        // Handle overflow in fractional part
        // (simplified - just propagate carries)
    }

    operation FixedPointMultiplier(
        a : Qubit[],
        b : Qubit[],
        product : Qubit[],
        fractionalBits : Int
    ) : Unit is Adj + Ctl {
        let n = Length(a);

        use fullProduct = Qubit[2 * n];
        QuantumMultiplier(a, b, fullProduct);

        // Scale result by 2^(-fractionalBits)
        // Keep middle bits for result
        let startIdx = fractionalBits;
        let endIdx = startIdx + Length(product);

        for i in startIdx..Min([endIdx - 1, 2 * n - 1]) {
            if (i - startIdx < Length(product)) {
                CNOT(fullProduct[i], product[i - startIdx]);
            }
        }

        ResetAll(fullProduct);
    }

    // ========================================
    // QUANTUM AVERAGE AND STATISTICS
    // ========================================

    operation QuantumAverage(
        values : Qubit[][],
        average : Qubit[]
    ) : Unit is Adj + Ctl {
        let numValues = Length(values);
        let numBits = Length(values[0]);

        // Sum all values
        use sum = Qubit[numBits + Ceiling(Lg(IntAsDouble(numValues))));

        for value in values {
            use tempSum = Qubit[Length(sum)];
            QuantumAdder(sum[0..numBits - 1], value, tempSum);

            for i in 0..Length(sum) - 1 {
                CNOT(tempSum[i], sum[i]);
            }

            ResetAll(tempSum);
        }

        // Divide by numValues (shift right)
        let shift = Ceiling(Lg(IntAsDouble(numValues)));
        for i in 0..Length(average) - 1 {
            if (i + shift < Length(sum)) {
                CNOT(sum[i + shift], average[i]);
            }
        }

        ResetAll(sum);
    }

    operation QuantumSumOfSquares(
        values : Qubit[][],
        result : Qubit[]
    ) : Unit is Adj + Ctl {
        // Compute sum of squares
        for value in values {
            use square = Qubit[2 * Length(value)];
            QuantumMultiplier(value, value, square);

            use tempSum = Qubit[Length(result)];
            QuantumAdder(result, square[0..Length(result) - 1], tempSum);

            for i in 0..Length(result) - 1 {
                CNOT(tempSum[i], result[i]);
            }

            ResetAll(square);
            ResetAll(tempSum);
        }
    }

    // ========================================
    // ADVANCED ARITHMETIC OPERATIONS
    // ========================================

    operation QuantumSquareRoot(
        value : Qubit[],
        result : Qubit[]
    ) : Unit is Adj + Ctl {
        // Newton-Raphson method for square root
        let n = Length(value);

        // Initial guess
        use guess = Qubit[n];
        for i in n / 2..n - 1 {
            X(guess[i - n / 2]);
        }

        // Iterate Newton's method
        for _ in 0..5 {
            use nextGuess = Qubit[n];

            // next = (guess + value/guess) / 2
            use quotient = Qubit[n];
            use sum = Qubit[n + 1];

            // Simplified: just average
            QuantumAdder(guess, value, sum);

            // Divide by 2 (shift right)
            for i in 0..n - 1 {
                CNOT(sum[i + 1], nextGuess[i]);
            }

            // Update guess
            for i in 0..n - 1 {
                CNOT(nextGuess[i], guess[i]);
            }

            ResetAll(nextGuess);
            ResetAll(quotient);
            ResetAll(sum);
        }

        // Copy result
        for i in 0..Length(result) - 1 {
            CNOT(guess[i], result[i]);
        }

        ResetAll(guess);
    }

    operation QuantumLogarithm(
        value : Qubit[],
        result : Qubit[],
        base : Double
    ) : Unit is Adj + Ctl {
        // CORDIC-like algorithm for logarithm
        let n = Length(value);

        // Find position of leading 1 (characteristic)
        use characteristic = Qubit[n];

        for i in 0..n - 1 {
            CNOT(value[i], characteristic[i]);
        }

        // Compute mantissa logarithm using series expansion
        // ln(1 + x) ≈ x - x^2/2 + x^3/3 - ...

        use logResult = Qubit[Length(result)];

        // Simplified: use lookup table or polynomial approximation
        for i in 0..Length(result) - 1 {
            // Placeholder for actual computation
            CNOT(characteristic[i], logResult[i]);
        }

        // Copy result
        for i in 0..Length(result) - 1 {
            CNOT(logResult[i], result[i]);
        }

        ResetAll(characteristic);
        ResetAll(logResult);
    }

    operation QuantumExponential(
        exponent : Qubit[],
        result : Qubit[],
        base : Double
    ) : Unit is Adj + Ctl {
        // CORDIC-like algorithm for exponential
        let n = Length(exponent);

        // Split into integer and fractional parts
        let intBits = n / 2;
        let fracBits = n - intBits;

        use intPart = Qubit[intBits];
        use fracPart = Qubit[fracBits];

        for i in 0..intBits - 1 {
            CNOT(exponent[i], intPart[i]);
        }
        for i in 0..fracBits - 1 {
            CNOT(exponent[intBits + i], fracPart[i]);
        }

        // Compute e^integer part (repeated squaring)
        use intResult = Qubit[Length(result)];
        X(intResult[0]);

        for i in 0..intBits - 1 {
            use squared = Qubit[2 * Length(intResult)];
            QuantumMultiplier(intResult, intResult, squared);

            Controlled Swap([intPart[i]], (squared[0..Length(intResult) - 1], intResult));

            ResetAll(squared);
        }

        // Compute e^fractional part (series or CORDIC)
        use fracResult = Qubit[Length(result)];
        X(fracResult[0]);

        // Taylor series: e^x ≈ 1 + x + x^2/2! + x^3/3! + ...
        for term in 1..4 {
            use termResult = Qubit[Length(result)];
            // Compute x^term / term!
            // Simplified implementation
            ResetAll(termResult);
        }

        // Multiply results
        use finalResult = Qubit[2 * Length(result)];
        QuantumMultiplier(intResult, fracResult, finalResult);

        for i in 0..Length(result) - 1 {
            CNOT(finalResult[i], result[i]);
        }

        ResetAll(intPart);
        ResetAll(fracPart);
        ResetAll(intResult);
        ResetAll(fracResult);
        ResetAll(finalResult);
    }

    // ========================================
    // MATRIX OPERATIONS
    // ========================================

    operation QuantumMatrixVectorProduct(
        matrix : Qubit[][],
        vector : Qubit[],
        result : Qubit[]
    ) : Unit is Adj + Ctl {
        let n = Length(vector);

        for i in 0..n - 1 {
            use rowProduct = Qubit[Length(result)];

            // Compute dot product of row i with vector
            for j in 0..n - 1 {
                use product = Qubit[Length(result)];
                // Simplified: assume matrix elements are encoded
                // In practice, would use controlled operations

                Controlled CNOT([vector[j]], (matrix[i][j], product[0]));

                use tempSum = Qubit[Length(result)];
                QuantumAdder(rowProduct, product, tempSum);

                for k in 0..Length(result) - 1 {
                    CNOT(tempSum[k], rowProduct[k]);
                }

                ResetAll(product);
                ResetAll(tempSum);
            }

            CNOT(rowProduct[0], result[i]);
            ResetAll(rowProduct);
        }
    }

    operation QuantumMatrixMultiplication(
        a : Qubit[][],
        b : Qubit[][],
        result : Qubit[][]
    ) : Unit is Adj + Ctl {
        let n = Length(a);

        for i in 0..n - 1 {
            for j in 0..n - 1 {
                use sum = Qubit[Length(result[i][j])];

                for k in 0..n - 1 {
                    use product = Qubit[2 * Length(a[i][k])];
                    QuantumMultiplier([a[i][k]], [b[k][j]], product);

                    use tempSum = Qubit[Length(sum)];
                    QuantumAdder(sum, product[0..Length(sum) - 1], tempSum);

                    for idx in 0..Length(sum) - 1 {
                        CNOT(tempSum[idx], sum[idx]);
                    }

                    ResetAll(product);
                    ResetAll(tempSum);
                }

                CNOT(sum[0], result[i][j]);
                ResetAll(sum);
            }
        }
    }

    // ========================================
    // POLYNOMIAL EVALUATION
    // ========================================

    operation QuantumPolynomialEvaluation(
        x : Qubit[],
        coefficients : Double[],
        result : Qubit[]
    ) : Unit is Adj + Ctl {
        let degree = Length(coefficients) - 1;

        // Horner's method: P(x) = a_0 + x(a_1 + x(a_2 + ...))
        use accumulator = Qubit[Length(result)];

        // Initialize with highest coefficient
        PrepareFixedPoint(coefficients[degree], accumulator);

        for i in degree - 1..-1..0 {
            // accumulator = accumulator * x + coefficients[i]
            use product = Qubit[2 * Length(accumulator)];
            QuantumMultiplier(accumulator, x, product);

            use coeffQubits = Qubit[Length(accumulator)];
            PrepareFixedPoint(coefficients[i], coeffQubits);

            use newAccumulator = Qubit[Length(accumulator)];
            QuantumAdder(product[0..Length(accumulator) - 1], coeffQubits, newAccumulator);

            for j in 0..Length(accumulator) - 1 {
                CNOT(newAccumulator[j], accumulator[j]);
            }

            ResetAll(product);
            ResetAll(coeffQubits);
            ResetAll(newAccumulator);
        }

        // Copy result
        for i in 0..Length(result) - 1 {
            CNOT(accumulator[i], result[i]);
        }

        ResetAll(accumulator);
    }

    operation PrepareFixedPoint(value : Double, qubits : Qubit[]) : Unit is Adj + Ctl {
        // Prepare a fixed-point representation of a classical value
        let scaled = Truncate(value * IntAsDouble(2^(Length(qubits) / 2)));
        PrepareIntState(scaled, qubits);
    }

    // ========================================
    // INTERPOLATION
    // ========================================

    operation QuantumLinearInterpolation(
        x0 : Qubit[],
        x1 : Qubit[],
        t : Qubit[],  // Interpolation parameter [0, 1]
        result : Qubit[]
    ) : Unit is Adj + Ctl {
        // result = x0 + t * (x1 - x0)

        use diff = Qubit[Length(x0)];
        QuantumSubtractor(x0, x1, diff);

        use product = Qubit[2 * Length(diff)];
        QuantumMultiplier(diff, t, product);

        QuantumAdder(x0, product[0..Length(result) - 1], result);

        ResetAll(diff);
        ResetAll(product);
    }

    // ========================================
    // SORTING NETWORKS
    // ========================================

    operation QuantumCompareSwap(
        a : Qubit[],
        b : Qubit[]
    ) : Unit is Adj + Ctl {
        // Compare and swap if a > b
        use comparison = Qubit();
        QuantumCompare(a, b, comparison);

        // Swap if comparison is true (a < b means b > a, so swap)
        X(comparison);

        for i in 0..Length(a) - 1 {
            Controlled SWAP([comparison], (a[i], b[i]));
        }

        Reset(comparison);
    }

    operation QuantumBitonicSort(
        values : Qubit[][]
    ) : Unit is Adj + Ctl {
        let n = Length(values);

        // Bitonic sort algorithm
        for k in 2..2..n {
            for j in k / 2..-1..1 {
                for i in 0..n - 1 {
                    let l = i ^ j;
                    if (l > i) {
                        if ((i & k) == 0) {
                            // Compare and swap in ascending order
                            QuantumCompareSwap(values[i], values[l]);
                        } else {
                            // Compare and swap in descending order
                            QuantumCompareSwap(values[l], values[i]);
                        }
                    }
                }
            }
        }
    }

    // ========================================
    // MIN/MAX OPERATIONS
    // ========================================

    operation QuantumMinimum(
        values : Qubit[][],
        minValue : Qubit[]
    ) : Unit is Adj + Ctl {
        // Tournament-style minimum finding
        mutable currentMin = values[0];

        for i in 1..Length(values) - 1 {
            use comparison = Qubit();
            QuantumCompare(currentMin, values[i], comparison);

            // If currentMin > values[i], update
            X(comparison);

            for j in 0..Length(minValue) - 1 {
                Controlled CNOT([comparison], (values[i][j], currentMin[j]));
            }

            Reset(comparison);
        }

        // Copy to output
        for i in 0..Length(minValue) - 1 {
            CNOT(currentMin[i], minValue[i]);
        }
    }

    operation QuantumMaximum(
        values : Qubit[][],
        maxValue : Qubit[]
    ) : Unit is Adj + Ctl {
        // Tournament-style maximum finding
        mutable currentMax = values[0];

        for i in 1..Length(values) - 1 {
            use comparison = Qubit();
            QuantumCompare(values[i], currentMax, comparison);

            // If values[i] > currentMax, update
            X(comparison);

            for j in 0..Length(maxValue) - 1 {
                Controlled CNOT([comparison], (values[i][j], currentMax[j]));
            }

            Reset(comparison);
        }

        for i in 0..Length(maxValue) - 1 {
            CNOT(currentMax[i], maxValue[i]);
        }
    }

    // ========================================
    // HAMMING WEIGHT
    // ========================================

    operation QuantumHammingWeight(
        input : Qubit[],
        weight : Qubit[]
    ) : Unit is Adj + Ctl {
        // Count number of 1s in input
        for q in input {
            Controlled Increment([q], weight);
        }
    }

    // ========================================
    // PARITY COMPUTATION
    // ========================================

    operation QuantumParity(
        input : Qubit[],
        parity : Qubit
    ) : Unit is Adj + Ctl {
        // Compute XOR of all input bits
        for q in input {
            CNOT(q, parity);
        }
    }

    // ========================================
    // PRIORITY ENCODER
    // ========================================

    operation QuantumPriorityEncoder(
        input : Qubit[],
        output : Qubit[]
    ) : Unit is Adj + Ctl {
        // Find position of highest-priority (leftmost) 1
        let n = Length(input);
        let outputBits = Ceiling(Lg(IntAsDouble(n)));

        // Use divide-and-conquer approach
        use found = Qubit();

        for i in 0..n - 1 {
            use isOne = Qubit();
            CNOT(input[i], isOne);

            // If not already found and this bit is 1, set output
            use notFound = Qubit();
            X(notFound);
            CNOT(found, notFound);

            use shouldSet = Qubit();
            CCNOT(notFound, isOne, shouldSet);

            // Set output bits to represent index i
            let binary = IntToBinary(i, outputBits);
            for j in 0..outputBits - 1 {
                if (binary[j] == 1) {
                    Controlled X([shouldSet], output[j]);
                }
            }

            // Mark as found
            CCNOT(notFound, isOne, found);

            Reset(isOne);
            Reset(notFound);
            Reset(shouldSet);
        }

        Reset(found);
    }

    // ========================================
    // BARREL SHIFTER
    // ========================================

    operation QuantumBarrelShifter(
        input : Qubit[],
        shiftAmount : Qubit[],
        direction : Qubit,  // 0 = left, 1 = right
        output : Qubit[]
    ) : Unit is Adj + Ctl {
        // Shift input by shiftAmount in specified direction
        let n = Length(input);
        let shiftBits = Ceiling(Lg(IntAsDouble(n)));

        // Copy input to output
        for i in 0..n - 1 {
            CNOT(input[i], output[i]);
        }

        // Apply shifts for each bit of shiftAmount
        for bit in 0..shiftBits - 1 {
            let shiftSize = 2^bit;

            for i in 0..n - 1 {
                use shouldShift = Qubit();
                CNOT(shiftAmount[bit], shouldShift);

                // Left shift
                let leftTarget = (i + shiftSize) % n;
                use notDirection = Qubit();
                X(notDirection);
                CNOT(direction, notDirection);

                use doLeft = Qubit();
                CCNOT(shouldShift, notDirection, doLeft);
                Controlled SWAP([doLeft], (output[i], output[leftTarget]));

                // Right shift
                let rightTarget = (i - shiftSize + n) % n;
                use doRight = Qubit();
                CCNOT(shouldShift, direction, doRight);
                Controlled SWAP([doRight], (output[i], output[rightTarget]));

                Reset(shouldShift);
                Reset(notDirection);
                Reset(doLeft);
                Reset(doRight);
            }
        }
    }

    // ========================================
    // SATURATING ARITHMETIC
    // ========================================

    operation SaturatingAdder(
        a : Qubit[],
        b : Qubit[],
        result : Qubit[],
        maxValue : Int
    ) : Unit is Adj + Ctl {
        use sum = Qubit[Length(result) + 1];
        QuantumAdder(a, b, sum[0..Length(result) - 1]);

        // Check for overflow
        use overflow = Qubit();
        CNOT(sum[Length(result)], overflow);

        // Check if sum > maxValue
        let maxQubits = IntToQubitArray(maxValue, Length(result));
        use exceedsMax = Qubit();
        QuantumCompare(sum[0..Length(result) - 1], maxQubits, exceedsMax);

        // Saturate if overflow or exceeds max
        use shouldSaturate = Qubit();
        X(shouldSaturate);
        CNOT(overflow, shouldSaturate);
        CNOT(exceedsMax, shouldSaturate);

        // Set to maxValue if saturating
        for i in 0..Length(result) - 1 {
            Controlled X([shouldSaturate], result[i]);
            if (maxQubits[i] == Zero) {
                Controlled X([shouldSaturate], result[i]);
            }
        }

        // Otherwise use normal sum
        use notSaturate = Qubit();
        X(notSaturate);
        CNOT(shouldSaturate, notSaturate);

        for i in 0..Length(result) - 1 {
            Controlled CNOT([notSaturate], (sum[i], result[i]));
        }

        ResetAll(sum);
        Reset(overflow);
        Reset(exceedsMax);
        Reset(shouldSaturate);
        Reset(notSaturate);
        ResetAll(maxQubits);
    }

    // ========================================
    // CLIPPING OPERATIONS
    // ========================================

    operation QuantumClip(
        value : Qubit[],
        minVal : Int,
        maxVal : Int,
        result : Qubit[]
    ) : Unit is Adj + Ctl {
        let minQubits = IntToQubitArray(minVal, Length(result));
        let maxQubits = IntToQubitArray(maxVal, Length(result));

        // Check if value < minVal
        use belowMin = Qubit();
        QuantumCompare(value, minQubits, belowMin);

        // Check if value > maxVal
        use aboveMax = Qubit();
        QuantumCompare(maxQubits, value, aboveMax);

        // Clip to minVal if below
        for i in 0..Length(result) - 1 {
            Controlled X([belowMin], result[i]);
            if (minQubits[i] == Zero) {
                Controlled X([belowMin], result[i]);
            }
        }

        // Clip to maxVal if above
        for i in 0..Length(result) - 1 {
            Controlled X([aboveMax], result[i]);
            if (maxQubits[i] == Zero) {
                Controlled X([aboveMax], result[i]);
            }
        }

        // Otherwise copy value
        use inRange = Qubit();
        X(inRange);
        CNOT(belowMin, inRange);
        CNOT(aboveMax, inRange);

        for i in 0..Length(result) - 1 {
            Controlled CNOT([inRange], (value[i], result[i]));
        }

        Reset(belowMin);
        Reset(aboveMax);
        Reset(inRange);
        ResetAll(minQubits);
        ResetAll(maxQubits);
    }
}
