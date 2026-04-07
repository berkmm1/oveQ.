namespace QuantumAgentic.Swarm {
    open Microsoft.Quantum.Canon;
    open Microsoft.Quantum.Intrinsic;
    open Microsoft.Quantum.Measurement;
    open Microsoft.Quantum.Arrays;
    open Microsoft.Quantum.Math;
    open Microsoft.Quantum.Convert;
    open Microsoft.Quantum.Random;
    open Microsoft.Quantum.Diagnostics;

    // ============================================
    // QUANTUM SWARM INTELLIGENCE
    // ============================================

    /// # Summary
    /// Particle in quantum swarm
    struct QuantumParticle {
        PositionQubits : Qubit[],
        VelocityQubits : Qubit[],
        PersonalBestQubits : Qubit[],
        FitnessQubits : Qubit[]
    }

    /// # Summary
    /// Swarm configuration
    struct SwarmConfig {
        NumParticles : Int,
        Dimension : Int,
        QubitsPerDimension : Int,
        InertiaWeight : Double,
        CognitiveCoeff : Double,
        SocialCoeff : Double,
        MaxIterations : Int
    }

    /// # Summary
    /// Swarm state
    struct SwarmState {
        Particles : QuantumParticle[],
        GlobalBestQubits : Qubit[],
        GlobalBestFitness : Double
    }

    /// # Summary
    /// Default swarm configuration
    function DefaultSwarmConfig() : SwarmConfig {
        return SwarmConfig(
            NumParticles: 20,
            Dimension: 4,
            QubitsPerDimension: 8,
            InertiaWeight: 0.7,
            CognitiveCoeff: 1.5,
            SocialCoeff: 1.5,
            MaxIterations: 100
        );
    }

    /// # Summary
    /// Initialize quantum swarm
    operation InitializeSwarm(config : SwarmConfig) : SwarmState {
        mutable particles = [];

        for i in 0..config.NumParticles - 1 {
            use positionQubits = Qubit[config.Dimension * config.QubitsPerDimension];
            use velocityQubits = Qubit[config.Dimension * config.QubitsPerDimension];
            use personalBestQubits = Qubit[config.Dimension * config.QubitsPerDimension];
            use fitnessQubits = Qubit[8];

            // Initialize with random superposition
            ApplyToEach(H, positionQubits);
            ApplyToEach(H, velocityQubits);
            ApplyToEach(H, personalBestQubits);

            let particle = QuantumParticle(
                PositionQubits: positionQubits,
                VelocityQubits: velocityQubits,
                PersonalBestQubits: personalBestQubits,
                FitnessQubits: fitnessQubits
            );

            set particles += [particle];
        }

        use globalBestQubits = Qubit[config.Dimension * config.QubitsPerDimension];
        ApplyToEach(H, globalBestQubits);

        return SwarmState(
            Particles: particles,
            GlobalBestQubits: globalBestQubits,
            GlobalBestFitness: 1000000.0
        );
    }

    /// # Summary
    /// Encode position in qubits
    operation EncodePosition(positionQubits : Qubit[], position : Double[]) : Unit {
        let n = Length(positionQubits);
        let d = Length(position);

        for i in 0..MinI(n, d) - 1 {
            let angle = (position[i] + 1.0) / 2.0 * PI();
            Ry(angle, positionQubits[i]);
        }
    }

    /// # Summary
    /// Measure position from qubits
    operation MeasurePosition(positionQubits : Qubit[]) : Double[] {
        mutable position = [];

        for q in positionQubits {
            let result = M(q);
            let value = result == One ? 1.0 | -1.0;
            set position += [value];
        }

        return position;
    }

    /// # Summary
    /// Quantum particle velocity update (PSO-inspired)
    operation UpdateVelocity(
        particle : QuantumParticle,
        globalBestQubits : Qubit[],
        config : SwarmConfig,
        iteration : Int
    ) : Unit {
        let numQubits = Length(particle.VelocityQubits);

        // Decaying inertia weight
        let w = config.InertiaWeight * (1.0 - IntAsDouble(iteration) / IntAsDouble(config.MaxIterations));

        // Cognitive component: move toward personal best
        for i in 0..numQubits - 1 {
            if i < Length(particle.PersonalBestQubits) {
                CNOT(particle.PersonalBestQubits[i], particle.VelocityQubits[i]);
                let cognitiveAngle = config.CognitiveCoeff * 0.1 * PI();
                Ry(cognitiveAngle, particle.VelocityQubits[i]);
            }
        }

        // Social component: move toward global best
        for i in 0..numQubits - 1 {
            if i < Length(globalBestQubits) {
                CNOT(globalBestQubits[i], particle.VelocityQubits[i]);
                let socialAngle = config.SocialCoeff * 0.1 * PI();
                Rz(socialAngle, particle.VelocityQubits[i]);
            }
        }

        // Inertia: maintain current velocity
        for i in 0..numQubits - 1 {
            let inertiaAngle = w * PI() / 4.0;
            Rx(inertiaAngle, particle.VelocityQubits[i]);
        }
    }

    /// # Summary
    /// Quantum particle position update
    operation UpdatePosition(
        particle : QuantumParticle,
        config : SwarmConfig
    ) : Unit {
        let numQubits = Length(particle.PositionQubits);

        for i in 0..numQubits - 1 {
            if i < Length(particle.VelocityQubits) {
                // Position += Velocity (quantum addition via CNOT)
                CNOT(particle.VelocityQubits[i], particle.PositionQubits[i]);

                // Apply boundary constraints
                H(particle.PositionQubits[i]);
                Rz(PI() / 4.0, particle.PositionQubits[i]);
                H(particle.PositionQubits[i]);
            }
        }
    }

    /// # Summary
    /// Evaluate fitness (quantum oracle)
    operation EvaluateFitness(
        positionQubits : Qubit[],
        fitnessQubits : Qubit[],
        objectiveFunction : (Double[] -> Double)
    ) : Double {
        // Measure position
        let position = MeasurePosition(positionQubits);

        // Compute fitness classically (would be quantum in full implementation)
        let fitness = objectiveFunction(position);

        // Encode fitness in qubits
        let fitnessNormalized = fitness / 100.0;  // Normalize
        let angle = fitnessNormalized * PI();

        for q in fitnessQubits {
            Ry(angle, q);
        }

        return fitness;
    }

    /// # Summary
    /// Update personal best
    operation UpdatePersonalBest(
        particle : QuantumParticle,
        currentFitness : Double,
        config : SwarmConfig
    ) : Unit {
        // Measure current fitness from qubits
        mutable storedFitness = 0.0;
        for q in particle.FitnessQubits {
            let result = M(q);
            set storedFitness += result == One ? 1.0 | -1.0;
        }
        set storedFitness = storedFitness / IntAsDouble(Length(particle.FitnessQubits)) * 100.0;

        // If current is better, update personal best
        if currentFitness < storedFitness {
            for i in 0..MinI(Length(particle.PositionQubits), Length(particle.PersonalBestQubits)) - 1 {
                SWAP(particle.PositionQubits[i], particle.PersonalBestQubits[i]);
            }
        }
    }

    /// # Summary
    /// Update global best
    operation UpdateGlobalBest(
        swarm : SwarmState,
        particleIndex : Int,
        particleFitness : Double,
        config : SwarmConfig
    ) : Unit {
        if particleFitness < swarm.GlobalBestFitness {
            // Update global best position
            let particle = swarm.Particles[particleIndex];

            for i in 0..MinI(Length(particle.PersonalBestQubits), Length(swarm.GlobalBestQubits)) - 1 {
                CNOT(particle.PersonalBestQubits[i], swarm.GlobalBestQubits[i]);
            }

            // Would update fitness value in classical register
        }
    }

    /// # Summary
    /// Quantum Ant Colony Optimization (QACO)
    operation QuantumACO(
        pheromoneQubits : Qubit[],
        pathQubits : Qubit[],
        numAnts : Int,
        numIterations : Int,
        evaporationRate : Double
    ) : Int[] {
        mutable bestPath = [];
        mutable bestPathLength = 1000000.0;

        for iteration in 0..numIterations - 1 {
            // Each ant constructs a path
            for ant in 0..numAnts - 1 {
                mutable path = [];
                mutable pathLength = 0.0;

                // Path construction based on pheromone levels
                for step in 0..Length(pathQubits) - 1 {
                    // Measure pheromone to decide next step
                    let pheromoneStrength = M(pheromoneQubits[step % Length(pheromoneQubits)]);

                    if pheromoneStrength == One {
                        set path += [step];
                        set pathLength += 1.0;
                    }
                }

                // Update best path
                if pathLength < bestPathLength {
                    set bestPathLength = pathLength;
                    set bestPath = path;
                }
            }

            // Pheromone evaporation
            for q in pheromoneQubits {
                let evapAngle = evaporationRate * PI() / 4.0;
                Rz(evapAngle, q);
            }

            // Pheromone deposition on best path
            for step in bestPath {
                if step < Length(pheromoneQubits) {
                    let depositAngle = PI() / 8.0;
                    Ry(depositAngle, pheromoneQubits[step]);
                }
            }
        }

        return bestPath;
    }

    /// # Summary
    /// Quantum Firefly Algorithm
    operation QuantumFirefly(
        fireflyQubits : Qubit[],
        attractivenessQubits : Qubit[],
        numFireflies : Int,
        numIterations : Int,
        absorptionCoeff : Double
    ) : Unit {
        for iteration in 0..numIterations - 1 {
            for i in 0..numFireflies - 1 {
                for j in 0..numFireflies - 1 {
                    if i != j {
                        // Compute attractiveness based on distance
                        let distance = IntAsDouble(AbsI(i - j));
                        let attractiveness = Exp(-absorptionCoeff * distance * distance);

                        // Move less attractive firefly toward more attractive one
                        if attractiveness > 0.5 {
                            let moveIdx = i * 4 + (j % 4);
                            if moveIdx < Length(fireflyQubits) {
                                let moveAngle = attractiveness * PI() / 4.0;
                                Ry(moveAngle, fireflyQubits[moveIdx]);
                            }
                        }
                    }
                }
            }
        }
    }

    /// # Summary
    /// Quantum Bee Algorithm
    operation QuantumBeeAlgorithm(
        employedBeeQubits : Qubit[],
        onlookerBeeQubits : Qubit[],
        scoutBeeQubits : Qubit[],
        numIterations : Int,
        limit : Int
    ) : Unit {
        mutable trialCounter = 0;

        for iteration in 0..numIterations - 1 {
            // Employed bees phase: explore neighborhood
            for i in 0..Length(employedBeeQubits) - 1 {
                let exploreAngle = PI() / 8.0;
                Ry(exploreAngle, employedBeeQubits[i]);
            }

            // Onlooker bees phase: select based on fitness
            for i in 0..Length(onlookerBeeQubits) - 1 {
                // Probabilistic selection
                let selectProb = DrawRandomDouble(0.0, 1.0);
                if selectProb > 0.5 {
                    let followAngle = PI() / 6.0;
                    Rz(followAngle, onlookerBeeQubits[i]);
                }
            }

            // Scout bees phase: random exploration
            if trialCounter >= limit {
                for i in 0..Length(scoutBeeQubits) - 1 {
                    H(scoutBeeQubits[i]);
                    set trialCounter = 0;
                }
            }

            set trialCounter += 1;
        }
    }

    /// # Summary
    /// Quantum Bat Algorithm
    operation QuantumBatAlgorithm(
        positionQubits : Qubit[],
        velocityQubits : Qubit[],
        frequencyQubits : Qubit[],
        loudnessQubits : Qubit[],
        pulseRateQubits : Qubit[],
        numIterations : Int
    ) : Unit {
        for iteration in 0..numIterations - 1 {
            for i in 0..Length(positionQubits) - 1 {
                if i < Length(velocityQubits) && i < Length(frequencyQubits) {
                    // Update frequency
                    let freqAngle = DrawRandomDouble(0.0, 0.5) * PI();
                    Ry(freqAngle, frequencyQubits[i]);

                    // Update velocity
                    CNOT(frequencyQubits[i], velocityQubits[i]);

                    // Update position
                    CNOT(velocityQubits[i], positionQubits[i]);

                    // Local search based on loudness
                    if i < Length(loudnessQubits) {
                        let localSearchAngle = PI() / 16.0;
                        Controlled Ry([loudnessQubits[i]], (localSearchAngle, positionQubits[i]));
                    }
                }
            }
        }
    }

    /// # Summary
    /// Quantum Cuckoo Search
    operation QuantumCuckooSearch(
        nestQubits : Qubit[],
        cuckooQubits : Qubit[],
        numNests : Int,
        numIterations : Int,
        pa : Double  // Discovery probability
    ) : Unit {
        for iteration in 0..numIterations - 1 {
            // Generate new cuckoo via Lévy flight (approximated)
            for i in 0..Length(cuckooQubits) - 1 {
                let levyAngle = DrawRandomDouble(0.0, PI());
                Ry(levyAngle, cuckooQubits[i]);
            }

            // Random discovery
            for nest in 0..numNests - 1 {
                let discoveryProb = DrawRandomDouble(0.0, 1.0);
                if discoveryProb < pa {
                    // Replace nest with new random solution
                    let nestIdx = nest * 4;
                    for i in 0..3 {
                        if nestIdx + i < Length(nestQubits) {
                            H(nestQubits[nestIdx + i]);
                        }
                    }
                }
            }
        }
    }

    /// # Summary
    /// Quantum Grey Wolf Optimizer
    operation QuantumGWO(
        wolfQubits : Qubit[],
        alphaQubits : Qubit[],
        betaQubits : Qubit[],
        deltaQubits : Qubit[],
        numIterations : Int
    ) : Unit {
        for iteration in 0..numIterations - 1 {
            // Linearly decreasing parameter a
            let a = 2.0 - IntAsDouble(iteration) * 2.0 / IntAsDouble(numIterations);

            for i in 0..Length(wolfQubits) - 1 {
                // Update position based on alpha, beta, delta
                if i < Length(alphaQubits) {
                    CNOT(alphaQubits[i], wolfQubits[i]);
                    let alphaAngle = a * PI() / 8.0;
                    Ry(alphaAngle, wolfQubits[i]);
                }

                if i < Length(betaQubits) {
                    CNOT(betaQubits[i], wolfQubits[i]);
                    let betaAngle = a * PI() / 12.0;
                    Rz(betaAngle, wolfQubits[i]);
                }

                if i < Length(deltaQubits) {
                    CNOT(deltaQubits[i], wolfQubits[i]);
                    let deltaAngle = a * PI() / 16.0;
                    Rx(deltaAngle, wolfQubits[i]);
                }
            }
        }
    }

    /// # Summary
    /// Quantum Whale Optimization Algorithm
    operation QuantumWOA(
        whaleQubits : Qubit[],
        preyQubits : Qubit[],
        numIterations : Int
    ) : Unit {
        for iteration in 0..numIterations - 1 {
            // Decreasing parameter a
            let a = 2.0 - IntAsDouble(iteration) * 2.0 / IntAsDouble(numIterations);
            let r = DrawRandomDouble(0.0, 1.0);
            let p = DrawRandomDouble(0.0, 1.0);

            for i in 0..Length(whaleQubits) - 1 {
                if p < 0.5 {
                    if AbsD(a) >= 1.0 {
                        // Encircling prey
                        if i < Length(preyQubits) {
                            CNOT(preyQubits[i], whaleQubits[i]);
                            let encircleAngle = a * PI() / 8.0;
                            Ry(encircleAngle, whaleQubits[i]);
                        }
                    } else {
                        // Spiral updating position
                        let spiralAngle = PI() / 4.0;
                        Rz(spiralAngle, whaleQubits[i]);
                    }
                } else {
                    // Search for prey (exploration)
                    H(whaleQubits[i]);
                }
            }
        }
    }

    /// # Summary
    /// Run complete quantum PSO optimization
    operation QuantumPSO(
        objectiveFunction : (Double[] -> Double),
        config : SwarmConfig
    ) : (Double[], Double) {
        // Initialize swarm
        let swarm = InitializeSwarm(config);

        mutable bestPosition = [];
        mutable bestFitness = 1000000.0;

        // Optimization loop
        for iteration in 0..config.MaxIterations - 1 {
            for particleIdx in 0..Length(swarm.Particles) - 1 {
                let particle = swarm.Particles[particleIdx];

                // Update velocity
                UpdateVelocity(particle, swarm.GlobalBestQubits, config, iteration);

                // Update position
                UpdatePosition(particle, config);

                // Evaluate fitness
                let fitness = EvaluateFitness(
                    particle.PositionQubits,
                    particle.FitnessQubits,
                    objectiveFunction
                );

                // Update personal best
                UpdatePersonalBest(particle, fitness, config);

                // Update global best
                UpdateGlobalBest(swarm, particleIdx, fitness, config);

                // Track overall best
                if fitness < bestFitness {
                    set bestFitness = fitness;
                    set bestPosition = MeasurePosition(particle.PositionQubits);
                }
            }
        }

        // Cleanup
        for particle in swarm.Particles {
            ResetAll(particle.PositionQubits);
            ResetAll(particle.VelocityQubits);
            ResetAll(particle.PersonalBestQubits);
            ResetAll(particle.FitnessQubits);
        }
        ResetAll(swarm.GlobalBestQubits);

        return (bestPosition, bestFitness);
    }

    /// # Summary
    /// Helper: Absolute value
    function AbsI(x : Int) : Int {
        return x >= 0 ? x | -x;
    }

    /// # Summary
    /// Helper: Absolute value for Double
    function AbsD(x : Double) : Double {
        return x >= 0.0 ? x | -x;
    }
}
