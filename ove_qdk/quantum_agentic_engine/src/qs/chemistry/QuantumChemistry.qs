// Quantum Chemistry Module
// Molecular simulation and quantum chemistry algorithms
// Part of the Quantum Agentic Loop Engine

namespace QuantumAgenticEngine.Chemistry {
    open Microsoft.Quantum.Canon;
    open Microsoft.Quantum.Intrinsic;
    open Microsoft.Quantum.Math;
    open Microsoft.Quantum.Convert;
    open Microsoft.Quantum.Arrays;
    open Microsoft.Quantum.Measurement;
    open Microsoft.Quantum.Diagnostics;
    open QuantumAgenticEngine.Utils;
    open QuantumAgenticEngine.Algorithms.Simulation;

    // ============================================
    // Molecular Structure Types
    // ============================================

    /// # Summary
    /// Atomic orbital information
    struct AtomicOrbital {
        AtomIndex : Int,
        OrbitalType : String,
        Energy : Double,
        Occupation : Double
    }

    /// # Summary
    /// Molecular geometry
    struct MolecularGeometry {
        AtomTypes : String[],
        Coordinates : Double[][],
        Charge : Int,
        Multiplicity : Int
    }

    /// # Summary
    /// Electronic structure data
    struct ElectronicStructure {
        NumElectrons : Int,
        NumOrbitals : Int,
        OneElectronIntegrals : Double[][],
        TwoElectronIntegrals : Double[][]
    }

    /// # Summary
    /// Basis set definition
    struct BasisSet {
        Name : String,
        ShellTypes : String[],
        Exponents : Double[],
        Coefficients : Double[][],
        ContractionDepths : Int[]
    }

    // ============================================
    // Molecular Hamiltonian Construction
    // ============================================

    /// # Summary
    /// Second-quantized Hamiltonian term
    struct SecondQuantizedTerm {
        Coefficient : Double,
        CreationIndices : Int[],
        AnnihilationIndices : Int[]
    }

    /// # Summary
    /// Molecular Hamiltonian in second quantization
    struct MolecularHamiltonian {
        Terms : SecondQuantizedTerm[],
        NumSpinOrbitals : Int,
        NuclearRepulsion : Double
    }

    /// # Summary
    /// Jordan-Wigner transformation
    operation JordanWignerTransform(
        molecularHamiltonian : MolecularHamiltonian,
        qubits : Qubit[]
    ) : Hamiltonian {
        mutable pauliTerms = new PauliTerm[0];

        for term in molecularHamiltonian.Terms {
            // Transform creation/annihilation operators to Pauli strings
            mutable pauliString = new Pauli[Length(qubits)];
            mutable qubitIndices = new Int[0];

            // For each creation operator
            for cIdx in term.CreationIndices {
                // a^\dagger_i = (X_i - iY_i) / 2 * Z_{<i}
                set pauliString w/= cIdx <- PauliX;
                set qubitIndices += [cIdx];

                // Apply Z string
                for j in 0 .. cIdx - 1 {
                    set pauliString w/= j <- PauliZ;
                }
            }

            // For each annihilation operator
            for aIdx in term.AnnihilationIndices {
                // a_i = (X_i + iY_i) / 2 * Z_{<i}
                set pauliString w/= aIdx <- PauliX;

                // Apply Z string
                for j in 0 .. aIdx - 1 {
                    if pauliString[j] == PauliI {
                        set pauliString w/= j <- PauliZ;
                    }
                }
            }

            // Add term
            let pauliTerm = PauliTerm(
                Coefficient = term.Coefficient,
                PauliString = pauliString,
                QubitIndices = qubitIndices
            );

            set pauliTerms += [pauliTerm];
        }

        return Hamiltonian(
            Terms = pauliTerms,
            NumQubits = Length(qubits),
            TotalCoefficients = 0.0
        );
    }

