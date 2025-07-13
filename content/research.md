## Research Projects

---

### Demand-driven Information Flow Analysis of WebView in Android Hybrid Apps

*WebView encapsulates information flows from Java to JavaScript and vice-versa.*  
In this project, we developed a **demand-driven information flow analysis** for Android hybrid apps.

- **Tool:** [IwanDroid](https://iwandroid.github.io)

---

### Unifying Pointer Analysis for Static Analysis of Multilingual Applications

*Can we combine different program analyses, say, WALA + SVF?*  
We developed an approach to combine existing analyses to analyze multilingual (polyglot) applications.

- **Tool:** _To be published soon_

---

### Understanding Fingerprinting in Hybrid Browsers

*How vulnerable are Android WebViews to fingerprinting?*  
We developed dynamic instrumentation to collect attributes related to fingerprinting in Android WebViews.  
Our study revealed that Android WebViews are **equally or more vulnerable** to fine-grained fingerprinting compared to traditional browsers.

- **Tool:** [Charlie](https://github.com/AliDevel/Charlie)

---

### Program Representation Effects on Pointer Analysis

*Do different intermediate representations affect the outcome of pointer analysis?*  
We created metrics to compare program analyses by isolating the effect of their underlying representations.  
The results showed that such parameters have **little to no effect on precision**, making fair comparisons viable.

- **Tool:** [PointEval](https://github.com/jpksh90/pointeval)

---

### Security Vulnerabilities in Android WebView

*How vulnerable are Android WebViews to JavaScript injection and misuse?*  
We designed a static analysis technique to collect JavaScript passed from Android to WebView.  
Our study showed that such flows are often vulnerable, and sometimes **Java control flow is influenced by external JS APIs.**

- **Tool:** _Available on request_

---

### Points-to Analysis using Push-Down Systems

In this project, we expressed **points-to analysis** as a **push-down system reachability** problem, enabling sound handling of recursive programs.

- **Tool:** [Points2Pds](https://github.com/jpksh90/Points2Pds)

---

> *Note: The tools listed here are research prototypes and should be treated as alpha-quality software.*
