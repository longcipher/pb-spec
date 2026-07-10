---
name: pb-prototype
description: Build a throwaway prototype to answer a design question — a terminal app for state/logic questions, or several UI variations toggleable from one route. Use when the user wants to sanity-check whether a state model feels right, or explore what a UI should look like.
---

# pb-prototype

A prototype is **throwaway code that answers a question**. The question decides the shape.

## Pick a branch

Identify which question is being answered — from the user's prompt, the surrounding code, or by asking if the user is around:

- **"Does this logic / state model feel right?"** → Logic prototype. Build a tiny interactive terminal app that pushes the state machine through cases that are hard to reason about on paper.
- **"What should this look like?"** → UI prototype. Generate several radically different UI variations on a single route, switchable via a URL search param and a floating bottom bar.

If the question is genuinely ambiguous and the user isn't reachable, default to whichever branch better matches the surrounding code (a backend module → logic; a page or component → UI) and state the assumption.

## Rules that apply to both

1. **Throwaway from day one, and clearly marked as such.** Locate the prototype code close to where it will actually be used. Name it so a casual reader can see it's a prototype, not production.
2. **One command to run.** Whatever the project's existing task runner supports. The user must be able to start it without thinking.
3. **No persistence by default.** State lives in memory. If the question explicitly involves a database, hit a scratch DB or a local file with a clear "PROTOTYPE — wipe me" name.
4. **Skip the polish.** No tests, no error handling beyond what makes the prototype _runnable_, no abstractions. The point is to learn something fast.
5. **Surface the state.** After every action (logic) or on every variant switch (UI), print or render the full relevant state so the user can see what changed.
6. **Capture it when done.** Fold any validated decision into the real code, then capture the prototype as a primary source: commit it to a throwaway branch, out of main, and leave a context pointer to that branch on the implementation issue. Capture the answer too — the verdict and the question it settled — in the issue or a commit.

## Logic Prototype

A tiny interactive terminal app that lets the user drive a state model by hand. Use when the question is about business logic, state transitions, or data shape.

### When this is the right shape

- "I'm not sure if this state machine handles the edge case where X then Y."
- "Does this data model actually let me represent the case where..."
- "I want to feel out what the API should look like before writing it."
- Anything where the user wants to **press buttons and watch state change**.

### Process

1. **State the question.** Before writing code, write down what state model and what question you're prototyping. One paragraph at the top of the file.

2. **Pick the language.** Use whatever the host project uses. Match existing conventions.

3. **Isolate the logic in a portable module.** Put the actual logic behind a small, pure interface that could be lifted out and dropped into the real codebase later. The TUI around it is throwaway; the logic module shouldn't be.

   The right shape depends on the question:
   - **A pure reducer** — `(state, action) => state`. Good when actions are discrete events.
   - **A state machine** — explicit states and transitions. Good when "which actions are legal right now" is part of the question.
   - **A small set of pure functions** over a plain data type. Good when there's no implicit current state.

   Keep it pure: no I/O, no terminal code, no logging for control flow. The TUI imports it and calls into it; nothing flows the other direction.

4. **Build the smallest TUI that exposes the state.** On every action, clear the screen and re-render the full frame: (1) current state, pretty-printed; (2) keyboard shortcuts at the bottom.

5. **Make it runnable in one command.** Add a script to the project's existing task runner.

6. **Hand it over.** Give the user the run command. They'll drive it themselves.

7. **Capture the answer.** Once the prototype has answered its question, capture the answer, then fold the validated logic module into the real code.

### Anti-patterns

- Don't add tests. A prototype that needs tests is no longer a prototype.
- Don't wire it to the real database unless the question is about persistence.
- Don't generalize. No "what if we wanted to support X later."
- Don't blur the logic and the TUI together.

## UI Prototype

Generate several radically different UI variations on a single route, switchable from a floating bottom bar.

### When this is the right shape

- "What should this page look like?"
- "I want to see a few options for this dashboard before committing."
- "Try a different layout for the settings screen."

### Process

1. **State the question and pick N.** Default to **3 variants**. More than 5 stops being radically different.

2. **Generate radically different variants.** Each variant should be structurally different — different layout, different information hierarchy, different primary affordance, not just different colors.

3. **Wire them together.** Create a single switcher component gated by a `?variant=` URL search param.

4. **Build the floating switcher.** A small fixed-position bar at the bottom with left/right arrows and a variant label. Keyboard arrows also cycle.

5. **Hand it over.** Surface the URL. The user flips through.

6. **Capture the answer.** Fold the winner into the real code. Drop the losing variants and the switcher from main.

### Anti-patterns

- Variants that differ only in colour or copy. That's a tweak, not a prototype.
- Sharing too much code between variants. A shared header is fine; a shared layout defeats the point.
- Promoting the prototype directly to production. Rewrite it properly.

## Integration with pb-spec

- **After pb-brainstorming:** When brainstorming surfaces a design question that needs hands-on exploration, use this skill before proceeding to pb-plan.
- **During pb-plan:** If a design decision is hard to resolve on paper, prototype it.
- **Standalone:** Use for any design exploration need.