    /// # Summary
    /// Bravyi-Kitaev transformation
    operation BravyiKitaevTransform(
        molecularHamiltonian : MolecularHamiltonian,
        qubits : Qubit[]
    ) : Hamiltonian {
        mutable pauliTerms = new PauliTerm[0];
        let numOrbitals = molecularHamiltonian.NumSpinOrbitals;

        // BK transformation uses parity and update sets
        for term in molecularHamiltonian.Terms {
            mutable pauliString = new Pauli[Length(qubits)];

            for cIdx in term.CreationIndices {
                // BK: more efficient encoding than JW
                set pauliString w/= cIdx <- PauliX;

                // Update set
                mutable updateIdx = cIdx;
                while updateIdx < numOrbitals {
                    set updateIdx = updateIdx + (updateIdx &&& (-updateIdx));
                    if updateIdx < numOrbitals {
                        set pauliString w/= updateIdx <- PauliZ;
                    }
                }
            }

            for aIdx in term.AnnihilationIndices {
                set pauliString w/= aIdx <- PauliX;

                // Parity set
                mutable parityIdx = aIdx - 1;
                while parityIdx >= 0 {
                    set pauliString w/= parityIdx <- PauliZ;
                    set parityIdx = parityIdx &&& (parityIdx + 1);
                    set parityIdx = parityIdx - 1;
                }
            }

            let pauliTerm = PauliTerm(
                Coefficient = term.Coefficient,
                PauliString = pauliString,
                QubitIndices = term.CreationIndices + term.AnnihilationIndices
            );

            set pauliTerms += [pauliTerm];
        }

        return Hamiltonian(
            Terms = pauliTerms,
            NumQubits = Length(qubits),
            TotalCoefficients = 0.0
        );
    }

    /// # Summary
    /// Parity transformation
    operation ParityTransform(
        molecularHamiltonian : MolecularHamiltonian,
        qubits : Qubit[]
    ) : Hamiltonian {
        mutable pauliTerms = new PauliTerm[0];
        let numOrbitals = molecularHamiltonian.NumSpinOrbitals;

        for term in molecularHamiltonian.Terms {
            mutable pauliString = new Pauli[Length(qubits)];

            // Parity encoding uses fewer qubits
            for cIdx in term.CreationIndices {
                set pauliString w/= cIdx <- PauliX;

                // Flip parity qubits
                for pIdx in 0 .. cIdx {
                    set pauliString w/= pIdx <- PauliZ;
                }
            }

            for aIdx in term.AnnihilationIndices {
                set pauliString w/= aIdx <- PauliX;

                for pIdx in 0 .. aIdx {
                    if pauliString[pIdx] == PauliI {
                        set pauliString w/= pIdx <- PauliZ;
                    }
                }
            }

            let pauliTerm = PauliTerm(
                Coefficient = term.Coefficient,
                PauliString = pauliString,
                QubitIndices = term.CreationIndices + term.AnnihilationIndices
            );

            set pauliTerms += [pauliTerm];
        }

        return Hamiltonian(
            Terms = pauliTerms,
            NumQubits = Length(qubits),
            TotalCoefficients = 0.0
        );
    }

    // ============================================
    // State Preparation
    // ============================================

    /// # Summary
    /// Prepare Hartree-Fock state
    operation PrepareHartreeFockState(
        qubits : Qubit[],
        numElectrons : Int,
        numOrbitals : Int
    ) : Unit {
        // Fill lowest numElectrons/2 orbitals (spin-restricted)
        let numOccupied = numElectrons / 2;

        for i in 0 .. numOccupied - 1 {
            // Occupied spin-up orbital
            if 2 * i < Length(qubits) {
                X(qubits[2 * i]);
            }

            // Occupied spin-down orbital
            if 2 * i + 1 < Length(qubits) {
                X(qubits[2 * i + 1]);
            }
        }
    }

