# 도메인 판단 기준서 — Blockchain and Distributed Ledger Technology

## 도메인 정의
An invention belongs to the domain of Blockchain and Distributed Ledger Technology if it enables the secure, immutable recording and management of transactions or data across a distributed network without a central authority. This includes facilitating consensus among distributed nodes to validate transactions, ensuring data integrity and preventing unauthorized alterations, and supporting the execution of smart contracts. The technology must provide transparency and traceability of transactions to all participants in the network, leveraging cryptographic methods to secure data and consensus algorithms to maintain the ledger's integrity.

## 도메인 판단 기준 (C)

- **C1.** The invention must enable secure and immutable recording of transactions or data across a distributed network.
  - 근거: https://en.wikipedia.org/wiki/Blockchain, https://en.wikipedia.org/wiki/Distributed_ledger
- **C2.** The invention must facilitate consensus among distributed nodes to validate transactions without a central authority.
  - 근거: https://en.wikipedia.org/wiki/Consensus_(computer_science), https://en.wikipedia.org/wiki/Blockchain
- **C3.** The invention must ensure data integrity and prevent unauthorized alterations to the ledger using cryptographic methods.
  - 근거: https://en.wikipedia.org/wiki/Blockchain, https://en.wikipedia.org/wiki/Distributed_ledger
- **C4.** The invention must mention the presence of smart contract functionality, such as self-executing contracts or code-based agreements, in the title or abstract.
  - 근거: https://en.wikipedia.org/wiki/Smart_contract, https://en.wikipedia.org/wiki/Blockchain
- **C5.** The invention must provide transparency and traceability of transactions to all participants in the network.
  - 근거: https://en.wikipedia.org/wiki/Blockchain, https://en.wikipedia.org/wiki/Distributed_ledger
- **C6.** The invention must use consensus algorithms to maintain the ledger's integrity and security.
  - 근거: https://en.wikipedia.org/wiki/Consensus_(computer_science), https://en.wikipedia.org/wiki/Blockchain

## 분석 대상 특허의 범위
The scope of analysis for this domain includes patents that involve the core functionalities of blockchain and distributed ledger technologies, such as secure transaction recording, consensus mechanisms, smart contract execution, and data integrity assurance. It excludes technologies that merely use blockchain outputs or vocabulary without performing these core functions.

## 범위 결정 (클러스터별 in/out)

- [IN] **Blockchain-based systems** — These systems are central to the domain as they involve the core functionalities of blockchain technology, including secure transaction recording and consensus mechanisms.
- [IN] **Cryptocurrency transactions and trading** — Cryptocurrency systems inherently rely on blockchain technology for secure and immutable transaction recording and consensus.
- [OUT] **Data encryption and protection methods** — While encryption is used in blockchain, this cluster focuses on encryption methods generally, not specifically on blockchain or distributed ledger technology.
- [IN] **Smart contracts** — Smart contracts are a defining feature of blockchain technology, enabling self-executing agreements on the blockchain.
- [OUT] **User identity authentication and management** — Unless specifically tied to blockchain or distributed ledger technology, identity management systems do not inherently belong to this domain.
- [IN] **Distributed ledger technology** — This cluster directly pertains to the domain as it encompasses the broader category of technologies that include blockchain.
- [IN] **Asset management in blockchain** — Managing digital assets on a blockchain involves core blockchain functionalities such as secure transaction recording and consensus.
- [OUT] **Electronic settlement systems** — Unless these systems specifically use blockchain or distributed ledger technology, they do not belong to this domain.
- [IN] **Medical record sharing** — Blockchain can be a core component of secure medical record systems, which is a significant application of blockchain technology.
- [OUT] **Secure communication protocols** — This cluster focuses on communication security generally, not specifically on blockchain or distributed ledger technology.

## 제외 기준 (E)

- **E1.** Patents that focus solely on data encryption methods without specific application to blockchain or distributed ledger technology are excluded.
  - 근거: corpus: Data encryption and protection methods
- **E2.** Patents that involve user identity authentication and management without explicit use of blockchain or distributed ledger technology are excluded.
  - 근거: corpus: User identity authentication and management
- **E3.** Patents that describe electronic settlement systems without specific implementation of blockchain or distributed ledger technology are excluded.
  - 근거: corpus: Electronic settlement systems
- **E4.** Patents that describe general distributed systems or non-blockchain-based consensus mechanisms without performing blockchain-specific tasks are excluded.
  - 근거: corpus: Distributed ledger technology

## 경계 판정 지침

- For patents like 'Web application exploit mitigation in an information technology environment,' if the security measures are not specifically tied to blockchain or distributed ledger technology, they should be excluded.
- For 'User identity authentication method and system for discovery service,' unless the method explicitly involves blockchain or distributed ledger technology, it should be excluded.
- For 'Data security service,' if the service does not detail the use of blockchain or distributed ledger technology, it should be excluded.
- For 'Architecture for an extensible real-time collaboration system,' unless blockchain or distributed ledger technology is a core component, it should be excluded.
- For 'Method and system for storing data using a continuous data protection system,' if blockchain or distributed ledger technology is not specifically mentioned, it should be excluded.
- For patents involving advanced consensus mechanisms like DAG and Hashgraph, if they perform similar functions to traditional blockchains, they should be included.
