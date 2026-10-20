# OpenSource Navigator AI — 3-Minute Hackathon Demo Script

**Target Audience:** Hacktoberfest Hack Day Pune × NIAT–ADYPU Judges & Hackathon Attendees  
**Category:** Best Open-Source AI Project  
**Presenter:** Swapnil Ghuge & OpenSource Navigator AI Team  
**Estimated Time:** ~3 minutes  

---

## [0:00 - 0:30] Hook & Problem Statement

**Action:** Open browser to `http://localhost:3000`. Point to the top bar showing the live **Ollama** status pill and **OpenSource Navigator AI** header.

> **Speaker:**  
> "Good evening judges and fellow open-source builders! Every Hacktoberfest, thousands of students and junior developers want to contribute to open-source software, but they face a daunting wall of complexity: unfamiliar codebases, cryptic issue descriptions, and fear of asking 'dumb' questions.
>
> We built **OpenSource Navigator AI** — your AI guide to your very first open-source contribution, powered 100% locally by open-weight AI models."

---

## [0:30 - 1:15] Step 1 & 2: Real GitHub Issue Discovery & Inspection

**Action:**
1. In the **Discover Issues** tab, show the live search bar and filter controls.
2. Click the quick filter chip `Python` and `#good first issue`.
3. Highlight that the issues shown are **real, live GitHub issues** (excluding PRs) pulled straight from the GitHub REST API.
4. Click the `GitHub` link on one issue to briefly preview the real issue on GitHub.com in a new tab.

> **Speaker:**  
> "Here on our discovery dashboard, we query the official GitHub Search API in real time. We automatically filter out noisy pull requests, support debounced search across languages like Python, TypeScript, and Rust, and filter for beginner labels like `good first issue`.
>
> Notice this real issue right here. Instead of leaving a beginner guessing what to do next, we click **'Analyze with AI'**."

---

## [1:15 - 2:00] Step 3: Local Open-Weight AI Analysis

**Action:**
1. Click **Analyze with AI** on the selected issue.
2. Watch the analysis screen generate the structured guide.
3. Walk through the generated cards:
   - Plain-English Summary (jargon-free)
   - Estimated Contributor Difficulty (`Beginner` / `Intermediate`) with rationale
   - Possible Skills required (badges)
   - Step-by-step Investigation Plan
   - Suggested Inspection Areas (labeled explicitly as *Hypotheses*)
   - Testing strategy & Maintainer questions

> **Speaker:**  
> "Under the hood, our FastAPI backend dispatches the issue text to our local **Ollama** engine running an open-weight model (`deepseek-r1:8b` / `qwen3:4b`). No paid APIs, no privacy leaks.
>
> Notice the AI doesn't just hallucinate — it decomposes the issue into a plain-English explanation for students, gives an honest difficulty assessment, outlines an investigation plan, and explicitly flags suspected files as hypotheses since we haven't cloned the repo yet."

---

## [2:00 - 2:30] Step 4: Interactive Contribution Roadmap

**Action:**
1. Click the **Create Contribution Plan** button.
2. The UI transitions smoothly to the **My Contribution Plans** tab.
3. Show the dynamic progress bar (0%).
4. Check off the first two preparation tasks (e.g. *'Fork repository'* and *'Verify CONTRIBUTING.md'*).
5. Watch the progress bar instantly update.
6. Change status from `Not Started` to `In Progress`.

> **Speaker:**  
> "With one click, we turn that AI breakdown into an actionable **Contribution Roadmap**.
>
> Stored locally in the browser, the student gets a structured checklist: setup, investigation, implementation, testing, and a final pull-request checklist. As they make progress, they tick off items and see their confidence and readiness grow."

---

## [2:30 - 3:00] Step 5: Architecture, Open-Source Value & Conclusion

**Action:** Switch to the **About the Project** tab, highlighting the System Architecture and Security posturing.

> **Speaker:**  
> "Architecturally, OpenSource Navigator AI uses Next.js with Tailwind on the frontend, FastAPI and Pydantic on the backend, and local Ollama inference. We follow strict security guardrails: untrusted issue text is sanitized, zero secrets are ever leaked or sent to the browser, and no destructive unattended actions are performed.
>
> By democratizing open-source discovery with local open-weight AI, we're helping the next generation of engineers make meaningful contributions to the global open-source ecosystem.
>
> Thank you, and we welcome your questions!"