    /// # Summary
    /// Prepare configuration interaction singles (CIS) state
    operation PrepareCISState(
        qubits : Qubit[],
        occupiedOrbitals : Int[],
        virtualOrbitals : Int[],
        excitationAmplitudes : Double[]
    ) : Unit {
        // Start with HF reference
        for occ in occupiedOrbitals {
            if occ < Length(qubits) {
                X(qubits[occ]);
            }
        }

        // Add single excitations
        for i in 0 .. Length(occupiedOrbitals) - 1 {
            for a in 0 .. Length(virtualOrbitals) - 1 {
                let ampIdx = i * Length(virtualOrbitals) + a;
                if ampIdx < Length(excitationAmplitudes) {
                    let amplitude = excitationAmplitudes[ampIdx];

                    // Excitation operator: a^\dagger_a a_i
                    let occIdx = occupiedOrbitals[i];
                    let virIdx = virtualOrbitals[a];

                    if occIdx < Length(qubits) && virIdx < Length(qubits) {
                        // Apply excitation with amplitude
                        Ry(amplitude, qubits[occIdx]);
                        CNOT(qubits[occIdx], qubits[virIdx]);
                        X(qubits[occIdx]);
                    }
                }
            }
        }
    }

    /// # Summary
    /// Prepare unitary coupled cluster state
    operation PrepareUCCSDState(
        qubits : Qubit[],
        occupiedOrbitals : Int[],
        virtualOrbitals : Int[],
        singlesAmplitudes : Double[],
        doublesAmplitudes : Double[]
    ) : Unit {
        // Reference state
        for occ in occupiedOrbitals {
            if occ < Length(qubits) {
                X(qubits[occ]);
            }
        }

        // Singles: t_i^a (a^\dagger_a a_i - h.c.)
        for i in 0 .. Length(occupiedOrbitals) - 1 {
            for a in 0 .. Length(virtualOrbitals) - 1 {
                let ampIdx = i * Length(virtualOrbitals) + a;
                if ampIdx < Length(singlesAmplitudes) {
                    let t = singlesAmplitudes[ampIdx];
                    let occ = occupiedOrbitals[i];
                    let vir = virtualOrbitals[a];

                    if occ < Length(qubits) && vir < Length(qubits) {
                        // Excitation operator
                        Ry(t, qubits[occ]);
                        CNOT(qubits[occ], qubits[vir]);
                        X(qubits[occ]);
                    }
                }
            }
        }

        // Doubles: t_ij^ab (a^\dagger_a a^\dagger_b a_j a_i - h.c.)
        for i in 0 .. Length(occupiedOrbitals) - 1 {
            for j in i + 1 .. Length(occupiedOrbitals) - 1 {
                for a in 0 .. Length(virtualOrbitals) - 1 {
                    for b in a + 1 .. Length(virtualOrbitals) - 1 {
                        let idx = i * Length(occupiedOrbitals) * Length(virtualOrbitals) * Length(virtualOrbitals) +
                                  j * Length(virtualOrbitals) * Length(virtualOrbitals) +
                                  a * Length(virtualOrbitals) + b;

                        if idx < Length(doublesAmplitudes) {
                            let t = doublesAmplitudes[idx];
                            let occ1 = occupiedOrbitals[i];
                            let occ2 = occupiedOrbitals[j];
                            let vir1 = virtualOrbitals[a];
                            let vir2 = virtualOrbitals[b];

                            if occ1 < Length(qubits) && occ2 < Length(qubits) &&
                               vir1 < Length(qubits) && vir2 < Length(qubits) {
                                // Double excitation
                                Ry(t, qubits[occ1]);
                                CNOT(qubits[occ1], qubits[occ2]);
                                CNOT(qubits[occ2], qubits[vir1]);
                                CNOT(qubits[vir1], qubits[vir2]);
                                X(qubits[occ1]);
                                X(qubits[occ2]);
                            }
                        }
                    }
                }
            }
        }
    }

