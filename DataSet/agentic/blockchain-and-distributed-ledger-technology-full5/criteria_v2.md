# 도메인 판단 기준서 — Blockchain and Distributed Ledger Technology

## 도메인 정의
Blockchain and Distributed Ledger Technology (DLT) encompasses systems that enable the secure, immutable recording and sharing of transactions across multiple nodes in a decentralized network. These systems must facilitate consensus mechanisms to validate and agree on the state of the ledger among participants, ensuring data integrity and privacy through cryptographic security. They should support decentralized control, eliminating the need for a central authority, and allow for the execution of smart contracts, which are self-executing agreements with terms directly written into code.

## 도메인 판단 기준 (C)

- **C1.** The invention must enable the secure and immutable recording of transactions across multiple nodes in a decentralized network.
  - 근거: https://en.wikipedia.org/wiki/Blockchain, https://en.wikipedia.org/wiki/Distributed_ledger
- **C2.** The invention must facilitate a consensus mechanism to validate and agree on the state of the ledger among participants.
  - 근거: https://en.wikipedia.org/wiki/Consensus_(computer_science), https://en.wikipedia.org/wiki/Blockchain
- **C3.** The invention must provide mechanisms for cryptographic security to ensure data integrity and privacy.
  - 근거: https://en.wikipedia.org/wiki/Cryptographic_hash_function, https://en.wikipedia.org/wiki/Public-key_cryptography
- **C4.** The invention must support decentralized control, eliminating the need for a central authority.
  - 근거: https://en.wikipedia.org/wiki/Decentralized_computing, https://en.wikipedia.org/wiki/Blockchain
- **C5.** The invention must support the execution of smart contracts, which are self-executing contracts with the terms of the agreement directly written into code.
  - 근거: https://en.wikipedia.org/wiki/Smart_contract, https://en.wikipedia.org/wiki/Ethereum

## 분석 대상 특허의 범위
The scope of analysis for Blockchain and Distributed Ledger Technology includes patents that implement, improve, or provide enabling components or methods specific to blockchain and distributed ledger systems. This encompasses inventions that facilitate secure, decentralized transaction recording, consensus mechanisms, cryptographic security, and smart contract execution. Patents that merely use blockchain outputs or vocabulary for unrelated purposes are excluded.

## 범위 결정 (클러스터별 in/out)

- [IN] **Cryptocurrency transaction systems** — These systems implement blockchain technology to enable secure and decentralized financial transactions.
- [IN] **Smart contract applications** — Smart contracts are a core functionality of blockchain systems, executing agreements autonomously.
- [IN] **Digital identity management** — Digital identity management using blockchain ensures secure and decentralized identity verification.
- [IN] **Data management and privacy** — Data management solutions that leverage blockchain for secure and immutable data storage are included.
- [IN] **Distributed ledger technology** — This cluster directly pertains to the core technology of the domain.
- [IN] **Energy transactions using blockchain** — These applications use blockchain to facilitate secure and decentralized energy trading.
- [IN] **Healthcare transaction validation** — Blockchain is used to securely validate and record healthcare transactions, ensuring data integrity.
- [IN] **Supply chain integrity** — Blockchain enhances supply chain transparency and traceability, aligning with the domain's core tasks.
- [IN] **Voting systems** — Blockchain-based voting systems ensure secure and tamper-proof election processes.
- [IN] **Digital asset management** — Managing digital assets on a blockchain ensures secure and decentralized asset control.
- [IN] **Peer-to-peer transactions** — These transactions utilize blockchain to enable direct, decentralized exchanges between parties.
- [CONDITIONAL] **Insurance claims processing** — In if the blockchain is integral to the claims process, not merely mentioned; otherwise, out.
- [IN] **Product provenance tracking** — Blockchain is used to verify and track the origin and history of products, ensuring authenticity.

## 제외 기준 (E)

- **E1.** Patents that mention blockchain but focus primarily on unrelated fields, such as traditional insurance processes, are excluded.
  - 근거: corpus: suspected_boundary_cases
- **E2.** Patents that use blockchain terminology but do not implement or improve blockchain technology are excluded.
  - 근거: corpus: suspected_boundary_cases

## 경계 판정 지침

- For patents like 'Method and apparatus for claiming insurance benefit,' determine if blockchain is integral to the claims process or merely mentioned.
- For patents like 'Intelligent water meter system with light wallet,' assess whether blockchain is a core component or a peripheral mention.

## 사용자 결정이 필요한 범위 질문

- **Q2. Should patents that mention blockchain peripherally, focusing on other technologies, be included?**
  - 영향: 측정: 풀 표본 60건 중 18건(~30%)의 판정이 넓게/좁게에 따라 갈립니다. This affects the inclusion of patents where blockchain is not the primary focus.
  - 선택지: Include if blockchain is mentioned., Exclude if blockchain is not the primary focus.
  - 현재 가정(미답변 시): Exclude if blockchain is not the primary focus.
- **Q1. Should patents that mention blockchain but focus on traditional insurance processes be included?**
  - 영향: 측정: 풀 표본 60건 중 12건(~20%)의 판정이 넓게/좁게에 따라 갈립니다. This determines whether the domain includes applications where blockchain is not central to the invention.
  - 선택지: Include if blockchain is integral to the process., Exclude if blockchain is merely mentioned.
  - 현재 가정(미답변 시): Exclude if blockchain is merely mentioned.
