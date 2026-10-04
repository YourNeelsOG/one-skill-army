# Prototype

## OSA execution contract

Read [portable runtime and policy](../references/runtime.md) before acting.
Reuse it once per task unless it changes or context is compacted.



**You own the design decision, not the code. The prototype is a throwaway instrument. The real build follows Feature.**

The one playbook where the Laziness Protocol's "smallest change" and the verification bar invert. Keep polish proportional to a throwaway artifact. Obtain approval for the spike design before building; preserve safety, purpose comments, and an executable check. The rigor is in picking the right design cheaply. Propose variations the user didn't ask for, throw an approach away and try another.

1. Scope the decision the prototype exists to make: which layout, which interaction, which density, or for an empirical fork which behavior, timing, or approach. No decision means no prototype. Route to Feature.
2. Gather references when the design space is open. Search for prior art, summarize a moodboard of themes, palettes, and layouts, let the user pick directions before building. Skip when the direction is set.
3. Build throwaway in an isolated scratch dir, separate from production source. For a visual decision, vanilla HTML/CSS/JS or the lightest stack that renders the idea, CDN deps, a dev server with hot reload. For a behavioral or timing decision, the smallest script that exercises the question. Keep the scratch implementation minimal and isolated. Establish an executable failure predicate before implementation; production work still requires failing-test-first.
4. When comparing alternatives, build them behind one switcher (buttons or a keypress), each variant labeled. This is the **exhaust-the-design-space** principle skill made cheap.
5. Verify on the matching surface. For a visual decision, screenshot each variant via the control skill and drive the interaction. For a behavioral or timing decision, observe the thing you are deciding by logging the timing, printing the output, or watching the render. The observation is the test here, not an assertion.
6. Present alternatives, tradeoffs, and a recommendation. The output is the decision plus the throwaway artifact, not shippable code. Hand the chosen direction to **Feature** (or `architect` for the shape) for the real build.

**Reply:** the variants explored, the evidence (screenshots for a visual decision, the observed output or timing for a behavioral one), tradeoffs, your recommendation, and the scratch path. Say plainly that the prototype is throwaway.