    /// # Summary
    /// Prepare adiabatic state based on molecular Hamiltonian
    operation PrepareAdiabaticGroundState(
        molecularHamiltonian : MolecularHamiltonian,
        qubits : Qubit[],
        evolutionTime : Double,
        numSteps : Int
    ) : Unit {
        // Initial Hamiltonian: sum of X operators
        let numOrbitals = molecularHamiltonian.NumSpinOrbitals;

        // Start in uniform superposition
        ApplyToEach(H, qubits);

        // Adiabatic evolution
        let dt = evolutionTime / IntAsDouble(numSteps);

        for step in 0 .. numSteps - 1 {
            let s = IntAsDouble(step) / IntAsDouble(numSteps);

            // Decrease initial Hamiltonian contribution
            for q in qubits {
                Rx(-2.0 * (1.0 - s) * dt, q);
            }

            // Increase molecular Hamiltonian contribution
            for term in molecularHamiltonian.Terms {
                mutable termQubits = new Qubit[0];
                for idx in term.CreationIndices + term.AnnihilationIndices {
                    if idx < Length(qubits) {
                        set termQubits += [qubits[idx]];
                    }
                }

                // Simplified: apply as rotation
                for q in termQubits {
                    Rz(-2.0 * term.Coefficient * s * dt, q);
                }
            }
        }
    }

    // ============================================
    // Energy Measurement
    // ============================================

    /// # Summary
    /// Measure molecular energy using phase estimation
    operation MeasureMolecularEnergyQPE(
        molecularHamiltonian : MolecularHamiltonian,
        stateQubits : Qubit[],
        precisionQubits : Qubit[]
    ) : Double {
        // Transform to Pauli Hamiltonian
        let pauliHamiltonian = JordanWignerTransform(molecularHamiltonian, stateQubits);

        // Initialize precision register
        ApplyToEach(H, precisionQubits);

        // Controlled time evolution
        let numPrecision = Length(precisionQubits);

        for i in 0 .. numPrecision - 1 {
            let power = 1 <<< i;
            let time = IntAsDouble(power) * PI() / 2.0;

            // Controlled evolution
            for term in pauliHamiltonian.Terms {
                mutable termQubits = new Qubit[0];
                for idx in term.QubitIndices {
                    if idx < Length(stateQubits) {
                        set termQubits += [stateQubits[idx]];
                    }
                }

                let angle = -2.0 * term.Coefficient * time;
                Controlled Exp([precisionQubits[i]], (term.PauliString, angle, termQubits));
            }
        }

        // Inverse QFT
        Adjoint QFT(precisionQubits);

        // Measure energy
        mutable energy = 0.0;
        for i in 0 .. numPrecision - 1 {
            let bit = M(precisionQubits[i]);
            if bit == One {
                set energy += 1.0 / IntAsDouble(1 <<< (numPrecision - i - 1));
            }
        }

        // Add nuclear repulsion
        set energy += molecularHamiltonian.NuclearRepulsion;

        return energy;
    }

    /// # Summary
    /// Measure energy using variational approach
    operation MeasureVariationalEnergy(
        molecularHamiltonian : MolecularHamiltonian,
        ansatzQubits : Qubit[],
        ansatzParameters : Double[],
        numShots : Int
    ) : Double {
        // Prepare variational ansatz
        for i in 0 .. Length(ansatzQubits) - 1 {
            if i < Length(ansatzParameters) {
                Ry(ansatzParameters[i], ansatzQubits[i]);
            }
        }

        // Entangle
        for i in 0 .. Length(ansatzQubits) - 2 {
            CNOT(ansatzQubits[i], ansatzQubits[i + 1]);
        }

        // Transform to Pauli Hamiltonian
        let pauliHamiltonian = JordanWignerTransform(molecularHamiltonian, ansatzQubits);

        // Measure energy
        mutable totalEnergy = 0.0;

        for _ in 0 .. numShots - 1 {
            for term in pauliHamiltonian.Terms {
                // Change basis
                for i in 0 .. Length(term.PauliString) - 1 {
                    if i < Length(ansatzQubits) {
                        if term.PauliString[i] == PauliX {
                            H(ansatzQubits[i]);
                        } elif term.PauliString[i] == PauliY {
                            Rx(PI() / 2.0, ansatzQubits[i]);
                        }
                    }
                }

                // Measure
                mutable parity = 1.0;
                for q in ansatzQubits {
                    let result = M(q);
                    if result == One {
                        set parity *= -1.0;
                    }
                }

                set totalEnergy += term.Coefficient * parity;
            }
        }

        let avgEnergy = totalEnergy / IntAsDouble(numShots);

        // Add nuclear repulsion
        return avgEnergy + molecularHamiltonian.NuclearRepulsion;
    }

