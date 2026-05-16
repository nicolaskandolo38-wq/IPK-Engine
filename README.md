# 🧱 IPK Engine — Strategic Decision Matrix

An operational decision-making matrix and priority framework engineered for optimization, time allocation, and strategic project auditing. This system leverages non-linear scoring and structural breaking laws to eliminate low-yield tasks and accelerate critical assets.

---

## 📐 Mathematical Modeling

The core engine evaluates any task using 5 standard bounded variables to compute a deterministic score, subject to a mathematical breaking condition (piecewise function).

### Variables & Admissible Spaces
* **Domain Weight ($w$):** Structural alignment factor $\implies w \in \{1.0, 1.2, 1.5\}$
* **Utility ($Ut$):** Future systemic ecosystem impact $\implies Ut \in \{1, 5, 10\}$
* **Feasibility ($F$):** Capability & technical stack sum $\implies F \in [0, 10] \cap \mathbb{N}$
* **Urgency ($U$):** Temporal pressure constraint $\implies U \in \{1, 5, 10\}$
* **Time Cost ($T$):** Operational effort / Resource friction $\implies T \in \{1, 5, 10\}$

### The Governing Function
$$IPK = \begin{cases} 0 & \text{if } F < 6 \\ \text{round}\left(\frac{w \cdot Ut \cdot F \cdot U}{T}\right) & \text{if } F \ge 6 \end{cases}$$

### 💥 The Turbo Exception (Non-Linear Overdrive)
To prevent critical strategic bottlenecks from stalling due to heavy time constraints, a logical bypass rule is triggered if and only if:
$$\text{If } Ut = 10 \text{ and } T = 10 \implies T \to 1$$

---

## 📊 Operational Classification Matrix

| Score Range | Zone Classification | Strategic Command & Action |
| :--- | :--- | :--- |
| **$Score \ge 500$** | 🔴 **ZONE ROUGE** | Critical Urgency. Immediate execution within 24h. |
| **$200 \le Score < 500$** | 🔵 **ZONE MAJEURE** | High-Yield Growth Asset. Standard planning. |
| **$50 \le Score < 200$** | ⚪ **ZONE DE FLUX** | Maintenance & Routine. Batch execution. |
| **$0 < Score < 50$** | ⚫ **ZONE DE BRUIT** | Yield Deficit. Total rejection or delegation. |
| **$F < 6$** | 🔕 **INFAISABILITÉ** | Structural Block. Acquire skills or outsource. |

---
*Engineered as a core decision model for high-performance management.*

