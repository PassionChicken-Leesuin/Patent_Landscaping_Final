# 도메인 판단 기준서 — Blockchain and Distributed Ledger Technology

## 도메인 정의
Blockchain and Distributed Ledger Technology (DLT) encompasses systems that enable the secure, immutable, and decentralized recording of transactions across a distributed network. These systems must facilitate consensus among distributed nodes to validate transactions without a central authority, ensuring data integrity and preventing unauthorized alterations. They should provide transparency and traceability of transactions to all participants in the network and support the execution of smart contracts, which are self-executing agreements with terms directly written into code.

## 도메인 판단 기준 (C)

- **C1.** The invention must enable the secure and immutable recording of transactions across a distributed network using cryptographic techniques.
  - 근거: https://en.wikipedia.org/wiki/Blockchain, https://en.wikipedia.org/wiki/Distributed_ledger
- **C2.** The invention must facilitate consensus among distributed nodes to validate transactions without a central authority.
  - 근거: https://en.wikipedia.org/wiki/Consensus_(computer_science), https://en.wikipedia.org/wiki/Blockchain
- **C3.** The invention must provide transparency and traceability of transactions to all participants in the network.
  - 근거: https://en.wikipedia.org/wiki/Blockchain, https://en.wikipedia.org/wiki/Distributed_ledger
- **C4.** The invention must ensure data integrity and prevent unauthorized alterations to the ledger.
  - 근거: https://en.wikipedia.org/wiki/Blockchain, https://en.wikipedia.org/wiki/Distributed_ledger
- **C5.** The invention must support the execution of smart contracts, which are self-executing contracts with the terms of the agreement directly written into code.
  - 근거: https://en.wikipedia.org/wiki/Smart_contract, https://en.wikipedia.org/wiki/Blockchain

## 분석 대상 특허의 범위
The scope of analysis for Blockchain and Distributed Ledger Technology includes patents that implement, improve, or provide enabling components or methods specific to blockchain and distributed ledger systems. This encompasses inventions that address the core functionalities of secure, immutable, and decentralized transaction recording, consensus mechanisms, transparency, data integrity, and smart contract execution. Patents that apply these technologies to specific domains, such as finance, supply chain, or identity verification, are also within scope, provided they perform a defining task of the domain.

## 범위 결정 (클러스터별 in/out)

- [IN] **Cryptocurrency transaction systems** — These systems implement blockchain technology to enable secure and decentralized financial transactions, aligning with the domain's core functionalities.
- [IN] **Smart contract applications** — Smart contract applications directly utilize blockchain technology to execute self-executing agreements, fulfilling a defining task of the domain.
- [IN] **Identity authentication mechanisms** — When these mechanisms use blockchain or DLT for decentralized and secure identity verification, they perform a defining task of the domain.
- [IN] **Blockchain-based document processing** — These systems use blockchain to ensure the integrity and traceability of documents, aligning with the domain's core functionalities.
- [IN] **Supply chain integrity** — Supply chain systems using blockchain for transparency and traceability of goods perform a defining task of the domain.
- [CONDITIONAL] **Data privacy protection** — In if the protection mechanism specifically uses blockchain or DLT to ensure data integrity and prevent unauthorized alterations.
- [IN] **Digital asset management** — These systems use blockchain to manage digital assets securely and transparently, aligning with the domain's core functionalities.
- [CONDITIONAL] **Blockchain for energy management** — In if blockchain is used to manage energy transactions or data securely and transparently, performing a defining task of the domain.
- [IN] **Healthcare transaction validation** — These systems use blockchain to validate healthcare transactions securely and transparently, aligning with the domain's core functionalities.
- [IN] **Voting systems** — Voting systems using blockchain for secure and transparent vote recording perform a defining task of the domain.
- [IN] **Peer-to-peer transactions** — These systems use blockchain to facilitate secure and decentralized transactions, aligning with the domain's core functionalities.
- [CONDITIONAL] **Insurance claims processing** — In if the processing specifically uses blockchain to ensure secure and transparent claims handling.
- [IN] **Product provenance tracking** — These systems use blockchain to track product origins and movements securely and transparently, aligning with the domain's core functionalities.

## 제외 기준 (E)

- **E1.** Patents that mention blockchain or DLT but focus on traditional processes without implementing any core functionalities of the domain are excluded.
  - 근거: corpus: suspected_boundary_cases
- **E2.** Patents that use blockchain-like terminology for unrelated fields without performing any defining task of the domain are excluded.
  - 근거: corpus: suspected_boundary_cases

## 경계 판정 지침

- For patents like 'Method and apparatus for claiming insurance benefit,' include only if blockchain is used for secure and transparent claims processing.
- For patents like 'Intelligent water meter system with light wallet,' exclude if blockchain is only mentioned peripherally and not used for core functionalities.
- For patents like 'Secure revisioning auditing system for electronic document files,' include only if blockchain is used for secure and immutable audit logs.