    // ============================================
    // Property Calculations
    // ============================================

    /// # Summary
    /// Calculate dipole moment
    operation CalculateDipoleMoment(
        stateQubits : Qubit[],
        dipoleIntegrals : Double[],
        numShots : Int
    ) : Double[] {
        mutable dipoleX = 0.0;
        mutable dipoleY = 0.0;
        mutable dipoleZ = 0.0;

        for _ in 0 .. numShots - 1 {
            // Measure x component
            for i in 0 .. Min(Length(stateQubits), Length(dipoleIntegrals) / 3) - 1 {
                let result = M(stateQubits[i]);
                let value = result == One ? 1.0 | -1.0;
                dipoleX += value * dipoleIntegrals[i];
            }

            // Measure y component
            for i in 0 .. Min(Length(stateQubits), Length(dipoleIntegrals) / 3) - 1 {
                let idx = Length(dipoleIntegrals) / 3 + i;
                if idx < Length(dipoleIntegrals) {
                    let result = M(stateQubits[i]);
                    let value = result == One ? 1.0 | -1.0;
                    dipoleY += value * dipoleIntegrals[idx];
                }
            }

            // Measure z component
            for i in 0 .. Min(Length(stateQubits), Length(dipoleIntegrals) / 3) - 1 {
                let idx = 2 * Length(dipoleIntegrals) / 3 + i;
                if idx < Length(dipoleIntegrals) {
                    let result = M(stateQubits[i]);
                    let value = result == One ? 1.0 | -1.0;
                    dipoleZ += value * dipoleIntegrals[idx];
                }
            }
        }

        let scale = 1.0 / IntAsDouble(numShots);
        return [dipoleX * scale, dipoleY * scale, dipoleZ * scale];
    }

    /// # Summary
    /// Calculate forces on nuclei
    operation CalculateForces(
        geometry : MolecularGeometry,
        stateQubits : Qubit[],
        gradientIntegrals : Double[],
        numShots : Int
    ) : Double[][] {
        let numAtoms = Length(geometry.AtomTypes);
        mutable forces = new Double[][numAtoms];

        for atomIdx in 0 .. numAtoms - 1 {
            mutable forceX = 0.0;
            mutable forceY = 0.0;
            mutable forceZ = 0.0;

            for _ in 0 .. numShots - 1 {
                // Hellmann-Feynman theorem approximation
                for i in 0 .. Length(stateQubits) - 1 {
                    let gradIdx = atomIdx * 3 * Length(stateQubits) + i;
                    if gradIdx < Length(gradientIntegrals) {
                        let result = M(stateQubits[i]);
                        let value = result == One ? 1.0 | -1.0;
                        forceX += value * gradientIntegrals[gradIdx];
                    }
                }
            }

            let scale = 1.0 / IntAsDouble(numShots);
            set forces w/= atomIdx <- [forceX * scale, forceY * scale, forceZ * scale];
        }

        return forces;
    }

    /// # Summary
    /// Calculate vibrational frequencies
    operation CalculateVibrationalFrequencies(
        hessianMatrix : Double[][],
        atomicMasses : Double[]
    ) : Double[] {
        let numModes = Length(hessianMatrix);
        mutable frequencies = new Double[numModes];

        // Mass-weighted Hessian
        for i in 0 .. numModes - 1 {
            for j in 0 .. numModes - 1 {
                let massI = i / 3 < Length(atomicMasses) ? atomicMasses[i / 3] | 1.0;
                let massJ = j / 3 < Length(atomicMasses) ? atomicMasses[j / 3] | 1.0;

                // Simplified: diagonal elements give frequencies
                if i == j {
                    let freq = Sqrt(AbsD(hessianMatrix[i][j]) / (massI * massJ));
                    set frequencies w/= i <- freq;
                }
            }
        }

        return frequencies;
    }

