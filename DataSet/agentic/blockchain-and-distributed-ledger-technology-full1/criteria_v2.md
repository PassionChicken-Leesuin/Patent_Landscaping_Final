# 도메인 판단 기준서 — Blockchain and Distributed Ledger Technology

## 도메인 정의
An invention belongs to the domain of Blockchain and Distributed Ledger Technology if it enables the secure, immutable recording and management of transactions or data across a distributed network without a central authority, using cryptographic techniques and consensus mechanisms to ensure data integrity, privacy, and decentralized control. It may also facilitate the execution of smart contracts, which are automated, self-executing agreements with terms directly written into code, and support decentralized applications (DApps) that operate on such networks.

## 도메인 판단 기준 (C)

- **C1.** The invention must facilitate the secure and immutable recording of transactions or data across a distributed network.
  - 근거: https://en.wikipedia.org/wiki/Blockchain, https://www.investopedia.com/terms/b/blockchain.asp
- **C2.** The invention must use cryptographic techniques to ensure data integrity and privacy.
  - 근거: https://en.wikipedia.org/wiki/Cryptographic_hash_function, https://www.investopedia.com/terms/c/cryptography.asp
- **C3.** The invention must employ a consensus mechanism, such as proof-of-work or proof-of-stake, to validate transactions or data entries without a central authority.
  - 근거: https://en.wikipedia.org/wiki/Consensus_(computer_science), https://www.investopedia.com/terms/c/consensus-mechanism.asp
- **C4.** The invention must support or facilitate the execution of smart contracts on a distributed ledger.
  - 근거: https://en.wikipedia.org/wiki/Smart_contract, https://www.investopedia.com/terms/s/smart-contracts.asp
- **C5.** The invention must enable decentralized storage and retrieval of data across multiple nodes.
  - 근거: https://en.wikipedia.org/wiki/Distributed_ledger, https://www.investopedia.com/terms/d/distributed-ledger-technology-dlt.asp

## 분석 대상 특허의 범위
The scope of analysis for this domain includes patents that focus on the core functionalities of blockchain and distributed ledger technologies, such as secure transaction recording, consensus mechanisms, cryptographic security, smart contracts, and decentralized applications. It excludes patents where blockchain is merely a secondary feature or where the primary focus is on unrelated technologies or applications that do not leverage the unique capabilities of blockchain or distributed ledgers.

## 범위 결정 (클러스터별 in/out)

- [IN] **cryptocurrency transaction systems** — These systems are core applications of blockchain technology, focusing on secure and decentralized transaction recording.
- [IN] **smart contract applications** — Smart contracts are a fundamental aspect of blockchain technology, enabling automated and secure execution of agreements.
- [IN] **identity authentication mechanisms** — When these mechanisms leverage blockchain's unique capabilities for decentralized and secure identity verification, they fall within the domain.
- [IN] **data management using blockchain** — This involves using blockchain for secure and decentralized data storage and retrieval, aligning with the domain's core functionalities.
- [IN] **digital asset management** — Managing digital assets securely and immutably on a blockchain is a primary use case of the technology.
- [IN] **secure payment methods** — If these methods utilize blockchain for secure and decentralized transaction processing, they are within scope.
- [IN] **distributed ledger technology** — This is the overarching technology category that includes blockchain and its applications.
- [IN] **blockchain-based document processing** — Using blockchain for secure and immutable document processing aligns with the domain's core functionalities.
- [IN] **energy management using blockchain** — While not emphasized in web evidence, using blockchain for decentralized energy management is a valid application of the technology.
- [IN] **supply chain provenance** — Blockchain's ability to provide secure and transparent tracking of goods in a supply chain is a recognized application.

## 제외 기준 (E)

- **E1.** Patents that mention blockchain but focus on traditional centralized databases or non-blockchain-based encryption systems are excluded.
  - 근거: corpus: Secure revisioning auditing system for electronic document files
- **E2.** Patents where blockchain is a secondary feature in applications like insurance claims or water metering are excluded.
  - 근거: corpus: Method and apparatus for claiming insurance benefit
- **E3.** Patents related to voting or communication systems that do not leverage blockchain's unique capabilities are excluded.
  - 근거: corpus: Method for providing secret electronic voting service on the basis of blockchain

## 경계 판정 지침

- For patents like 'Method and apparatus for claiming insurance benefit', if blockchain is merely a secondary feature and not central to the invention's purpose, it should be excluded.
- Patents such as 'Secure revisioning auditing system for electronic document files' should be excluded if they do not clearly leverage blockchain's unique capabilities for secure and decentralized data management.
- In cases like 'Method for providing secret electronic voting service on the basis of blockchain', if the primary focus is not on blockchain's unique functionalities, the patent should be excluded.
- For identity verification or authentication patents, if they do not utilize blockchain's decentralized and secure features, they should be excluded.
