## Research & Publications

My work sits under four themes. Most papers cross-cut more than one of them — each publication below is labeled with every theme it belongs to.

- 🔀 **Cross-Language Program Analysis** `cross-language` — This is my core research theme: reasoning about programs that span multiple languages and runtimes joined by mechanisms such as FFI, JNI, and embedded WebViews, where single-language tools stop short at the language boundary. My **IwanDroid** tool performs demand-driven information-flow analysis across the Java–JavaScript boundary inside Android WebViews, tracking flows precisely in both directions. To generalize beyond a single language pair, I have proposed an approach for unifying independent static analyses — such as WALA and SVF — so that multilingual (polyglot) applications can be reasoned about consistently across language boundaries, and I am investigating the open challenges of analyzing N-language systems that communicate through foreign function interfaces.

- 🔒 **Cross-Language Security & Privacy Analysis** `security-privacy` — Applying cross-language analysis to security-critical Android hybrid apps, where the Java–JavaScript boundary inside WebView is a recurring source of vulnerabilities and privacy leaks. Using dynamic instrumentation, my **Charlie** tool collects fingerprinting-relevant attributes from Android WebViews, and our study found WebViews to be equally or more vulnerable to fine-grained fingerprinting than traditional browsers. On the static side, I designed an analysis that collects JavaScript passed from Android code into WebView, showing that such flows are frequently vulnerable and that in some cases Java control flow is influenced by external JavaScript APIs.

- 👉 **Foundations of Program Analysis** `program-analysis` — The foundations underlying my analyses. My **PointEval** tool introduces metrics for isolating the effect of a program's intermediate representation on pointer-analysis outcomes, showing that such representational choices have little to no effect on precision and enabling fairer comparisons between analyses. On the formal side, **Points2Pds** formulates points-to analysis as a push-down-system reachability problem, giving sound handling of recursion and improved precision for context-sensitive analysis.

- 🧪 **Testing of Static Analyzers** `analyzer-testing` — Turning the analysis lens onto the analysers themselves: testing that static analyses tools behave soundly and that their reported results are reproducible. This is an emerging direction for me, currently reflected in three filed patents (titles undisclosed under NDA) on testing static analyzers with AI and on detecting non-deterministically reported vulnerabilities.

---

### 📄 Publications