    // ============================================
    // Specific Molecule Calculations
    // ============================================

    /// # Summary
    /// Hydrogen molecule (H2) calculation
    operation HydrogenMoleculeVQE(
        qubits : Qubit[],
        bondLength : Double,
        numIterations : Int
    ) : Double {
        // STO-3G basis H2 Hamiltonian parameters (simplified)
        let h11 = -1.2525;
        let h22 = -0.4759;
        let h12 = -0.4759;
        let g1111 = 0.6746;
        let g2222 = 0.6974;
        let g1122 = 0.6636;
        let g1212 = 0.1813;

        // Nuclear repulsion
        let nuclearRepulsion = 1.0 / bondLength;

        // VQE ansatz parameters
        mutable theta = 0.0;
        mutable minEnergy = 1000.0;

        for iter in 0 .. numIterations - 1 {
            // Parameterized ansatz
            Ry(theta, qubits[0]);
            CNOT(qubits[0], qubits[1]);
            Ry(-theta, qubits[1]);

            // Measure energy (simplified)
            mutable energy = nuclearRepulsion;

            let result0 = M(qubits[0]);
            let result1 = M(qubits[1]);

            if result0 == Zero && result1 == Zero {
                set energy += 2.0 * h11 + g1111;
            } elif result0 == One && result1 == One {
                set energy += 2.0 * h22 + g2222;
            } else {
                set energy += h11 + h22 + h12 + g1122;
            }

            if energy < minEnergy {
                set minEnergy = energy;
            }

            // Update parameter (gradient descent)
            set theta += 0.1;
        }

        return minEnergy;
    }

    /// # Summary
    /// Water molecule (H2O) calculation setup
    operation WaterMoleculeSetup(
        qubits : Qubit[]
    ) : MolecularHamiltonian {
        // H2O in minimal basis has 7 orbitals (1s O, 2s O, 2px O, 2py O, 2pz O, 1s H1, 1s H2)
        let numOrbitals = 7;
        let numElectrons = 10;

        // Simplified Hamiltonian terms
        mutable terms = new SecondQuantizedTerm[0];

        // Core Hamiltonian (one-electron terms)
        let coreIntegrals = [-20.0, -1.0, -0.5, -0.5, -0.5, -1.0, -1.0];
        for i in 0 .. numOrbitals - 1 {
            let term = SecondQuantizedTerm(
                Coefficient = coreIntegrals[i],
                CreationIndices = [i],
                AnnihilationIndices = [i]
            );
            set terms += [term];
        }

        // Two-electron terms (simplified)
        for i in 0 .. numOrbitals - 1 {
            for j in 0 .. numOrbitals - 1 {
                let term = SecondQuantizedTerm(
                    Coefficient = 0.5,
                    CreationIndices = [i, j],
                    AnnihilationIndices = [j, i]
                );
                set terms += [term];
            }
        }

        return MolecularHamiltonian(
            Terms = terms,
            NumSpinOrbitals = 2 * numOrbitals,
            NuclearRepulsion = 8.0
        );
    }

    /// # Summary
    /// Lithium hydride (LiH) calculation
    operation LithiumHydrideCalculation(
        qubits : Qubit[],
        bondLength : Double
    ) : Double {
        // LiH has 4 electrons in minimal basis
        // Simplified Hamiltonian

        // Prepare HF state
        X(qubits[0]);
        X(qubits[1]);
        X(qubits[2]);
        X(qubits[3]);

        // UCCSD ansatz (simplified)
        let t1 = 0.1;
        let t2 = 0.05;

        Ry(t1, qubits[0]);
        CNOT(qubits[0], qubits[4]);
        X(qubits[0]);

        Ry(t2, qubits[1]);
        CNOT(qubits[1], qubits[5]);
        X(qubits[1]);

        // Measure energy
        mutable energy = 0.0;
        for q in qubits {
            let result = M(q);
            if result == One {
                set energy -= 1.0;
            }
        }

        // Nuclear repulsion
        let nuclearRepulsion = 3.0 / bondLength;

        return energy + nuclearRepulsion;
    }
}
