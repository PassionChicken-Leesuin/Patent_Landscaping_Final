# 도메인 판단 기준서 — Blockchain and Distributed Ledger Technology

## 도메인 정의
An invention belongs to the domain of Blockchain and Distributed Ledger Technology if it enables the secure, immutable recording and management of transactions or data across a distributed network without a central authority. It must facilitate consensus mechanisms to validate and agree on the state of the ledger among participants, provide cryptographic security to ensure data integrity and privacy, and support decentralized control. Additionally, the technology should allow for the execution of smart contracts, which are self-executing contracts with terms directly written into code.

## 도메인 판단 기준 (C)

- **C1.** The invention must enable the secure and immutable recording of transactions or data across a distributed network.
  - 근거: corpus: definition, https://en.wikipedia.org/wiki/Blockchain
- **C2.** The invention must facilitate a consensus mechanism to validate and agree on the state of the ledger among participants.
  - 근거: corpus: definition, https://en.wikipedia.org/wiki/Consensus_(computer_science)
- **C3.** The invention must provide cryptographic security to ensure data integrity and privacy.
  - 근거: corpus: definition, https://en.wikipedia.org/wiki/Cryptography
- **C4.** The invention must support decentralized control, eliminating the need for a central authority.
  - 근거: corpus: definition, https://en.wikipedia.org/wiki/Decentralized_computing
- **C5.** The invention must support the execution of smart contracts, which are self-executing contracts with terms directly written into code.
  - 근거: corpus: definition, https://en.wikipedia.org/wiki/Smart_contract
- **C6.** The invention must claim to use blockchain or distributed ledger technology for identity authentication, ensuring it manages identity data securely and immutably, as stated in the title or abstract.
  - 근거: corpus: definition, https://en.wikipedia.org/wiki/Blockchain

## 분석 대상 특허의 범위
Patents within the scope of Blockchain and Distributed Ledger Technology include those that perform tasks related to the secure, decentralized management of transactions or data using distributed ledger systems. This includes technologies that implement consensus mechanisms, cryptographic security, and smart contracts. Patents that merely use blockchain or distributed ledger outputs for unrelated purposes, or that focus on traditional processes with peripheral mentions of blockchain, are outside the scope.

## 범위 결정 (클러스터별 in/out)

- [IN] **Cryptocurrency transaction systems** — These systems perform the core task of managing transactions securely and immutably across a distributed network.
- [IN] **Smart contract applications** — These applications directly involve the execution of smart contracts, a defining task of the domain.
- [CONDITIONAL] **Identity authentication mechanisms** — In if the mechanism uses blockchain or distributed ledger technology to manage identity data securely and immutably; out if it merely uses blockchain terminology without performing these tasks.
- [IN] **Digital asset management** — These systems manage digital assets using distributed ledger technology, aligning with the domain's core tasks.
- [IN] **Blockchain-based document processing** — These systems use blockchain to securely and immutably manage document data, fitting the domain's definition.
- [IN] **Supply chain integrity** — These systems use blockchain to ensure the secure and immutable tracking of supply chain data.
- [CONDITIONAL] **Data privacy protection** — In if the protection is achieved through blockchain's cryptographic and decentralized features; out if it uses blockchain terminology without these features.
- [IN] **Energy transactions** — These systems use distributed ledger technology to manage energy transactions securely and immutably.
- [IN] **Healthcare transaction validation** — These systems use blockchain to validate healthcare transactions securely and immutably.
- [IN] **Voting systems** — These systems use blockchain to manage voting data securely and immutably, fitting the domain's core tasks.
- [IN] **Peer-to-peer transactions** — These systems facilitate secure and immutable peer-to-peer transactions using distributed ledger technology.
- [OUT] **Insurance claims processing** — These patents focus on traditional insurance processes with peripheral mentions of blockchain, not performing the domain's core tasks.
- [IN] **Product provenance tracking** — These systems use blockchain to track product provenance securely and immutably, aligning with the domain's core tasks.
- [CONDITIONAL] **DApps** — In if the DApp uses blockchain for decentralized operations and smart contract execution; out if it merely uses blockchain terminology without performing these tasks.

## 제외 기준 (E)

- **E1.** Patents that focus on traditional processes with peripheral mentions of blockchain or distributed ledger technology are excluded.
  - 근거: corpus: boundary_case, patent-pool digest
- **E2.** Patents that use blockchain or distributed ledger outputs for unrelated purposes without performing the domain's core tasks are excluded.
  - 근거: corpus: boundary_case, patent-pool digest
- **E3.** Patents that appear to use blockchain but are fundamentally traditional databases or centralized systems, without performing blockchain's core tasks, are excluded.
  - 근거: corpus: boundary_case, patent-pool digest

## 경계 판정 지침

- For patents like 'Intelligent water meter system with light wallet', focus on whether the blockchain component performs a core task such as secure transaction management. If not, rule out.
- For patents such as 'Method for Providing Asynchronous Reverse Direction Payment by using Sound Signal Device and Blockchain', assess if the blockchain component is central to the payment processing. If it is peripheral, rule out.
- For 'Secure revisioning auditing system for electronic document files', determine if the blockchain-like audit logs perform secure and immutable data management. If not, rule out.
- For identity authentication mechanisms, assess if they use blockchain or distributed ledger technology to manage identity data securely and immutably. If not, rule out.
- For patents like 'Electric power mobile terminal identity authentication mechanism based on block chain', determine if the blockchain component is essential for secure and immutable identity data management. If not, rule out.
