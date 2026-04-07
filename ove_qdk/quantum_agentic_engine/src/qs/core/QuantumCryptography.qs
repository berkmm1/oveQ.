namespace QuantumAgentic.Cryptography {
    open Microsoft.Quantum.Canon;
    open Microsoft.Quantum.Intrinsic;
    open Microsoft.Quantum.Measurement;
    open Microsoft.Quantum.Arrays;
    open Microsoft.Quantum.Math;
    open Microsoft.Quantum.Convert;
    open Microsoft.Quantum.Random;
    open Microsoft.Quantum.Diagnostics;

    // ============================================
    // QUANTUM CRYPTOGRAPHY PROTOCOLS
    // ============================================

    /// # Summary
    /// BB84 Quantum Key Distribution
    operation BB84KeyDistribution(
        aliceQubits : Qubit[],
        bobQubits : Qubit[],
        eveQubits : Qubit[],
        keyLength : Int,
        eavesdropperPresent : Bool
    ) : (Bool[], Bool[], Double) {
        mutable aliceKey = [];
        mutable bobKey = [];
        mutable errorRate = 0.0;

        // Alice prepares qubits
        for i in 0..keyLength - 1 {
            // Random bit
            let bit = DrawRandomBool(0.5) ? 1 | 0;

            // Random basis (0 = Z, 1 = X)
            let basis = DrawRandomBool(0.5) ? 1 | 0;

            // Prepare qubit
            if bit == 1 {
                X(aliceQubits[i]);
            }
            if basis == 1 {
                H(aliceQubits[i]);
            }

            // Send to Bob (potentially through Eve)
            if eavesdropperPresent and i < Length(eveQubits) {
                // Eve intercepts
                let eveBasis = DrawRandomBool(0.5) ? 1 | 0;
                if eveBasis == 1 {
                    H(eveQubits[i]);
                }
                let eveResult = M(eveQubits[i]);

                // Eve resends
                if eveResult == One {
                    X(aliceQubits[i]);
                }
                if eveBasis == 1 {
                    H(aliceQubits[i]);
                }
            }

            // Bob receives and measures
            let bobBasis = DrawRandomBool(0.5) ? 1 | 0;
            if bobBasis == 1 {
                H(bobQubits[i]);
            }
            let bobResult = M(bobQubits[i]);

            // Sift key (keep only matching bases)
            if basis == bobBasis {
                set aliceKey += [bit == 1];
                set bobKey += [bobResult == One];
            }
        }

        // Estimate error rate
        mutable errors = 0;
        for i in 0..MinI(Length(aliceKey), Length(bobKey)) - 1 {
            if aliceKey[i] != bobKey[i] {
                set errors += 1;
            }
        }
        set errorRate = IntAsDouble(errors) / IntAsDouble(Length(aliceKey));

        return (aliceKey, bobKey, errorRate);
    }

    /// # Summary
    /// E91 Entanglement-based QKD
    operation E91EntanglementQKD(
        entangledPairs : Qubit[][],
        aliceBases : Int[],
        bobBases : Int[],
        keyLength : Int
    ) : (Bool[], Bool[], Double) {
        mutable aliceKey = [];
        mutable bobKey = [];
        mutable bellViolations = 0;

        for i in 0..keyLength - 1 {
            // Create Bell pair
            H(entangledPairs[i][0]);
            CNOT(entangledPairs[i][0], entangledPairs[i][1]);

            // Alice measures
            if aliceBases[i] == 1 {
                H(entangledPairs[i][0]);
            } else if aliceBases[i] == 2 {
                Ry(PI() / 4.0, entangledPairs[i][0]);
            }
            let aliceResult = M(entangledPairs[i][0]);

            // Bob measures
            if bobBases[i] == 1 {
                H(entangledPairs[i][1]);
            } else if bobBases[i] == 2 {
                Ry(-PI() / 4.0, entangledPairs[i][1]);
            }
            let bobResult = M(entangledPairs[i][1]);

            // Check Bell inequality violations
            if aliceBases[i] == 2 and bobBases[i] == 2 {
                if aliceResult != bobResult {
                    set bellViolations += 1;
                }
            }

            // Sift key (matching bases)
            if aliceBases[i] == bobBases[i] {
                set aliceKey += [aliceResult == One];
                set bobKey += [bobResult == One];
            }
        }

        // Calculate CHSH violation
        let violation = IntAsDouble(bellViolations) / IntAsDouble(keyLength);

        return (aliceKey, bobKey, violation);
    }

    /// # Summary
    /// Quantum Secret Sharing (3-party)
    operation QuantumSecretSharing(
        secretQubit : Qubit,
        share1 : Qubit,
        share2 : Qubit,
        share3 : Qubit
    ) : Unit {
        // Encode secret into GHZ state
        H(secretQubit);
        CNOT(secretQubit, share1);
        CNOT(secretQubit, share2);
        CNOT(secretQubit, share3);

        // Distribute shares
        // Any 2 out of 3 can reconstruct
    }

    /// # Summary
    /// Reconstruct secret from shares
    operation ReconstructSecret(
        shareA : Qubit,
        shareB : Qubit,
        reconstructedQubit : Qubit
    ) : Unit {
        // Combine two shares
        CNOT(shareA, reconstructedQubit);
        CNOT(shareB, reconstructedQubit);

        // Apply correction
        H(reconstructedQubit);
    }

    /// # Summary
    /// Quantum Digital Signature
    operation QuantumDigitalSignature(
        messageQubits : Qubit[],
        privateKeyQubits : Qubit[],
        signatureQubits : Qubit[]
    ) : Unit {
        // Create signature using private key
        for i in 0..MinI(Length(messageQubits), Length(privateKeyQubits)) - 1 {
            // Entangle message with private key
            CNOT(messageQubits[i], privateKeyQubits[i]);
            CNOT(privateKeyQubits[i], signatureQubits[i]);
        }
    }

    /// # Summary
    /// Verify quantum signature
    operation VerifyQuantumSignature(
        messageQubits : Qubit[],
        signatureQubits : Qubit[],
        publicKeyQubits : Qubit[],
        resultQubit : Qubit
    ) : Bool {
        // Verify signature against public key
        for i in 0..MinI(Length(messageQubits), Length(publicKeyQubits)) - 1 {
            CNOT(messageQubits[i], resultQubit);
            CNOT(signatureQubits[i], resultQubit);
            CNOT(publicKeyQubits[i], resultQubit);
        }

        let result = M(resultQubit);
        return result == Zero;  // Zero means valid
    }

    /// # Summary
    /// Quantum Commitment Protocol
    operation QuantumBitCommitment(
        commitQubit : Qubit,
        commitBit : Bool,
        randomBit : Bool
    ) : Unit {
        // Commit phase
        if commitBit {
            X(commitQubit);
        }
        if randomBit {
            H(commitQubit);
        }

        // Qubit is now committed
    }

    /// # Summary
    /// Reveal commitment
    operation RevealCommitment(
        commitQubit : Qubit,
        commitBit : Bool,
        randomBit : Bool
    ) : Bool {
        // Reveal phase
        if randomBit {
            H(commitQubit);
        }

        let result = M(commitQubit);
        let revealedBit = result == One;

        // Verify
        return revealedBit == commitBit;
    }

    /// # Summary
    /// Quantum Coin Flipping
    operation QuantumCoinFlipping(
        aliceQubit : Qubit,
        bobQubit : Qubit,
        resultQubit : Qubit
    ) : Bool {
        // Alice prepares
        H(aliceQubit);
        let aliceBit = M(aliceQubit);

        // Bob prepares
        H(bobQubit);
        let bobBit = M(bobQubit);

        // XOR for result
        if aliceBit == One {
            X(resultQubit);
        }
        if bobBit == One {
            X(resultQubit);
        }

        let result = M(resultQubit);
        return result == One;
    }

    /// # Summary
    /// Quantum Oblivious Transfer
    operation QuantumObliviousTransfer(
        message0 : Qubit[],
        message1 : Qubit[],
        choiceQubit : Qubit,
        receivedMessage : Qubit[]
    ) : Unit {
        // Sender has two messages
        // Receiver chooses which to receive without sender knowing

        let choice = M(choiceQubit);

        // Transfer chosen message
        if choice == Zero {
            for i in 0..MinI(Length(message0), Length(receivedMessage)) - 1 {
                CNOT(message0[i], receivedMessage[i]);
            }
        } else {
            for i in 0..MinI(Length(message1), Length(receivedMessage)) - 1 {
                CNOT(message1[i], receivedMessage[i]);
            }
        }
    }

    /// # Summary
    /// Quantum Secure Multi-Party Computation
    operation QuantumSecureMPC(
        inputQubits : Qubit[],
        computationQubits : Qubit[],
        outputQubits : Qubit[],
        numParties : Int
    ) : Unit {
        // Encode inputs
        ApplyToEach(H, computationQubits);

        for i in 0..MinI(Length(inputQubits), Length(computationQubits)) - 1 {
            CNOT(inputQubits[i], computationQubits[i]);
        }

        // Perform secure computation (simplified sum)
        for i in 0..Length(computationQubits) - 2 {
            CNOT(computationQubits[i], computationQubits[i + 1]);
        }

        // Output
        for i in 0..MinI(Length(computationQubits), Length(outputQubits)) - 1 {
            CNOT(computationQubits[i], outputQubits[i]);
        }
    }

    /// # Summary
    /// Quantum Random Number Generation
    operation QuantumRandomNumberGenerator(
        outputQubits : Qubit[],
        numBits : Int
    ) : Int {
        mutable result = 0;

        for i in 0..MinI(numBits, Length(outputQubits)) - 1 {
            // Create superposition
            H(outputQubits[i]);

            // Measure
            let bit = M(outputQubits[i]);
            if bit == One {
                set result += 1 <<< i;
            }
        }

        return result;
    }

    /// # Summary
    /// Quantum One-Time Pad Encryption
    operation QuantumOneTimePadEncrypt(
        messageQubits : Qubit[],
        keyQubits : Qubit[],
        ciphertextQubits : Qubit[]
    ) : Unit {
        // XOR message with key
        for i in 0..MinI(Length(messageQubits), Length(keyQubits)) - 1 {
            CNOT(messageQubits[i], ciphertextQubits[i]);
            CNOT(keyQubits[i], ciphertextQubits[i]);
        }
    }

    /// # Summary
    /// Quantum One-Time Pad Decryption
    operation QuantumOneTimePadDecrypt(
        ciphertextQubits : Qubit[],
        keyQubits : Qubit[],
        messageQubits : Qubit[]
    ) : Unit {
        // XOR ciphertext with key (same as encryption)
        for i in 0..MinI(Length(ciphertextQubits), Length(keyQubits)) - 1 {
            CNOT(ciphertextQubits[i], messageQubits[i]);
            CNOT(keyQubits[i], messageQubits[i]);
        }
    }

    /// # Summary
    /// Quantum Authentication
    operation QuantumAuthentication(
        messageQubits : Qubit[],
        authKeyQubits : Qubit[],
        tagQubits : Qubit[]
    ) : Unit {
        // Create authentication tag
        for i in 0..MinI(Length(messageQubits), Length(authKeyQubits)) - 1 {
            // Controlled operation based on key
            Controlled X([authKeyQubits[i]], messageQubits[i]);
            CNOT(messageQubits[i], tagQubits[i % Length(tagQubits)]);
        }
    }

    /// # Summary
    /// Verify quantum authentication
    operation VerifyQuantumAuthentication(
        messageQubits : Qubit[],
        authKeyQubits : Qubit[],
        tagQubits : Qubit[],
        resultQubit : Qubit
    ) : Bool {
        // Recompute tag
        use computedTag = Qubit[Length(tagQubits)];

        QuantumAuthentication(messageQubits, authKeyQubits, computedTag);

        // Compare tags
        for i in 0..MinI(Length(tagQubits), Length(computedTag)) - 1 {
            CNOT(tagQubits[i], computedTag[i]);
            CNOT(computedTag[i], resultQubit);
        }

        let result = M(resultQubit);

        ResetAll(computedTag);

        return result == Zero;
    }

    /// # Summary
    /// Quantum Key Recycling
    operation QuantumKeyRecycling(
        usedKeyQubits : Qubit[],
        recycledKeyQubits : Qubit[],
        errorRate : Double
    ) : Unit {
        // Privacy amplification
        let threshold = 0.11;  // BB84 threshold

        if errorRate < threshold {
            // Key can be recycled
            for i in 0..MinI(Length(usedKeyQubits), Length(recycledKeyQubits)) - 1 {
                // Hash-like transformation
                H(usedKeyQubits[i]);
                CNOT(usedKeyQubits[i], recycledKeyQubits[i]);
                H(recycledKeyQubits[i]);
            }
        }
    }

    /// # Summary
    /// Prepare and Measure QKD
    operation PrepareAndMeasureQKD(
        prepareQubits : Qubit[],
        measureQubits : Qubit[],
        basisChoices : Int[],
        keyLength : Int
    ) : (Bool[], Bool[]) {
        mutable aliceKey = [];
        mutable bobKey = [];

        for i in 0..keyLength - 1 {
            // Prepare in random basis
            if basisChoices[i] == 1 {
                H(prepareQubits[i]);
            }

            // Send to Bob
            CNOT(prepareQubits[i], measureQubits[i]);

            // Bob measures in random basis
            if basisChoices[(i + 1) % keyLength] == 1 {
                H(measureQubits[i]);
            }

            let result = M(measureQubits[i]);

            // Sift key
            if basisChoices[i] == basisChoices[(i + 1) % keyLength] {
                set aliceKey += [basisChoices[i] == 1];
                set bobKey += [result == One];
            }
        }

        return (aliceKey, bobKey);
    }

    /// # Summary
    /// Helper: XOR two bit arrays
    function XorArrays(a : Bool[], b : Bool[]) : Bool[] {
        mutable result = [];
        for i in 0..MinI(Length(a), Length(b)) - 1 {
            set result += [a[i] != b[i]];
        }
        return result;
    }
}
