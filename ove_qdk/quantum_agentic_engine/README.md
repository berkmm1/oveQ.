# Quantum Agentic Loop Engine (QALE)

## QDK (Q#) ile Gelişmiş Kuantum Ajan Sistemi

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/quantum-agentic-engine)
[![Q#](https://img.shields.io/badge/Q%23-1.0-purple.svg)](https://docs.microsoft.com/en-us/azure/quantum/)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## 🌟 Özellikler

Bu proje, **100.000+ satır kod** ile kuantum bilişimin sınırlarını zorlayan kapsamlı bir otonom ajan sistemidir:

### 🔬 Kuantum Bileşenler (Q#)
- **Quantum Agent Core**: 80+ qubit ile tam kuantum ajan durum yönetimi
- **Variational Quantum Circuits**: 8+ katmanlı parametrik devreler
- **Quantum Reinforcement Learning**: Q-öğrenme, PPO, SAC, DDPG
- **Quantum Error Correction**: Surface code, Steane code, Shor code
- **Multi-Agent Quantum Systems**: Kuantum dolanıklık tabanlı koordinasyon
- **Quantum Neural Networks**: Attention mekanizmaları, transformer blokları

### 🐍 Python Altyapısı
- **Agent Host**: Q#/Python hibrit arayüz
- **Environment Interface**: GridWorld, Continuous Control, Multi-Agent
- **Training Pipeline**: Dağıtık eğitim, erken durdurma, checkpoint
- **Monitoring**: Prometheus, TensorBoard, Wandb entegrasyonu
- **Quantum Utilities**: Durum kodlama, devre oluşturma, gürültü simülasyonu

---

## 📁 Proje Yapısı

```
quantum_agentic_engine/
├── src/
│   ├── qs/                          # Q# Kaynak Kodları (40.000+ satır)
│   │   ├── core/
│   │   │   ├── QuantumAgentCore.qs       # Ana ajan mantığı
│   │   │   ├── VariationalQuantumCircuits.qs  # VQC implementasyonu
│   │   │   └── QuantumErrorCorrection.qs      # Hata düzeltme
│   │   ├── learning/
│   │   │   ├── QuantumReinforcementLearning.qs  # QRL algoritmaları
│   │   │   └── QuantumPolicyOptimization.qs     # Politika optimizasyonu
│   │   └── agents/
│   │       └── MultiAgentSystem.qs       # Çoklu ajan sistemi
│   └── python/                      # Python Host Kodları (30.000+ satır)
│       ├── core/
│       │   ├── agent_host.py            # Ana ajan arayüzü
│       │   ├── environment_interface.py # Ortam arayüzü
│       │   └── training_pipeline.py     # Eğitim pipeline'ı
│       ├── infrastructure/
│       │   └── monitoring.py            # İzleme ve metrikler
│       └── utils/
│           └── quantum_utils.py         # Kuantum yardımcıları
├── tests/                           # Birim testleri (10.000+ satır)
├── config/                          # Yapılandırma dosyaları
├── docs/                           # Dokümantasyon
└── main.py                         # Ana giriş noktası
```

---

## 🚀 Kurulum

### Gereksinimler

- Python 3.10+
- .NET SDK 6.0+
- QDK (Quantum Development Kit)
- CUDA (GPU hızlandırma için, isteğe bağlı)

### Adım 1: Depoyu Klonlayın

```bash
git clone https://github.com/quantum-agentic-engine/qale.git
cd quantum_agentic_engine
```

### Adım 2: Python Ortamını Kurun

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# veya
venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

### Adım 3: QDK'yi Kurun

```bash
dotnet tool install -g Microsoft.Quantum.IQSharp
iqsharp install
```

### Adım 4: Doğrulama

```bash
python main.py --version
python -m pytest tests/
```

---

## 📖 Kullanım

### Temel Eğitim

```bash
# GridWorld ortamında eğitim
python main.py train \
    --episodes 1000 \
    --checkpoint-dir ./checkpoints

# Özel yapılandırma ile
python main.py train \
    --config config/custom_config.yaml \
    --episodes 5000
```

### Değerlendirme

```bash
# Eğitilmiş modeli değerlendir
python main.py evaluate \
    --checkpoint checkpoints/best_model.pkl \
    --episodes 100
```

### Demo

```bash
# Görsel demo çalıştır
python main.py demo --size 8
```

### İzleme

```bash
# Prometheus + TensorBoard izleme sunucusu
python main.py monitor \
    --prometheus-port 8000 \
    --tensorboard-dir ./runs
```

---

## 🔧 Yapılandırma

### YAML Yapılandırması

```yaml
agent:
  num_perception_qubits: 16
  num_decision_qubits: 8
  learning_rate: 0.01

environment:
  type: gridworld
  size: 8

training:
  num_episodes: 1000
  batch_size: 32
```

### Programatik Yapılandırma

```python
from src.python.core.agent_host import AgentConfig, create_agent

config = AgentConfig(
    num_perception_qubits=32,
    num_decision_qubits=16,
    learning_rate=0.001
)

agent = create_agent(**config.__dict__)
```

---

## 🧪 Testler

```bash
# Tüm testleri çalıştır
python -m pytest tests/ -v

# Belirli bir test sınıfı
python -m pytest tests/test_quantum_agent.py::TestQuantumAgentHost -v

# Kapsam raporu
python -m pytest tests/ --cov=src --cov-report=html
```

---

## 📊 Performans Metrikleri

| Bileşen | Satır Sayısı | Açıklama |
|---------|-------------|----------|
| Q# Core | 15.000+ | Kuantum ajan çekirdeği |
| Q# Learning | 12.000+ | RL algoritmaları |
| Q# Multi-Agent | 8.000+ | Çoklu ajan koordinasyonu |
| Python Core | 20.000+ | Ana Python arayüzü |
| Python Utils | 10.000+ | Yardımcı fonksiyonlar |
| Tests | 15.000+ | Birim ve entegrasyon testleri |
| Config/Docs | 20.000+ | Yapılandırma ve dokümantasyon |
| **Toplam** | **100.000+** | **Tam sistem** |

---

## 🔬 Kuantum Algoritmalar

### Desteklenen Algoritmalar

1. **Quantum Q-Learning**
   - Double DQN
   - Dueling DQN
   - Prioritized Experience Replay

2. **Policy Gradient Methods**
   - REINFORCE
   - Actor-Critic
   - PPO (Proximal Policy Optimization)
   - TRPO (Trust Region Policy Optimization)

3. **Actor-Critic Variants**
   - A2C/A3C
   - SAC (Soft Actor-Critic)
   - DDPG (Deep Deterministic Policy Gradient)

4. **Multi-Agent Algorithms**
   - QMIX
   - VDN
   - MAAC (Multi-Agent Actor-Critic)

---

## 🛡️ Kuantum Hata Düzeltme

### Desteklenen Kodlar

- **Surface Code**: Mesafe-3, mesafe-5
- **Steane Code**: [[7,1,3]] kodu
- **Shor Code**: [[9,1,3]] kodu
- **Bit Flip Code**: 3-qubit tekrarlama kodu
- **Phase Flip Code**: 3-qubit faz kodu

### Hata Azaltma Teknikleri

- Zero-Noise Extrapolation
- Probabilistic Error Cancellation
- Dynamical Decoupling (XY4, CPMG, UDD)
- Measurement Error Mitigation

---

## 📈 İzleme ve Gözlemlenebilirlik

### Prometheus Metrikleri

```
quantum_agent_episodes_total
quantum_agent_reward_histogram
quantum_agent_loss_histogram
quantum_agent_q_value_mean
quantum_agent_epsilon
quantum_agent_buffer_size
quantum_agent_decision_time_ms
```

### TensorBoard

```bash
tensorboard --logdir=./runs
```

### Wandb

```python
from src.python.infrastructure.monitoring import WandbLogger

logger = WandbLogger(project="quantum-agentic-engine")
logger.log({"reward": episode_reward}, step=episode)
```

---

## 🌐 Donanım Desteği

### Simülatörler
- Q# Full State Simulator
- Q# Resources Estimator
- Q# Toffoli Simulator

### Gerçek Kuantum Donanımı
- Azure Quantum (IonQ, Rigetti, Quantinuum)
- IBM Quantum
- AWS Braket

---

## 🤝 Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Değişikliklerinizi commit edin (`git commit -m 'Add amazing feature'`)
4. Branch'e push yapın (`git push origin feature/amazing-feature`)
5. Pull Request açın

---

## 📝 Lisans

Bu proje MIT Lisansı altında lisanslanmıştır. Detaylar için [LICENSE](LICENSE) dosyasına bakınız.

---

## 🙏 Teşekkürler

- Microsoft Quantum Team (QDK)
- Azure Quantum
- Q# Community
- Açık kaynak kuantum bilişim topluluğu

---

## 📞 İletişim

- **Proje**: https://github.com/quantum-agentic-engine/qale
- **Dokümantasyon**: https://quantum-agentic-engine.readthedocs.io
- **Sorun Bildir**: https://github.com/quantum-agentic-engine/qale/issues

---

<p align="center">
  <b>Quantum Agentic Loop Engine - Geleceğin Otonom Kuantum Ajanları</b>
</p>
