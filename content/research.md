## Research

---

## Program Analysis for Polyglot and Hybrid Systems

- **Demand-Driven Information Flow Analysis of WebView in Android Hybrid Apps**  
  `static-analysis` `information-flow` `android` `polyglot`  
    * *WebView encapsulates information flows from Java to JavaScript and vice versa.*  
    * We developed a **demand-driven information flow analysis** for Android hybrid applications that precisely tracks cross-language data flows between Java and JavaScript.  
    * Tool → **IwanDroid**
- **Unifying Pointer Analysis for Static Analysis of Multilingual Applications**  
  `static-analysis` `pointer-analysis` `polyglot` `analysis-integration`  
    * *Can we combine different program analyses, such as WALA and SVF?*  
    * We proposed an approach to unify existing static analyses to analyze **multilingual (polyglot) applications**, enabling consistent reasoning across language boundaries.  
    * Status → *To be published*
- **Toward Program Analysis of N-Language Systems
    * We proposed the challenges in static analysis of N-Language systems that communicate through FFI.

---

## Security and Privacy Analysis of Android WebView

- **Understanding Fingerprinting in Hybrid Browsers**  
  `security` `privacy` `dynamic-analysis` `android`  
    * *How vulnerable are Android WebViews to fingerprinting?*  
    * We developed **dynamic instrumentation** to collect fingerprinting-relevant attributes in Android WebViews. Our study showed that WebViews are **equally or more vulnerable** to fine-grained fingerprinting compared to traditional browsers.  
    * Tool → **Charlie**
- **Security Vulnerabilities in Android WebView**  
  `security` `static-analysis` `android` `webview`  
    * *How vulnerable are Android WebViews to JavaScript injection and misuse?*  
    * We designed a **static analysis technique** to collect JavaScript passed from Android code to WebView. Our results show that such flows are frequently vulnerable, and in some cases **Java control flow is influenced by external JavaScript APIs**.  
    * Availability → *Available on request*

---

## Foundations of Pointer Analysis

- **Program Representation Effects on Pointer Analysis**  
  `pointer-analysis` `program-representation` `empirical-study`  
    * *Do different intermediate representations affect the outcome of pointer analysis?*  
    * We introduced metrics to compare pointer analyses by isolating the impact of their underlying program representations. Results show that such parameters have **little to no effect on precision**, enabling fair and meaningful comparisons.  
    * Tool → **PointEval**
- **Points-to Analysis using Push-Down Systems**  
  `pointer-analysis` `formal-methods` `static-analysis`  
    * We formulated **points-to analysis** as a **push-down system reachability** problem, enabling sound handling of recursion and improved precision for context-sensitive analysis.  
    * Tool → **Points2Pds**

---

**Note:** *All tools listed here are research prototypes and should be treated as alpha-quality software.*