- **JetTyped: A Study of Cross-Language Type Bugs in Android's JavaScriptEngine** [<i class="fa-solid fa-file-pdf" aria-hidden="true"></i>](assests/jettyped-issre-2026.pdf)<br>
  `cross-language`<br>
  Abhishek Tiwari, Jyoti Prakash, Dimitrios Dafnis, Mikkel Baun Kjærgaard<br>
  *34th IEEE International Symposium on Software Reliability Engineering (ISSRE'26)*

- **Sentry: Towards a Cross-Language Dynamic Analysis Framework for Hybrid Android Applications** [<i class="fa-solid fa-file-pdf" aria-hidden="true"></i>]()<br>
  `cross-language` `security-privacy`<br>
  Jyoti Prakash, Abhishek Tiwari, Mikkel Baun Kjærgaard<br>
  *Second International Workshop on Software Security Testing (SECUTE@ASE 2026)*

- **Towards Analyzing N-language Polyglot Programs** [<i class="fa-solid fa-file-pdf" aria-hidden="true"></i>](https://arxiv.org/abs/2602.00303)<br>
  `cross-language`<br>
  Jyoti Prakash, Abhishek Tiwari, Mikkel Baun Kjærgaard<br>
  *33rd IEEE International Conference on Software Analysis, Evolution and Reengineering*

- **Modular Unification of Unilingual Pointer Analyses to Multilingual FFI-based Programs** [<i class="fa-solid fa-file-pdf" aria-hidden="true"></i>](https://www.sciencedirect.com/science/article/pii/S0167642325000176)<br>
  `cross-language` `program-analysis`<br>
  Jyoti Prakash, Abhishek Tiwari, Christian Hammer<br>
  *Science of Computer Programming 243*<br>
  Journal First Track @ SANER'26

- **Automated Repair of Information Flow Security in Android Implicit Inter-App Communication** [<i class="fa-solid fa-file-pdf" aria-hidden="true"></i>](https://link.springer.com/chapter/10.1007/978-3-031-71162-6_15)<br>
  `security-privacy` `program-analysis`<br>
  *Abhishek Tiwari*, Jyoti Prakash, Zhen Dong, Carlo A. Furia<br>
  *26th IEEE International Symposium on Formal Methods (FM'24)*

- **Demand-driven Information Flow Analysis of WebView in Android Hybrid Apps** [<i class="fa-solid fa-file-pdf" aria-hidden="true"></i>](https://arxiv.org/pdf/2305.03916)<br>
  `cross-language` `security-privacy`<br>
  *Abhishek Tiwari*, *Jyoti Prakash*, Christian Hammer<br>
  *34th IEEE International Symposium on Software Reliability Engineering (ISSRE'23)*

- **Understanding the Impact of Fingerprinting in Android Hybrid Apps** [<i class="fa-solid fa-file-pdf" aria-hidden="true"></i>](assests/charlie.pdf)<br>
  `security-privacy`<br>
  *Abhishek Tiwari*, *Jyoti Prakash*, Alimerdan Rahimov, Christian Hammer<br>
  *MobileSoft'23 (co-located with ICSE'23)*<br>
  🏅 **ACM SIGSOFT Distinguished Paper Award**

- **Effects of Program Representation on Pointer Analyses — An Empirical Study** [<i class="fa-solid fa-file-pdf" aria-hidden="true"></i>](assests/pointeval.pdf)<br>
  `program-analysis`<br>
  Jyoti Prakash, Abhishek Tiwari, Christian Hammer<br>
  *24th International Conference on Fundamental Approaches to Software Engineering (FASE'21)*

- **A Large Scale Analysis of Android–Web Hybridization** [<i class="fa-solid fa-file-pdf" aria-hidden="true"></i>](assests/ludroid-journal.pdf)<br>
  `cross-language`<br>
  Abhishek Tiwari, Jyoti Prakash, Sascha Groß, Christian Hammer<br>
  *Journal of Systems and Software 170*

- **A Large Scale Analysis of Android–Web Hybridization** [<i class="fa-solid fa-file-pdf" aria-hidden="true"></i>](assests/ludroid.pdf)<br>
  `cross-language`<br>
  Abhishek Tiwari, Jyoti Prakash, Sascha Groß, Christian Hammer<br>
  *19th International Working Conference on Source Code Analysis and Manipulation (SCAM'2019)*

**Note:** *All tools mentioned above are research prototypes and should be treated as alpha-quality software.*

---

### 🎤 Talks

- **Building Trust in Open-Ended Software Systems: From Static Analysis to LLM Assurance**<br>
  `analyzer-testing`<br>
  AI Conference @ ExxonMobil, Bangalore

- **Demand-driven Information Flow Analysis of WebView in Android Hybrid Apps**<br>
  `cross-language` `security-privacy`<br>
  Research Highlights in Programming Languages @ FSTTCS'2024 (IIT Gandhinagar)

- **On the Soundness of Pointer Analyses**<br>
  `program-analysis`<br>
  The MathWorks, Bangalore

---

### 📘 Thesis

- **Static Analyses of Interlanguage Interoperations** [Dissertation <i class="fa-solid fa-file-pdf" aria-hidden="true"></i>](assests/thesis.pdf) · [Slides](assests/DisputationSlidesPublic.pdf)<br>
  `cross-language`<br>
  Jyoti Prakash<br>
  University of Passau, Germany (2024)

- **Points-to Analysis for Java using Push-Down Systems**<br>
  `program-analysis`<br>
  Jyoti Prakash<br>
  Master's Thesis, Saarland University (2017)

---
